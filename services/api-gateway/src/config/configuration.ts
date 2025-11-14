export default () => ({
  port: parseInt(process.env.PORT || '3000', 10),
  api_key: process.env.API_KEY || '',
  rabbitmq_url: process.env.RABBITMQ_URL || 'amqp://guest:guest@localhost:5672',
  rabbitmq_exchange: process.env.RABBITMQ_EXCHANGE || 'notifications.direct',
  user_service_url: process.env.USER_SERVICE_URL || 'http://localhost:4000',
  template_service_url:
    process.env.TEMPLATE_SERVICE_URL || 'http://localhost:4001',
  redis_url: process.env.REDIS_URL || 'redis://localhost:6379',
  enable_redis: (process.env.ENABLE_REDIS || 'false') === 'true',
});
