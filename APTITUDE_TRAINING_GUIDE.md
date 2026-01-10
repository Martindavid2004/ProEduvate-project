# AI-Based Aptitude Training System - Feature Guide

## Overview
The Aptitude Training System is a comprehensive AI-powered module integrated into the Student Page's Placement Training section. It provides students with interactive learning, practice questions, and timed tests for 20 different aptitude topics.

## Features

### 1. Topic Selection
Students can choose from 20 different aptitude topics:
- **Number System** - Binary, Octal, Hexadecimal conversions
- **HCF & LCM** - Highest Common Factor and Least Common Multiple
- **Percentage** - Percentage calculations and applications
- **Profit & Loss** - Business mathematics
- **Simple & Compound Interest** - Financial calculations
- **Time & Work** - Work efficiency problems
- **Time & Distance** - Speed, distance, time calculations
- **Average** - Mean, median, mode
- **Ratio & Proportion** - Ratio analysis and proportions
- **Ages** - Age-based logical problems
- **Alligation & Mixture** - Mixture problems
- **Permutation & Combination** - Counting principles
- **Probability** - Probability theory and applications
- **Data Interpretation** - Charts, graphs, tables analysis
- **Logical Reasoning** - Pattern recognition and logic
- **Series & Sequences** - Number and letter series
- **Blood Relations** - Family relationship problems
- **Coding-Decoding** - Pattern-based coding
- **Direction Sense** - Directional reasoning
- **Calendar** - Date and day calculations

### 2. Learning Modes

#### Learn Mode
- **Video Tutorials**: Watch embedded YouTube videos for each topic
- **AI-Generated Concepts**: Get detailed explanations and key concepts
- **Key Points**: Important formulas, shortcuts, and tips
- **Examples**: Step-by-step solved examples

#### Practice Mode
- **10 Practice Questions**: AI-generated practice problems
- **Detailed Solutions**: Step-by-step explanations for each answer
- **Instant Feedback**: See correct answers immediately
- **No Time Limit**: Practice at your own pace

#### Test Mode
- **50 Questions**: Comprehensive test covering the topic
- **60-Minute Timer**: Countdown timer with auto-submit
- **Camera Proctoring**: Live camera feed monitoring
- **Question Navigator**: Grid showing answered/unanswered questions (10 columns × 5 rows)
- **Screen Toggle Detection**: Prevents tab switching during test
- **Auto-Submit**: Automatically submits when time expires

### 3. Evaluation & Results
- **Instant Scoring**: Get results immediately after submission
- **Detailed Analysis**: 
  - Score percentage
  - Time taken
  - Questions breakdown (correct/incorrect/unanswered)
  - Performance level (Excellent/Good/Average/Needs Improvement)
- **Answer Review**: See all questions with:
  - Your answer
  - Correct answer
  - Detailed explanation
  - Color coding (Green = Correct, Red = Incorrect, Gray = Unanswered)

### 4. Progress Tracking
- **Test History**: View all completed tests
- **Performance Trends**: Track improvement over time
- **Topic-wise Analysis**: See which topics need more practice
- **Average Score**: Overall performance metric

## Technical Architecture

### Backend Components

#### 1. Aptitude Configuration (`aptitude_config.py`)
```python
APTITUDE_TOPICS = [
    {
        'id': 'number_system',
        'name': 'Number System',
        'description': 'Binary, Octal, Hexadecimal conversions',
        'category': 'Quantitative Aptitude'
    },
    # ... 19 more topics
]

VIDEO_RESOURCES = {
    'number_system': 'https://www.youtube.com/watch?v=...',
    # ... video URLs for each topic
}
```

#### 2. Aptitude Service (`aptitude_service.py`)
Key functions:
- `generate_aptitude_questions(topic, difficulty, num_questions)` - AI generates test questions
- `generate_practice_questions(topic, num_questions)` - Creates practice problems
- `evaluate_aptitude_test(questions, user_answers)` - Scores and analyzes results
- `get_topic_concepts(topic)` - Fetches learning materials
- `get_performance_analysis(score)` - Provides feedback

#### 3. API Routes (`aptitude_routes.py`)
Endpoints:
- `GET /api/aptitude/topics` - List all topics
- `GET /api/aptitude/concepts/<topic>` - Get learning materials
- `GET /api/aptitude/practice/<topic>` - Generate practice questions
- `POST /api/aptitude/test/generate` - Create new test
- `POST /api/aptitude/test/submit` - Evaluate and save results
- `GET /api/aptitude/progress/<student_id>` - Get statistics

### Frontend Component

#### AptitudeTraining.js (1000+ lines)
State Management:
- `currentMode` - 'select'|'options'|'learn'|'practice'|'test'|'results'
- `selectedTopic` - Current topic object
- `questions` - Array of test/practice questions
- `userAnswers` - Student's answer selections
- `timeRemaining` - Countdown timer (3600 seconds)
- `cameraStream` - MediaStream from camera
- `testResults` - Evaluation results from AI

Key Features:
- Responsive grid layouts
- Real-time timer countdown
- Camera permission handling
- Answer validation
- Progress persistence

## Usage Flow

