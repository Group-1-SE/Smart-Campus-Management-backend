// attendanceRoutes.js
import express from "express";
import { scheduleAssignment, getAssignment, getAllAssignments, updateAssignment, deleteAssignment, scheduleExam, getExam, getAllExams, updateExam, deleteExam} from "../controllers/scheduleManagerController.js";
const scheduleManagerRouter = express.Router();

// define routes
scheduleManagerRouter.get("/", (req, res) => {
  res.send("Schedule manager Home");
});

scheduleManagerRouter.post("/schedule-assignment", scheduleAssignment);
scheduleManagerRouter.post("/get-assignment", getAssignment);
scheduleManagerRouter.get("/get-all-assignments", getAllAssignments);
scheduleManagerRouter.put("/update-assignment", updateAssignment);
scheduleManagerRouter.delete("/delete-assignment", deleteAssignment);

scheduleManagerRouter.post("/schedule-exam", scheduleExam);
scheduleManagerRouter.post("/get-exam", getExam);
scheduleManagerRouter.get("/get-all-exams", getAllExams);
scheduleManagerRouter.put("/update-exam", updateExam);
scheduleManagerRouter.delete("/delete-exam", deleteExam);

export default scheduleManagerRouter;   // <-- IMPORTANT
