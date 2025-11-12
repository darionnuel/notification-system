import { Controller, Get } from '@nestjs/common';

@Controller('health')
export class HealthController {
  @Get()
  health() {
    return {
      success: true,
      data: { status: 'ok' },
      error: null,
      message: 'healthy',
      meta: null,
    };
  }
}
