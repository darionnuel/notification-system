import {
  Injectable,
  Logger,
  OnModuleInit,
  OnModuleDestroy,
} from '@nestjs/common';
import * as amqp from 'amqplib';
import { v4 as uuidv4 } from 'uuid';
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
    const url = process.env.RABBITMQ_URL || 'amqp://guest:guest@localhost:5672';

    try {
      this.logger.log(`🔌 Connecting to RabbitMQ at ${url}...`);
      
      const connection = await amqp.connect(url);
      this.connection = connection;
      this.channel = await this.connection.createConfirmChannel();

      // 1. Create main exchange (DIRECT type as per task.md)
      await this.channel.assertExchange(EXCHANGE, 'direct', { durable: true });
      this.logger.log(`✅ Exchange created: ${EXCHANGE} (type: direct)`);

      // 2. Create Dead Letter Queue (failed.queue as per task.md)
      await this.channel.assertQueue('failed.queue', {
        durable: true,
        arguments: {
          'x-message-ttl': 86400000, // 24 hours in ms
          'x-max-length': 10000, // Max 10k messages
        },
      });
      this.logger.log(`✅ Dead Letter Queue created: failed.queue`);

      // 3. Create Email Queue with DLQ configuration
      await this.channel.assertQueue('email.queue', {
        durable: true,
        arguments: {
          'x-dead-letter-exchange': EXCHANGE,
          'x-dead-letter-routing-key': 'failed',
          'x-message-ttl': 3600000, // 1 hour
          'x-max-priority': 10, // Enable priority
        },
      });
      this.logger.log(`✅ Email queue created: email.queue`);

      // 4. Create Push Queue with DLQ configuration
      await this.channel.assertQueue('push.queue', {
        durable: true,
        arguments: {
          'x-dead-letter-exchange': EXCHANGE,
          'x-dead-letter-routing-key': 'failed',
          'x-message-ttl': 3600000, // 1 hour
          'x-max-priority': 10, // Enable priority
        },
      });
      this.logger.log(`✅ Push queue created: push.queue`);

      // 5. Bind queues to exchange (as per task.md structure)
      await Promise.all([
        this.channel.bindQueue('email.queue', exchange, 'email'),
        this.channel.bindQueue('push.queue', exchange, 'push'),
        this.channel.bindQueue('failed.queue', exchange, 'failed'),
      ]);
      this.logger.log(`✅ Queue bindings configured`);

      this.logger.log(
        `🚀 RabbitMQ initialized successfully | Exchange: ${EXCHANGE}`,
      );
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

    try {
      const payload = Buffer.from(JSON.stringify(message));
      const priority = typeof message.priority === 'number' ? message.priority : 5;

      await new Promise<void>((resolve, reject) => {
        this.channel!.publish(
          EXCHANGE,
          routingKey,
          payload,
          {
            persistent: true,
            priority, // Support message priority
            contentType: 'application/json',
            contentEncoding: 'utf-8',
            timestamp: Date.now(),
            messageId: message.notification_id || uuidv4(),
            correlationId: message.correlation_id || message.request_id,
          },
          (err?: Error | null) => {
            if (err) {
              this.logger.error(
                `Failed to publish message to ${routingKey}: ${err.message}`,
              );
              return reject(err);
            }
            resolve();
          },
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

      const correlationId =
        typeof message.request_id === 'string' ? message.request_id : 'n/a';
      const notificationId =
        typeof message.notification_id === 'string'
          ? message.notification_id
          : 'n/a';

    return new Promise<void>((resolve, reject) => {
      this.pendingPublishes.push({
        routingKey,
        payload,
        options,
        resolve,
        reject,
      });
      this.logger.log(
        `📨 Published | Queue: ${routingKey} | ID: ${notificationId} | Priority: ${priority}`,
      );
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : JSON.stringify(err);
      this.logger.error(`❌ RabbitMQ publish failed: ${errorMsg}`);
      throw new Error(`RabbitMQ publish failed: ${errorMsg}`);
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
