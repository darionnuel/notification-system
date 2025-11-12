import * as fs from 'fs';
import * as path from 'path';
import Ajv, { JSONSchemaType, ValidateFunction } from 'ajv';
import addFormats from 'ajv-formats';
import { EmailMessage, PushMessage } from '../../shared/message.types';

export class SchemaValidator {
  private ajv: Ajv;
  private readonly validators: Record<string, ValidateFunction>;

  constructor() {
    this.ajv = new Ajv({ allErrors: true, strict: false });
    addFormats(this.ajv);
  }

  validateMessage(type: 'email', message: EmailMessage): void;
  validateMessage(type: 'push', message: PushMessage): void;
  validateMessage(
    type: 'email' | 'push',
    message: EmailMessage | PushMessage,
  ): void {
    let validate = this.validators[type];

    // Compile and cache the schema if not already done
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
