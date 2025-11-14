import {
  Controller,
  Post,
  Body,
  Req,
  UseGuards,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import type { Request } from 'express';
import { CreateNotificationDto } from './dto/create-notification.dto';
import { NotificationsService } from './notifications.service';
import { ApiKeyGuard } from '../../common/guards/api-key.guard';
import { v4 as uuidv4 } from 'uuid';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBearerAuth,
  ApiHeader,
} from '@nestjs/swagger';
import { NotificationResult } from './types/notification-result.type';

@ApiTags('notifications')
@ApiBearerAuth('api-key')
@ApiHeader({
  name: 'x-correlation-id',
  description: 'Optional request correlation ID',
})
@Controller('api/notifications')
@UseGuards(ApiKeyGuard)
export class NotificationsController {
  constructor(private readonly notificationsService: NotificationsService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Queue a new notification (email or push)' })
  @ApiResponse({
    status: 201,
    description: 'Notification queued successfully',
    schema: {
      example: {
        success: true,
        data: { notification_id: 'notif_12345', request_id: 'uuid_abc123' },
        error: null,
        message: 'notification_queued',
        meta: null,
      },
    },
  })
  @ApiResponse({
    status: 200,
    description: 'Duplicate request ignored',
    schema: {
      example: {
        success: true,
        data: { request_id: 'uuid_abc123' },
        error: null,
        message: 'duplicate_request_ignored',
        meta: null,
      },
    },
  })
  async create(@Body() dto: CreateNotificationDto, @Req() req: Request) {
    const correlation_id = req.headers['x-correlation-id'] as
      | string
      | undefined;
    const request_id = dto.request_id || correlation_id || uuidv4();

    const result: NotificationResult =
      await this.notificationsService.sendNotification({
        ...dto,
        request_id,
      });

    if (result.duplicate) {
      return {
        success: true,
        data: { request_id: result.request_id },
        error: null,
        message: 'duplicate_request_ignored',
        meta: null,
      };
    }

    return {
      success: true,
      data: {
        notification_id: result.notification_id,
        request_id: result.request_id,
      },
      error: null,
      message: 'notification_queued',
      meta: null,
    };
  }
}
