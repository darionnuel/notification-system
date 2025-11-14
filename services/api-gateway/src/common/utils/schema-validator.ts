import * as fs from 'fs';
import * as path from 'path';
import Ajv, { JSONSchemaType, ValidateFunction } from 'ajv';
import addFormats from 'ajv-formats';
import {
  NotificationQueueMessage,
  EmailMessage,
  PushMessage,
} from '../../shared/message.types';

export class SchemaValidator {
  private ajv: Ajv;
  private readonly validators: Record<string, ValidateFunction> = {};

  constructor() {
    this.ajv = new Ajv({ allErrors: true, strict: false });
    addFormats(this.ajv);
  }

  // Overloaded signatures for type safety
  validateMessage(type: 'email', message: NotificationQueueMessage): void;
  validateMessage(type: 'push', message: NotificationQueueMessage): void;
  validateMessage(
    type: 'email' | 'push',
    message: NotificationQueueMessage,
  ): void {
    // For now, skip file-based validation and do basic checks
    // TODO: Create proper JSON schemas for NotificationQueueMessage
    this.validateQueueMessage(message, type);
  }

  /**
   * Validate notification queue message structure
   */
  private validateQueueMessage(
    message: NotificationQueueMessage,
    type: 'email' | 'push',
  ): void {
    const errors: string[] = [];

    // Required fields
    if (!message.notification_id)
      errors.push('notification_id is required');
    if (!message.request_id) errors.push('request_id is required');
    if (!message.correlation_id) errors.push('correlation_id is required');
    if (!message.version) errors.push('version is required');
    if (!message.type) errors.push('type is required');
    if (!message.user_id) errors.push('user_id is required');
    if (!message.template_code) errors.push('template_code is required');
    if (!message.variables) errors.push('variables is required');
    if (message.priority === undefined) errors.push('priority is required');
    if (!message.timestamp) errors.push('timestamp is required');
    if (message.retry_count === undefined)
      errors.push('retry_count is required');
    if (message.max_retries === undefined)
      errors.push('max_retries is required');

    // Type matching
    if (message.type !== type) {
      errors.push(`type mismatch: expected ${type}, got ${message.type}`);
    }

    // Value validation
    if (message.priority < 0 || message.priority > 10) {
      errors.push('priority must be between 0 and 10');
    }

    if (message.retry_count < 0) {
      errors.push('retry_count must be >= 0');
    }

    if (message.max_retries < 0) {
      errors.push('max_retries must be >= 0');
    }

    if (errors.length > 0) {
      throw new Error(`Invalid ${type} message: ${errors.join(', ')}`);
    }
  }

  /**
   * @deprecated Legacy method for old message types
   */
  validateLegacyMessage(type: 'email', message: EmailMessage): void;
  validateLegacyMessage(type: 'push', message: PushMessage): void;
  validateLegacyMessage(
    type: 'email' | 'push',
    message: EmailMessage | PushMessage,
  ): void {
    let validate = this.validators[type];

    if (!validate) {
      const schemaPath = path.join(
        __dirname,
        '../../../../contracts/message_schemas',
        `${type}_message_v1.json`,
      );

      if (!fs.existsSync(schemaPath)) {
        throw new Error(`Schema file for ${type} not found at ${schemaPath}`);
      }

      const schema = JSON.parse(
        fs.readFileSync(schemaPath, 'utf-8'),
      ) as JSONSchemaType<any>;

      validate = this.ajv.compile(schema);
      this.validators[type] = validate;
    }

    const valid = validate(message);
    if (!valid) {
      const errors = validate.errors
        ?.map((err) => `${err.instancePath || '(root)'} ${err.message}`)
        .join(', ');
      throw new Error(`Invalid ${type} message: ${errors}`);
    }
  }
}
