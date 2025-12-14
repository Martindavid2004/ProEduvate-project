# ProEduvate React Application

A comprehensive Learning Management System built with React and Flask backend.

## Features

- **Admin Portal**: Manage users, assign work, track status, and manage tasks
- **Teacher Portal**: Create assignments, view submissions, track student progress
- **Student Portal**: Complete assignments, take AI interviews, analyze resumes, access chatbot
- **HR Portal**: View candidates, interview results, and resume analysis
- **AI-Powered Features**:
  - AI Chatbot for learning assistance
  - AI Mock Interviews (text and voice)
  - Resume ATS Analysis
  - Custom quiz generation
- **Dark Mode**: Full dark mode support with theme persistence
- **Responsive Design**: Mobile-friendly interface with sidebar navigation

## Tech Stack

### Frontend
- React 18
- React Router DOM (routing)
- Axios (API calls)
- Tailwind CSS (styling)
- Lucide React (icons)

### Backend
- Flask (Python)
- See `backend/requirements.txt` for full dependencies

## Project Structure

```
my-app/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Chatbot.js       # AI chatbot component
│   │   ├── Modal.js         # Reusable modal component
│   │   ├── Navbar.js        # Top navigation bar
│   │   └── Sidebar.js       # Side navigation menu
│   ├── context/
│   │   ├── AuthContext.js   # Authentication state management
│   │   └── DataContext.js   # Global data management
│   ├── pages/
│   │   ├── AdminPage.js     # Admin dashboard
│   │   ├── TeacherPage.js   # Teacher dashboard
│   │   ├── StudentPage.js   # Student dashboard
│   │   ├── HRPage.js        # HR dashboard
│   │   └── Login.js         # Login page
│   ├── services/
│   │   └── api.js           # API integration layer
│   ├── App.js               # Main app component with routing
│   ├── index.js             # React entry point
│   └── index.css            # Global styles
├── package.json
└── README.md
```

## Installation

### Prerequisites
- Node.js (v14 or higher)
- Python 3.8+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd ProeduVate-main/backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run the Flask backend:
```bash
python run.py
```

The backend will run on `http://127.0.0.1:5001`

### Frontend Setup

1. Navigate to the React app directory:
```bash
cd my-app
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

## Usage

### Login Credentials

The application has 4 different portals:

- **Admin**: username: `admin`, password: `password`
- **Teacher**: username: `teacher`, password: `password`
- **Student**: username: `student`, password: `password`
- **HR**: username: `hr`, password: `password`

### Admin Portal Features
- Manage users (add/remove students, teachers, admins, HR)
- Assign work to teachers
- View system status and teacher assignments
- Track and edit created tasks

### Teacher Portal Features
- View tasks assigned by admin
- Create and manage assignments for students
- View student submissions
- Track student progress

### Student Portal Features
- View and submit assignments
- Take AI mock interviews (text or voice)
- Upload and analyze resume with ATS scoring
- Access AI chatbot for learning assistance
- Track personal progress

### HR Portal Features
- View all candidates
- Review interview results
- Analyze resume submissions
- View detailed candidate profiles

## API Integration

The application connects to the Flask backend at `http://127.0.0.1:5001/api`. All API calls are centralized in `src/services/api.js`.

### API Endpoints Used:
- Admin: `/api/admin/*`
- Teacher: `/api/teacher/*`
- Student: `/api/student/*`
- HR: `/api/hr/*`
- Interview: `/api/interview/*`
- Chatbot: `/api/chatbot/*`

## Features in Detail

### Dark Mode
Toggle between light and dark themes using the moon/sun icon in the navbar. Theme preference is saved to localStorage.

### AI Interview
- Choose between 10, 20, or 30-minute interviews
- Text or voice input options
- Real-time speech recognition for voice interviews
- Automatic timer with countdown
- AI-powered evaluation and feedback

### Resume Analysis
- Upload resume in PDF, DOC, or DOCX format
- ATS (Applicant Tracking System) scoring
- Skill matching analysis
- Identification of missing skills
- Summary and recommendations

### Chatbot
- Available on student portal
- Natural language processing
- Custom quiz generation
- Course and assignment help

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## Troubleshooting

### Backend Connection Issues
- Ensure Flask backend is running on port 5001
- Check `proxy` setting in `package.json`
- Verify API_URL in `src/services/api.js`

### Speech Recognition Issues
- Speech recognition requires HTTPS in production
- Ensure microphone permissions are granted
- Use Chrome or Edge for best compatibility

### CORS Issues
- Backend must have CORS enabled for frontend origin
- Check Flask CORS configuration

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

Note: Speech recognition works best in Chrome and Edge.

## License

This project is part of the ProEduvate Learning Management System.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
