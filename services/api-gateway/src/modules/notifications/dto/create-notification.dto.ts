import { ApiProperty } from '@nestjs/swagger';
import {
  IsEnum,
  IsNotEmpty,
  IsObject,
  IsString,
  IsOptional,
} from 'class-validator';

export enum NotificationType {
  EMAIL = 'email',
  PUSH = 'push',
}

export class CreateNotificationDto {
  @ApiProperty({
    description: 'Type of notification',
    enum: NotificationType,
    example: NotificationType.EMAIL,
  })
  @IsEnum(NotificationType)
  type: NotificationType;

  @ApiProperty({
    description: 'User ID to send the notification to',
    example: 'user_12345',
  })
  @IsString()
  @IsNotEmpty()
  user_id: string;

  @ApiProperty({
    description: 'Template code to use for the notification',
    example: 'welcome_email',
  })
  @IsString()
  @IsNotEmpty()
  template_code: string;

  @ApiProperty({
    description: 'Priority level (0-10, higher = more important)',
    example: 5,
    required: false,
    minimum: 0,
    maximum: 10,
  })
  priority?: number;

  @ApiProperty({
    description: 'Optional metadata for overrides (language, from_email, etc.)',
    type: Object,
    required: false,
    example: { language: 'en', from_email: 'noreply@example.com' },
  })
  metadata?: Record<string, unknown>;

  @ApiProperty({
    description: 'Variables to populate the template',
    type: Object,
    example: { name: 'Darion', link: 'https://example.com' },
  })
  @IsObject()
  variables: Record<string, unknown>;

  @ApiProperty({
    description: 'Idempotency / correlation request id',
    example: '08f1d7ba-c6bb-4f35-9bb1-e97d9c84b93b',
    required: false,
  })
  @IsOptional()
  @IsString()
  request_id?: string;
}
