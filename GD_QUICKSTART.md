# Quick Start: AI-Based GD Round Feature

## For Developers

### 1. Backend Setup (5 minutes)

```bash
# Navigate to backend
cd ProeduVate-main/backend

# Install new dependencies (if not already installed)
pip install openai

# Add OpenAI API key to .env file
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env

# Start backend server
python run.py
```

The backend is ready! All routes are automatically registered.

### 2. Frontend Setup (2 minutes)

```bash
# Navigate to frontend
cd my-app

# Start React app
npm start
```

Frontend is ready! The GD Round component is automatically integrated.

### 3. Test the Feature

1. Login as a student
2. Navigate to: **Placement Training** → **Non-Technical Skills**
3. Click on **AI Group Discussion**
4. Grant camera and microphone permissions when prompted
5. Start your first GD round!

---

## For Students

### How to Access
1. Login to your student account
2. Go to **Placement Training** tab
3. Select **Non-Technical Skills**
4. Click on **AI Group Discussion** card
5. Click "Start GD Round"

### During GD
- **Select Topic**: Choose from dropdown (30 seconds)
- **Prepare**: Read topic and plan points (3 minutes)
- **Participate**: Speak when it's your turn
- **Control Media**: Use buttons to toggle camera/mic
- **Complete**: View your results and ranking

---

## For Admins

### Schedule a GD Round

Use this API endpoint:

```javascript
POST http://localhost:5000/api/gd/schedule

Body:
{
  "title": "Weekly GD Practice",
  "scheduled_time": "2026-01-15T10:00:00Z",
  "duration": 20,
  "topic": "Impact of AI on Employment",
  "allow_topic_selection": true,
  "num_ai_agents": 7,
  "ai_agent_voices": ["male", "female", "male", "female", "male", "female", "male"],
  "assigned_students": ["student_id_1", "student_id_2"],
  "created_by": "admin_id"
}
```

### View All Rounds
```javascript
GET http://localhost:5000/api/gd/rounds
```

### View Student Results
```javascript
GET http://localhost:5000/api/gd/results/:student_id
```

---

## Configuration

### Change Number of AI Agents
Edit [StudentPage.js](my-app/src/pages/StudentPage.js) line ~617:
```javascript
num_ai_agents: 7,  // Change to 5-10
```

### Add New Topics
Edit [gd_routes.py](ProeduVate-main/backend/app/routes/gd_routes.py) line ~19:
```python
DEFAULT_GD_TOPICS = [
    "Your New Topic Here",
    # ... existing topics
]
```

### Modify Evaluation Criteria
Edit [gd_routes.py](ProeduVate-main/backend/app/routes/gd_routes.py) line ~36:
```python
DEFAULT_EVALUATION_CRITERIA = {
    "communication_skills": {"weight": 25, ...},
    # Adjust weights as needed
}
```

---

## Tech Stack Summary

### Backend
- **Flask** - REST API
- **MongoDB** - Database (3 new collections)
- **OpenAI** - AI responses & evaluation
- **Python** - Backend logic

### Frontend
- **React** - UI framework
- **Web Speech API** - Voice features
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

### New Files Created
```
Backend:
✅ app/routes/gd_routes.py (460 lines)
✅ app/services/gd_service.py (320 lines)
✅ app/database.py (updated - added 3 collections)
✅ app/__init__.py (updated - registered blueprint)

Frontend:
✅ components/GDRound.js (830 lines)
✅ pages/StudentPage.js (updated - integrated GD)

Documentation:
✅ GD_ROUND_IMPLEMENTATION_GUIDE.md (complete guide)
✅ GD_QUICKSTART.md (this file)
```

---

## Key Features

### ✅ Implemented
- [x] AI-powered group discussion with 5-10 agents
- [x] Topic selection with timer
- [x] 3-minute preparation phase
- [x] Real-time voice/text interaction
- [x] Camera and microphone integration
- [x] Speech recognition and synthesis
- [x] Multi-criteria evaluation system
- [x] Top 3 ranking display
- [x] Detailed performance metrics
- [x] Notification system
- [x] Admin scheduling API
- [x] Results tracking

