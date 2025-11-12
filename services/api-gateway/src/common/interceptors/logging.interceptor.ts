import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
} from '@nestjs/common';
import { Observable, tap } from 'rxjs';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const req = context.switchToHttp().getRequest<{
      method: string;
      url: string;
      headers: Record<string, string | string[] | undefined>;
    }>();
    const method = req.method;
    const url = req.url;
    const start = Date.now();

    let correlationId: string | null = null;
    const headerValue = req.headers['x-correlation-id'];
    if (typeof headerValue === 'string') {
      correlationId = headerValue;
    } else if (Array.isArray(headerValue) && headerValue.length > 0) {
      correlationId = headerValue[0]; // take the first if array
    }

    return next.handle().pipe(
      tap(() => {
        const ms = Date.now() - start;
        console.log(
          `[${method}] ${url} ${ms}ms correlation_id=${correlationId}`,
        );
      }),
    );
  }
}
