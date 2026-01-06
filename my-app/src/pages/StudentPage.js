import React, { useState, useEffect, useRef } from 'react';
import Sidebar from '../components/Sidebar';
import Chatbot from '../components/Chatbot';
import Modal from '../components/Modal';
import CodingInterface from '../components/CodingInterface';
import { useData } from '../context/DataContext';
import { studentAPI, interviewAPI, chatbotAPI } from '../services/api';
import { FileText, Briefcase, Upload, MessageSquare, Trophy, User, Code, Database, Globe, BarChart3, Network, Cloud, MessageCircle, Users, Users2, Brain, Clock, Target, CheckCircle, Award, ArrowLeft, ClipboardList, Mic, Check, X, Menu } from 'lucide-react';

const StudentPage = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { users, assignments, fetchAllData } = useData();
  
  // Student data
  const currentStudent = users.find(u => u.role === 'student') || { id: 1, name: 'Demo Student' };
  const [studentAssignments, setStudentAssignments] = useState([]);
  const [progress, setProgress] = useState(null);
  
  // Resume analysis
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeAnalyzing, setResumeAnalyzing] = useState(false);
  const [resumeResults, setResumeResults] = useState(null);
  
  // Interview
  const [interviewModalOpen, setInterviewModalOpen] = useState(false);
  const [interviewMode, setInterviewMode] = useState(null);
  const [interviewQuestions, setInterviewQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState([]);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [interviewDuration, setInterviewDuration] = useState(20);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [timerActive, setTimerActive] = useState(false);
  const [interviewResults, setInterviewResults] = useState(null);
  
  // Quiz
  const [quizModalOpen, setQuizModalOpen] = useState(false);
  const [currentQuiz, setCurrentQuiz] = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [quizResults, setQuizResults] = useState(null);
  
  // Placement Training
  const [trainingType, setTrainingType] = useState(null); // 'technical' or 'non-technical'
  const [trainingCategory, setTrainingCategory] = useState(null);
  const [trainingModalOpen, setTrainingModalOpen] = useState(false);
  const [trainingQuestions, setTrainingQuestions] = useState([]);
  const [currentTrainingIndex, setCurrentTrainingIndex] = useState(0);
  const [trainingAnswer, setTrainingAnswer] = useState('');
  const [trainingFeedback, setTrainingFeedback] = useState([]);
  const [trainingLoading, setTrainingLoading] = useState(false);
  const [trainingComplete, setTrainingComplete] = useState(false);
  
  // Coding Practice
  const [codingInterfaceOpen, setCodingInterfaceOpen] = useState(false);
  const [codingLanguage, setCodingLanguage] = useState('python'); // 'python' or 'c';
  
  // Speech recognition and synthesis
  const recognitionRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  useEffect(() => {
    fetchAllData();
    loadStudentData();
  }, []);

  useEffect(() => {
    if (timerActive && timeRemaining > 0) {
      timerIntervalRef.current = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            clearInterval(timerIntervalRef.current);
            setTimerActive(false);
            handleFinishInterview();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, [timerActive, timeRemaining]);

  const loadStudentData = async () => {
    try {
      const [assignmentsRes, progressRes] = await Promise.all([
        studentAPI.getAssignments(currentStudent.id),
        studentAPI.getProgress(currentStudent.id),
      ]);
      setStudentAssignments(assignmentsRes.data);
      setProgress(progressRes.data);
    } catch (error) {
      console.error('Error loading student data:', error);
    }
  };

  const handleSubmitAssignment = async (assignmentId) => {
    const fileInput = document.getElementById(`file-${assignmentId}`);
    if (!fileInput || fileInput.files.length === 0) {
      alert('Please select a file to submit.');
      return;
    }

    const formData = new FormData();
    formData.append('assignment_file', fileInput.files[0]);
    formData.append('student_id', currentStudent.id);

    try {
      await studentAPI.submitAssignment(currentStudent.id, assignmentId, formData);
      alert('Assignment submitted successfully!');
      fileInput.value = '';
      await loadStudentData();
    } catch (error) {
      console.error('Error submitting assignment:', error);
      alert('Failed to submit assignment.');
    }
  };

  const handleResumeAnalysis = async () => {
    if (!resumeFile) {
      alert('Please select a resume file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('resume', resumeFile);
    
    setResumeAnalyzing(true);
    setResumeResults(null);

    try {
      const response = await studentAPI.uploadResume(currentStudent.id, formData);
      const result = response.data;
      
      setResumeResults({
        score: result.match_score || result.score || result.overall_score || 'N/A',
        summary: result.summary || 'No summary available.',
        matchingKeywords: result.matching_keywords || [],
        missingKeywords: result.missing_keywords || [],
      });
      
      await loadStudentData();
    } catch (error) {
      console.error('Error analyzing resume:', error);
      alert('Failed to analyze resume.');
    } finally {
      setResumeAnalyzing(false);
    }
  };

  const handleStartQuiz = (assignment) => {
    setCurrentQuiz(assignment);
    setQuizAnswers({});
    setQuizResults(null);
    setQuizModalOpen(true);
  };

  const handleQuizAnswerChange = (questionIndex, answer) => {
    setQuizAnswers(prev => ({
      ...prev,
      [questionIndex]: answer
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!currentQuiz) return;
    
    // Check if all questions are answered
    const totalQuestions = currentQuiz.quiz_questions?.length || 0;
    const answeredQuestions = Object.keys(quizAnswers).length;
    
    if (answeredQuestions < totalQuestions) {
      const proceed = window.confirm(`You have answered ${answeredQuestions} out of ${totalQuestions} questions. Do you want to submit anyway?`);
      if (!proceed) return;
    }

    setQuizSubmitting(true);
    
    try {
      // Auto-grade MCQ quiz
      let totalScore = 0;
      const questionFeedback = [];
      const pointsPerQuestion = Math.floor(100 / totalQuestions);
      
      for (let i = 0; i < totalQuestions; i++) {
        const question = currentQuiz.quiz_questions[i];
        const questionText = typeof question === 'string' ? question : question?.question || '';
        const correctAnswer = question?.correct_answer || '';
        const studentAnswer = quizAnswers[i] || '';
        
        // Check if answer is correct
        const isCorrect = studentAnswer.trim().toLowerCase() === correctAnswer.trim().toLowerCase();
        const points = isCorrect ? pointsPerQuestion : 0;
        totalScore += points;
        
        questionFeedback.push({
          question: questionText,
          answer: studentAnswer || 'No answer provided',
          correctAnswer: correctAnswer,
          feedback: isCorrect ? 'Correct!' : `Incorrect. The correct answer is: ${correctAnswer}`,
          points: points,
          isCorrect: isCorrect
        });
      }

      const evaluationData = {
        score: Math.round(totalScore),
        questionFeedback: questionFeedback,
        overallFeedback: `You scored ${Math.round(totalScore)}% on this quiz. ${totalScore >= 70 ? 'Great job!' : 'Keep practicing!'}`
      };

      // Submit the quiz assignment
      const submissionData = new FormData();
      const quizBlob = new Blob([JSON.stringify({
        answers: Object.values(quizAnswers),
        score: evaluationData.score,
        feedback: evaluationData
      })], { type: 'application/json' });
      submissionData.append('assignment_file', quizBlob, 'quiz_answers.json');
      submissionData.append('student_id', currentStudent.id);
      submissionData.append('quiz_score', evaluationData.score);

      await studentAPI.submitAssignment(currentStudent.id, currentQuiz.id, submissionData);
      
      setQuizResults(evaluationData);
      await loadStudentData();
    } catch (error) {
      console.error('Error submitting quiz:', error);
      alert('Failed to submit quiz. Please try again.');
    } finally {
      setQuizSubmitting(false);
    }
  };

  const closeQuizModal = () => {
    setQuizModalOpen(false);
    setCurrentQuiz(null);
    setQuizAnswers({});
    setQuizResults(null);
  };

  const technicalCategories = [
    { id: 'programming', name: 'Python Programming', icon: Code, description: 'Practice Python coding problems and algorithms' },
    { id: 'c-programming', name: 'C Programming', icon: Code, description: 'Practice C coding problems and algorithms' },
    { id: 'databases', name: 'Database & SQL', icon: Database, description: 'Master database concepts and queries' },
    { id: 'webdev', name: 'Web Development', icon: Globe, description: 'Learn frontend and backend technologies' },
    { id: 'dsa', name: 'Data Structures & Algorithms', icon: BarChart3, description: 'Strengthen problem-solving skills' },
    { id: 'system-design', name: 'System Design', icon: Network, description: 'Learn to design scalable systems' },
    { id: 'devops', name: 'DevOps & Cloud', icon: Cloud, description: 'Master deployment and cloud platforms' },
  ];

  const nonTechnicalCategories = [
    { id: 'communication', name: 'Communication Skills', icon: MessageCircle, description: 'Improve verbal and written communication' },
    { id: 'leadership', name: 'Leadership & Management', icon: Users, description: 'Develop leadership qualities' },
    { id: 'teamwork', name: 'Teamwork & Collaboration', icon: Users2, description: 'Learn to work effectively in teams' },
    { id: 'problem-solving', name: 'Problem Solving', icon: Brain, description: 'Enhance analytical thinking' },
    { id: 'time-management', name: 'Time Management', icon: Clock, description: 'Learn to manage time efficiently' },
    { id: 'aptitude', name: 'Aptitude & Reasoning', icon: Target, description: 'Practice logical reasoning' },
  ];

  const startTraining = async (category) => {
    // Special handling for Programming & Coding categories
    if (category === 'programming') {
      setCodingLanguage('python');
      setCodingInterfaceOpen(true);
      return;
    }
    
    if (category === 'c-programming') {
      setCodingLanguage('c');
      setCodingInterfaceOpen(true);
      return;
    }

    setTrainingCategory(category);
    setTrainingModalOpen(true);
    setTrainingLoading(true);
    setCurrentTrainingIndex(0);
    setTrainingFeedback([]);
    setTrainingComplete(false);

    try {
      const categoryName = trainingType === 'technical' 
        ? technicalCategories.find(c => c.id === category)?.name
        : nonTechnicalCategories.find(c => c.id === category)?.name;

      const response = await chatbotAPI.sendMessage({
        message: `Generate 5 ${trainingType} training questions for the topic: ${categoryName}. Format: Return a JSON array of 5 questions as strings. Each question should be clear, specific, and relevant to ${categoryName}. Make them interview-style questions that test understanding and practical knowledge.`,
        user_id: currentStudent.id
      });

      let questions = [];
      try {
        const responseText = response.data.response;
        const jsonMatch = responseText.match(/\[.*\]/s);
        if (jsonMatch) {
          questions = JSON.parse(jsonMatch[0]);
        } else {
          questions = [
            `What are the key concepts in ${categoryName}?`,
            `Can you explain a practical application of ${categoryName}?`,
            `What challenges might you face when working with ${categoryName}?`,
            `How would you approach a problem related to ${categoryName}?`,
            `What best practices should be followed for ${categoryName}?`
          ];
        }
      } catch (parseError) {
        questions = [
          `What are the key concepts in ${categoryName}?`,
          `Can you explain a practical application of ${categoryName}?`,
          `What challenges might you face when working with ${categoryName}?`,
          `How would you approach a problem related to ${categoryName}?`,
          `What best practices should be followed for ${categoryName}?`
        ];
      }

      setTrainingQuestions(questions);
    } catch (error) {
      console.error('Error starting training:', error);
      alert('Failed to start training session.');
      setTrainingModalOpen(false);
    } finally {
      setTrainingLoading(false);
    }
  };

  const submitTrainingAnswer = async () => {
    if (!trainingAnswer.trim()) {
      alert('Please provide an answer before submitting.');
      return;
    }

    setTrainingLoading(true);
    try {
      const response = await chatbotAPI.sendMessage({
        message: `As an expert interviewer, evaluate this answer and provide constructive feedback. Question: "${trainingQuestions[currentTrainingIndex]}" Answer: "${trainingAnswer}". Provide: 1) A brief evaluation (2-3 sentences), 2) What was good, 3) What could be improved, 4) A rating out of 10. Be encouraging but honest.`,
        user_id: currentStudent.id
      });

      const feedback = {
        question: trainingQuestions[currentTrainingIndex],
        answer: trainingAnswer,
        feedback: response.data.response,
        timestamp: new Date().toISOString()
      };

      setTrainingFeedback(prev => [...prev, feedback]);
      setTrainingAnswer('');

      if (currentTrainingIndex < trainingQuestions.length - 1) {
        setCurrentTrainingIndex(prev => prev + 1);
      } else {
        setTrainingComplete(true);
      }
    } catch (error) {
      console.error('Error submitting training answer:', error);
      alert('Failed to get feedback. Please try again.');
    } finally {
      setTrainingLoading(false);
    }
  };

  const closeTrainingModal = () => {
    setTrainingModalOpen(false);
    setTrainingType(null);
    setTrainingCategory(null);
    setTrainingQuestions([]);
    setCurrentTrainingIndex(0);
    setTrainingAnswer('');
    setTrainingFeedback([]);
    setTrainingComplete(false);
  };

  const speakText = (text) => {
    if (synthRef.current && interviewMode === 'voice') {
      // Cancel any ongoing speech
      synthRef.current.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 1;
      
      synthRef.current.speak(utterance);
    }
  };

  const startInterview = async (mode) => {
    setInterviewMode(mode);
    setInterviewModalOpen(true);
    setCurrentQuestionIndex(0);
    setUserAnswers([]);
    setInterviewResults(null);
    
    try {
      const response = await interviewAPI.startInterview({ user_id: currentStudent.id });
      const questions = response.data.questions || [];
      setInterviewQuestions(questions);
      setTimeRemaining(interviewDuration * 60);
      setTimerActive(true);
      
      if (mode === 'voice') {
        initializeSpeechRecognition();
        // Speak the first question
        setTimeout(() => {
          if (questions.length > 0) {
            speakText(`Question 1. ${questions[0]}`);
          }
        }, 500);
      }
    } catch (error) {
      console.error('Error starting interview:', error);
      alert('Failed to start interview.');
      setInterviewModalOpen(false);
    }
  };

  const initializeSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in your browser.');
      return;
    }

    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = 'en-US';

    recognitionRef.current.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          transcript += event.results[i][0].transcript;
        }
      }
      if (transcript) {
        setCurrentAnswer(prev => prev + ' ' + transcript);
      }
    };

    recognitionRef.current.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
    };
  };

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      initializeSpeechRecognition();
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      recognitionRef.current.start();
      setIsRecording(true);
    }
  };

  const submitAnswer = async () => {
    const answer = currentAnswer.trim();
    if (!answer && interviewMode === 'text') {
      alert('Please provide an answer before submitting.');
      return;
    }

    const newAnswers = [...userAnswers, answer || 'No answer provided'];
    setUserAnswers(newAnswers);
    setCurrentAnswer('');
    
    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }

    if (currentQuestionIndex < interviewQuestions.length - 1) {
      const nextIndex = currentQuestionIndex + 1;
      
      // In voice mode, get AI feedback and speak it
      if (interviewMode === 'voice') {
        try {
          // Get AI feedback for the answer
          const feedbackResponse = await chatbotAPI.sendMessage({
            message: `Provide a brief, encouraging 1-2 sentence feedback for this interview answer. Question: "${interviewQuestions[currentQuestionIndex]}" Answer: "${answer}". Be supportive and constructive.`,
            user_id: currentStudent.id
          });
          
          const feedback = feedbackResponse.data.response || "Thank you for your answer.";
          
          // Speak the feedback and then the next question
          speakText(`${feedback} Now, question ${nextIndex + 1}. ${interviewQuestions[nextIndex]}`);
        } catch (error) {
          console.error('Error getting feedback:', error);
          speakText(`Thank you. Question ${nextIndex + 1}. ${interviewQuestions[nextIndex]}`);
        }
      }
      
      setCurrentQuestionIndex(nextIndex);
    } else {
      // Speak completion message in voice mode
      if (interviewMode === 'voice') {
        try {
          // Get final feedback
          const feedbackResponse = await chatbotAPI.sendMessage({
            message: `Provide a brief, encouraging 1-2 sentence feedback for this final interview answer. Question: "${interviewQuestions[currentQuestionIndex]}" Answer: "${answer}". Be supportive.`,
            user_id: currentStudent.id
          });
          
          const feedback = feedbackResponse.data.response || "Thank you for your answer.";
          speakText(`${feedback} Your interview is complete. Please wait while we evaluate your responses.`);
        } catch (error) {
          console.error('Error getting feedback:', error);
          speakText('Thank you. Your interview is complete. Please wait while we evaluate your responses.');
        }
      }
      handleFinishInterview(newAnswers);
    }
  };

  const skipQuestion = () => {
    submitAnswer();
  };

  const handleFinishInterview = async (answers = userAnswers) => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }
    setTimerActive(false);
    
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }

    try {
      const response = await interviewAPI.submitAnswers({
        questions: interviewQuestions,
        answers: answers,
        studentId: currentStudent.id,
      });
      
      setInterviewResults(response.data);
      await loadStudentData();
    } catch (error) {
      console.error('Error evaluating interview:', error);
      alert('Failed to evaluate interview.');
    }
  };

  const closeInterviewModal = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }
    setTimerActive(false);
    
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
    
    // Stop any ongoing speech
    if (synthRef.current) {
      synthRef.current.cancel();
    }
    
    setInterviewModalOpen(false);
    setInterviewMode(null);
    setCurrentQuestionIndex(0);
    setUserAnswers([]);
    setCurrentAnswer('');
    setInterviewResults(null);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const sidebarItems = [
    { id: 'profile', label: 'Profile', icon: <User size={20} /> },
    { id: 'resume', label: 'Resume Analysis', icon: <Upload size={20} /> },
    { id: 'interview', label: 'AI Interview', icon: <Briefcase size={20} /> },
    { id: 'assignments', label: 'My Assignments', icon: <FileText size={20} /> },
    { id: 'training', label: 'Placement Training', icon: <Trophy size={20} /> },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Floating Menu Button for Mobile */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="floating-menu-btn md:hidden"
      >
        <Menu size={24} className="text-gray-700" />
      </button>

      <div className="max-w-7xl mx-auto p-2 sm:p-4 h-screen">
        <div className="bg-gray-100 shadow-lg border-b-4 border-blue-500 rounded-lg sm:rounded-xl overflow-hidden flex h-full">
          <Sidebar
            items={sidebarItems}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            isOpen={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
            isCollapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          />

          <main className="flex-1 overflow-y-auto p-8 bg-gradient-to-br from-gray-50 to-slate-100">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">My Profile</h2>
                
                <div className="bg-white p-8 rounded-xl shadow-md mb-6">
                  <div className="flex items-center space-x-6 mb-8">
                    <div className="w-24 h-24 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center text-white text-4xl font-bold">
                      {currentStudent.name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold text-gray-800">{currentStudent.name}</h3>
                      <p className="text-gray-600 capitalize">{currentStudent.role}</p>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="border-l-4 border-blue-500 pl-4">
                      <p className="text-sm font-medium text-gray-600">Student ID</p>
                      <p className="text-lg text-gray-800">{currentStudent.id}</p>
                    </div>
                    <div className="border-l-4 border-blue-500 pl-4">
                      <p className="text-sm font-medium text-gray-600">Email</p>
                      <p className="text-lg text-gray-800">{currentStudent.email || 'student@example.com'}</p>
                    </div>
                  </div>
                </div>

                {/* Progress Stats */}
                <h3 className="text-2xl font-bold mb-4 text-gray-800">My Progress</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-blue-500">
                    <h4 className="text-lg font-semibold text-gray-600">Assignments Submitted</h4>
                    <p className="text-4xl font-bold text-blue-600 mt-2">
                      {progress?.submittedAssignments || 0}
                    </p>
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-green-500">
                    <h4 className="text-lg font-semibold text-gray-600">Interview Score</h4>
                    <p className="text-4xl font-bold text-green-600 mt-2">
                      {progress?.interviewScore ? `${progress.interviewScore}%` : 'N/A'}
                    </p>
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-purple-500">
                    <h4 className="text-lg font-semibold text-gray-600">Resume Match Score</h4>
                    <p className="text-4xl font-bold text-purple-600 mt-2">
                      {progress?.resumeScore ? `${progress.resumeScore}%` : 'N/A'}
                    </p>
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-orange-500">
                    <h4 className="text-lg font-semibold text-gray-600">Quiz Average</h4>
                    <p className="text-4xl font-bold text-orange-600 mt-2">
                      {progress?.quizScore || progress?.averageQuizScore ? `${Math.round(progress.quizScore || progress.averageQuizScore)}%` : 'N/A'}
                    </p>
                    {progress?.totalQuizzes > 0 && (
                      <p className="text-sm text-gray-500 mt-1">{progress.totalQuizzes} quiz{progress.totalQuizzes !== 1 ? 'zes' : ''} taken</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Assignments Tab */}
            {activeTab === 'assignments' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">My Assignments</h2>
                
                <div className="space-y-4">
                  {studentAssignments.length > 0 ? (
                    studentAssignments.map(assignment => (
                      <div key={assignment.id} className="bg-white p-6 rounded-xl shadow-md">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="text-lg font-bold text-gray-800">{assignment.title}</h3>
                              <span className={`px-3 py-1 text-xs rounded-full ${
                                assignment.type === 'Quiz' 
                                  ? 'bg-purple-100 text-purple-800' 
                                  : 'bg-blue-100 text-blue-800'
                              }`}>
                                {assignment.type || 'Assignment'}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-2">{assignment.description}</p>
                            {assignment.type === 'Quiz' && assignment.quiz_questions && (
                              <div className="flex items-center gap-1 mt-2">
                                <ClipboardList className="text-gray-500" size={16} />
                                <p className="text-sm text-gray-500">{assignment.quiz_questions.length} questions</p>
                              </div>
                            )}
                          </div>
                          {assignment.submitted && (
                            <div className="ml-4 px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium flex items-center">
                              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                              Submitted
                              {assignment.quiz_score && (
                                <span className="ml-2 font-bold">• {assignment.quiz_score}%</span>
                              )}
                            </div>
                          )}
                        </div>
                        
                        {!assignment.submitted ? (
                          assignment.type === 'Quiz' && assignment.quiz_questions ? (
                            <div className="mt-4">
                              <button
                                onClick={() => handleStartQuiz(assignment)}
                                className="bg-purple-500 hover:bg-purple-600 text-white px-6 py-3 rounded-lg font-medium transition-colors w-full flex items-center justify-center gap-2"
                              >
                                <ClipboardList size={20} />
                                Start Quiz
                              </button>
                            </div>
                          ) : (
                            <div className="mt-4 flex items-center space-x-4">
                              <input
                                type="file"
                                id={`file-${assignment.id}`}
                                className="flex-1 text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                              />
                              <button
                                onClick={() => handleSubmitAssignment(assignment.id)}
                                className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                              >
                                Submit
                              </button>
                            </div>
                          )
                        ) : (
                          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                            <p className="text-sm text-gray-700">
                              <span className="font-medium">Status:</span> Assignment submitted successfully
                              {assignment.submittedAt && (
                                <span className="text-gray-500"> on {new Date(assignment.submittedAt).toLocaleDateString()}</span>
                              )}
                            </p>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="bg-white p-12 rounded-xl shadow-md text-center">
                      <p className="text-gray-500 italic">No assignments available.</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Progress Tab */}
            {activeTab === 'progress' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">My Progress</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-blue-500">
                    <h3 className="text-lg font-semibold text-gray-600">Assignments Submitted</h3>
                    <p className="text-4xl font-bold text-blue-600 mt-2">
                      {progress?.submittedAssignments || 0}
                    </p>
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-green-500">
                    <h3 className="text-lg font-semibold text-gray-600">Interview Score</h3>
                    <p className="text-4xl font-bold text-green-600 mt-2">
                      {progress?.interviewScore ? `${progress.interviewScore}%` : 'N/A'}
                    </p>
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-purple-500">
                    <h3 className="text-lg font-semibold text-gray-600">Resume Match Score</h3>
                    <p className="text-4xl font-bold text-purple-600 mt-2">
                      {progress?.resumeScore ? `${progress.resumeScore}%` : 'N/A'}
                    </p>
                  </div>
                </div>

                {progress?.details && (
                  <div className="bg-white p-6 rounded-xl shadow-md">
                    <h3 className="text-xl font-bold mb-4 text-gray-700">Detailed Progress</h3>
                    <div className="space-y-3">
                      {progress.details.map((detail, index) => (
                        <div key={index} className="border-l-4 border-blue-500 pl-4">
                          <p className="font-medium text-gray-800">{detail.label}</p>
                          <p className="text-sm text-gray-600">{detail.value}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Interview Tab */}
            {activeTab === 'interview' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">AI Mock Interview</h2>
                
                <div className="bg-white p-6 rounded-xl shadow-md mb-6">
                  <h3 className="text-xl font-bold mb-4 text-gray-700">Select Interview Duration</h3>
                  <div className="grid grid-cols-3 gap-4">
                    {[10, 20, 30].map(duration => (
                      <button
                        key={duration}
                        onClick={() => setInterviewDuration(duration)}
                        className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                          interviewDuration === duration
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {duration} minutes
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white p-8 rounded-xl shadow-md text-center">
                    <div className="flex justify-center mb-4">
                      <div className="bg-blue-100 p-6 rounded-full">
                        <MessageSquare className="text-blue-600" size={48} />
                      </div>
                    </div>
                    <h3 className="text-xl font-bold mb-3 text-gray-800">Text Interview</h3>
                    <p className="text-gray-600 mb-6">Answer questions by typing your responses</p>
                    <button
                      onClick={() => startInterview('text')}
                      className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-lg font-medium transition-colors"
                    >
                      Start Text Interview
                    </button>
                  </div>

                  <div className="bg-white p-8 rounded-xl shadow-md text-center">
                    <div className="flex justify-center mb-4">
                      <div className="bg-green-100 p-6 rounded-full">
                        <Mic className="text-green-600" size={48} />
                      </div>
                    </div>
                    <h3 className="text-xl font-bold mb-3 text-gray-800">Voice Interview</h3>
                    <p className="text-gray-600 mb-6">Answer questions using your voice</p>
                    <button
                      onClick={() => startInterview('voice')}
                      className="bg-green-500 hover:bg-green-600 text-white px-8 py-3 rounded-lg font-medium transition-colors"
                    >
                      Start Voice Interview
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Placement Training Tab */}
            {activeTab === 'training' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Placement Training</h2>
                
                {!trainingType ? (
                  <div>
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl shadow-md mb-6">
                      <div className="flex items-center gap-3 mb-2">
                        <Target className="text-blue-600" size={28} />
                        <h3 className="text-xl font-bold text-gray-800">AI-Powered Skill Training</h3>
                      </div>
                      <p className="text-gray-600">Choose a training path and let our AI help you prepare for placements with personalized questions and feedback.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-white p-8 rounded-xl shadow-md hover:shadow-xl transition-shadow cursor-pointer border-2 border-transparent hover:border-blue-500"
                           onClick={() => setTrainingType('technical')}>
                        <div className="flex justify-center mb-4">
                          <div className="bg-blue-100 p-6 rounded-full">
                            <Code className="text-blue-600" size={48} />
                          </div>
                        </div>
                        <h3 className="text-2xl font-bold mb-3 text-gray-800 text-center">Technical Skills</h3>
                        <p className="text-gray-600 text-center mb-4">Master programming, databases, algorithms, and system design</p>
                        <div className="flex justify-center">
                          <button className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                            Start Training
                          </button>
                        </div>
                      </div>

                      <div className="bg-white p-8 rounded-xl shadow-md hover:shadow-xl transition-shadow cursor-pointer border-2 border-transparent hover:border-green-500"
                           onClick={() => setTrainingType('non-technical')}>
                        <div className="flex justify-center mb-4">
                          <div className="bg-green-100 p-6 rounded-full">
                            <MessageCircle className="text-green-600" size={48} />
                          </div>
                        </div>
                        <h3 className="text-2xl font-bold mb-3 text-gray-800 text-center">Non-Technical Skills</h3>
                        <p className="text-gray-600 text-center mb-4">Develop communication, leadership, and problem-solving abilities</p>
                        <div className="flex justify-center">
                          <button className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                            Start Training
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div>
                    <button
                      onClick={() => setTrainingType(null)}
                      className="mb-6 text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2"
                    >
                      <ArrowLeft size={20} />
                      Back to Training Types
                    </button>

                    <div className="flex items-center gap-3 mb-6">
                      {trainingType === 'technical' ? (
                        <Code className="text-blue-600" size={32} />
                      ) : (
                        <MessageCircle className="text-green-600" size={32} />
                      )}
                      <h3 className="text-2xl font-bold text-gray-800">
                        {trainingType === 'technical' ? 'Technical Skills Training' : 'Non-Technical Skills Training'}
                      </h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {(trainingType === 'technical' ? technicalCategories : nonTechnicalCategories).map(category => (
                        <div
                          key={category.id}
                          className="bg-white p-6 rounded-xl shadow-md hover:shadow-xl transition-all cursor-pointer border-2 border-transparent hover:border-blue-500 transform hover:-translate-y-1"
                          onClick={() => startTraining(category.id)}
                        >
                          <div className="flex justify-center mb-3">
                            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-full">
                              <category.icon className="text-blue-600" size={40} />
                            </div>
                          </div>
                          <h4 className="text-lg font-bold text-gray-800 mb-2 text-center">{category.name}</h4>
                          <p className="text-sm text-gray-600 text-center mb-4">{category.description}</p>
                          <div className="flex justify-center">
                            <button className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white px-4 py-2 rounded-lg font-medium transition-colors text-sm">
                              Start Session
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Resume Analysis Tab */}
            {activeTab === 'resume' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Resume ATS Analysis</h2>
                
                <div className="bg-white p-6 rounded-xl shadow-md mb-6">
                  <h3 className="text-xl font-bold mb-4 text-gray-700">Upload Your Resume</h3>
                  <div className="space-y-4">
                    <input
                      type="file"
                      accept=".pdf,.doc,.docx"
                      onChange={(e) => setResumeFile(e.target.files[0])}
                      className="w-full text-sm text-gray-600 file:mr-4 file:py-3 file:px-6 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    <button
                      onClick={handleResumeAnalysis}
                      disabled={!resumeFile || resumeAnalyzing}
                      className="w-full bg-purple-500 hover:bg-purple-600 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {resumeAnalyzing ? 'Analyzing...' : 'Analyze Resume'}
                    </button>
                  </div>
                </div>

                {resumeResults && (
                  <div className="bg-white p-6 rounded-xl shadow-md">
                    <h3 className="text-xl font-bold mb-4 text-gray-700">Analysis Results</h3>
                    
                    <div className="mb-6">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-lg font-semibold text-gray-700">ATS Match Score</span>
                        <span className="text-3xl font-bold text-purple-600">{resumeResults.score}</span>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold text-gray-800 mb-2">Summary</h4>
                        <p className="text-gray-700">{resumeResults.summary}</p>
                      </div>

                      <div>
                        <h4 className="font-semibold text-green-700 mb-2">Matching Skills</h4>
                        <ul className="list-disc list-inside text-green-600">
                          {resumeResults.matchingKeywords.map((keyword, index) => (
                            <li key={index}>{keyword}</li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <h4 className="font-semibold text-red-700 mb-2">Missing Skills</h4>
                        <ul className="list-disc list-inside text-red-600">
                          {resumeResults.missingKeywords.map((keyword, index) => (
                            <li key={index}>{keyword}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Chatbot Toggle */}
      <div className="chatbot-toggle">
        <button
          onClick={() => setChatbotOpen(!chatbotOpen)}
          className="w-16 h-16 bg-indigo-500 hover:bg-indigo-600 text-white rounded-full shadow-lg flex items-center justify-center"
        >
          <MessageSquare size={28} />
        </button>
      </div>

      {/* Chatbot Window */}
      <Chatbot isOpen={chatbotOpen} onClose={() => setChatbotOpen(false)} />

      {/* Quiz Modal */}
      <Modal
        isOpen={quizModalOpen}
        onClose={closeQuizModal}
        title={quizResults ? 'Quiz Results' : `${currentQuiz?.title || 'Quiz'}`}
      >
        {!quizResults ? (
          <div className="space-y-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-700">
                <span className="font-bold">Instructions:</span> Answer all questions to the best of your ability. 
                Your quiz will be evaluated by AI once submitted.
              </p>
              <p className="text-sm text-gray-600 mt-2">
                Total Questions: {currentQuiz?.quiz_questions?.length || 0}
              </p>
            </div>

            <div className="space-y-6 max-h-96 overflow-y-auto">
              {currentQuiz?.quiz_questions?.map((question, index) => {
                // Handle both string and object question formats
                const questionText = typeof question === 'string' 
                  ? question 
                  : question?.question || JSON.stringify(question);
                const options = question?.options || [];
                const hasOptions = Array.isArray(options) && options.length > 0;
                
                return (
                  <div key={index} className="bg-white p-4 rounded-lg border border-gray-200">
                    <h4 className="font-bold text-gray-800 mb-3">
                      {index + 1}. {questionText}
                    </h4>
                    {hasOptions ? (
                      <div className="space-y-2">
                        {options.map((option, optIndex) => (
                          <label 
                            key={optIndex}
                            className={`flex items-center p-3 rounded-lg border-2 cursor-pointer transition-all ${
                              quizAnswers[index] === option
                                ? 'border-purple-500 bg-purple-50'
                                : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50'
                            }`}
                          >
                            <input
                              type="radio"
                              name={`question-${index}`}
                              value={option}
                              checked={quizAnswers[index] === option}
                              onChange={(e) => handleQuizAnswerChange(index, e.target.value)}
                              className="w-4 h-4 text-purple-600 focus:ring-purple-500"
                            />
                            <span className="ml-3 text-gray-700">{option}</span>
                          </label>
                        ))}
                      </div>
                    ) : (
                      <textarea
                        value={quizAnswers[index] || ''}
                        onChange={(e) => handleQuizAnswerChange(index, e.target.value)}
                        placeholder="Type your answer here..."
                        rows="3"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    )}
                  </div>
                );
              })}
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSubmitQuiz}
                disabled={quizSubmitting}
                className="flex-1 bg-purple-500 hover:bg-purple-600 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {quizSubmitting ? 'Submitting...' : 'Submit Quiz'}
              </button>
              <button
                onClick={closeQuizModal}
                disabled={quizSubmitting}
                className="px-6 py-3 bg-gray-300 hover:bg-gray-400 text-gray-700 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-6 rounded-lg text-center">
              <p className="text-sm text-gray-600 mb-2">Your Score</p>
              <p className="text-5xl font-bold text-purple-600 mb-2">
                {quizResults.score}%
              </p>
              <p className="text-gray-700">{quizResults.overallFeedback}</p>
            </div>

            {quizResults.questionFeedback && quizResults.questionFeedback.length > 0 && (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                <h4 className="font-bold text-gray-800">Question Feedback:</h4>
                {quizResults.questionFeedback.map((feedback, index) => (
                  <div key={index} className={`p-4 rounded-lg border-2 ${
                    feedback.isCorrect 
                      ? 'bg-green-50 border-green-300' 
                      : 'bg-red-50 border-red-300'
                  }`}>
                    <div className="flex justify-between items-start mb-2">
                      <p className="font-medium text-gray-800 flex-1">Q{index + 1}: {feedback.question}</p>
                      <span className={`ml-2 px-3 py-1 rounded-full text-sm font-bold flex items-center gap-1 ${
                        feedback.isCorrect 
                          ? 'bg-green-200 text-green-800' 
                          : 'bg-red-200 text-red-800'
                      }`}>
                        {feedback.isCorrect ? (
                          <><Check size={16} /> Correct</>
                        ) : (
                          <><X size={16} /> Incorrect</>
                        )}
                      </span>
                    </div>
                    <div className="space-y-1 text-sm">
                      <p className={`${
                        feedback.isCorrect ? 'text-green-700' : 'text-red-700'
                      }`}>
                        <span className="font-medium">Your answer:</span> {feedback.answer || 'No answer provided'}
                      </p>
                      {!feedback.isCorrect && feedback.correctAnswer && (
                        <p className="text-green-700">
                          <span className="font-medium">Correct answer:</span> {feedback.correctAnswer}
                        </p>
                      )}
                      <p className="text-gray-700 mt-2">
                        <span className="font-medium">Points earned:</span> {feedback.points}/{Math.floor(100 / quizResults.questionFeedback.length)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={closeQuizModal}
              className="w-full bg-purple-500 hover:bg-purple-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </Modal>

      {/* Training Modal */}
      <Modal
        isOpen={trainingModalOpen}
        onClose={closeTrainingModal}
        title={trainingComplete ? 'Training Complete!' : `Question ${currentTrainingIndex + 1} of ${trainingQuestions.length}`}
      >
        {trainingLoading && trainingQuestions.length === 0 ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Generating training questions...</p>
          </div>
        ) : trainingComplete ? (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-green-50 to-blue-50 p-6 rounded-lg text-center">
              <div className="flex justify-center mb-4">
                <div className="bg-green-100 p-4 rounded-full">
                  <Award className="text-green-600" size={48} />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-2">Great Work!</h3>
              <p className="text-gray-600">You've completed all {trainingQuestions.length} questions in this training session.</p>
            </div>

            <div className="space-y-4 max-h-96 overflow-y-auto">
              <h4 className="font-bold text-gray-800">Your Performance Summary:</h4>
              {trainingFeedback.map((item, index) => (
                <div key={index} className="bg-white p-4 rounded-lg border-2 border-gray-200">
                  <div className="mb-3">
                    <p className="font-bold text-gray-800 mb-2">Q{index + 1}: {item.question}</p>
                    <p className="text-sm text-gray-600 mb-2"><span className="font-medium">Your Answer:</span> {item.answer}</p>
                  </div>
                  <div className="bg-blue-50 p-3 rounded">
                    <p className="text-sm text-gray-700 whitespace-pre-line">{item.feedback}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  closeTrainingModal();
                  setTrainingType(null);
                }}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                Back to Categories
              </button>
              <button
                onClick={() => {
                  setCurrentTrainingIndex(0);
                  setTrainingFeedback([]);
                  setTrainingComplete(false);
                  setTrainingAnswer('');
                }}
                className="flex-1 bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                Practice Again
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-600">Progress</span>
                <span className="text-sm font-bold text-blue-600">{currentTrainingIndex + 1} / {trainingQuestions.length}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${((currentTrainingIndex + 1) / trainingQuestions.length) * 100}%` }}
                ></div>
              </div>
            </div>

            {trainingQuestions[currentTrainingIndex] && (
              <div className="bg-white p-6 rounded-lg border-2 border-blue-200">
                <h4 className="font-bold text-lg text-gray-800 mb-4">
                  {trainingQuestions[currentTrainingIndex]}
                </h4>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Answer:
              </label>
              <textarea
                value={trainingAnswer}
                onChange={(e) => setTrainingAnswer(e.target.value)}
                placeholder="Type your answer here... Be detailed and explain your thought process."
                rows="6"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={trainingLoading}
              />
            </div>

            {trainingFeedback[currentTrainingIndex - 1] && (
              <div className="bg-green-50 p-4 rounded-lg border-2 border-green-200">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="text-green-600" size={20} />
                  <h5 className="font-bold text-green-800">Previous Feedback:</h5>
                </div>
                <p className="text-sm text-gray-700 whitespace-pre-line">{trainingFeedback[currentTrainingIndex - 1].feedback}</p>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={submitTrainingAnswer}
                disabled={trainingLoading || !trainingAnswer.trim()}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {trainingLoading ? 'Getting Feedback...' : (currentTrainingIndex < trainingQuestions.length - 1 ? 'Submit & Next' : 'Submit & Finish')}
              </button>
              <button
                onClick={closeTrainingModal}
                disabled={trainingLoading}
                className="px-6 py-3 bg-gray-300 hover:bg-gray-400 text-gray-700 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                Exit
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Interview Modal */}
      <Modal
        isOpen={interviewModalOpen}
        onClose={closeInterviewModal}
        title={interviewResults ? 'Interview Results' : `Question ${currentQuestionIndex + 1} of ${interviewQuestions.length}`}
      >
        {!interviewResults ? (
          <div className="space-y-6">
            {/* Timer */}
            <div className="bg-gray-100 p-4 rounded-lg text-center">
              <p className="text-sm font-medium text-gray-600 mb-1">Time Remaining</p>
              <p className={`text-3xl font-bold ${timeRemaining < 60 ? 'text-red-600' : 'text-blue-600'}`}>
                {formatTime(timeRemaining)}
              </p>
            </div>

            {/* Question */}
            {interviewQuestions[currentQuestionIndex] && (
              <div className="bg-blue-50 p-6 rounded-lg">
                <h4 className="font-bold text-lg text-gray-800 mb-3">
                  {interviewQuestions[currentQuestionIndex]}
                </h4>
              </div>
            )}

            {/* Answer Input */}
            {interviewMode === 'text' ? (
              <textarea
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                placeholder="Type your answer here..."
                rows="6"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            ) : (
              <div className="text-center space-y-4">
                <div className="bg-blue-50 p-4 rounded-lg mb-4">
                  <p className="text-sm text-gray-600 mb-2">🎧 Listen to the question, then click the microphone to record your answer</p>
                  <p className="text-xs text-gray-500">The AI will respond to your answer and ask the next question</p>
                </div>
                <button
                  onClick={toggleRecording}
                  className={`px-8 py-4 rounded-full font-bold text-white transition-colors ${
                    isRecording ? 'bg-red-500 hover:bg-red-600 animate-pulse' : 'bg-green-500 hover:bg-green-600'
                  }`}
                >
                  {isRecording ? '⏸ Stop Recording' : '🎤 Start Recording'}
                </button>
                {currentAnswer && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Your Answer:</p>
                    <p className="text-gray-800">{currentAnswer}</p>
                  </div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex space-x-3">
              <button
                onClick={submitAnswer}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                {currentQuestionIndex < interviewQuestions.length - 1 ? 'Next Question' : 'Finish Interview'}
              </button>
              <button
                onClick={skipQuestion}
                className="px-6 py-3 bg-gray-300 hover:bg-gray-400 text-gray-700 rounded-lg font-medium transition-colors"
              >
                Skip
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-green-50 p-6 rounded-lg text-center">
              <p className="text-2xl font-bold text-green-600 mb-2">
                Score: {interviewResults.score || 'N/A'}%
              </p>
              <p className="text-gray-700">{interviewResults.feedback || 'Interview completed successfully!'}</p>
            </div>

            {interviewResults.details && (
              <div className="space-y-3">
                <h4 className="font-bold text-gray-800">Detailed Feedback:</h4>
                {interviewResults.details.map((detail, index) => (
                  <div key={index} className="bg-gray-50 p-4 rounded-lg">
                    <p className="font-medium text-gray-800">{detail.question}</p>
                    <p className="text-sm text-gray-600 mt-2">{detail.feedback}</p>
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={closeInterviewModal}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </Modal>

      {/* Coding Interface Modal */}
      {codingInterfaceOpen && (
        <CodingInterface 
          onClose={() => setCodingInterfaceOpen(false)} 
          language={codingLanguage}
        />
      )}
    </div>
  );
};

export default StudentPage;
