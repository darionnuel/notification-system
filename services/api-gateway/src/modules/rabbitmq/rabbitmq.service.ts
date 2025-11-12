import {
  Injectable,
  Logger,
  OnModuleInit,
  OnModuleDestroy,
} from '@nestjs/common';
import * as amqp from 'amqplib';
import { EXCHANGE } from '../../shared/constants';

@Injectable()
export class RabbitmqService implements OnModuleInit, OnModuleDestroy {
  private connection: amqp.Connection;
  private channel: amqp.ConfirmChannel;
  private readonly logger = new Logger(RabbitmqService.name);

  async onModuleInit(): Promise<void> {
    const url = process.env.RABBITMQ_URL || 'amqp://guest:guest@rabbitmq:5672';

    try {
      const connection = await amqp.connect(url);
      this.connection = connection;
      this.channel = await this.connection.createConfirmChannel();
      await this.channel.assertExchange(EXCHANGE, 'direct', { durable: true });

      // assert queues so they exist
      await Promise.all([
        this.channel.assertQueue('email.queue', { durable: true }),
        this.channel.assertQueue('push.queue', { durable: true }),
        this.channel.assertQueue('failed.queue', { durable: true }),
      ]);

      await Promise.all([
        this.channel.bindQueue('email.queue', EXCHANGE, 'email'),
        this.channel.bindQueue('push.queue', EXCHANGE, 'push'),
        this.channel.bindQueue('failed.queue', EXCHANGE, 'failed'),
      ]);

      this.logger.log(`Connected to RabbitMQ exchange=${EXCHANGE}`);
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

      await new Promise<void>((resolve, reject) => {
        this.channel!.publish(
          EXCHANGE,
          routingKey,
          payload,
          { persistent: true },
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

      this.logger.log(
        `📨 Published message routing_key=${routingKey} correlation_id=${correlationId}`,
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : JSON.stringify(err);
      this.logger.error(`❌ RabbitMQ publish failed: ${message}`);
      throw new Error(`RabbitMQ publish failed: ${message}`);
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
