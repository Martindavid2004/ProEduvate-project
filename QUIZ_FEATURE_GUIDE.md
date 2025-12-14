# Quiz Feature Implementation Guide

## Overview
The quiz feature allows teachers to create AI-generated quizzes that students can take, submit, and receive automatic evaluation with scores tracked in their progress.

## Complete Workflow

### 1. Teacher Creates Quiz Assignment

**Location:** Teacher Page → Create Assignment Tab

**Steps:**
1. Navigate to "Create Assignment" tab
2. Enter assignment title (e.g., "Python Programming Quiz")
3. Select "Quiz" from the Assignment Type dropdown
4. Add description/instructions
5. Click "Create Assignment"
6. **AI automatically generates 10 quiz questions** based on the title
7. Quiz is saved with questions and appears in "My Assignments"

**Technical Details:**
- Uses `chatbotAPI.generateQuiz(topic, 10)` to generate questions
- Questions are stored in MongoDB with the assignment
- Field: `quizQuestions` array in `teacher_assignments_collection`

### 2. Student Views Quiz Assignment

**Location:** Student Page → My Assignments Tab

**Display:**
- Quiz assignments show with purple "Quiz" badge
- Displays number of questions (📝 10 questions)
- "Start Quiz" button (purple) instead of file upload
- Shows quiz score if already submitted

**Technical Details:**
- Fetches assignments from `/api/student/<id>/assignments`
- Backend includes `quiz_questions` array for Quiz type assignments
- Distinguishes quiz from regular assignments by `type` field

### 3. Student Takes Quiz

**Location:** Student clicks "Start Quiz" button

**Features:**
- Modal displays all 10 quiz questions
- Each question has a text area for answers
- Students can scroll through all questions
- Can see progress (e.g., "answered 7 out of 10")
- Confirmation prompt if submitting incomplete quiz
- "Submit Quiz" button to finalize answers

**Technical Details:**
- Quiz modal state: `quizModalOpen`, `currentQuiz`, `quizAnswers`
- Answers stored in object: `{0: "answer1", 1: "answer2", ...}`
- All questions shown at once (not one-by-one)

### 4. AI Evaluation

**Automatic Process:**
1. Student submits quiz
2. Frontend sends questions + answers to AI via `chatbotAPI.sendMessage()`
3. AI evaluates each answer and provides:
   - Overall score (0-100%)
   - Per-question feedback
   - Points per question
   - Overall feedback/comments

**Evaluation Format:**
```json
{
  "score": 85,
  "questionFeedback": [
    {
      "question": "What is Python?",
      "answer": "Python is a programming language",
      "feedback": "Correct! Good understanding.",
      "points": 10
    }
  ],
  "overallFeedback": "Great job! Strong understanding of concepts."
}
```

### 5. Quiz Results Display

**Immediate Feedback:**
- Score displayed prominently (large purple number)
- Overall feedback message
- Detailed per-question breakdown:
  - Each question shown with student's answer
  - AI feedback for each answer
  - Points earned per question
- "Close" button to return to assignments

**After Closing:**
- Assignment marked as "Submitted" with green checkmark
- Quiz score displayed next to submission status
- Score added to student progress

### 6. Progress Tracking

**Student Progress Dashboard:**
- New "Quiz Average" card (orange) showing average quiz score
- Displays number of quizzes taken
- Formula: Average of all quiz scores
- Shown alongside Interview Score and Resume Score

**Student Progress API Response:**
```json
{
  "quizScore": 85.5,
  "averageQuizScore": 85.5,
  "totalQuizzes": 3,
  "submittedAssignments": 8,
  ...
}
```

### 7. Teacher Views Quiz Submissions

**Location:** Teacher Page → Submissions Tab

**Display:**
- Quiz submissions shown with "Quiz" badge
- Quiz score displayed prominently (purple badge)
- Example: "Score: 85%"
- Can view submission file (contains JSON with answers + evaluation)
- See when quiz was submitted

**Features:**
- Expandable student list showing all assignments
- Filter/search by student name
- View quiz scores at a glance
- Access detailed submission data

## Database Structure

