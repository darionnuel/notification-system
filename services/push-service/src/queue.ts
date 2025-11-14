import amqplib from "amqplib";
import { PushNotificationService } from "./services/push-notification-service";

const pushService = new PushNotificationService();

export const startQueue = async () => {
	const rabbitmqUrl = process.env.RABBITMQ_URL || "amqp://localhost:5672";
	const queueName = "push.queue";

	console.log(`Connecting to RabbitMQ - ${rabbitmqUrl}`);

	const connection = await amqplib.connect(rabbitmqUrl);
	const channel = await connection.createChannel();

	await channel.assertQueue(queueName, { durable: true });
	await channel.prefetch(parseInt(process.env.RABBITMQ_PREFETCH || "10"));

	console.log(`Connected to RabbitMQ. Listening to queue - ${queueName}`);

	channel.consume(queueName, async (msg) => {
		if (msg !== null) {
			try {
				const data = JSON.parse(msg.content.toString());

				console.log(`Message Received - ${data.notification_id}`);

				if (
					!data.notification_id ||
					!data.request_id ||
					!data.device_tokens
				) {
					throw new Error("Invalid message: missing required fields");
				}

				if (!data.title || !data.body) {
					throw new Error("Invalid message: missing title or body");
				}

				await pushService.processNotification(data);
				channel.ack(msg);
			} catch (error) {
				const errorMessage =
					error instanceof Error ? error.message : String(error);
				console.error(`Failed to process message: ${errorMessage}`);

				channel.nack(msg, false, false);
				console.log(`Message sent to dead letter queue`);
			}
		}
	});

	connection.on("error", (err) => {
		console.error("connection error:", err);
	});

	connection.on("close", () => {
		console.log("connection closed");

		setTimeout(() => {
			console.log("Reconnecting");
			startQueue().catch(console.error);
		}, 5000);
	});
};
