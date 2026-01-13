# AI-Based Group Discussion (GD) Round - Implementation Guide

## Overview
The AI-Based Group Discussion (GD) Round feature allows students to practice group discussions with AI-powered agents. This comprehensive implementation includes frontend components, backend APIs, and admin controls.

## Table of Contents
1. [Tech Stack](#tech-stack)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Installation & Setup](#installation--setup)
5. [API Documentation](#api-documentation)
6. [Frontend Components](#frontend-components)
7. [Admin Configuration](#admin-configuration)
8. [Usage Guide](#usage-guide)
9. [Evaluation Criteria](#evaluation-criteria)
10. [Customization](#customization)

---

## Tech Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: MongoDB (Collections: gd_rounds, gd_results, gd_notifications)
- **AI Integration**: OpenAI API (GPT-3.5-turbo)
- **APIs**: RESTful APIs for GD management

### Frontend
- **Framework**: React.js
- **UI Library**: Tailwind CSS, Lucide React (icons)
- **Media**: Web Speech API (Speech Recognition & Synthesis)
- **State Management**: React Hooks

### AI Features
- **Speech Recognition**: Web Speech API (webkitSpeechRecognition)
- **Text-to-Speech**: Web Speech Synthesis API
- **AI Agent Responses**: OpenAI GPT-3.5-turbo
- **Evaluation**: AI-powered scoring based on multiple criteria

---

## Features

### Core Features
1. **Real-time GD Simulation**
   - Live interaction with 5-10 AI agents
   - Voice and text-based communication
   - Real-time speaker tracking
   - Dynamic conversation flow

2. **Topic Selection**
   - 15+ pre-configured topics
   - 30-second selection timer
   - Custom topic support
   - Topic-based AI responses

3. **AI Agent Configuration**
   - Configurable number of agents (5-10)
   - Male/female voice selection
   - Different personalities (analytical, creative, diplomatic, aggressive, supportive)
   - Intelligent response generation

4. **Camera & Microphone Integration**
   - Live video feed from user's camera
   - Microphone input for voice responses
   - Real-time audio transcription
   - Controls for enabling/disabling media

5. **Comprehensive Evaluation**
   - Multi-criteria assessment
   - Weighted scoring system
   - Top 3 ranking system
   - Detailed performance breakdown

6. **Notifications & Scheduling**
   - GD round scheduling by admin
   - Push notifications to assigned students
   - Email notifications (configurable)
   - Round status tracking

### Enhanced Features
- **3-minute preparation time** before GD starts
- **Configurable duration** (10-30 minutes)
- **Real-time transcript** of all responses
- **Post-GD summary** with AI insights
- **Historical results** tracking
- **Progress analytics**

---

## Architecture

### Database Schema

#### `gd_rounds` Collection
```javascript
{
  "_id": ObjectId,
  "title": String,
  "scheduled_time": ISODate,
  "duration": Number, // minutes
  "topic": String,
  "allow_topic_selection": Boolean,
  "available_topics": [String],
  "num_ai_agents": Number,
  "ai_agent_voices": [String], // 'male' or 'female'
  "assigned_students": [String], // student IDs
  "evaluation_criteria": Object,
  "created_by": String,
  "created_at": ISODate,
  "status": String, // 'scheduled', 'in_progress', 'completed'
  "responses": [Object]
}
```

#### `gd_results` Collection
```javascript
{
  "_id": ObjectId,
  "round_id": String,
  "student_id": String,
  "all_participants": [Object],
  "top_3": [Object],
  "student_rank": Number,
  "evaluation_criteria": Object,
  "completed_at": ISODate
}
```

#### `gd_notifications` Collection
```javascript
{
  "_id": ObjectId,
  "student_id": String,
  "gd_round_id": String,
  "title": String,
  "message": String,
  "type": String,
  "read": Boolean,
  "created_at": ISODate
}
```

### API Endpoints

#### Student APIs
- `GET /api/gd/topics` - Get available GD topics
- `GET /api/gd/evaluation-criteria` - Get evaluation criteria
- `GET /api/gd/student/:id/rounds` - Get student's GD rounds
- `GET /api/gd/notifications/:id` - Get student notifications
- `POST /api/gd/round/:id/select-topic` - Select GD topic
- `POST /api/gd/round/:id/start` - Start GD round
- `POST /api/gd/round/:id/submit-response` - Submit response
- `POST /api/gd/round/:id/evaluate` - Evaluate and complete GD
- `GET /api/gd/results/:id` - Get student's results

#### Admin APIs
- `POST /api/gd/schedule` - Schedule a GD round
- `GET /api/gd/rounds` - Get all GD rounds
- `GET /api/gd/round/:id` - Get specific round details
- `GET /api/gd/admin/config` - Get GD configuration
- `POST /api/gd/admin/config` - Update GD configuration
- `PUT /api/gd/notifications/:id/mark-read` - Mark notification as read

---

## Installation & Setup

### Backend Setup

1. **Install Dependencies**
```bash
cd ProeduVate-main/backend
pip install openai pymongo flask flask-cors python-dotenv
```

2. **Environment Variables**
Add to `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
MONGO_URI=your_mongodb_connection_string
```

3. **Register Blueprint**
Already done in `app/__init__.py`:
```python
from .routes.gd_routes import gd_bp
app.register_blueprint(gd_bp)
```

4. **Start Backend Server**
```bash
python run.py
```

### Frontend Setup

1. **Install Dependencies** (if needed)
```bash
cd my-app
npm install
```

2. **Components Added**
- `src/components/GDRound.js` - Main GD component
- Integrated into `src/pages/StudentPage.js`

3. **Start Frontend**
```bash
npm start
```

---

## API Documentation

### 1. Get GD Topics
**Endpoint**: `GET /api/gd/topics`

**Response**:
```json
{
  "topics": [
    "Impact of Artificial Intelligence on Employment",
    "Remote Work vs Office Work",
    ...
  ],
  "success": true
}
```

### 2. Schedule GD Round
**Endpoint**: `POST /api/gd/schedule`

**Request Body**:
```json
{
  "title": "Weekly GD Session",
  "scheduled_time": "2026-01-15T10:00:00Z",
  "duration": 20,
  "topic": "Impact of AI on Employment",
  "allow_topic_selection": false,
  "num_ai_agents": 7,
  "assigned_students": ["student1", "student2"],
  "evaluation_criteria": {
    "communication_skills": {"weight": 25},
    "leadership": {"weight": 20},
    ...
  },
  "created_by": "admin_id"
}
```

**Response**:
```json
{
  "message": "GD Round scheduled successfully",
  "gd_round": {...},
  "success": true
}
```

### 3. Start GD Round
**Endpoint**: `POST /api/gd/round/:id/start`

**Request Body**:
```json
{
  "student_id": "student123"
}
```

**Response**:
```json
{
  "message": "GD round started",
  "round": {
    "_id": "round_id",
    "topic": "Selected Topic",
    "duration": 20,
    "num_ai_agents": 7
  },
  "success": true
}
```

### 4. Evaluate GD Round
**Endpoint**: `POST /api/gd/round/:id/evaluate`

**Request Body**:
```json
{
  "student_id": "student123",
  "responses": [
    {
      "participant": "user",
      "name": "You",
      "text": "Response text...",
      "timestamp": "2026-01-11T10:00:00Z"
    }
  ],
  "evaluation_criteria": {...},
  "num_ai_agents": 7
}
```

**Response**:
```json
{
  "message": "GD round evaluated successfully",
  "results": {
    "round_id": "...",
    "student_id": "...",
    "all_participants": [...],
    "top_3": [...],
    "student_rank": 2,
    "evaluation_criteria": {...}
  },
  "success": true
}
```

---

## Frontend Components

### GDRound Component

**Location**: `my-app/src/components/GDRound.js`

**Props**:
- `gdRound`: GD round configuration object
- `studentId`: Current student ID
- `onClose`: Function to close the component
- `onComplete`: Function called when GD completes

**Phases**:
1. **Pre-start**: Introduction and instructions
2. **Topic Selection**: Select topic within 30 seconds
3. **Preparation**: 3-minute preparation time
4. **Active**: Live GD session
5. **Evaluating**: AI evaluation in progress
6. **Completed**: Display results

**Key Features**:
```javascript
// Camera & Microphone
- initializeMedia() - Request camera/mic access
- toggleCamera() - Enable/disable camera
- toggleMic() - Enable/disable microphone

// Speech
- initializeSpeechRecognition() - Setup speech recognition
- speakText() - Text-to-speech for AI agents
- startUserSpeaking() - Begin user's turn
- stopUserSpeaking() - End user's turn

// AI Agents
- speakAIAgent() - Trigger AI agent response
- generateAIResponse() - Generate AI content
- scheduleNextSpeaker() - Manage turn-taking

// Evaluation
- endGDRound() - Complete and evaluate GD
```

### Integration in StudentPage

**Location**: `my-app/src/pages/StudentPage.js`

**New State Variables**:
```javascript
const [gdRoundOpen, setGdRoundOpen] = useState(false);
const [currentGDRound, setCurrentGDRound] = useState(null);
const [gdNotifications, setGdNotifications] = useState([]);
const [gdResults, setGdResults] = useState([]);
```

**New Functions**:
```javascript
const startGDRound = async () => {...}
const handleGDComplete = async (results) => {...}
const closeGDRound = () => {...}
```

**Access Point**:
Navigate to: **Student Dashboard** → **Placement Training** → **Non-Technical Skills** → **AI Group Discussion**

---

## Admin Configuration

### Scheduling GD Rounds

Admins can schedule GD rounds for students using the admin API:

```javascript
// Example admin schedule function
const scheduleGDRound = async () => {
  const response = await fetch('http://localhost:5000/api/gd/schedule', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: "Monthly GD Assessment",
      scheduled_time: "2026-01-20T14:00:00Z",
      duration: 20,
      topic: "Climate Change and Corporate Responsibility",
      allow_topic_selection: false,
      num_ai_agents: 7,
      ai_agent_voices: ['male', 'female', 'male', 'female', 'male', 'female', 'male'],
      assigned_students: ["student1", "student2", "student3"],
      evaluation_criteria: {
        communication_skills: { weight: 25, description: "..." },
        leadership: { weight: 20, description: "..." },
        logical_reasoning: { weight: 20, description: "..." },
        content_relevance: { weight: 20, description: "..." },
        listening_team_dynamics: { weight: 15, description: "..." }
      },
      created_by: "admin_id"
    })
  });
  
  const data = await response.json();
  if (data.success) {
    alert('GD Round scheduled successfully!');
  }
};
```

### Configuring Topics

Admins can modify available topics in:
`backend/app/routes/gd_routes.py`

```python
DEFAULT_GD_TOPICS = [
    "Impact of Artificial Intelligence on Employment",
    "Remote Work vs Office Work: Future of Workplace",
    # Add more topics here
]
```

### Configuring Evaluation Criteria

Modify weights and descriptions:
```python
DEFAULT_EVALUATION_CRITERIA = {
    "communication_skills": {
        "weight": 25,  # Percentage weight
        "description": "Clarity, articulation, and language proficiency"
    },
    "leadership": {
        "weight": 20,
        "description": "Initiative taking and group steering ability"
    },
    # Add more criteria
}
```

---

## Usage Guide

### For Students

1. **Access GD Round**
   - Login to student portal
   - Navigate to **Placement Training**
   - Select **Non-Technical Skills**
   - Click on **AI Group Discussion**

2. **Before Starting**
   - Ensure camera and microphone permissions are granted
   - Check audio/video settings
   - Read instructions carefully

3. **Topic Selection** (if enabled)
   - Review available topics
   - Select within 30 seconds
   - Click to confirm selection

4. **Preparation Phase**
   - 3 minutes to organize thoughts
   - Topic is displayed
   - Plan your key points

5. **During GD**
   - Wait for your turn to speak
   - Speak clearly when indicator shows
   - Can type or use voice
   - Listen to AI agents
   - Build on others' points

6. **Controls**
   - Camera toggle (enable/disable video)
   - Microphone toggle (mute/unmute)
   - Volume toggle (mute AI voices)
   - End Early button (if needed)

7. **After Completion**
   - View your rank and score
   - Check detailed evaluation
   - See top 3 performers
   - Review performance metrics

### For Admins

1. **Schedule GD Rounds**
   - Use admin API to create rounds
   - Assign students
   - Set duration and topic
   - Configure AI agents

2. **Monitor Progress**
   - View scheduled rounds
   - Check completion status
   - Review student performance

3. **Configure Settings**
   - Update topics list
   - Modify evaluation criteria
   - Set default parameters

---

## Evaluation Criteria

### Default Criteria (Total: 100%)

1. **Communication Skills (25%)**
   - Clarity of expression
   - Language proficiency
   - Articulation
   - Voice modulation
   - Confidence

2. **Leadership (20%)**
   - Initiative taking
   - Guiding discussion
   - Encouraging others
   - Decision making
   - Direction setting

3. **Logical Reasoning (20%)**
   - Quality of arguments
   - Critical thinking
   - Evidence-based points
   - Analytical approach
   - Problem-solving

4. **Content Relevance (20%)**
   - Topic knowledge
   - Point relevance
   - Depth of understanding
   - Real-world examples
   - Practical insights

5. **Listening & Team Dynamics (15%)**
   - Active listening
   - Building on others' points
   - Respectful interruptions
   - Team collaboration
   - Turn-taking etiquette

### Scoring System

- Each criterion scored 0-100
- Weighted average calculated
- Final score = Σ(criterion_score × weight/100)
- Students ranked by final score
- Top 3 identified automatically

---

## Customization

### Changing AI Agent Personalities

Edit `backend/app/services/gd_service.py`:

```python
def generate_ai_agent_response(self, topic, context, agent_personality, agent_gender):
    personality_prompts = {
        'analytical': 'You are analytical and data-driven...',
        'creative': 'You are creative and innovative...',
        # Add custom personalities
        'technical': 'You focus on technical aspects...',
        'business': 'You have a business perspective...',
    }
```

### Adding New Topics

Two methods:

1. **Code-based** (gd_routes.py):
```python
DEFAULT_GD_TOPICS.append("Your New Topic Here")
```

2. **Database-based** (implement admin UI):
Store topics in MongoDB collection and fetch dynamically

### Adjusting GD Duration

Frontend component (`GDRound.js`):
```javascript
// Default durations
const [gdTimer, setGdTimer] = useState(gdRound?.duration * 60 || 1200);
```

Backend API (`gd_routes.py`):
```python
"duration": data.get("duration", 20),  # minutes
```

### Customizing Voice Settings

Edit voice configuration in `gd_service.py`:
```python
def text_to_speech_config(self, gender='male'):
    voices = {
        'male': {
            'rate': 1.0,
            'pitch': 0.9,
            'voice_name': 'Microsoft David Desktop'
        },
        'female': {
            'rate': 1.0,
            'pitch': 1.1,
            'voice_name': 'Microsoft Zira Desktop'
        }
    }
```

### Modifying Number of AI Agents

Frontend (`StudentPage.js`):
```javascript
const mockGDRound = {
  num_ai_agents: 7,  // Change to 5-10
```

Backend validation (`gd_routes.py`):
```python
"num_ai_agents": data.get("num_ai_agents", 7),  # Default 7
```

---

## Advanced Features

### 1. AI-Powered Evaluation

The system uses OpenAI GPT-3.5-turbo to evaluate student responses:

```python
# In gd_service.py
def evaluate_participant_response(self, response_text, evaluation_criteria, topic):
    # AI analyzes response and provides scores
    # Considers context, relevance, and quality
```

### 2. Real-time Transcription

Uses Web Speech API for live transcription:
```javascript
recognitionRef.current.onresult = (event) => {
  // Process speech-to-text
  // Update transcript in real-time
}
```

### 3. Dynamic Speaker Management

Intelligent turn-taking system:
- 40% chance user speaks next
- 60% chance AI agent speaks
- Agents with fewer turns prioritized
- Natural conversation flow

### 4. Performance Analytics

Track historical performance:
- View all past GD rounds
- Compare scores over time
- Identify improvement areas
- Generate progress reports

---

## Troubleshooting

### Common Issues

1. **Camera/Microphone Not Working**
   - Check browser permissions
   - Ensure HTTPS connection (required for media access)
   - Try different browser (Chrome recommended)

2. **Speech Recognition Not Working**
   - Use Chrome or Edge browser
   - Check microphone input levels
   - Ensure quiet environment

3. **AI Responses Not Generating**
   - Verify OpenAI API key in `.env`
   - Check API quota/limits
   - Review backend logs

4. **Evaluation Failing**
   - Check backend connection
   - Verify MongoDB connection
   - Review error logs

### Browser Compatibility

**Recommended**: Chrome 90+, Edge 90+
**Supported**: Firefox 85+ (limited speech features)
**Not Supported**: IE, Safari (limited Web Speech API)

---

## Future Enhancements

1. **Video Recording**
   - Record entire GD session
   - Playback for review
   - Share with mentors

2. **Advanced Analytics**
   - Speaking time tracking
   - Interruption analysis
   - Eye contact detection (using ML)
   - Facial expression analysis

3. **Multilingual Support**
   - GD in multiple languages
   - Language proficiency scoring
   - Accent neutralization tips

4. **Team GD Mode**
   - Multiple real students
   - Mixed AI + human participants
   - Group performance metrics

5. **Industry-Specific Topics**
   - Finance sector topics
   - Technology industry topics
   - Healthcare topics
   - Custom topic categories

6. **Mentorship Integration**
   - Teacher can observe live
   - Real-time feedback
   - Post-GD mentoring sessions

---

## Security Considerations

1. **Authentication**
   - Verify user identity before GD
   - Secure API endpoints
   - Token-based authentication

2. **Data Privacy**
   - Encrypt stored recordings
   - Anonymize evaluation data
   - GDPR compliance

3. **Content Moderation**
   - Filter inappropriate content
   - Monitor AI responses
   - Report mechanism

---

## Performance Optimization

1. **Backend**
   - Cache frequently used topics
   - Optimize MongoDB queries
   - Use connection pooling
   - Implement rate limiting

2. **Frontend**
   - Lazy load components
   - Optimize media streams
   - Minimize re-renders
   - Efficient state management

3. **AI Integration**
   - Batch API requests when possible
   - Cache AI responses for similar inputs
   - Implement fallback mechanisms

---

## Support & Maintenance

### Logs Location
- Backend: `backend/logs/`
- Frontend: Browser console
- MongoDB: Atlas logs (if using Atlas)

### Monitoring
- Track API response times
- Monitor GD completion rates
- Analyze user feedback
- Review error rates

### Updates
- Regularly update OpenAI API usage
- Keep dependencies current
- Test new browser versions
- Update topic database

---

## Contact & Resources

**Documentation**: This file
**Backend Code**: `ProeduVate-main/backend/app/`
**Frontend Code**: `my-app/src/components/GDRound.js`

For issues or questions:
1. Check troubleshooting section
2. Review API documentation
3. Check backend/frontend logs
4. Contact development team

---

## License & Credits

This implementation is part of the ProeduVate LMS platform.
- OpenAI for AI capabilities
- Web Speech API for voice features
- React and Flask communities

---

## Changelog

### Version 1.0.0 (January 2026)
- Initial implementation
- Core GD functionality
- AI agent integration
- Evaluation system
- Admin scheduling
- Notification system

---

## Quick Reference

### API Base URL
```
http://localhost:5000/api/gd
```

### Key Files
```
Backend:
- app/routes/gd_routes.py (API endpoints)
- app/services/gd_service.py (AI logic)
- app/database.py (MongoDB collections)

Frontend:
- components/GDRound.js (Main component)
- pages/StudentPage.js (Integration)
```

### Default Configuration
```javascript
{
  duration: 20,          // minutes
  num_ai_agents: 7,      // 5-10 range
  preparation_time: 180, // seconds
  topic_selection_time: 30, // seconds
  evaluation_criteria: {
    communication_skills: 25%,
    leadership: 20%,
    logical_reasoning: 20%,
    content_relevance: 20%,
    listening_team_dynamics: 15%
  }
}
```

---

**End of Documentation**
