import { Injectable, Logger, BadRequestException } from '@nestjs/common';
import { RabbitmqService } from '../rabbitmq/rabbitmq.service';
import { SchemaValidator } from '../../common/utils/schema-validator';
import { v4 as uuidv4 } from 'uuid';
import { NotificationQueueMessage } from '../../shared/message.types';
import { NotificationResult } from './types/notification-result.type';
import Redis from 'ioredis';

const ENABLE_REDIS = (process.env.ENABLE_REDIS || 'false') === 'true';
const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379';

@Injectable()
export class NotificationsService {
  private readonly logger = new Logger(NotificationsService.name);
  private readonly schemaValidator = new SchemaValidator();
  private redis: Redis | null = null;

  constructor(private readonly rabbitmqService: RabbitmqService) {
    if (ENABLE_REDIS) {
      this.redis = new Redis(REDIS_URL);
    }
  }

  private async isDuplicate(request_id: string): Promise<boolean> {
    if (!this.redis) return false;
    return !!(await this.redis.get(`idempotency:${request_id}`));
  }

  private async markProcessed(request_id: string, ttl = 24 * 60 * 60) {
    if (!this.redis) return;
    await this.redis.set(`idempotency:${request_id}`, '1', 'EX', ttl);
  }

  /**
   * Build minimal notification queue message.
   * Contains only references - workers will fetch user/template data.
   */
  private buildQueueMessage(params: {
    type: 'email' | 'push';
    user_id: string;
    template_code: string;
    variables: Record<string, any>;
    request_id: string;
    notification_id: string;
    priority?: number;
    metadata?: Record<string, any>;
  }): NotificationQueueMessage {
    return {
      // Identification
      notification_id: params.notification_id,
      request_id: params.request_id,
      correlation_id: params.request_id, // Use request_id as correlation_id
      version: 'v1',

      // Core References (NO fetched data)
      type: params.type,
      user_id: params.user_id,
      template_code: params.template_code,
      variables: params.variables,

      // Operational
      priority: params.priority ?? 5, // Default medium priority
      timestamp: new Date().toISOString(),
      retry_count: 0,
      max_retries: 3,

      // Optional
      metadata: params.metadata,
    };
  }

  /**
   * Queue notification for async processing.
   * Gateway does NOT fetch user or template data - workers do that.
   */
  async sendNotification(dto: {
    type: 'email' | 'push';
    user_id: string;
    template_code: string;
    variables: Record<string, any>;
    request_id?: string;
    priority?: number;
    metadata?: Record<string, any>;
  }): Promise<NotificationResult> {
    const request_id = dto.request_id ?? uuidv4();

    // 1. Check idempotency
    if (await this.isDuplicate(request_id)) {
      this.logger.warn(`⚠️ Duplicate request_id: ${request_id}`);
      return { request_id, duplicate: true };
    }

    // 2. Generate notification ID
    const notification_id = `notif_${Date.now()}_${uuidv4().slice(0, 8)}`;

    // 3. Build minimal message (NO user/template fetching!)
    const message = this.buildQueueMessage({
      type: dto.type,
      user_id: dto.user_id,
      template_code: dto.template_code,
      variables: dto.variables,
      request_id,
      notification_id,
      priority: dto.priority,
      metadata: dto.metadata,
    });

    // 4. Validate message schema
    try {
      if (dto.type === 'email') {
        this.schemaValidator.validateMessage('email', message);
      } else {
        this.schemaValidator.validateMessage('push', message);
      }
    } catch (err: unknown) {
      const msgErr = err instanceof Error ? err.message : String(err);
      this.logger.error(`❌ Message validation failed: ${msgErr}`);
      throw new BadRequestException(`validation_failed: ${msgErr}`);
    }

    // 5. Publish to appropriate queue
    const routingKey = dto.type === 'email' ? EMAIL_ROUTING_KEY : PUSH_ROUTING_KEY;
    
    try {
      await this.rabbitmqService.publish(routingKey, message);
      this.logger.log(
        `✅ Queued ${dto.type} notification | ID: ${notification_id} | User: ${dto.user_id}`,
      );
    } catch (err: unknown) {
      const msgErr = err instanceof Error ? err.message : String(err);
      this.logger.error(`❌ Failed to publish message: ${msgErr}`);
      throw new BadRequestException('failed_to_queue_notification');
    }

    // 6. Mark as processed (idempotency)
    await this.markProcessed(request_id);

    // 7. Return immediately (async processing)
    return { notification_id, request_id };
  }
}
