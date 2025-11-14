/**
 * Minimal queue message structure for notifications.
 * Contains only references (user_id, template_code) - NO fetched data.
 * Workers (Email/Push services) will fetch user details and templates.
 */
export interface NotificationQueueMessage {
  // Identification & Tracing
  notification_id: string; // e.g., "notif_1731542400_a1b2c3d4"
  request_id: string; // Idempotency key
  correlation_id: string; // For distributed tracing
  version: string; // Message schema version (e.g., "v1")

  // Core References (NOT fetched data)
  type: 'email' | 'push'; // Routing type
  user_id: string; // Worker fetches user details
  template_code: string; // Worker fetches template by code
  variables: Record<string, any>; // Template variables

  // Operational Metadata
  priority: number; // 0-10 (higher = more important)
  timestamp: string; // ISO 8601
  retry_count: number; // Current retry attempt
  max_retries: number; // Maximum retry attempts

  // Optional Overrides
  metadata?: {
    language?: string; // e.g., "en", "es"
    from_email?: string; // Override default sender
    from_name?: string; // Override default sender name
    reply_to?: string; // Reply-to address
    cc?: string[]; // CC recipients
    bcc?: string[]; // BCC recipients
    [key: string]: any; // Allow additional metadata
  };
}

/**
 * @deprecated Use NotificationQueueMessage instead
 * Kept for backward compatibility during migration
 */
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

/**
 * @deprecated Use NotificationQueueMessage instead
 */
export interface EmailMessage extends BaseMessage {
  type: 'email';
  email: string;
  device_tokens?: never;
}

/**
 * @deprecated Use NotificationQueueMessage instead
 */
export interface PushMessage extends BaseMessage {
  type: 'push';
  device_tokens: string[];
  email?: never;
}
