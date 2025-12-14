# API Documentation

This document describes the API endpoints used by the ProEduvate React application.

## Base URL

**Development**: `http://127.0.0.1:5001/api`
**Production**: Determined automatically based on host

## Authentication

The application uses session-based authentication through the Flask backend.

## Admin Endpoints

### Get All Users
```
GET /api/admin/users
```
Returns all users in the system.

### Add User
```
POST /api/admin/users
Body: {
  name: string,
  role: 'student' | 'teacher' | 'admin' | 'hr'
}
```
Creates a new user.

### Remove User
```
DELETE /api/admin/users/:userId
```
Deletes a user by ID.

### Get Assignments
```
GET /api/admin/assignments
```
Returns all assignments.

### Create Assignment
```
POST /api/admin/assignments
Body: {
  title: string,
  teacherId: string,
  description: string
}
```
Creates a new assignment and assigns it to a teacher.

### Get Status
```
GET /api/admin/status
```
Returns system status including teacher assignments and progress.

### Get Admin Tasks
```
GET /api/admin/tasks
```
Returns tasks created by the admin.

### Update Task
```
PUT /api/admin/tasks/:taskId
Body: {
  title: string,
  teacherId: string,
  description: string
}
```
Updates an existing task.

## Teacher Endpoints

### Get Teacher Assignments
```
GET /api/teacher/assignments
```
Returns assignments created by the teacher.

### Create Assignment
```
POST /api/teacher/assignments
Body: {
  title: string,
  description: string
}
```
Creates a new assignment for students.

### Update Assignment
```
PUT /api/teacher/assignments/:assignmentId
Body: {
  title: string,
  description: string
}
```
Updates an existing assignment.

### Get Submissions
```
GET /api/teacher/submissions
```
Returns all student submissions.

### Get Admin Tasks
```
GET /api/teacher/admin_tasks
```
Returns tasks assigned to the teacher by admin.

### Mark Task Complete
```
POST /api/teacher/admin_tasks/:taskId/complete
```
Marks a task as completed.

## Student Endpoints

### Get Student Assignments
```
GET /api/student/:studentId/assignments
```
Returns assignments for a specific student.

### Submit Assignment
```
POST /api/student/:studentId/assignments/:assignmentId/submit
Content-Type: multipart/form-data
Body: {
  file: File
}
```
Submits a file for an assignment.

### Upload Resume
```
POST /api/student/:studentId/upload_resume
Content-Type: multipart/form-data
Body: {
  resume: File
}
```
Uploads a resume for ATS analysis.

### Get Student Progress
```
GET /api/student/:studentId/progress
```
Returns student's progress data.

## Interview Endpoints

### Start Interview
```
POST /api/interview/start
```
Starts a new interview session and returns questions.

### Submit Answers
```
POST /api/interview/evaluate
Body: {
  questions: string[],
  answers: string[],
  studentId: string
}
```
Submits interview answers for evaluation.

## Chatbot Endpoints

### Send Message
```
POST /api/chatbot/general_query
Body: {
  prompt: string
}
```
Sends a message to the AI chatbot.

### Generate Quiz
```
POST /api/chatbot/generate_quiz
Body: {
  topic: string,
  num_questions: number
}
```
Generates a custom quiz on a specific topic.

## HR Endpoints

### Get Candidates
```
GET /api/hr/candidates
```
Returns all candidates (students) with their evaluation data.

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message"
}
```

## File Upload Format

For file uploads (assignments, resumes), use `multipart/form-data`:

```javascript
const formData = new FormData();
formData.append('file', fileObject);
```

## Error Codes

- `200`: Success
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (not logged in)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `500`: Internal Server Error

## Notes

- All POST/PUT requests expect JSON body (except file uploads)
- File uploads must use `multipart/form-data`
- Authentication is handled via session cookies
- CORS must be enabled on the backend for cross-origin requests
- The `api.js` service layer handles all API calls with Axios
