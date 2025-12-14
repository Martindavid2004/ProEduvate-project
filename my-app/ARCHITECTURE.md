# ProEduvate React Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser (Client)                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              React Application (Port 3000)              │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │              App.js (Root)                       │  │ │
│  │  │  - AuthProvider (Authentication State)          │  │ │
│  │  │  - DataProvider (Global Data State)             │  │ │
│  │  │  - Router (Navigation)                           │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │                         │                               │ │
│  │           ┌─────────────┼─────────────┐                 │ │
│  │           │             │             │                 │ │
│  │       ┌───▼───┐    ┌───▼───┐    ┌───▼───┐             │ │
│  │       │ Login │    │ Admin │    │Teacher│             │ │
│  │       │ Page  │    │ Page  │    │ Page  │             │ │
│  │       └───────┘    └───────┘    └───────┘             │ │
│  │           │             │             │                 │ │
│  │       ┌───▼───┐    ┌───▼───┐    ┌───▼───┐             │ │
│  │       │Student│    │  HR   │    │Shared │             │ │
│  │       │ Page  │    │ Page  │    │Comps  │             │ │
│  │       └───────┘    └───────┘    └───────┘             │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │           Services Layer (api.js)                │  │ │
│  │  │  - Centralized API calls                         │  │ │
│  │  │  - Axios configuration                            │  │ │
│  │  │  - Error handling                                 │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  │                         │                               │ │
│  └─────────────────────────┼───────────────────────────────┘ │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             │ HTTP/HTTPS
                             │ REST API
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                  Flask Backend (Port 5001)                    │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                       │  │
│  │  /api/admin/*      - Admin operations                 │  │
│  │  /api/teacher/*    - Teacher operations               │  │
│  │  /api/student/*    - Student operations               │  │
│  │  /api/hr/*         - HR operations                    │  │
│  │  /api/interview/*  - Interview system                 │  │
│  │  /api/chatbot/*    - AI Chatbot                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Database / File Storage                   │  │
│  │  - User data                                           │  │
│  │  - Assignments                                         │  │
│  │  - Submissions (files)                                 │  │
│  │  - Resumes                                             │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

```
App
├── AuthProvider (Context)
│   ├── login state
│   ├── user info
│   └── theme state
│
├── DataProvider (Context)
│   ├── users data
│   ├── assignments data
│   └── refresh functions
│
└── Router
    ├── /login
    │   └── Login Component
    │
    ├── /admin (Protected)
    │   └── AdminPage
    │       ├── Navbar
    │       ├── Sidebar
    │       └── Tab Content
    │           ├── Overview
    │           ├── Manage Users
    │           ├── Assign Work
    │           ├── Status
    │           └── Tasks
    │
    ├── /teacher (Protected)
    │   └── TeacherPage
    │       ├── Navbar
    │       ├── Sidebar
    │       └── Tab Content
    │           ├── Admin Tasks
    │           ├── My Assignments
    │           ├── Student Progress
    │           └── Submissions
    │
    ├── /student (Protected)
    │   └── StudentPage
    │       ├── Navbar
    │       ├── Sidebar
    │       ├── Chatbot (floating)
    │       └── Tab Content
    │           ├── My Assignments
    │           ├── My Progress
    │           ├── AI Interview
    │           │   └── Interview Modal
    │           └── Resume Analysis
    │
    └── /hr (Protected)
        └── HRPage
            ├── Navbar
            ├── Sidebar
            └── Tab Content
                ├── Candidates
                ├── Interview Results
                └── Resume Analysis
```

## Data Flow

```
┌──────────────┐
│  User Action │
│  (UI Event)  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│   Component      │
│   Event Handler  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   API Service    │
│   (api.js)       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Flask Backend   │
│  Endpoint        │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   Database /     │
│   File System    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   Response       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   State Update   │
│   (Context/Hook) │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   UI Re-render   │
└──────────────────┘
```

## Authentication Flow

```
┌─────────────┐
│ User visits │
│   /admin    │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ ProtectedRoute   │
│ checks auth      │
└──────┬───────────┘
       │
       ├─── Not Authenticated ──→ Redirect to /login
       │
       └─── Authenticated
              │
              ▼
         ┌──────────────┐
         │ Check Role   │
         └──────┬───────┘
                │
                ├─── Wrong Role ──→ Redirect to /login
                │
                └─── Correct Role ──→ Show Page
```

## State Management

```
┌────────────────────────────────────────────┐
│           AuthContext (Global)             │
│  - user (current user info)                │
│  - login() function                        │
│  - logout() function                       │
│  - theme (dark/light)                      │
│  - toggleTheme() function                  │
└────────────────┬───────────────────────────┘
                 │
                 │ provides to all components
                 │
┌────────────────▼───────────────────────────┐
│           DataContext (Global)             │
│  - users[] (all users)                     │
│  - assignments[] (all assignments)         │
│  - fetchAllData() function                 │
│  - refreshUsers() function                 │
│  - refreshAssignments() function           │
└────────────────┬───────────────────────────┘
                 │
                 │ provides to all components
                 │
┌────────────────▼───────────────────────────┐
│        Component Local State               │
│  - Form inputs                             │
│  - UI state (modals, tabs)                 │
│  - Component-specific data                 │
└────────────────────────────────────────────┘
```

## API Integration Pattern

```javascript
// 1. User clicks button
<button onClick={handleSubmit}>Submit</button>

// 2. Event handler in component
const handleSubmit = async () => {
  try {
    // 3. Call API service
    const response = await studentAPI.submitAssignment(
      studentId, 
      assignmentId, 
      formData
    );
    
    // 4. Update UI based on response
    alert('Success!');
    
    // 5. Refresh data
    await loadStudentData();
    
  } catch (error) {
    // 6. Handle errors
    console.error(error);
    alert('Failed!');
  }
};
```

## File Structure

```
my-app/
│
├── public/
│   └── index.html              # HTML template
│
├── src/
│   │
│   ├── components/             # Reusable components
│   │   ├── Navbar.js           # Top navigation
│   │   ├── Sidebar.js          # Side menu
│   │   ├── Modal.js            # Popup dialogs
│   │   └── Chatbot.js          # AI chatbot
│   │
│   ├── pages/                  # Page components
│   │   ├── Login.js            # Login page
│   │   ├── AdminPage.js        # Admin dashboard
│   │   ├── TeacherPage.js      # Teacher dashboard
│   │   ├── StudentPage.js      # Student dashboard
│   │   └── HRPage.js           # HR dashboard
│   │
│   ├── context/                # State management
│   │   ├── AuthContext.js      # Authentication state
│   │   └── DataContext.js      # Global data state
│   │
│   ├── services/               # External services
│   │   └── api.js              # API calls
│   │
│   ├── App.js                  # Main app component
│   ├── index.js                # Entry point
│   └── index.css               # Global styles
│
├── package.json                # Dependencies
├── README.md                   # Project documentation
├── QUICKSTART.md               # Setup guide
├── API_DOCUMENTATION.md        # API reference
├── CONVERSION_SUMMARY.md       # Conversion details
└── ARCHITECTURE.md             # This file
```

## Technology Stack

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│                                         │
│  React 18.2.0                           │
│  ├── Component-based architecture       │
│  ├── Hooks for state management         │
│  ├── Context API for global state       │
│  └── Virtual DOM for performance        │
│                                         │
│  React Router DOM 6.20.1                │
│  ├── Client-side routing                │
│  ├── Protected routes                   │
│  └── Navigation management              │
│                                         │
│  Axios 1.6.2                            │
│  ├── HTTP client                        │
│  ├── Promise-based                      │
│  └── Request/response interceptors      │
│                                         │
│  Tailwind CSS (CDN)                     │
│  ├── Utility-first CSS                  │
│  ├── Responsive design                  │
│  └── Dark mode support                  │
│                                         │
│  Lucide React 0.294.0                   │
│  └── Icon library                       │
└─────────────────────────────────────────┘
                    │
                    │ HTTP/HTTPS
                    │ REST API
                    │
┌─────────────────────▼───────────────────┐
│         Backend (Flask)                  │
│                                         │
│  Python 3.8+                            │
│  Flask Web Framework                    │
│  SQLAlchemy (Database ORM)              │
│  AI/ML Libraries                        │
│  File Storage System                    │
└─────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Container/Presentational Pattern
```
Page Components (Containers)
└── Handle business logic
    └── Pass data to presentational components
        └── Shared Components (Presentational)
            └── Handle UI rendering only
```

### 2. Context Provider Pattern
```
App
└── AuthProvider
    └── DataProvider
        └── All child components
            └── Access context via useAuth() and useData()
```

### 3. Service Layer Pattern
```
Component
└── Calls service function
    └── api.js (Service Layer)
        └── Makes HTTP request
            └── Backend API
```

### 4. Protected Route Pattern
```
<Route path="/admin" element={
  <ProtectedRoute allowedRole="admin">
    <AdminPage />
  </ProtectedRoute>
} />
```

## Security Architecture

```
┌─────────────────────────────────────────┐
│          Client Security                │
│                                         │
│  ✓ Protected Routes                     │
│  ✓ Authentication Check                 │
│  ✓ Role-based Access Control            │
│  ✓ XSS Prevention (React auto-escape)   │
│  ✓ Input Validation                     │
└─────────────────┬───────────────────────┘
                  │
                  │ HTTPS (Production)
                  │
┌─────────────────▼───────────────────────┐
│          Server Security                │
│                                         │
│  ✓ CORS Configuration                   │
│  ✓ Session Management                   │
│  ✓ Input Sanitization                   │
│  ✓ File Upload Validation               │
│  ✓ Rate Limiting                        │
└─────────────────────────────────────────┘
```

## Deployment Architecture

```
Development:
React Dev Server (3000) ←→ Flask Dev Server (5001)

Production:
┌────────────────────────────────────┐
│  Web Server (Nginx/Apache)         │
│  ├── Serves React build/           │
│  └── Proxies /api to Flask         │
└────────────┬───────────────────────┘
             │
             ├── Static Files (React)
             │   └── Port 80/443
             │
             └── API Requests
                 └── Flask (WSGI)
                     └── Port 5001
```

This architecture provides a scalable, maintainable, and secure foundation for the ProEduvate Learning Management System.