1. **Student Login** → Navigate to Placement Training
2. **Select Training Type** → Choose "Non-Technical Skills"
3. **Select Category** → Click "Aptitude & Reasoning"
4. **Choose Topic** → Select from 20 topics grid
5. **Select Mode**:
   - **Learn** → Watch video + Read concepts → Back to options
   - **Practice** → Solve 10 questions → See solutions → Back to options
   - **Test** → Allow camera → Start 50-question test → Submit → View results
6. **View Progress** → See all test history and performance metrics

## Camera Proctoring

### Setup
- Browser requests camera permission on test start
- Live video feed displayed in top-right corner
- Red "REC" indicator shows recording status

### Privacy Notes
- Video is NOT recorded or stored
- Only used for live monitoring
- Can be disabled by closing/refreshing page
- Camera access is released after test submission

## AI Question Generation

### How It Works
1. **Topic Selection**: Student chooses aptitude topic
2. **Prompt Engineering**: System sends structured prompt to Google Gemini AI:
   ```
   Generate 50 multiple-choice aptitude questions on [topic].
   Include: question text, 4 options (A/B/C/D), correct answer, explanation
   Format: JSON array
   ```
3. **AI Response**: Gemini generates unique questions each time
4. **Validation**: System validates JSON structure and question format
5. **Display**: Questions shown one at a time with navigation

### Quality Control
- Questions follow standard aptitude patterns
- Difficulty matched to placement requirements
- Detailed explanations for learning
- Variety in question types and complexity

## Adding New Topics

To add a new aptitude topic:

1. **Update `aptitude_config.py`**:
```python
APTITUDE_TOPICS.append({
    'id': 'new_topic_id',
    'name': 'New Topic Name',
    'description': 'Topic description',
    'category': 'Quantitative Aptitude'  # or 'Logical Reasoning'
})
```

2. **Add Video Resource**:
```python
VIDEO_RESOURCES['new_topic_id'] = 'https://www.youtube.com/embed/VIDEO_ID'
```

3. **No frontend changes needed** - Component automatically loads topics from API

## Troubleshooting

### Camera Not Working
- Check browser permissions (Settings → Privacy → Camera)
- Ensure HTTPS or localhost (camera requires secure context)
- Try different browser (Chrome/Firefox recommended)

### Questions Not Generating
- Check backend logs for AI API errors
- Verify Google Gemini API key is valid
- Ensure `GOOGLE_API_KEY` environment variable is set

### Timer Not Starting
- Check browser console for JavaScript errors
- Verify component is properly mounted
- Ensure `useEffect` cleanup is working

### Results Not Saving
- Check MongoDB connection
- Verify `aptitude_results` collection exists
- Check student authentication token

## Performance Metrics

### Response Times (Expected)
- Topic list load: < 500ms
- Practice questions: 2-3 seconds
- Test generation: 5-8 seconds (AI processing)
- Test evaluation: 2-4 seconds
- Results save: < 1 second

### Browser Compatibility
- Chrome 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅
- Edge 90+ ✅

## Future Enhancements

### Planned Features
- [ ] Adaptive difficulty (AI adjusts based on performance)
- [ ] Multiplayer challenges
- [ ] Leaderboards
- [ ] Topic recommendations based on weak areas
- [ ] Export results as PDF
- [ ] Practice mode with hints
- [ ] Timed practice sessions
- [ ] Detailed analytics dashboard

### AI Improvements
- [ ] Natural language question input
- [ ] Personalized question difficulty
- [ ] Learning path recommendations
- [ ] Performance prediction

## API Reference

### Get All Topics
```http
GET /api/aptitude/topics
Response: Array of topic objects
```

### Get Topic Concepts
```http
GET /api/aptitude/concepts/<topic_id>
Response: { concepts: string, video_url: string }
```

### Generate Practice Questions
```http
GET /api/aptitude/practice/<topic_id>?num=10
Response: { questions: Array[10] }
```

### Generate Test
```http
POST /api/aptitude/test/generate
Body: { topic_id: string, num_questions: 50 }
Response: { test_id: string, questions: Array[50] }
```

### Submit Test
```http
POST /api/aptitude/test/submit
Body: { 
  test_id: string,
  student_id: string,
  questions: Array,
  user_answers: Array,
  time_taken: number
}
Response: { score, analysis, correct_answers, explanations }
```

### Get Progress
```http
GET /api/aptitude/progress/<student_id>
Response: { 
  tests_taken: number,
  average_score: number,
  tests: Array,
  topics_covered: Array
}
```

## Database Schema

### Collection: `aptitude_results`
```javascript
{
  _id: ObjectId,
  student_id: string,
  test_id: string,
  topic_id: string,
  topic_name: string,
  score: number,
  total_questions: number,
  correct_answers: number,
  time_taken: number,
  submitted_at: ISODate,
  questions: Array[{
    question: string,
    options: Array[4],
    user_answer: string,
    correct_answer: string,
    explanation: string
  }]
}
```

## Security Considerations

1. **Authentication**: All endpoints require JWT token
2. **Input Validation**: Topic IDs and answers are sanitized
3. **Rate Limiting**: API calls limited to prevent abuse
4. **Camera Privacy**: No video recording, only live monitoring
5. **Data Encryption**: Results stored with MongoDB encryption

## Support

For issues or questions:
1. Check this guide first
2. Review backend logs: `ProeduVate-main/backend/app.log`
3. Check browser console for frontend errors
4. Contact: ProEduVate Support Team

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Component**: Student Page → Placement Training → Aptitude & Reasoning
