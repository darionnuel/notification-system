import { getMessaging } from "firebase-admin/messaging";
import { applicationDefault, initializeApp } from "firebase-admin/app";

const app = initializeApp({
	credential: applicationDefault(),
});

const messaging = getMessaging(app);

export async function handlePushNotification(data) {
	const message = {
		token: data.device_token,
		notification: {
			title: data.title,
			body: data.message,
			image: data.image,
		},
	};

	try {
		const response = await messaging.send(message);
		console.log("✅ Push sent:", response);
	} catch (error) {
		console.error("❌ Push failed:", error.message);
		throw error;
	}
}
