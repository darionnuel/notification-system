import amqplib from "amqplib";
import { handlePushNotification } from "./push-handler";

export const startQueue = async () => {
	const connection = await amqplib.connect("amqp://localhost:5672");
	console.log(connection, "connection");
	const channel = await connection.createChannel();
	const queueT = "push.queue";

	channel.assertQueue(queueT);

	channel.consume(queueT, async (msg) => {
		console.log("msg", msg);
		if (msg !== null) {
			const data = JSON.parse(msg.content.toString());
			console.log("message recieved", data);

			try {
				await handlePushNotification(data);
				channel.ack(msg);
			} catch (error) {
				console.error("Failed:", error?.message);
				channel.nack(msg, false, false);
			}
		}
	});
};
