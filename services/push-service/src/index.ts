import dotenv from "dotenv";
import { startServer } from "./server";
import { startQueue } from "./queue";

dotenv.config();

(async () => {
	startServer();

	await startQueue();
})();