### 🎯 Customizable
- Number of AI agents (5-10)
- GD duration (10-30 minutes)
- Topics list
- Evaluation criteria weights
- AI agent voices (male/female)
- AI personalities

---

## Troubleshooting

### Issue: Camera/Mic not working
**Solution**: 
- Use Chrome or Edge browser
- Grant permissions when prompted
- Ensure HTTPS (or localhost)

### Issue: Speech recognition not working
**Solution**:
- Chrome/Edge only (best support)
- Check microphone input
- Speak clearly

### Issue: AI responses not generating
**Solution**:
- Verify `OPENAI_API_KEY` in `.env`
- Check API quota/limits
- Mock responses work as fallback

### Issue: Backend errors
**Solution**:
- Check MongoDB connection
- Verify all collections exist
- Review Python console logs

---

## API Quick Reference

```javascript
// Get topics
GET /api/gd/topics

// Get evaluation criteria  
GET /api/gd/evaluation-criteria

// Schedule GD round (admin)
POST /api/gd/schedule

// Get student's rounds
GET /api/gd/student/:id/rounds

// Start GD round
POST /api/gd/round/:id/start

// Evaluate GD round
POST /api/gd/round/:id/evaluate

// Get student results
GET /api/gd/results/:student_id
```

---

## Evaluation Criteria (Default)

1. **Communication Skills** (25%)
   - Clarity, articulation, language

2. **Leadership** (20%)
   - Initiative, guiding discussion

3. **Logical Reasoning** (20%)
   - Arguments quality, critical thinking

4. **Content Relevance** (20%)
   - Topic knowledge, point relevance

5. **Listening & Team Dynamics** (15%)
   - Active listening, collaboration

**Total**: 100%

---

## Demo Workflow

### Student Experience
1. **Login** → Student dashboard
2. **Navigate** → Placement Training → Non-Technical
3. **Select** → AI Group Discussion
4. **Start** → Grant permissions
5. **Choose** → Topic (30 sec)
6. **Prepare** → Read topic (3 min)
7. **Participate** → Interact with AI agents (20 min)
8. **Complete** → View results & ranking

**Result**: Detailed evaluation with rank and scores

### Admin Experience
1. **API Call** → Schedule GD round
2. **Assign** → Students receive notification
3. **Monitor** → Track round status
4. **Review** → View student performance
5. **Analyze** → Historical data

**Result**: Comprehensive analytics dashboard

---

## Next Steps

### Immediate (Already Done ✅)
- [x] Backend API endpoints
- [x] Frontend component
- [x] Integration with StudentPage
- [x] Database models
- [x] Documentation

### Future Enhancements (Optional)
- [ ] Video recording of GD session
- [ ] Multi-student real-time GD
- [ ] Advanced analytics dashboard
- [ ] Multilingual support
- [ ] Industry-specific topics
- [ ] Teacher live observation

---

## Support

For detailed information, see:
- **[GD_ROUND_IMPLEMENTATION_GUIDE.md](GD_ROUND_IMPLEMENTATION_GUIDE.md)** - Complete documentation
- **Backend Code**: `ProeduVate-main/backend/app/routes/gd_routes.py`
- **Frontend Code**: `my-app/src/components/GDRound.js`

---

## Summary

✅ **Complete Implementation**
- 6 new files created/updated
- 1600+ lines of code
- Full-stack integration
- Comprehensive documentation

🚀 **Ready to Use**
- Start backend: `python run.py`
- Start frontend: `npm start`
- Test: Login as student → Placement Training → AI GD

📊 **Features**
- AI-powered GD simulation
- Voice & camera integration
- Multi-criteria evaluation
- Admin scheduling & monitoring
- Detailed performance analytics

---

**That's it! Your AI-Based GD Round feature is ready to use! 🎉**
