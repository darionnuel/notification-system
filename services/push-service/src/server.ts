import express from "express";

export const startServer = () => {
	const app = express();

	app.get("/health", (req, res) => {
		res.json({
			status: "ok",
			service: "push-service",
			uptime: process.uptime(),
		});
	});

	const port = process.env.PORT || 4003;
	app.listen(port, () => {
		console.log(`Push service started on port ${port}`);
	});
};
