import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import configuration from './config/configuration';
import { RabbitmqModule } from './modules/rabbitmq/rabbitmq.module';
import { NotificationsController } from './modules/notifications/notifications.controller';
import { NotificationsService } from './modules/notifications/notifications.service';
import { HttpModule } from '@nestjs/axios';
import { UserService } from './modules/user/user.service';
import { TemplateService } from './modules/template/template.service';
import { HealthController } from './modules/health/health.controller';

@Module({
  imports: [
    ConfigModule.forRoot({ load: [configuration], isGlobal: true }),
    RabbitmqModule,
    HttpModule,
  ],
  controllers: [NotificationsController, HealthController],
  providers: [NotificationsService, UserService, TemplateService],
})
export class AppModule {}
