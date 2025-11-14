import { getMessaging } from "firebase-admin/messaging";
import { applicationDefault, initializeApp } from "firebase-admin/app";

type PushData = {
	device_token: string;
	title: string;
	message: string;
	image?: string;
	data?: Record<string, string>;
};

const app = initializeApp({
	credential: applicationDefault(),
});

const messaging = getMessaging(app);

export async function handlePushNotification(data: PushData): Promise<string> {
	const message: any = {
		token: data.device_token,
		notification: {
			title: data.title,
			body: data.message,
		},
	};

	if (data.image) {
		message.notification.image = data.image;
	}

	if (data.data) {
		message.data = data.data;
	}

	try {
		const response = await messaging.send(message);
		return response;
	} catch (error) {
		const errorMessage =
			error instanceof Error
				? error.message
				: "Couldn't send notification";

		console.error(`Push failed: ${errorMessage}`);

		throw new Error(`Firebase push notification failed: ${errorMessage}`);
	}
}
