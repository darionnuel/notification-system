import {
  Injectable,
  Logger,
  OnModuleInit,
  OnModuleDestroy,
} from '@nestjs/common';
import * as amqp from 'amqplib';
import { v4 as uuidv4 } from 'uuid';
import { EXCHANGE } from '../../shared/constants';

@Injectable()
export class RabbitmqService implements OnModuleInit, OnModuleDestroy {
  private connection: amqp.Connection;
  private channel: amqp.ConfirmChannel;
  private readonly logger = new Logger(RabbitmqService.name);

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
        this.channel.bindQueue('email.queue', EXCHANGE, 'email'),
        this.channel.bindQueue('push.queue', EXCHANGE, 'push'),
        this.channel.bindQueue('failed.queue', EXCHANGE, 'failed'),
      ]);
      this.logger.log(`✅ Queue bindings configured`);

      this.logger.log(
        `🚀 RabbitMQ initialized successfully | Exchange: ${EXCHANGE}`,
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : JSON.stringify(err);
      this.logger.error(`❌ Failed to initialize RabbitMQ: ${message}`);
      throw new Error(`RabbitMQ initialization failed: ${message}`);
    }
  }

  async publish(
    routingKey: string,
    message: Record<string, any>,
  ): Promise<void> {
    if (!this.channel) {
      throw new Error('RabbitMQ channel not initialized');
    }

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
      });

      const correlationId =
        typeof message.request_id === 'string' ? message.request_id : 'n/a';
      const notificationId =
        typeof message.notification_id === 'string'
          ? message.notification_id
          : 'n/a';

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
      if (this.channel) await this.channel.close();
      if (this.connection) await this.connection.close();
      this.logger.log('🔌 RabbitMQ connection closed gracefully');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : JSON.stringify(err);
      this.logger.warn(`⚠️ RabbitMQ cleanup failed: ${message}`);
    }
  }
}