### Assignment Document (MongoDB)
```javascript
{
  "_id": ObjectId("..."),
  "title": "Python Programming Quiz",
  "description": "Test your Python knowledge",
  "type": "Quiz",
  "quizQuestions": [
    "What is Python?",
    "Explain list comprehension",
    // ... 8 more questions
  ],
  "createdBy": "teacher",
  "dueDate": "2024-12-20T00:00:00",
  "createdAt": "2024-12-14T10:30:00"
}
```

### Submission Document (MongoDB)
```javascript
{
  "_id": ObjectId("..."),
  "assignment_id": "abc123",
  "student_id": "student456",
  "filename": "quiz_answers.json",
  "file_path": "/uploads/submissions/abc123/student456_quiz_answers.json",
  "quiz_score": 85.5,
  "submitted_at": ISODate("2024-12-14T11:00:00"),
  "notes": ""
}
```

### User Document (Updated)
```javascript
{
  "_id": ObjectId("..."),
  "name": "John Doe",
  "role": "student",
  "quizScore": 85.5,
  "averageQuizScore": 85.5,
  "submittedAssignments": 8,
  "interviewScore": 90,
  "resumeScore": 78,
  ...
}
```

## API Endpoints

### Quiz Creation
- **POST** `/api/teacher/assignments`
- Body: `{ title, description, type: "Quiz", quizQuestions: [...] }`

### Get Student Assignments (with quizzes)
- **GET** `/api/student/<student_id>/assignments`
- Returns assignments with `quiz_questions` array for Quiz type

### Submit Quiz
- **POST** `/api/student/assignments/<assignment_id>/submit`
- FormData: `assignment_file`, `student_id`, `quiz_score`
- Accepts JSON file with answers and evaluation

### Get Student Progress
- **GET** `/api/student/<student_id>/progress`
- Returns `quizScore`, `averageQuizScore`, `totalQuizzes`

### Get Submissions (Teacher)
- **GET** `/api/teacher/submissions`
- Returns all submissions including quiz scores

## Key Features

### ✅ AI-Generated Questions
- Automatic generation of 10 relevant questions
- Based on assignment title/topic
- Uses Ollama/ChatGPT API

### ✅ Automatic Evaluation
- AI evaluates student answers
- Provides detailed feedback
- Assigns score (0-100%)

### ✅ Progress Tracking
- Quiz scores averaged
- Displayed in progress dashboard
- Tracked separately from assignments

### ✅ Teacher Dashboard
- View all quiz submissions
- See scores at a glance
- Monitor student performance

### ✅ Student Experience
- Easy-to-use quiz interface
- Immediate feedback
- Clear score display
- Progress tracking

## File Locations

### Frontend
- **Student Quiz UI:** `my-app/src/pages/StudentPage.js`
  - Lines: ~30-150 (quiz state & handlers)
  - Lines: ~550-650 (quiz modal)
- **Teacher Submissions:** `my-app/src/pages/TeacherPage.js`
  - Lines: ~350-450 (submissions with quiz scores)

### Backend
- **Student Routes:** `ProeduVate-main/backend/app/routes/student_routes.py`
  - Quiz submission: Lines ~200-280
  - Progress with quiz scores: Lines ~100-150
  - Assignment with questions: Lines ~70-100
- **Teacher Routes:** `ProeduVate-main/backend/app/routes/teacher_routes.py`
  - Create quiz: Lines ~40-80
  - Submissions with scores: Lines ~230-280

## Usage Example

1. **Teacher:** Creates "JavaScript Basics Quiz"
2. **System:** Generates 10 questions about JavaScript
3. **Student:** Sees quiz in assignments, clicks "Start Quiz"
4. **Student:** Answers all 10 questions, clicks "Submit"
5. **System:** AI evaluates answers, calculates score (e.g., 88%)
6. **Student:** Sees results immediately with detailed feedback
7. **System:** Updates progress - "Quiz Average: 88%"
8. **Teacher:** Views submission - sees 88% score

## Benefits

- **Time-Saving:** Automatic question generation and grading
- **Consistent:** AI provides objective evaluation
- **Immediate Feedback:** Students get instant results
- **Comprehensive:** Detailed feedback helps learning
- **Trackable:** Progress monitoring for teachers and students
- **Scalable:** Works for any number of students

## Future Enhancements

- Multiple choice questions with auto-grading
- Question bank/reusability
- Timed quizzes
- Randomized question order
- Export quiz results to CSV
- Quiz analytics dashboard
