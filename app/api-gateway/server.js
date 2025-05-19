import express from "express";
import cors from "cors";
import "dotenv/config";
import cookieParser from "cookie-parser";
import http from 'http';
import { WebSocketServer } from 'ws';

import userProfileRouter from "./routes/userProfileRoutes.js";
import attendenceRouter, {setupWebSocketHandler} from "./routes/attendanceRoutes.js";
import chatbotRouter from "./routes/chatbotRoutes.js";
import courseEnrollmentRouter from "./routes/courseEnrollmentRoutes.js";
import sheduleManagerRouter from "./routes/scheduleManagerRoutes.js";
import notificationRouter from "./routes/notificationRoutes.js";


const app = express(); // initializing express app
const port = process.env.PORT || 8000;

const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/realtime/face-recognition' });

const allowedOrigins = ["http://localhost:5173", "https://campus-portal.ovindu.com"];

app.use(express.json());
app.use(cookieParser());
app.use(cors({ origin: allowedOrigins, credentials: true })); // aloowed to send cookies in the response from the express app

// API Endpoints
app.get("/", (req, res) => {
  res.send("API is Working");
});
// app.use("/api/auth", authRouter);
app.use("/api-gateway/user-profile", userProfileRouter);
app.use("/api-gateway/attendance", attendenceRouter);
app.use("/api-gateway/chatbot", chatbotRouter);
app.use("/api-gateway/courses", courseEnrollmentRouter);
app.use("/api-gateway/schedule-manager", sheduleManagerRouter);
app.use("/api-gateway/notifications", notificationRouter);

// Delegate WS handling to the route
setupWebSocketHandler(wss);

// app.listen(port, () => {
//   console.log(`Server is running on port http://localhost:${port}/`);
// });

server.listen(port, () => {
  console.log(`Server is running on port http://localhost:${port}/`);
});

