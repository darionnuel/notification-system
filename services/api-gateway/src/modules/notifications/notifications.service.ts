import { Injectable, Logger, BadRequestException } from '@nestjs/common';
import { RabbitmqService } from '../rabbitmq/rabbitmq.service';
import { SchemaValidator } from '../../common/utils/schema-validator';
import { v4 as uuidv4 } from 'uuid';
import { UserService } from '../user/user.service';
import { TemplateService } from '../template/template.service';
import { EmailMessage, PushMessage } from '../../shared/message.types';
import { NotificationResult } from './types/notification-result.type';
import Redis from 'ioredis';

const ENABLE_REDIS = (process.env.ENABLE_REDIS || 'false') === 'true';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

@Injectable()
export class NotificationsService {
  private readonly logger = new Logger(NotificationsService.name);
  private readonly schemaValidator = new SchemaValidator();
  private redis: Redis | null = null;

  constructor(
    private readonly rabbitmqService: RabbitmqService,
    private readonly userService: UserService,
    private readonly templateService: TemplateService,
  ) {
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

  private buildEmailMessage(params: {
    request_id: string;
    notification_id: string;
    user_id: string;
    email: string;
    template_id: string;
    variables: Record<string, any>;
  }): EmailMessage {
    return {
      version: 'v1',
      type: 'email',
      timestamp: new Date().toISOString(),
      metadata: {},
      ...params,
    };
  }

  private buildPushMessage(params: {
    request_id: string;
    notification_id: string;
    user_id: string;
    device_tokens: string[];
    template_id: string;
    variables: Record<string, any>;
  }): PushMessage {
    return {
      version: 'v1',
      type: 'push',
      timestamp: new Date().toISOString(),
      metadata: {},
      ...params,
    };
  }

  async sendNotification(dto: {
    type: 'email' | 'push';
    user_id: string;
    template_id: string;
    variables: Record<string, any>;
    request_id?: string;
  }): Promise<NotificationResult> {
    const request_id = dto.request_id ?? uuidv4();

    if (await this.isDuplicate(request_id)) {
      this.logger.warn(`Duplicate request_id detected: ${request_id}`);
      return { request_id, duplicate: true };
    }

    const [userRes, templateRes] = await Promise.all([
      this.userService.getUser(dto.user_id),
      this.templateService.getTemplate(dto.template_id),
    ]);

    const user = userRes?.data ?? null;
    const template = templateRes?.data ?? null;

    if (!user) throw new BadRequestException('user_not_found');
    if (!template) throw new BadRequestException('template_not_found');

    const notification_id = `notif_${Date.now()}`;

    let message: EmailMessage | PushMessage;
    let routingKey: string;

    if (dto.type === 'email') {
      if (!user.email) throw new BadRequestException('user_email_missing');

      message = this.buildEmailMessage({
        request_id,
        notification_id,
        user_id: dto.user_id,
        email: user.email,
        template_id: dto.template_id,
        variables: dto.variables,
      });

      this.schemaValidator.validateMessage('email', message);
      routingKey = 'email';
    } else {
      const tokens = Array.isArray(user.push_tokens) ? user.push_tokens : [];

      if (tokens.length === 0)
        throw new BadRequestException('user_device_tokens_missing');

      message = this.buildPushMessage({
        request_id,
        notification_id,
        user_id: dto.user_id,
        device_tokens: tokens,
        template_id: dto.template_id,
        variables: dto.variables,
      });

      this.schemaValidator.validateMessage('push', message);
      routingKey = 'push';
    }

    await this.rabbitmqService.publish(routingKey, message);

    await this.markProcessed(request_id);

    this.logger.log(
      `Queued notification ${notification_id} request_id=${request_id}`,
    );

    return {
      notification_id,
      request_id,
    };
  }
}
