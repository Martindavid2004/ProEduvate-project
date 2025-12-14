# ProEduvate React App - Quick Start Guide

## 🚀 Getting Started

This guide will help you set up and run the ProEduvate React application.

## ✅ What's Been Done

Your React application has been fully converted with:
- ✅ Complete React component architecture
- ✅ All pages (Admin, Teacher, Student, HR) converted
- ✅ Authentication and routing setup
- ✅ API integration layer
- ✅ Dark mode support
- ✅ Mobile responsive design
- ✅ AI Chatbot component
- ✅ Interview system with voice/text support
- ✅ Resume analysis integration
- ✅ All original HTML functionality preserved

## 📋 Prerequisites

Before you begin, ensure you have:
- Node.js (v14 or higher) installed
- Python 3.8+ installed
- The Flask backend from ProeduVate-main/backend

## 🔧 Installation Steps

### Step 1: Backend Setup (Flask)

1. Open a terminal and navigate to the backend:
   ```bash
   cd C:\Users\kitty\Downloads\ProeduVate-main\ProeduVate-main\backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the Flask server:
   ```bash
   python run.py
   ```

   The backend should run on `http://127.0.0.1:5001`

### Step 2: Frontend Setup (React)

1. Open a **NEW** terminal and navigate to the React app:
   ```bash
   cd C:\Users\kitty\Downloads\ProeduVate-main\my-app
   ```

2. Dependencies are already installed! Just start the app:
   ```bash
   npm start
   ```

   The app will automatically open at `http://localhost:3000`

## 🎯 Testing the Application

### Login Credentials:
- **Admin**: username: `admin`, password: `password`
- **Teacher**: username: `teacher`, password: `password`
- **Student**: username: `student`, password: `password`
- **HR**: username: `hr`, password: `password`

### Test Each Portal:

#### Admin Portal
1. Login as admin
2. Try adding a new user
3. Assign work to a teacher
4. Check the status tab
5. View your created tasks

#### Teacher Portal
1. Login as teacher
2. View admin-assigned tasks
3. Create a new assignment
4. Check student submissions
5. View student progress

#### Student Portal
1. Login as student
2. View and submit assignments
3. Click the chatbot icon (💬) to chat with AI
4. Try the AI interview (both text and voice)
5. Upload a resume for ATS analysis
6. Check your progress

#### HR Portal
1. Login as hr
2. View all candidates
3. Check interview results
4. Review resume analyses

## 🎨 Features to Test

### Dark Mode
- Click the moon/sun icon in the navbar
- Theme persists across sessions

### Mobile Responsive
- Resize your browser window
- Test the hamburger menu on mobile view

### AI Features
- **Chatbot**: Ask questions about courses or request quizzes
- **Interview**: Choose duration (10/20/30 min) and mode (text/voice)
- **Resume Analysis**: Upload PDF/DOC/DOCX for ATS scoring

## 🔍 Troubleshooting

### If the backend isn't connecting:
1. Verify Flask is running on port 5001
2. Check for any error messages in the Flask terminal
3. Ensure no firewall is blocking port 5001

### If speech recognition doesn't work:
1. Use Chrome or Edge browser (best support)
2. Grant microphone permissions when prompted
3. Note: HTTPS is required in production (localhost is fine)

### If styles look broken:
1. Ensure Tailwind CDN is loading (check browser console)
2. Hard refresh the page (Ctrl + F5)

### If you see CORS errors:
1. Verify the Flask backend has CORS enabled
2. Check that the backend allows requests from localhost:3000

## 📁 Project Structure

```
my-app/
├── src/
│   ├── components/      # Reusable components
│   │   ├── Navbar.js
│   │   ├── Sidebar.js
│   │   ├── Modal.js
│   │   └── Chatbot.js
│   ├── pages/          # Main page components
│   │   ├── Login.js
│   │   ├── AdminPage.js
│   │   ├── TeacherPage.js
│   │   ├── StudentPage.js
│   │   └── HRPage.js
│   ├── context/        # State management
│   │   ├── AuthContext.js
│   │   └── DataContext.js
│   ├── services/       # API integration
│   │   └── api.js
│   ├── App.js          # Main app with routing
│   └── index.css       # Global styles
└── package.json
```

## 🚀 Building for Production

When ready to deploy:

```bash
npm run build
```

This creates an optimized build in the `build/` folder.

## 📝 Key Differences from Original HTML

### Improvements:
- ✅ Component-based architecture (easier to maintain)
- ✅ Centralized state management
- ✅ Single Page Application (no page reloads)
- ✅ Better code organization
- ✅ Type-safe API calls with Axios
- ✅ Reusable components (Modal, Sidebar, Navbar)
- ✅ Protected routes with authentication

### Maintained:
- ✅ All original functionality
- ✅ Same UI/UX design
- ✅ All API integrations
- ✅ Dark mode
- ✅ Mobile responsiveness
- ✅ AI features (interview, chatbot, resume)

## 🆘 Need Help?

Common commands:
- Start app: `npm start`
- Build app: `npm run build`
- Install dependencies: `npm install`
- Check for issues: `npm audit`

## 🎉 You're All Set!

Your React application is ready to use. Both terminals should be running:
1. **Terminal 1**: Flask backend (port 5001)
2. **Terminal 2**: React app (port 3000)

Access the app at: http://localhost:3000

Enjoy your new React-powered ProEduvate LMS! 🎓
