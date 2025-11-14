const amqplib = require("amqplib");

async function sendTestMessage() {
  try {
    const connection = await amqplib.connect("amqp://localhost:5672");
    const channel = await connection.createChannel();
    const queueName = "push.queue";

    await channel.assertQueue(queueName);

    const testMessage = {
      device_token: "test_token_123",
      title: "Test Notification",
      message: "This is a test push notification from RabbitMQ",
      image: "https://example.com/test-image.png"
    };

    channel.sendToQueue(queueName, Buffer.from(JSON.stringify(testMessage)));
    console.log("✅ Test message sent to queue:", testMessage);

    setTimeout(() => {
      connection.close();
      process.exit(0);
    }, 500);
  } catch (error) {
    console.error("❌ Error sending test message:", error.message);
    process.exit(1);
  }
}

sendTestMessage();
