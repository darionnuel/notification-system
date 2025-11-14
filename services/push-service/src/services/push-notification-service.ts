import { handlePushNotification } from "../push-handler";
import { retryWithBackoff } from "../utils/retry";

interface PushMessage {
	notification_id: string;
	request_id: string;
	device_tokens: string[];
	title: string;
	body: string;
	image?: string;
	data?: Record<string, string>;
}

export class PushNotificationService {
	private processedRequests: Set<string>;

	constructor() {
		this.processedRequests = new Set();
	}

	async processNotification(message: PushMessage): Promise<void> {
		if (this.processedRequests.has(message.request_id)) {
			return;
		}

		if (!message.device_tokens || message.device_tokens.length === 0) {
			return;
		}

		let successCount = 0;
		let failureCount = 0;

		for (const token of message.device_tokens) {
			try {
				await retryWithBackoff(
					() =>
						handlePushNotification({
							device_token: token,
							title: message.title,
							message: message.body,
							image: message.image,
							data: message.data,
						}),
					{
						maxAttempts: 3,
						baseDelay: 2000,
						onRetry: (attempt, error) => {
							console.log(
								`Push attempt ${attempt}/3 failed for token ${token}...: ${error.message}`
							);
						},
					}
				);

				successCount++;
			} catch (error) {
				const errorMessage =
					error instanceof Error ? error.message : String(error);
				failureCount++;
				console.error(
					`Push failed for token ${token}...: ${errorMessage}`
				);
			}
		}

		console.log(
			`Notification ${message.notification_id} completed: ${successCount} sent, ${failureCount} failed`
		);

		// Mark request as processed
		this.processedRequests.add(message.request_id);
	}
}
