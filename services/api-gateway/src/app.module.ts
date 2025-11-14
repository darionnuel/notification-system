import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import configuration from './config/configuration';
import { RabbitmqModule } from './modules/rabbitmq/rabbitmq.module';
import { NotificationsController } from './modules/notifications/notifications.controller';
import { NotificationsService } from './modules/notifications/notifications.service';
import { HealthController } from './modules/health/health.controller';

/**
 * API Gateway Module
 * 
 * Responsibilities:
 * - Accept notification requests
 * - Validate request format
 * - Check authentication (API key)
 * - Check idempotency (Redis)
 * - Publish minimal messages to RabbitMQ
 * - Return immediately (async processing)
 * 
 * NOT Responsible For:
 * - Fetching user data (Email/Push services do this)
 * - Fetching templates (Email/Push services do this)
 * - Sending notifications (Email/Push services do this)
 */
@Module({
  imports: [
    ConfigModule.forRoot({ load: [configuration], isGlobal: true }),
    RabbitmqModule,
  ],
  controllers: [NotificationsController, HealthController],
  providers: [NotificationsService],
})
export class AppModule {}
