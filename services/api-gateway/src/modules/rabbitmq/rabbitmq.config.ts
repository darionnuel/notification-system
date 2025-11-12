import { ConfigService } from '@nestjs/config';

export const getRabbitMQConfig = (configService: ConfigService) => ({
  uri: configService.get<string>('RABBITMQ_URL'),
  exchanges: [
    {
      name: 'notifications.direct',
      type: 'direct',
    },
  ],
});
