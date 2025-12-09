import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import logo from './assets/WhatsApp_Image_2025-12-02_at_14.51.15__1_-removebg-preview.png';

const API_URL = 'http://127.0.0.1:5001/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [role, setRole] = useState('student'); // default fallback
  const [users, setUsers] = useState([]);
  const [assignments, setAssignments] = useState([]);
  
  // Navigation State
  const [activeTab, setActiveTab] = useState('profile'); // For student/teacher sidebar

  // Modals & Chatbot State
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [quizModalOpen, setQuizModalOpen] = useState(false);
  const [interviewModalOpen, setInterviewModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);

  // Forms State
  const [newUser, setNewUser] = useState({ name: '', role: 'student' });
  const [adminTask, setAdminTask] = useState({ title: '', teacherId: '', description: '' });
  const [assignmentForm, setAssignmentForm] = useState({ title: '', description: '', dueDate: '', type: 'manual' });
  const [editForm, setEditForm] = useState({ id: '', title: '', description: '', dueDate: '' });
  
  // Chat & Quiz State
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([{ sender: 'ai', text: 'Hello! Ask me a question or click \'Quiz\' to start a test.' }]);
  const [quizConfig, setQuizConfig] = useState({ topic: '', questions: 5, duration: 10 });
  const chatScrollRef = useRef(null);

  // Interview State
  const [interviewQuestions, setInterviewQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isVoiceInterview, setIsVoiceInterview] = useState(false);
  const [interviewContent, setInterviewContent] = useState(null); // JSX to render inside modal
  const [transcriptPreview, setTranscriptPreview] = useState('Waiting for you to speak...');
  const [isRecording, setIsRecording] = useState(false);
  const userAnswers = useRef([]);
  
  // Admin Task View for Teacher
  const [adminAssignedTasks, setAdminAssignedTasks] = useState([]);

  // --- INITIALIZATION ---
  useEffect(() => {
    const storedRole = localStorage.getItem('userRole');
    if (!storedRole) {
      navigate('/');
    } else {
      setRole(storedRole);
      // Set default tabs based on role
      if (storedRole === 'teacher') setActiveTab('progress');
      if (storedRole === 'student') setActiveTab('profile');
      fetchAllData();
    }
  }, [navigate]);

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const fetchAllData = async () => {
    try {
      const [usersRes, assignRes] = await Promise.all([
        fetch(`${API_URL}/admin/users`),
        fetch(`${API_URL}/student/assignments`)
      ]);
      if (usersRes.ok) setUsers(await usersRes.json());
      if (assignRes.ok) setAssignments(await assignRes.json());
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('userRole');
    navigate('/');
  };

  // --- ADMIN FUNCTIONS ---
  const addUser = async () => {
    if (!newUser.name) return alert('Enter name.');
    await fetch(`${API_URL}/admin/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newUser)
    });
    setNewUser({ ...newUser, name: '' });
    fetchAllData();
  };

  const removeUser = async (userId) => {
    if (!window.confirm('Remove user?')) return;
    await fetch(`${API_URL}/admin/users/${userId}`, { method: 'DELETE' });
    fetchAllData();
  };

  const assignWork = async () => {
    if (!adminTask.title || !adminTask.teacherId) return alert('Missing fields');
    await fetch(`${API_URL}/admin/assignments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(adminTask)
    });
    alert('Assigned!');
    setAdminTask({ title: '', teacherId: '', description: '' });
    fetchAllData();
  };

  // --- TEACHER FUNCTIONS ---
  const createAssignment = async () => {
    if (!assignmentForm.title || !assignmentForm.description || !assignmentForm.dueDate) return alert('Fill all fields.');
    
    try {
      const res = await fetch(`${API_URL}/teacher/assignments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(assignmentForm)
      });
      if (res.ok) {
        alert('Assignment Created!');
        setAssignmentForm({ title: '', description: '', dueDate: '', type: 'manual' });
        await fetchAllData();
        setActiveTab('my-assignments');
      } else {
        alert('Failed to create assignment.');
      }
    } catch (e) {
      console.error(e);
      alert('Error creating assignment');
    }
  };

  const fetchAdminAssignedWork = async () => {
    const currentTeacher = users.find(u => u.role === 'teacher'); // In real app, use auth ID
    if (!currentTeacher) return;
    try {
      const res = await fetch(`${API_URL}/teacher/admin-assignments/${currentTeacher.id}`);
      if (res.ok) setAdminAssignedTasks(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const markTaskComplete = async (taskId) => {
    await fetch(`${API_URL}/teacher/admin-assignments/${taskId}/complete`, { method: 'PATCH' });
    fetchAdminAssignedWork();
  };

  // Need to trigger fetching tasks when teacher views that tab
  useEffect(() => {
    if (role === 'teacher' && activeTab === 'assignment') {
      fetchAdminAssignedWork();
    }
  }, [role, activeTab, users]);

  // Edit Assignment Logic
  const openEditModal = (assignment) => {
    setEditForm({
      id: assignment.id,
      title: assignment.title,
      description: assignment.description,
      dueDate: assignment.dueDate
    });
    setEditModalOpen(true);
  };

  const saveAssignmentChanges = async () => {
    if (!editForm.title || !editForm.description || !editForm.dueDate) return alert("Fill all fields");
    
    const res = await fetch(`${API_URL}/teacher/assignments/${editForm.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        title: editForm.title, 
        description: editForm.description, 
        dueDate: editForm.dueDate 
      })
    });

    if (res.ok) {
      alert("Updated!");
      setEditModalOpen(false);
      fetchAllData();
    } else {
      alert("Update failed");
    }
  };

  // --- STUDENT FUNCTIONS ---
  const getCurrentStudent = () => users.find(u => u.role === 'student'); // Demo logic

  const submitAssignment = async (assignmentId, file, notes) => {
    if (!file) return alert('Please select a file');
    const student = getCurrentStudent();
    if (!student) return alert('Student not found');

    const formData = new FormData();
    formData.append('assignment_file', file);
    formData.append('student_id', student.id);
    formData.append('assignment_id', assignmentId);
    if (notes) formData.append('notes', notes);

    try {
      const res = await fetch(`${API_URL}/student/assignments/${assignmentId}/submit`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        alert(`Assignment submitted: ${file.name}`);
      } else {
        const err = await res.text();
        alert(`Failed: ${err}`);
      }
    } catch (e) {
      console.error(e);
      alert('Error submitting');
    }
  };

  const analyzeResume = async (file) => {
    if (!file) return alert('Select a resume');
    const student = getCurrentStudent();
    
    const formData = new FormData();
    formData.append('resume', file);

    alert('Analyzing... (Simulated UI Update)');
    try {
      const res = await fetch(`${API_URL}/student/${student.id}/upload_resume`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        fetchAllData(); // Update user score
        alert('Analysis Complete!');
      } else {
        alert('Analysis failed: ' + (data.error || 'Unknown'));
      }
    } catch (e) { console.error(e); }
  };

  // --- INTERVIEW LOGIC ---
  const speak = (text, onEndCallback) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.onend = () => { if (onEndCallback) onEndCallback(); };
    window.speechSynthesis.speak(utterance);
  };

  const startInterview = async (mode) => {
    const voiceMode = mode === 'voice';
    setIsVoiceInterview(voiceMode);
    
    // Check permissions if voice
    if (voiceMode) {
      if (!navigator.mediaDevices || !window.SpeechRecognition && !window.webkitSpeechRecognition) {
        return alert("Browser does not support voice features.");
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(t => t.stop());
      } catch (e) {
        return alert("Microphone access denied.");
      }
    }

    const student = getCurrentStudent();
    if (!student || !student.resume_filename) return alert('Upload resume first.');

    setInterviewModalOpen(true);
    setInterviewContent(<p className="text-gray-600 text-center">🤖 Generating questions...</p>);

    try {
      const res = await fetch(`${API_URL}/interview/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: student.id, difficulty: 'easy' })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      setInterviewQuestions(data.questions);
      userAnswers.current = [];
      setCurrentQuestionIndex(0);
      // We need to trigger the display of the first question. 
      // Since state updates are async, we pass data directly to the display function.
      displayQuestion(0, data.questions, voiceMode);
    } catch (e) {
      setInterviewContent(<p className="text-red-500">Error: {e.message}</p>);
    }
  };

  const displayQuestion = (index, questions, isVoice) => {
    if (index >= questions.length) {
      finishInterview();
      return;
    }
    const question = questions[index];
    
    // Logic to render the question UI
    const renderContent = (
      <div className="space-y-6">
        <div className="text-center mb-6">
          <div className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold mb-4">
            Question {index + 1} of {questions.length}
          </div>
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border-l-4 border-blue-500">
            <p className="text-gray-800 text-lg font-medium leading-relaxed">"{question}"</p>
          </div>
        </div>
        
        {isVoice ? (
          <VoiceAnswerSection 
            question={question} 
            onAnswer={(ans) => handleAnswerSubmit(ans, index, questions, isVoice)} 
          />
        ) : (
          <TextAnswerSection 
            onAnswer={(ans) => handleAnswerSubmit(ans, index, questions, isVoice)}
          />
        )}
      </div>
    );
    setInterviewContent(renderContent);
  };

  const handleAnswerSubmit = (answer, index, questions, isVoice) => {
    userAnswers.current.push({ question: questions[index], answer });
    const nextIndex = index + 1;
    setCurrentQuestionIndex(nextIndex);
    displayQuestion(nextIndex, questions, isVoice);
  };

  const finishInterview = async () => {
    setInterviewContent(<div className="text-center"><p>Evaluating...</p></div>);
    const student = getCurrentStudent();
    try {
      const res = await fetch(`${API_URL}/interview/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: student.id, transcript: userAnswers.current })
      });
      const result = await res.json();
      
      const feedback = (
        <div className="space-y-6">
          <div className="text-center bg-green-50 p-8 rounded-xl border-l-4 border-green-500">
            <h4 className="font-bold text-3xl text-green-800">Score: {result.score}/100</h4>
          </div>
          <div className="bg-blue-50 p-6 rounded-xl">
            <p className="whitespace-pre-wrap">{result.feedback}</p>
          </div>
          <div className="text-center">
            <button onClick={() => setInterviewModalOpen(false)} className="px-6 py-2 bg-gray-500 text-white rounded">Close</button>
          </div>
        </div>
      );
      setInterviewContent(feedback);
      fetchAllData();
    } catch (e) {
      setInterviewContent(<p className="text-red-500">Error evaluating.</p>);
    }
  };

  // --- CHATBOT LOGIC ---
  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    const userMsg = { sender: 'user', text: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    
    // Add thinking placeholder
    setChatMessages(prev => [...prev, { sender: 'ai', text: 'Thinking...', isTemp: true }]);

    try {
      const res = await fetch(`${API_URL}/chatbot/general_query`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ prompt: userMsg.text })
      });
      const data = await res.json();
      const answer = data.answer?.text || data.answer || "I couldn't generate a response.";
      
      setChatMessages(prev => prev.filter(m => !m.isTemp).concat({ sender: 'ai', text: answer }));
    } catch (e) {
      setChatMessages(prev => prev.filter(m => !m.isTemp).concat({ sender: 'ai', text: 'Error connecting to AI.' }));
    }
  };

  const startQuiz = async () => {
    setQuizModalOpen(false);
    setChatMessages(prev => [...prev, { sender: 'ai', text: `Generating quiz on ${quizConfig.topic}...` }]);
    try {
      const res = await fetch(`${API_URL}/chatbot/query`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ topic: quizConfig.topic, num_questions: quizConfig.questions })
      });
      const data = await res.json();
      // Render quiz (simplified for React: just show JSON or formatted text for now, or build a Quiz component)
      // To strictly follow the "don't change functionality" we mimic the HTML approach of injecting buttons
      const quizBlock = (
        <div className="bg-indigo-50 p-3 rounded-lg border">
          <h4 className="font-bold text-indigo-800">Quiz: {quizConfig.topic}</h4>
          {data.questions.map((q, i) => (
            <div key={i} className="mb-4 text-sm mt-2">
              <p className="font-semibold">{i+1}. {q.question}</p>
              <div className="grid grid-cols-2 gap-2 mt-2">
                {q.options.map((opt, idx) => (
                  <button 
                    key={idx} 
                    className="text-left p-2 border rounded-md bg-white hover:bg-gray-100"
                    onClick={(e) => {
                      const isCorrect = opt === q.correct_answer;
                      e.target.classList.add(isCorrect ? 'bg-green-200' : 'bg-red-200');
                      e.target.disabled = true;
                    }}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      );
      setChatMessages(prev => [...prev, { sender: 'ai', component: quizBlock }]);
    } catch (e) {
      setChatMessages(prev => [...prev, { sender: 'ai', text: 'Error generating quiz.' }]);
    }
  };

  // --- SUB-COMPONENTS FOR INTERVIEW (Defined locally to access state/functions) ---
  const VoiceAnswerSection = ({ question, onAnswer }) => {
    const [status, setStatus] = useState('Reading question...');
    const [btnDisabled, setBtnDisabled] = useState(true);
    const recognitionRef = useRef(null);

    useEffect(() => {
      // Speak question on mount
      speak(question, () => {
        setStatus('Ready! Click record.');
        setBtnDisabled(false);
      });
      return () => window.speechSynthesis.cancel();
    }, [question]);

    const toggleRecord = () => {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!recognitionRef.current) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false; // Stop after one sentence for simplicity or true for long
        recognitionRef.current.lang = 'en-US';
        
        recognitionRef.current.onresult = (e) => {
          const transcript = e.results[0][0].transcript;
          setTranscriptPreview(transcript);
          onAnswer(transcript); // Auto submit on silence/end
        };
        recognitionRef.current.onstart = () => setStatus('Listening...');
        recognitionRef.current.onerror = (e) => setStatus('Error: ' + e.error);
      }

      if (isRecording) {
        recognitionRef.current.stop();
        setIsRecording(false);
      } else {
        setTranscriptPreview('');
        recognitionRef.current.start();
        setIsRecording(true);
      }
    };

    return (
      <div className="space-y-6">
        <div className="text-center">
          <button 
            onClick={toggleRecord} 
            disabled={btnDisabled}
            className={`px-8 py-4 rounded-full text-lg font-semibold transition-all shadow-lg min-w-[200px] text-white
              ${isRecording ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-500 hover:bg-blue-600'}
              ${btnDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isRecording ? 'Stop Recording' : 'Record Answer'}
          </button>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg border">
          <p className="text-sm text-gray-500 mb-1">Transcript:</p>
          <div className="bg-white p-3 rounded border min-h-[4rem] text-gray-600 italic">
            {transcriptPreview}
          </div>
        </div>
        <div className="text-center text-blue-600 text-sm">{status}</div>
      </div>
    );
  };

  const TextAnswerSection = ({ onAnswer }) => {
    const [txt, setTxt] = useState('');
    return (
      <div className="space-y-4">
        <textarea 
          className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg h-32 focus:border-purple-500 outline-none"
          placeholder="Type your answer here..."
          value={txt}
          onChange={e => setTxt(e.target.value)}
        />
        <div className="flex gap-3">
          <button onClick={() => onAnswer(txt || 'No answer')} className="flex-1 px-6 py-3 bg-purple-500 text-white rounded-lg">Submit</button>
          <button onClick={() => onAnswer('Skipped')} className="px-4 py-3 bg-gray-300 rounded-lg">Skip</button>
        </div>
      </div>
    );
  };

  // --- RENDER HELPERS ---
  
  // 1. ADMIN VIEW
  const renderAdmin = () => (
    <div className="fade-in">
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <h2 className="text-3xl font-bold text-gray-800 mb-6 flex items-center"><span className="mr-3">👨‍💼</span>Admin Dashboard</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="text-xl font-semibold mb-4 text-blue-800">User Management</h3>
            <div className="space-y-4">
              <div className="flex space-x-2">
                <input value={newUser.name} onChange={e => setNewUser({...newUser, name: e.target.value})} placeholder="Full Name" className="flex-1 px-3 py-2 border rounded-lg"/>
                <select value={newUser.role} onChange={e => setNewUser({...newUser, role: e.target.value})} className="px-3 py-2 border rounded-lg">
                  <option value="student">Student</option>
                  <option value="teacher">Teacher</option>
                </select>
                <button onClick={addUser} className="px-4 py-2 bg-blue-500 text-white rounded-lg">Add</button>
              </div>
              <div className="max-h-40 overflow-y-auto space-y-2">
                {users.map(u => (
                  <div key={u.id} className="flex justify-between items-center bg-white p-2 border rounded">
                    <span>{u.name} ({u.role})</span>
                    <button onClick={() => removeUser(u.id)} className="text-red-500 text-sm">Remove</button>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="bg-green-50 rounded-lg p-6">
            <h3 className="text-xl font-semibold mb-4 text-green-800">Assignment Management</h3>
            <div className="space-y-2">
              <input value={adminTask.title} onChange={e => setAdminTask({...adminTask, title: e.target.value})} placeholder="Title" className="w-full px-3 py-2 border rounded-lg"/>
              <select value={adminTask.teacherId} onChange={e => setAdminTask({...adminTask, teacherId: e.target.value})} className="w-full px-3 py-2 border rounded-lg">
                <option value="">Select Teacher</option>
                {users.filter(u => u.role === 'teacher').map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
              <textarea value={adminTask.description} onChange={e => setAdminTask({...adminTask, description: e.target.value})} placeholder="Description" className="w-full px-3 py-2 border rounded-lg h-20"/>
              <button onClick={assignWork} className="w-full px-4 py-2 bg-green-500 text-white rounded-lg">Assign Work</button>
            </div>
          </div>
        </div>
        {/* Stats */}
        <div className="mt-6 grid md:grid-cols-4 gap-4 text-center">
          <div className="bg-blue-100 p-4 rounded-lg"><div className="text-2xl font-bold text-blue-600">{users.filter(u => u.role === 'student').length}</div><div className="text-sm">Students</div></div>
          <div className="bg-green-100 p-4 rounded-lg"><div className="text-2xl font-bold text-green-600">{users.filter(u => u.role === 'teacher').length}</div><div className="text-sm">Teachers</div></div>
          <div className="bg-purple-100 p-4 rounded-lg"><div className="text-2xl font-bold text-purple-600">{assignments.length}</div><div className="text-sm">Assignments</div></div>
          <div className="bg-orange-100 p-4 rounded-lg"><div className="text-2xl font-bold text-orange-600">{users.filter(s => s.interviewScore).length}</div><div className="text-sm">Interviews</div></div>
        </div>
      </div>
    </div>
  );

  // 2. TEACHER VIEW
  const renderTeacher = () => (
    <div className="h-[calc(100vh-80px)] flex bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
      <aside className="w-64 bg-gray-50 border-r flex flex-col">
        <div className="p-6 border-b bg-white"><h2 className="text-xl font-bold">👩‍🏫 Dashboard</h2></div>
        <nav className="flex-1 p-4 space-y-2">
          {['progress', 'create', 'my-assignments', 'assignment'].map(tab => (
            <button 
              key={tab} 
              onClick={() => setActiveTab(tab)}
              className={`w-full text-left px-4 py-3 rounded-lg font-medium flex items-center transition-all ${activeTab === tab ? 'bg-blue-500 text-white shadow-md' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              {tab === 'progress' && '📈 Student Progress'}
              {tab === 'create' && '➕ Create Assignment'}
              {tab === 'my-assignments' && '📂 My Assignments'}
              {tab === 'assignment' && '📥 Admin Tasks'}
            </button>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto p-8 bg-gray-50/50">
        {activeTab === 'progress' && (
          <div className="fade-in">
            <h3 className="text-2xl font-bold mb-6">Student Progress</h3>
            <div className="bg-white p-6 rounded-xl shadow-sm border space-y-3">
              {users.filter(u => u.role === 'student').map(s => (
                <div key={s.id} className="bg-white p-4 rounded-lg border">
                  <div className="flex justify-between font-bold"><span>{s.name}</span><span className="text-blue-600">ATS: {s.atsScore || 'N/A'}</span></div>
                  <div className="w-full bg-gray-100 rounded-full h-2 mt-2"><div className="bg-blue-500 h-2 rounded-full" style={{width: `${s.atsScore || 0}%`}}></div></div>
                </div>
              ))}
            </div>
          </div>
        )}
        {activeTab === 'create' && (
          <div className="fade-in">
            <h3 className="text-2xl font-bold mb-6">Create Assignment</h3>
            <div className="bg-white p-8 rounded-xl shadow-sm border max-w-3xl space-y-6">
              <div><label className="block text-sm font-medium mb-2">Title</label><input value={assignmentForm.title} onChange={e => setAssignmentForm({...assignmentForm, title: e.target.value})} className="w-full px-4 py-3 border rounded-lg"/></div>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Type</label>
                  <select value={assignmentForm.type} onChange={e => setAssignmentForm({...assignmentForm, type: e.target.value})} className="w-full px-4 py-3 border rounded-lg">
                    <option value="manual">Manual</option><option value="quiz">AI Quiz</option><option value="presentation">Presentation</option>
                  </select>
                </div>
                <div><label className="block text-sm font-medium mb-2">Due Date</label><input type="date" value={assignmentForm.dueDate} onChange={e => setAssignmentForm({...assignmentForm, dueDate: e.target.value})} className="w-full px-4 py-3 border rounded-lg"/></div>
              </div>
              <div><label className="block text-sm font-medium mb-2">Description</label><textarea value={assignmentForm.description} onChange={e => setAssignmentForm({...assignmentForm, description: e.target.value})} className="w-full px-4 py-3 border rounded-lg h-32"/></div>
              <button onClick={createAssignment} className="w-full py-3 bg-blue-600 text-white rounded-lg">Publish Assignment</button>
            </div>
          </div>
        )}
        {activeTab === 'my-assignments' && (
          <div className="fade-in">
            <h3 className="text-2xl font-bold mb-6">My Created Assignments</h3>
            <div className="bg-white p-6 rounded-xl shadow-sm border min-h-[400px] grid gap-4 grid-cols-1 lg:grid-cols-2">
              {assignments.filter(a => a.createdBy === 'teacher').length === 0 ? <p className="text-gray-500">None created.</p> :
               assignments.filter(a => a.createdBy === 'teacher').map(a => (
                 <div key={a.id} className="bg-white p-5 rounded-lg border hover:shadow-md">
                   <div className="flex justify-between items-start mb-2"><h4 className="font-bold text-lg">{a.title}</h4><span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">{a.type}</span></div>
                   <p className="text-sm text-gray-600 mb-4 line-clamp-2">{a.description}</p>
                   <div className="flex items-center justify-between border-t pt-3">
                     <span className="text-xs text-gray-500">📅 {a.dueDate}</span>
                     <button onClick={() => openEditModal(a)} className="px-3 py-1 bg-gray-100 text-sm rounded border hover:text-blue-600">✏️ Edit</button>
                   </div>
                 </div>
               ))}
            </div>
          </div>
        )}
        {activeTab === 'assignment' && (
          <div className="fade-in">
            <h3 className="text-2xl font-bold mb-6">Admin Tasks</h3>
            <div className="bg-white p-6 rounded-xl shadow-sm border grid gap-4">
              {adminAssignedTasks.length === 0 ? <p className="text-center text-gray-500">No tasks.</p> : 
                adminAssignedTasks.map(t => (
                  <div key={t.id} className={`bg-white p-5 rounded-lg border-l-4 ${t.status === 'Completed' ? 'border-l-green-500' : 'border-l-yellow-500'} border`}>
                    <div className="flex justify-between items-center">
                      <div><h4 className="font-bold">{t.title}</h4><p className="text-sm text-gray-600">{t.description}</p></div>
                      <button onClick={() => t.status !== 'Completed' && markTaskComplete(t.id)} className={`px-4 py-2 rounded text-sm font-medium ${t.status === 'Completed' ? 'bg-gray-100 text-gray-400' : 'bg-green-500 text-white'}`}>
                        {t.status === 'Completed' ? 'Completed' : 'Mark Done'}
                      </button>
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
        )}
      </main>
    </div>
  );

  // 3. STUDENT VIEW
  const renderStudent = () => {
    const student = getCurrentStudent() || { name: 'Student', id: '000', atsScore: '--' };
    return (
      <div className="h-[calc(100vh-80px)] flex bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
        <aside className="w-64 bg-gray-50 border-r flex flex-col">
          <div className="p-6 border-b bg-white"><h2 className="text-xl font-bold">🎓 Dashboard</h2></div>
          <nav className="flex-1 p-4 space-y-2">
            {['profile', 'resume', 'interview', 'assignments'].map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)} className={`w-full text-left px-4 py-3 rounded-lg font-medium flex items-center transition-all ${activeTab === tab ? 'bg-blue-500 text-white shadow-md' : 'text-gray-600 hover:bg-gray-100'}`}>
                {tab === 'profile' && '👤 Profile'}
                {tab === 'resume' && '📄 Resume Analysis'}
                {tab === 'interview' && '🎤 Mock Interview'}
                {tab === 'assignments' && '📚 Assignments'}
              </button>
            ))}
          </nav>
        </aside>
        <main className="flex-1 overflow-y-auto p-8 bg-gray-50/50">
          {activeTab === 'profile' && (
            <div className="fade-in bg-white p-8 rounded-xl shadow-sm border max-w-2xl">
              <div className="flex items-center space-x-6 mb-8"><div className="w-24 h-24 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-full flex items-center justify-center text-4xl shadow-lg">👤</div><div><h4 className="text-2xl font-bold">{student.name}</h4><p className="text-gray-500 text-lg">ID: {student.id.slice(-4)}</p></div></div>
              <div className="grid grid-cols-2 gap-4"><div className="bg-blue-50 p-6 rounded-lg"><p className="text-sm text-blue-600 font-bold">ATS Score</p><p className="text-3xl font-bold text-blue-700">{student.atsScore || '--'}</p></div><div className="bg-purple-50 p-6 rounded-lg"><p className="text-sm text-purple-600 font-bold">Status</p><p className="text-xl font-bold text-purple-700">Active</p></div></div>
            </div>
          )}
          {activeTab === 'resume' && (
            <div className="fade-in bg-white p-6 rounded-xl shadow-sm border max-w-3xl">
              <div className="bg-green-50 rounded-lg p-6 mb-6">
                <h4 className="text-lg font-semibold mb-4 text-green-800">Upload Resume</h4>
                <input type="file" id="resumeUpload" accept=".pdf" className="w-full mb-4"/>
                <button onClick={() => analyzeResume(document.getElementById('resumeUpload').files[0])} className="w-full py-3 bg-green-600 text-white rounded-lg">Analyze Resume</button>
              </div>
            </div>
          )}
          {activeTab === 'interview' && (
            <div className="fade-in bg-white p-6 rounded-xl shadow-sm border max-w-3xl">
              <div className="bg-purple-50 rounded-lg p-8 text-center">
                <h4 className="text-xl font-bold text-purple-900 mb-2">Ready to practice?</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-lg mx-auto mt-6">
                  <button onClick={() => startInterview('voice')} className="p-4 bg-white border-2 border-purple-200 rounded-xl hover:border-purple-500"><span className="text-3xl block">🎙️</span>Voice Interview</button>
                  <button onClick={() => startInterview('text')} className="p-4 bg-white border-2 border-indigo-200 rounded-xl hover:border-indigo-500"><span className="text-3xl block">⌨️</span>Text Interview</button>
                </div>
              </div>
            </div>
          )}
          {activeTab === 'assignments' && (
            <div className="fade-in bg-white p-6 rounded-xl shadow-sm border min-h-[400px] grid gap-4 grid-cols-1 xl:grid-cols-2">
              {assignments.length === 0 ? <p>No assignments.</p> : assignments.map(a => (
                <div key={a.id} className="bg-white p-4 rounded border">
                  <h4 className="font-semibold">{a.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{a.description}</p>
                  <p className="text-xs text-gray-500 mt-2">Due: {a.dueDate}</p>
                  <div className="mt-3 space-y-2">
                    <input type="file" id={`file-${a.id}`} className="text-sm w-full"/>
                    <input type="text" id={`note-${a.id}`} placeholder="Optional notes" className="text-sm w-full border px-2 py-1 rounded"/>
                    <button onClick={() => submitAssignment(a.id, document.getElementById(`file-${a.id}`).files[0], document.getElementById(`note-${a.id}`).value)} className="w-full bg-blue-500 text-white py-2 rounded text-sm">Submit</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    );
  };

  // 4. HR VIEW
  const renderHR = () => (
    <div className="fade-in bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 flex items-center"><span className="mr-3">👔</span>HR Dashboard</h2>
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-blue-50 rounded-lg p-6"><h3 className="text-xl font-semibold mb-4 text-blue-800">Resumes</h3><div className="space-y-4 max-h-96 overflow-y-auto">{users.filter(u => u.role === 'student').map(s => <div key={s.id} className="bg-white p-4 border flex justify-between"><span>{s.name}</span><span className="text-blue-600">ATS: {s.atsScore || 'N/A'}</span></div>)}</div></div>
        <div className="bg-green-50 rounded-lg p-6"><h3 className="text-xl font-semibold mb-4 text-green-800">Interviews</h3><div className="space-y-4 max-h-96 overflow-y-auto">{users.filter(s => s.interviewScore).map(s => <div key={s.id} className="bg-white p-4 border flex justify-between"><span>{s.name}</span><span>Score: {s.interviewScore}</span></div>)}</div></div>
      </div>
    </div>
  );

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
      {/* NAVBAR */}
      <nav className="bg-white shadow-lg border-b-4 border-blue-500">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              {/* UPDATED LOGO IN NAVBAR */}
              <img src={logo} alt="Logo" className="h-12 w-auto" />
              <h1 className="text-2xl font-bold text-gray-800">ProEduvate</h1>
            </div>
            <button onClick={handleLogout} className="px-4 py-2 rounded-lg font-medium bg-red-500 text-white hover:bg-red-600">Logout</button>
          </div>
        </div>
      </nav>

      {/* MAIN CONTENT AREA */}
      <div className="max-w-7xl mx-auto p-4 sm:p-6">
        {role === 'admin' && renderAdmin()}
        {role === 'teacher' && renderTeacher()}
        {role === 'student' && renderStudent()}
        {role === 'hr' && renderHR()}
      </div>

      {/* CHATBOT TOGGLE & WINDOW */}
      {role === 'student' && (
        <>
          <div className="fixed bottom-5 right-5 z-[1000]">
            <button onClick={() => setChatbotOpen(!chatbotOpen)} className="w-16 h-16 bg-indigo-500 hover:bg-indigo-600 text-white rounded-full shadow-lg text-2xl flex items-center justify-center">💬</button>
          </div>
          {chatbotOpen && (
            <div className="fixed bottom-20 right-5 w-96 h-[600px] z-[999] bg-white rounded-lg shadow-xl border flex flex-col">
              <div className="bg-indigo-500 text-white p-4 rounded-t-lg flex justify-between"><h3 className="font-semibold">AI Assistant</h3><button onClick={() => setChatbotOpen(false)}>✕</button></div>
              <div className="flex-1 p-4 overflow-y-auto" ref={chatScrollRef}>
                {chatMessages.map((msg, idx) => (
                  <div key={idx} className={`mb-2 ${msg.sender === 'user' ? 'text-right font-bold' : 'text-left text-gray-600'}`}>
                    {msg.component ? msg.component : msg.text}
                  </div>
                ))}
              </div>
              <div className="p-4 border-t flex space-x-2">
                <input value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyPress={e => e.key === 'Enter' && sendChatMessage()} className="flex-1 px-3 py-2 border rounded-lg" placeholder="Ask..."/>
                <button onClick={sendChatMessage} className="bg-indigo-500 text-white px-3 py-2 rounded-lg">Send</button>
                <button onClick={() => setQuizModalOpen(true)} className="bg-purple-500 text-white px-3 py-2 rounded-lg">Quiz</button>
              </div>
            </div>
          )}
        </>
      )}

      {/* QUIZ MODAL */}
      {quizModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[1050]">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-bold mb-4">Create Quiz</h3>
            <div className="space-y-4">
              <input value={quizConfig.topic} onChange={e => setQuizConfig({...quizConfig, topic: e.target.value})} placeholder="Topic (e.g. Java)" className="w-full px-3 py-2 border rounded-lg"/>
              <input type="number" value={quizConfig.questions} onChange={e => setQuizConfig({...quizConfig, questions: e.target.value})} className="w-full px-3 py-2 border rounded-lg"/>
            </div>
            <div className="mt-6 flex justify-end space-x-3">
              <button onClick={() => setQuizModalOpen(false)} className="px-4 py-2 bg-gray-200 rounded">Cancel</button>
              <button onClick={startQuiz} className="px-4 py-2 bg-indigo-500 text-white rounded">Start</button>
            </div>
          </div>
        </div>
      )}

      {/* EDIT ASSIGNMENT MODAL (FIXED) */}
      {editModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[1050]">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg mx-4">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Edit Assignment</h3>
            <div className="space-y-4">
              <div><label className="block text-sm font-medium">Title</label><input value={editForm.title} onChange={e => setEditForm({...editForm, title: e.target.value})} className="w-full px-3 py-2 border rounded-lg"/></div>
              <div><label className="block text-sm font-medium">Description</label><textarea value={editForm.description} onChange={e => setEditForm({...editForm, description: e.target.value})} className="w-full px-3 py-2 border rounded-lg h-24"/></div>
              <div><label className="block text-sm font-medium">Due Date</label><input type="date" value={editForm.dueDate} onChange={e => setEditForm({...editForm, dueDate: e.target.value})} className="w-full px-3 py-2 border rounded-lg"/></div>
            </div>
            <div className="mt-6 flex justify-end space-x-3 pt-4 border-t">
              <button onClick={() => setEditModalOpen(false)} className="px-4 py-2 bg-gray-200 rounded-lg">Cancel</button>
              <button onClick={saveAssignmentChanges} className="px-4 py-2 bg-blue-600 text-white rounded-lg">Save Changes</button>
            </div>
          </div>
        </div>
      )}

      {/* INTERVIEW MODAL */}
      {interviewModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[1050] p-4">
          <div className="bg-white rounded-12 shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto relative rounded-xl">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center z-10">
              <h3 className="text-xl font-bold">🎤 Mock Interview</h3>
              <button onClick={() => setInterviewModalOpen(false)} className="text-2xl font-bold text-gray-400 hover:text-gray-600">×</button>
            </div>
            <div className="p-6">
              {interviewContent}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;