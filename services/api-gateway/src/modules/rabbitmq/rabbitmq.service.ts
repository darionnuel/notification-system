import {
  Injectable,
  Logger,
  OnModuleInit,
  OnModuleDestroy,
} from '@nestjs/common';
import * as amqp from 'amqplib';
import { EXCHANGE } from '../../shared/constants';

type PendingPublish = {
  routingKey: string;
  payload: Buffer;
  options?: amqp.Options.Publish;
  resolve: () => void;
  reject: (err: any) => void;
};

@Injectable()
export class RabbitmqService implements OnModuleInit, OnModuleDestroy {
  private connection: amqp.Connection;
  private channel: amqp.ConfirmChannel;
  private readonly logger = new Logger(RabbitmqService.name);

  // Backoff state
  private reconnectAttempts = 0;
  private reconnectTimer?: NodeJS.Timeout;

  // Simple in-memory buffer for publishes while reconnecting.
  // Keep this small to avoid OOM in extreme failure scenarios.
  private pendingPublishes: PendingPublish[] = [];
  private readonly maxPending = 500;
  private connected = false;

  isConnected(): boolean {
    return this.connected;
  }

  private getRabbitUrl(): string {
    // prefer env var RABBITMQ_URL; fallback to default exchange hostless config
    return process.env.RABBITMQ_URL || 'amqp://guest:guest@localhost:5672';
  }

  async onModuleInit(): Promise<void> {
    await this.connectWithRetry();
  }

