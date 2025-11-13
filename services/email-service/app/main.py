"""Main FastAPI application."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import init_db
from app.api.email import router as email_router
from app.services.queue_service import queue_service
from app.services.email_service import email_service
from app.db.session import SessionLocal


# Background task for consuming RabbitMQ messages
consumer_task = None


async def consume_email_queue():
    """Background task to consume email notifications from RabbitMQ."""
    async def process_email_message(message: dict, correlation_id: str = None):
        """Process incoming email notification."""
        try:
            # Create database session
            db = SessionLocal()
            
            try:
                # Import here to avoid circular dependency
                from app.schemas.email import EmailNotificationRequest
                
                # Parse message
                request = EmailNotificationRequest(**message)
                
                # Process notification
                await email_service.process_notification(request, db, correlation_id)
                
            finally:
                db.close()
        
        except Exception as e:
            print(f"❌ Error processing email message: {e}")
    
    # Start consuming
    await queue_service.consume_emails(process_email_message)
    
    # Keep running
    while True:
        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting Email Service...")
    
    # Initialize database
    init_db()
    print("✅ Database initialized")
    
    # Connect to RabbitMQ
    await queue_service.connect()
    
    # Start consumer task
    global consumer_task
    consumer_task = asyncio.create_task(consume_email_queue())
    print("✅ Email queue consumer started")
    
    yield
    
    # Shutdown
    print("⏹️ Shutting down Email Service...")
    
    # Cancel consumer task
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    
    # Disconnect from RabbitMQ
    await queue_service.disconnect()
    
    print("✅ Email Service stopped")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Email Service API for sending emails via SMTP and SendGrid",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(email_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": settings.app_name
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )
