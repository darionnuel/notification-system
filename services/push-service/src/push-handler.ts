import { getMessaging } from "firebase-admin/messaging";
import { applicationDefault, initializeApp } from "firebase-admin/app";

type PushData = {
	device_token: string;
	title: string;
	message: string;
	image: string;
};

const app = initializeApp({
	credential: applicationDefault(),
});

const messaging = getMessaging(app);

export async function handlePushNotification(data: PushData) {
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
	} catch (error) {
		console.error(
			"❌ Push failed:",
			error instanceof Error
				? error?.message
				: "Couldn't send notification"
		);
		throw error;
	}
}
