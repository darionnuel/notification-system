export type NotificationResult =
  | {
      duplicate: true;
      request_id: string;
    }
  | {
      duplicate?: false;
      request_id: string;
      notification_id: string;
    };
