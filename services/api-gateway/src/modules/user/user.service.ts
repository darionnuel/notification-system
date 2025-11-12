import {
  Injectable,
  Logger,
  InternalServerErrorException,
} from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';
import { AxiosError, AxiosResponse } from 'axios';

interface UserResponse {
  data: {
    data: {
      id: string;
      email?: string;
      name?: string;
      push_tokens?: string[];
      // TODO Add more fields as needed
    };
  };
}

interface PreferencesResponse {
  data: {
    data: Record<string, any>;
  };
}

@Injectable()
export class UserService {
  private readonly logger = new Logger(UserService.name);

  constructor(private readonly http: HttpService) {}

  async getUser(user_id: string) {
    const url = `${process.env.USER_SERVICE_URL}/users/${user_id}`;
    try {
      const resp: AxiosResponse<UserResponse> = await firstValueFrom(
        this.http.get(url),
      );
      return resp.data.data;
    } catch (error) {
      const err = error as AxiosError;
      const message = err.response?.data
        ? JSON.stringify(err.response.data)
        : err.message;
      this.logger.error(`Failed to fetch user ${user_id}: ${message}`);
      throw new InternalServerErrorException('Failed to fetch user');
    }
  }

  async getUserPreferences(user_id: string) {
    const url = `${process.env.USER_SERVICE_URL}/users/${user_id}/preferences`;
    try {
      const resp: AxiosResponse<PreferencesResponse> = await firstValueFrom(
        this.http.get(url),
      );
      return resp.data.data;
    } catch (error) {
      const err = error as AxiosError;
      const message = err.response?.data
        ? JSON.stringify(err.response.data)
        : err.message;
      this.logger.error(
        `Failed to fetch preferences for ${user_id}: ${message}`,
      );
      throw new InternalServerErrorException(
        'Failed to fetch user preferences',
      );
    }
  }
}
