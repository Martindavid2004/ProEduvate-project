import axios from 'axios';

const getApiUrl = () => {
  // Force localhost for development (when running on localhost)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://127.0.0.1:5000/api';
  }
  
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

console.log('API_URL configured as:', API_URL);

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

// Automatically set Content-Type and Authorization token based on request data
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
    // Debug log for GD endpoints
    if (config.url.includes('/gd/')) {
      console.log(`[API] GD ${config.method?.toUpperCase() || 'GET'} ${config.url} with token`);
    }
  } else {
    // Debug log for GD endpoints when no token (never print the token itself)
    if (config.url.includes('/gd/')) {
      console.warn('[API] GD request WITHOUT token!');
      console.warn('[API] localStorage user:', localStorage.getItem('user'));
    }
  }
  if (config.data instanceof FormData) {
    // Let browser set Content-Type with correct boundary for FormData
    if (config.headers) {
      if (typeof config.headers.delete === 'function') {
        config.headers.delete('Content-Type');
        config.headers.delete('content-type');
      } else {
        delete config.headers['Content-Type'];
        delete config.headers['content-type'];
      }
    }
  } else {
    config.headers['Content-Type'] = 'application/json';
  }
  return config;
});

// Admin API calls
export const adminAPI = {
  getUsers: () => api.get('/admin/users'),
  addUser: (userData) => api.post('/admin/users', userData),
  removeUser: (userId) => api.delete(`/admin/users/${userId}`),
  assignStudentsToTeacher: (data) => api.post('/admin/assign-students', data),
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

// Assessment API calls (teacher-assigned MCQ assessments + training MCQs).
// Shared helpers: server-side expiry countdown + automatic failure (tab switch / time expiry).
export const assessmentAPI = {
  startTeacherQuiz: (assignmentId, studentId, retake = false) =>
    api.post(`/teacher/assignments/${assignmentId}/assessment/start`, { student_id: studentId, retake }),
  // Training-section test attempt state for a topic (Start / Resume / Retake
  // decision + last result). Never starts an attempt.
  aptitudeTestStatus: (studentId, topic) =>
    api.get('/aptitude/test/status', { params: { student_id: studentId, topic } }),
  teacherQuizStatus: (assignmentId, studentId) =>
    api.get(`/teacher/assignments/${assignmentId}/assessment/status`, { params: { student_id: studentId } }),
  failTeacherQuiz: (assignmentId, studentId, reason) =>
    api.post(`/teacher/assignments/${assignmentId}/assessment/fail`, { student_id: studentId, reason }),
  submitTeacherQuiz: (assignmentId, payload) =>
    api.post(`/teacher/assignments/${assignmentId}/assessment/submit`, payload),
  failAptitude: (testId, reason, extra = {}) =>
    api.post('/aptitude/test/fail', { test_id: testId, reason, ...extra }),
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
  saveAnswer: (data) => api.post('/interview/answer', data),
  getSession: (sessionId) => api.get(`/interview/session/${sessionId}`),
  // Voice-mode speech-to-text: REUSES the existing /gd/transcribe endpoint,
  // which serves the shared faster-whisper singleton (stt_service.py).
  // No second Whisper model/service is created. Response contract (same as
  // GDRound): { success, transcript, text, status, message?, warning? }.
  transcribeAudio: (audioBlob) => {
    const formData = new FormData();
    const mime = (audioBlob && audioBlob.type) || 'audio/webm';
    let ext = 'webm';
    if (mime.includes('mp4')) ext = 'mp4';
    else if (mime.includes('ogg')) ext = 'ogg';
    else if (mime.includes('wav')) ext = 'wav';
    formData.append('audio', audioBlob, `speech.${ext}`);
    return api.post('/gd/transcribe', formData);
  },
};

// Chatbot API calls
export const chatbotAPI = {
  sendMessage: (promptOrObj) => {
    const message = typeof promptOrObj === 'string' ? promptOrObj : (promptOrObj.message || promptOrObj.prompt || JSON.stringify(promptOrObj));
    return api.post('/chatbot/general_query', { prompt: message });
  },
  generateQuiz: (topic, numQuestions, categories = [], source = 'bank') => 
    api.post('/chatbot/generate_quiz', { topic, num_questions: numQuestions, categories, source }),
};

// HR API calls
export const hrAPI = {
  getCandidates: () => api.get('/hr/candidates'),
};

// Group Discussion (GD) API calls
export const gdAPI = {
  getTopics: () => api.get('/gd/topics'),
  getCriteria: () => api.get('/gd/evaluation-criteria'),
  scheduleRound: (data) => api.post('/gd/schedule', data),
  schedulePracticeRound: (data) => api.post('/gd/practice-round', data),
  getRounds: () => api.get('/gd/rounds'),
  getStudentRounds: (studentId) => api.get(`/gd/student/${studentId}/rounds`),
  getNotifications: (studentId) => api.get(`/gd/notifications/${studentId}`),
  markNotificationRead: (id) => api.put(`/gd/notifications/${id}/mark-read`),
  getRoundDetails: (id) => api.get(`/gd/round/${id}`),
  selectTopic: (id, topic) => api.post(`/gd/round/${id}/select-topic`, { topic }),
  startRound: (id) => api.post(`/gd/round/${id}/start`),
  submitResponse: (id, response_text, duration = 0) => api.post(`/gd/round/${id}/submit-response`, { response_text, duration }),
  evaluateRound: (id) => api.post(`/gd/round/${id}/evaluate`),
  getStudentResults: (studentId) => api.get(`/gd/results/${studentId}`),
  getConfig: () => api.get('/gd/admin/config'),
  updateConfig: (data) => api.post('/gd/admin/config', data),
  getAgentResponse: (data) => api.post('/gd/agent-response', data),
  transcribeAudio: (audioBlob) => {
    console.log('[GD API] transcribeAudio called');
    const endpoint = `${API_URL}/gd/transcribe`;
    console.log('[GD API] endpoint:', endpoint);
    console.log('[GD API] blob size:', audioBlob ? audioBlob.size : 0);
    console.log('[GD API] blob type:', audioBlob ? audioBlob.type : 'unknown');

    const formData = new FormData();
    const mime = (audioBlob && audioBlob.type) || 'audio/webm';
    let ext = 'webm';
    if (mime.includes('mp4')) ext = 'mp4';
    else if (mime.includes('ogg')) ext = 'ogg';
    else if (mime.includes('wav')) ext = 'wav';
    formData.append('audio', audioBlob, `speech.${ext}`);

    return api.post('/gd/transcribe', formData);
  },
};

export default api;
