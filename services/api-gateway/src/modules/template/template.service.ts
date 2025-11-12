import { Injectable, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';
import { AxiosError } from 'axios';

interface TemplateData {
  id: string;
  name: string;
  subject?: string;
  body: string;
  type?: string; // e.g. 'email' or 'push'
  [key: string]: any; // allow additional metadata
}

interface TemplateServiceResponse {
  data: TemplateData;
  status: string;
}

@Injectable()
export class TemplateService {
  private readonly logger = new Logger(TemplateService.name);

  constructor(private readonly http: HttpService) {}

  async getTemplate(template_id: string): Promise<TemplateData> {
    const url = `${process.env.TEMPLATE_SERVICE_URL}/templates/${template_id}`;

    try {
      const resp = await firstValueFrom(
        this.http.get<TemplateServiceResponse>(url),
      );

      if (!resp.data?.data) {
        throw new Error(`Template not found or malformed response`);
      }

      return resp.data.data;
    } catch (err: unknown) {
      if (err instanceof AxiosError) {
        this.logger.error(
          `Failed to fetch template ${template_id}: ${err.message}`,
        );
        if (err.response) {
          this.logger.error(`Response: ${JSON.stringify(err.response.data)}`);
        }
      } else if (err instanceof Error) {
        this.logger.error(
          `Unexpected error while fetching template ${template_id}: ${err.message}`,
        );
      } else {
        this.logger.error(
          `Unknown error while fetching template ${template_id}`,
        );
      }
      throw err;
    }
  }
}
