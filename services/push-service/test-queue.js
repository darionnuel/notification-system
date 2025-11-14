const amqplib = require("amqplib");
const { v4: uuidv4 } = require("uuid");

async function sendTestMessage() {
  try {
    console.log("🔌 Connecting to RabbitMQ...");
    const connection = await amqplib.connect("amqp://localhost:5672");
    const channel = await connection.createChannel();
    const queueName = "push.queue";

    await channel.assertQueue(queueName, { durable: true });
    console.log(`Connected to queue: ${queueName}`);

    const notification_id = `notif_${Date.now()}_${uuidv4().slice(0, 8)}`;
    const request_id = uuidv4();

    const testMessage = {
      notification_id: notification_id,
      request_id: request_id,
      device_tokens: [
        "test_device_token_1",
        "test_device_token_2"
      ],
      title: "Test Notification",
      body: "This is a test push notification from RabbitMQ",
      image: "https://example.com/test-image.png",
      data: {
        action_url: "https://example.com/action",
        type: "test"
      }
    };

    channel.sendToQueue(
      queueName,
      Buffer.from(JSON.stringify(testMessage)),
      {
        persistent: true,
        contentType: "application/json",
        messageId: notification_id,
        correlationId: request_id
      }
    );

    console.log("\nTest message sent successfully!\n");
    console.log("Notification ID:", notification_id);
    console.log("Device Tokens:", testMessage.device_tokens.length);
    console.log("Title:", testMessage.title);
    console.log("Body:", testMessage.body);

    setTimeout(() => {
      connection.close();
      process.exit(0);
    }, 500);
  } catch (error) {
    console.error("Error:", error.message);
    process.exit(1);
  }
}

sendTestMessage();
