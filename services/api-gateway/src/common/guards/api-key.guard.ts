import { CanActivate, ExecutionContext, Injectable } from '@nestjs/common';
import { Request } from 'express';

@Injectable()
export class ApiKeyGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest<Request>();
    const auth = request.headers['authorization'] || '';
    const token = String(auth).replace('Bearer ', '');
    return token === process.env.API_KEY;
  }
}
