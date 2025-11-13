"""RabbitMQ queue service for consuming and publishing messages."""
import json
import asyncio
from typing import Optional, Callable
import aio_pika
from aio_pika import Message, ExchangeType
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue

from app.core.config import settings


class QueueService:
    """Service for RabbitMQ message queue operations."""
    
    def __init__(self):
        """Initialize queue service."""
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.exchange = None
        self.email_queue: Optional[AbstractQueue] = None
        self.status_queue: Optional[AbstractQueue] = None
        self.failed_queue: Optional[AbstractQueue] = None
    
    async def connect(self):
        """Connect to RabbitMQ and setup queues."""
        # Connect to RabbitMQ
        self.connection = await aio_pika.connect_robust(
            settings.rabbitmq_url,
            timeout=settings.rabbitmq_connection_timeout,
        )
        
        # Create channel
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=settings.rabbitmq_prefetch_count)
        
        # Declare exchange
        self.exchange = await self.channel.declare_exchange(
            settings.rabbitmq_exchange,
            ExchangeType.TOPIC,
            durable=True,
        )
        
        # Declare queues
        self.email_queue = await self.channel.declare_queue(
            settings.rabbitmq_email_queue,
            durable=True,
            arguments={"x-message-ttl": 86400000}  # 24 hours TTL
        )
        
        self.status_queue = await self.channel.declare_queue(
            settings.rabbitmq_status_queue,
            durable=True,
        )
        
        self.failed_queue = await self.channel.declare_queue(
            settings.rabbitmq_failed_queue,
            durable=True,
        )
        
        # Bind queues to exchange
        await self.email_queue.bind(
            self.exchange,
            routing_key="email.*"
        )
        
        await self.status_queue.bind(
            self.exchange,
            routing_key="status.*"
        )
        
        await self.failed_queue.bind(
            self.exchange,
            routing_key="failed.*"
        )
        
        print(f"✅ Connected to RabbitMQ at {settings.rabbitmq_url}")
        print(f"📥 Listening on queue: {settings.rabbitmq_email_queue}")
    
    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        if self.connection:
            await self.connection.close()
            print("❌ Disconnected from RabbitMQ")
    
    async def consume_emails(self, callback: Callable):
        """
        Start consuming email notification messages.
        
        Args:
            callback: Async function to process each message
        """
        if not self.email_queue:
            raise Exception("Queue service not connected")
        
        async def process_message(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    # Parse message
                    body = json.loads(message.body.decode())
                    
                    # Extract correlation ID from headers
                    correlation_id = None
                    if message.correlation_id:
                        correlation_id = message.correlation_id
                    elif message.headers and "correlation_id" in message.headers:
                        correlation_id = message.headers["correlation_id"]
                    
                    # Process message
                    await callback(body, correlation_id)
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON in message: {e}")
                    # Send to failed queue
                    await self.publish_to_failed_queue(
                        message.body.decode(),
                        f"JSON decode error: {str(e)}"
                    )
                
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    # Send to failed queue
                    await self.publish_to_failed_queue(
                        message.body.decode(),
                        f"Processing error: {str(e)}"
                    )
        
        # Start consuming
        await self.email_queue.consume(process_message)
        print(f"🔄 Started consuming from {settings.rabbitmq_email_queue}")
    
    async def publish_status_update(
        self,
        notification_id: str,
        status: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Publish email status update to status queue.
        
        Args:
            notification_id: Notification ID
            status: Email status
            correlation_id: Request correlation ID
            metadata: Additional metadata
        """
        if not self.exchange:
            raise Exception("Queue service not connected")
        
        # Prepare message
        payload = {
            "notification_id": notification_id,
            "status": status,
            "timestamp": None,  # Will be set by receiver
            "metadata": metadata or {}
        }
        
        # Create message
        message = Message(
            body=json.dumps(payload).encode(),
            correlation_id=correlation_id,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        
        # Publish to status queue
        await self.exchange.publish(
            message,
            routing_key=f"status.{status.lower()}"
        )
    
    async def publish_to_failed_queue(
        self,
        original_message: str,
        error_message: str,
        correlation_id: Optional[str] = None
    ):
        """
        Publish failed message to dead letter queue.
        
        Args:
            original_message: Original message that failed
            error_message: Error description
            correlation_id: Request correlation ID
        """
        if not self.exchange:
            raise Exception("Queue service not connected")
        
        # Prepare message
        payload = {
            "original_message": original_message,
            "error": error_message,
            "timestamp": None,
        }
        
        # Create message
        message = Message(
            body=json.dumps(payload).encode(),
            correlation_id=correlation_id,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        
        # Publish to failed queue
        await self.exchange.publish(
            message,
            routing_key="failed.email"
        )


# Global instance
queue_service = QueueService()
