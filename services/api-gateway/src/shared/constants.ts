export const EXCHANGE = process.env.RABBITMQ_EXCHANGE || 'notifications.direct';
export const EMAIL_ROUTING_KEY = 'email';
export const PUSH_ROUTING_KEY = 'push';
export const EMAIL_QUEUE = 'email.queue';
export const PUSH_QUEUE = 'push.queue';
export const FAILED_QUEUE = 'failed.queue';
