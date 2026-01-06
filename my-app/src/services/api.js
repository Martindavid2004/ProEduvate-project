import axios from 'axios';

const getApiUrl = () => {
  // Use environment variable for production, fallback to localhost for development
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Check if we're in production (Netlify or other hosting)
  if (process.env.NODE_ENV === 'production') {
    return 'https://proeduvate-project.onrender.com/api';
  }
  
  // Default to localhost for local development
  return 'http://127.0.0.1:5000/api';
};

export const API_URL = getApiUrl();
export const BACKEND_URL = API_URL.replace('/api', '');

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Admin API calls
export const adminAPI = {
  getUsers: () => api.get('/admin/users'),
  addUser: (userData) => api.post('/admin/users', userData),
  removeUser: (userId) => api.delete(`/admin/users/${userId}`),
  getAssignments: () => api.get('/admin/assignments'),
  createAssignment: (assignmentData) => api.post('/admin/assignments', assignmentData),
  getStatus: () => api.get('/admin/status'),
  getTasks: () => api.get('/admin/tasks'),
  updateTask: (taskId, taskData) => api.put(`/admin/tasks/${taskId}`, taskData),
  deleteTask: (taskId) => api.delete(`/admin/tasks/${taskId}`),
};

// Teacher API calls
export const teacherAPI = {
  getAssignments: () => api.get('/teacher/assignments'),
  createAssignment: (assignmentData) => api.post('/teacher/assignments', assignmentData),
  updateAssignment: (assignmentId, assignmentData) => api.put(`/teacher/assignments/${assignmentId}`, assignmentData),
  getSubmissions: () => api.get('/teacher/submissions'),
  getAdminTasks: () => api.get('/teacher/admin_tasks'),
  markTaskComplete: (taskId) => api.post(`/teacher/admin_tasks/${taskId}/complete`),
};

// Student API calls
export const studentAPI = {
  getAssignments: (studentId) => api.get(`/student/${studentId}/assignments`),
  submitAssignment: (studentId, assignmentId, formData) => 
    api.post(`/student/assignments/${assignmentId}/submit`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  uploadResume: (studentId, formData) => 
    api.post(`/student/${studentId}/upload_resume`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getProgress: (studentId) => api.get(`/student/${studentId}/progress`),
};

// Interview API calls
export const interviewAPI = {
  startInterview: (data = {}) => api.post('/interview/start', data),
  submitAnswers: (answersData) => api.post('/interview/evaluate', answersData),
};

// Chatbot API calls
export const chatbotAPI = {
  sendMessage: (prompt) => api.post('/chatbot/general_query', { prompt }),
  generateQuiz: (topic, numQuestions) => 
    api.post('/chatbot/generate_quiz', { topic, num_questions: numQuestions }),
};

// HR API calls
export const hrAPI = {
  getCandidates: () => api.get('/hr/candidates'),
};

export default api;
