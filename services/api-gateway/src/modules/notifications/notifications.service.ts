import { Injectable, Logger, BadRequestException } from '@nestjs/common';
import { RabbitmqService } from '../rabbitmq/rabbitmq.service';
import { SchemaValidator } from '../../common/utils/schema-validator';
import { v4 as uuidv4 } from 'uuid';
import { UserService } from '../user/user.service';
import { TemplateService } from '../template/template.service';
import { EmailMessage, PushMessage } from '../../shared/message.types';
import { NotificationResult } from './types/notification-result.type';
import { EMAIL_ROUTING_KEY, PUSH_ROUTING_KEY } from '../../shared/constants';
import Redis from 'ioredis';

const ENABLE_REDIS = (process.env.ENABLE_REDIS || 'false') === 'true';
const REDIS_URL = process.env.REDIS_URL || 'redis://redis:6379';

interface User {
  id: string;
  email?: string;
  push_tokens?: string[];
}

interface Template {
  id: string;
  content: string;
  type: 'email' | 'push';
}

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
    const key = `idempotency:${request_id}`;
    const exists = await this.redis.get(key);
    return !!exists;
  }

  private async markProcessed(request_id: string, ttlSeconds = 60 * 60 * 24) {
    if (!this.redis) return;
    const key = `idempotency:${request_id}`;
    await this.redis.set(key, '1', 'EX', ttlSeconds);
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
      request_id: params.request_id,
      notification_id: params.notification_id,
      type: 'email', // strictly "email"
      user_id: params.user_id,
      email: params.email,
      template_id: params.template_id,
      variables: params.variables,
      timestamp: new Date().toISOString(),
      metadata: {},
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
      request_id: params.request_id,
      notification_id: params.notification_id,
      type: 'push', // strictly "push"
      user_id: params.user_id,
      device_tokens: params.device_tokens,
      template_id: params.template_id,
      variables: params.variables,
      timestamp: new Date().toISOString(),
      metadata: {},
    };
  }

  async sendNotification(dto: {
    type: 'email' | 'push';
    user_id: string;
    template_id: string;
    variables: Record<string, any>;
    request_id?: string;
  }): Promise<NotificationResult> {
    const request_id: string = dto.request_id ?? uuidv4();

    if (await this.isDuplicate(request_id)) {
      this.logger.warn(`Duplicate request_id detected: ${request_id}`);
      return { request_id, duplicate: true };
    }

    // fetch user and template
    const [userRes, templateRes] = await Promise.all([
      this.userService.getUser(dto.user_id),
      this.templateService.getTemplate(dto.template_id),
    ]);

    const user: User | null = userRes?.data ?? null;
    const template: Template | null =
      templateRes?.data &&
      typeof templateRes.data === 'object' &&
      'id' in templateRes.data &&
      'content' in templateRes.data &&
      'type' in templateRes.data
        ? {
            id: templateRes.data.id,
            content: templateRes.data.content,
            type: templateRes.data.type,
          }
        : null;

    if (!user) throw new BadRequestException('user_not_found');
    if (!template) throw new BadRequestException('template_not_found');

    const notification_id = `notif_${Date.now()}`;

    // prepare message depending on type
    let msg: EmailMessage | PushMessage;

    if (dto.type === 'email') {
      if (!user.email) throw new BadRequestException('user_email_missing');

      msg = this.buildEmailMessage({
        request_id,
        notification_id,
        user_id: dto.user_id,
        email: user.email,
        template_id: dto.template_id,
        variables: dto.variables,
      });

      // AJV schema validation
      try {
        this.schemaValidator.validateMessage('email', msg);
      } catch (err: unknown) {
        const msgErr = err instanceof Error ? err.message : String(err);
        this.logger.error(`Email message validation failed: ${msgErr}`);
        throw new BadRequestException(
          `email_schema_validation_failed: ${msgErr}`,
        );
      }

      await this.rabbitmqService.publish(EMAIL_ROUTING_KEY, msg);
    } else {
      // push
      const device_tokens: string[] = Array.isArray(user.push_tokens)
        ? user.push_tokens
        : user.push_tokens || [];

      if (!device_tokens || device_tokens.length === 0)
        throw new BadRequestException('user_device_tokens_missing');

      msg = this.buildPushMessage({
        request_id,
        notification_id,
        user_id: dto.user_id,
        device_tokens,
        template_id: dto.template_id,
        variables: dto.variables,
      });

      // AJV schema validation
      try {
        this.schemaValidator.validateMessage('push', msg);
      } catch (err: unknown) {
        const msgErr = err instanceof Error ? err.message : String(err);
        this.logger.error(`Push message validation failed: ${msgErr}`);
        throw new BadRequestException(
          `push_schema_validation_failed: ${msgErr}`,
        );
      }

      await this.rabbitmqService.publish(PUSH_ROUTING_KEY, msg);
    }

    // mark processed for idempotency
    await this.markProcessed(request_id);

    // write a queued status into whatever status store you have (left as TODO)
    // TODO: call status service or write to shared DB

    this.logger.log(
      `Queued notification ${notification_id} request_id=${request_id}`,
    );
    return { notification_id, request_id };
  }
}
