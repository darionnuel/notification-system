export interface BaseMessage {
  version: string;
  request_id: string;
  notification_id: string;
  type: 'email' | 'push';
  user_id: string;
  template_id: string;
  variables: Record<string, any>;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface EmailMessage extends BaseMessage {
  type: 'email';
  email: string;
  device_tokens?: never;
}

export interface PushMessage extends BaseMessage {
  type: 'push';
  device_tokens: string[];
  email?: never;
}
