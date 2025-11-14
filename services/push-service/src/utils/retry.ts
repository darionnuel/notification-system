export interface RetryOptions {
	maxAttempts?: number;
	baseDelay?: number;
	maxDelay?: number;
	onRetry?: (attempt: number, error: Error) => void;
}

export async function retryWithBackoff<T>(
	fn: () => Promise<T>,
	options: RetryOptions = {}
): Promise<T> {
	const {
		maxAttempts = 3,
		baseDelay = 1000,
		maxDelay = 30000,
		onRetry,
	} = options;

	let lastError: Error;

	for (let attempt = 1; attempt <= maxAttempts; attempt++) {
		try {
			return await fn();
		} catch (error) {
			lastError = error as Error;

			if (attempt === maxAttempts) {
				throw lastError;
			}

			const delay = Math.min(
				baseDelay * Math.pow(2, attempt - 1),
				maxDelay
			);

			if (onRetry) {
				onRetry(attempt, lastError);
			}

			console.log(
				`Retry attempt ${attempt}/${maxAttempts} failed: ${lastError.message}. Retrying in ${delay}ms...`
			);

			await sleep(delay);
		}
	}

	throw lastError!;
}

export function sleep(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}
