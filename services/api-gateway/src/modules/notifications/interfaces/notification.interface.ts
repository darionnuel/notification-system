export interface NotificationMessage {
  version?: string;
  request_id: string;
  notification_id: string;
  type: 'email' | 'push';
  user_id: string;
  email?: string;
  device_tokens?: string[];
  template_id: string;
  variables: Record<string, any>;
  timestamp: string;
  metadata?: Record<string, any>;
}
