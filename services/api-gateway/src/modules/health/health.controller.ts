// services/api-gateway/src/health/health.controller.ts
import { Controller, Get } from '@nestjs/common';
import { RabbitmqService } from '../rabbitmq/rabbitmq.service';
import Redis from 'ioredis';

const ENABLE_REDIS = (process.env.ENABLE_REDIS || 'false') === 'true';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

@Controller('health')
export class HealthController {
  private redis: Redis | null = null;
  private redisEnabled = ENABLE_REDIS;

  constructor(private readonly rabbitmqService: RabbitmqService) {
    if (this.redisEnabled) {
      this.redis = new Redis(REDIS_URL);
    }
  }

  @Get()
  async check() {
    const rabbitConnected = this.rabbitmqService?.isConnected?.() ?? false;

    let redisOk: boolean | null = null;

    if (this.redisEnabled && this.redis) {
      try {
        await this.redis.ping();
        redisOk = true;
      } catch {
        redisOk = false;
      }
    }

    return {
      uptime: process.uptime(),
      rabbitmq: rabbitConnected ? 'ok' : 'disconnected',
      redis: this.redisEnabled ? (redisOk ? 'ok' : 'disconnected') : 'disabled',
      time: new Date().toISOString(),
    };
  }
}