  private async connectWithRetry(): Promise<void> {
    const attempt = this.reconnectAttempts + 1;
    const url = this.getRabbitUrl();
    const exchange =
      process.env.RABBITMQ_EXCHANGE || EXCHANGE || 'notifications.direct';

    try {
      this.logger.log(
        `Attempting RabbitMQ connection to ${url} (attempt ${attempt})`,
      );
      this.connection = await amqp.connect(url);

      this.connected = true;

      this.connection.on('error', (err) => {
        const msg = err instanceof Error ? err.message : String(err);
        this.logger.warn(`RabbitMQ connection error: ${msg}`);

        this.connected = false;
      });

      this.connection.on('close', () => {
        this.logger.warn('RabbitMQ connection closed — scheduling reconnect');

        this.connected = false;

        this.safeClearChannelAndConnection();
        this.scheduleReconnect();
      });

      this.channel = await this.connection.createConfirmChannel();

      // Ensure exchange & queues exist and are bound.
      await this.channel.assertExchange(exchange, 'direct', { durable: true });

      await Promise.all([
        this.channel.assertQueue('email.queue', { durable: true }),
        this.channel.assertQueue('push.queue', { durable: true }),
        this.channel.assertQueue('failed.queue', { durable: true }),
      ]);

      // use the same `exchange` variable for binds
      await Promise.all([
        this.channel.bindQueue('email.queue', exchange, 'email'),
        this.channel.bindQueue('push.queue', exchange, 'push'),
        this.channel.bindQueue('failed.queue', exchange, 'failed'),
      ]);

      this.logger.log(
        `✅ RabbitMQ connected and exchange/assertions done (exchange=${exchange})`,
      );

      // reset reconnect attempts and flush any buffered publishes
      this.reconnectAttempts = 0;
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = undefined;
      }

      // Flush pending publishes
      this.flushPendingPublishes(exchange).catch((e) => {
        this.logger.warn(
          'Failed flushing pending publishes: ' +
            (e instanceof Error ? e.message : String(e)),
        );
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      this.logger.warn(`RabbitMQ connect failed: ${msg}`);

      this.connected = false;

      this.reconnectAttempts += 1;
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return; // already scheduled
    // exponential backoff with cap
    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000);
    this.logger.log(
      `Scheduling RabbitMQ reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`,
    );
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = undefined;
      this.connectWithRetry().catch((e) =>
        this.logger.warn(
          'Reconnect attempt failed: ' +
            (e instanceof Error ? e.message : String(e)),
        ),
      );
    }, delay);
  }

  private safeClearChannelAndConnection() {
    this.channel = null;
    this.connection = null;
  }

  /**
   * Publish a message. If the channel is not available the message will be buffered
   * (up to `maxPending`) and flushed when the connection is restored.
   *
   * @param routingKey 'email' | 'push' | etc.
   * @param message POJO or Buffer (if POJO it will be JSON.stringified)
   * @param options amqp publish options
   */
  async publish(
    routingKey: string,
    message: Record<string, any>,
    options?: amqp.Options.Publish,
  ): Promise<void> {
    const payload = Buffer.isBuffer(message)
      ? message
      : Buffer.from(JSON.stringify(message));
    const exchange =
      process.env.RABBITMQ_EXCHANGE || EXCHANGE || 'notifications.direct';

    // If channel is available, attempt immediate publish with confirms
    if (this.channel) {
      try {
        await this.publishOnChannel(exchange, routingKey, payload, options);
        const correlationId =
          typeof (message as any).request_id === 'string'
            ? (message as any).request_id
            : 'n/a';
        this.logger.log(
          `📨 Published message routing_key=${routingKey} correlation_id=${correlationId}`,
        );
        return;
      } catch (err: unknown) {
        // If immediate publish fails, fall through to buffering behavior
        this.logger.warn(
          'Immediate publish failed, will buffer message: ' +
            (err instanceof Error ? err.message : String(err)),
        );
      }
    }

    // Buffer the publish for later flush
    if (this.pendingPublishes.length >= this.maxPending) {
      const errMsg = 'Pending publish queue full';
      this.logger.error(errMsg);
      throw new Error(errMsg);
    }

    return new Promise<void>((resolve, reject) => {
      this.pendingPublishes.push({
        routingKey,
        payload,
        options,
        resolve,
        reject,
      });
      this.logger.log(
        `Buffered message routing_key=${routingKey} pending_count=${this.pendingPublishes.length}`,
      );
    });
  }

  private async publishOnChannel(
    exchange: string,
    routingKey: string,
    payload: Buffer,
    options?: amqp.Options.Publish,
  ): Promise<void> {
    if (!this.channel) throw new Error('RabbitMQ channel not available');

    // Use confirm channel pattern: publish + waitForConfirms()
    const published = this.channel.publish(exchange, routingKey, payload, {
      persistent: true,
      ...options,
    });

    // Even if publish returns true/false, we should wait for confirm
    await this.channel.waitForConfirms();
    if (!published) {
      // not fatal — just log. confirm ensures broker accepted it.
      this.logger.debug(
        `publishOnChannel: publish returned ${published} for ${routingKey}`,
      );
    }
  }

  private async flushPendingPublishes(exchange: string) {
    if (!this.channel) return;
    if (this.pendingPublishes.length === 0) return;

    this.logger.log(
      `Flushing ${this.pendingPublishes.length} buffered messages...`,
    );
    const toFlush = this.pendingPublishes.splice(
      0,
      this.pendingPublishes.length,
    );
    for (const item of toFlush) {
      try {
        await this.publishOnChannel(
          exchange,
          item.routingKey,
          item.payload,
          item.options,
        );
        item.resolve();
        this.logger.log(
          `Flushed buffered message routing_key=${item.routingKey}`,
        );
      } catch (err) {
        item.reject(err);
        this.logger.warn(
          `Failed to flush buffered message routing_key=${item.routingKey}: ${err instanceof Error ? err.message : String(err)}`,
        );
      }
    }
  }

  async onModuleDestroy(): Promise<void> {
    try {
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = undefined;
      }

      // attempt to close channel & connection gracefully
      if (this.channel) {
        try {
          await this.channel.close();
        } catch (e) {
          this.logger.warn(
            'Error closing RabbitMQ channel: ' +
              (e instanceof Error ? e.message : String(e)),
          );
        }
        this.channel = null;
      }

      if (this.connection) {
        try {
          await this.connection.close();
        } catch (e) {
          this.logger.warn(
            'Error closing RabbitMQ connection: ' +
              (e instanceof Error ? e.message : String(e)),
          );
        }
        this.connection = null;
      }

      // reject any pending publishes to avoid unresolved promises on shutdown
      while (this.pendingPublishes.length) {
        const p = this.pendingPublishes.shift();
        p?.reject(new Error('Service shutting down; publish cancelled'));
      }

      this.logger.log('🔌 RabbitMQ connection closed gracefully');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : JSON.stringify(err);
      this.logger.warn(`⚠️ RabbitMQ cleanup failed: ${message}`);
    }
  }
}
