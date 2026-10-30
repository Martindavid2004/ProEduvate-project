import React, { useState, useEffect, useRef } from 'react';
import Sidebar from '../components/Sidebar';
import Chatbot from '../components/Chatbot';
import Modal from '../components/Modal';
import CodingInterface from '../components/CodingInterface';
import AptitudeTraining from '../components/AptitudeTraining';
import GDRound from '../components/GDRound';
import SkillCardDashboard from '../components/SkillCardDashboard';
import { useData } from '../context/DataContext';
import { studentAPI, interviewAPI, chatbotAPI, gdAPI, assessmentAPI, API_URL } from '../services/api';
import { FileText, Briefcase, Upload, MessageSquare, Trophy, User, Code, Database, Globe, BarChart3, Network, Cloud, MessageCircle, Users, Users2, Brain, Clock, Target, CheckCircle, Award, ArrowLeft, ClipboardList, Mic, Check, X, Menu, Settings, Lock, AlertCircle, UserCircle, Bell, Info, Save, Edit2 } from 'lucide-react';

const StudentPage = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { users, fetchAllData } = useData();
  
  // Get logged-in user data from localStorage
  const loggedInUser = JSON.parse(localStorage.getItem('user') || '{}');
  
  // Student data - prioritize logged-in user data
  const currentStudent = loggedInUser.id 
    ? loggedInUser 
    : users.find(u => u.role === 'student') || { id: 1, name: 'Demo Student' };
  
  const [studentAssignments, setStudentAssignments] = useState([]);
  const [progress, setProgress] = useState(null);
  
  // Resume analysis
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeAnalyzing, setResumeAnalyzing] = useState(false);
  const [resumeResults, setResumeResults] = useState(null);
  
  // Interview
  const [interviewModalOpen, setInterviewModalOpen] = useState(false);
  // RESUME GATEKEEPER: AI Interview cannot start until a resume is on file.
  // The backend uses resume text to generate targeted questions, so this is
  // enforced before startInterview() is ever called.
  // interviewResumeReady is a REAL 3-state flag: null = still checking the
  // database, true = resume uploaded, false = no resume. The UI must never
  // render a "Resume on file" banner while the state is unknown.
  const [interviewResumeGate, setInterviewResumeGate] = useState(false);
  const [interviewResumeUploading, setInterviewResumeUploading] = useState(false);
  const [interviewResumeReady, setInterviewResumeReady] = useState(null); // null=unknown, true/false
  const [interviewCheckingResume, setInterviewCheckingResume] = useState(true);
  // Interview type the student clicked (text/voice) while being held at the
  // mandatory upload step - used to auto-start right after a successful upload.
  const [pendingInterviewMode, setPendingInterviewMode] = useState(null);
  const interviewResumeInputRef = useRef(null);
  const [interviewMode, setInterviewMode] = useState(null);
  const [interviewStarting, setInterviewStarting] = useState(false);
  const [interviewEvaluating, setInterviewEvaluating] = useState(false);
  const [interviewQuestions, setInterviewQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState([]);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [interviewDuration, setInterviewDuration] = useState(20);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [timerActive, setTimerActive] = useState(false);
  const [interviewResults, setInterviewResults] = useState(null);
  const [interviewSessionId, setInterviewSessionId] = useState(null);
  const [interviewResuming, setInterviewResuming] = useState(false);
  const interviewFinalizedRef = useRef(false);
  
  // Quiz (server-controlled MCQ assessment)
  const [quizModalOpen, setQuizModalOpen] = useState(false);
  const [currentQuiz, setCurrentQuiz] = useState(null);
  // Per-attempt question paper: the backend serves each attempt (and every
  // retake) its own randomized snapshot (dynamic question pooling), so the
  // modal renders THIS list, not the assignment's static stored bank.
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [quizResults, setQuizResults] = useState(null);
  const [quizAttempt, setQuizAttempt] = useState(null); // server-side attempt (expiry authority)
  const [quizTimeRemaining, setQuizTimeRemaining] = useState(0); // display only
  const [quizLockMessage, setQuizLockMessage] = useState(null);
  // Retake flow: true while a retake start request is in flight.
  const [quizRetaking, setQuizRetaking] = useState(false);
  const quizTimerRef = useRef(null);
  const quizFinalizedRef = useRef(false); // guards duplicate fail/submit calls
  // Refs mirror the latest state so event listeners (visibilitychange) and
  // interval ticks never read a stale closure (BUG 3: the old listener
  // captured outdated currentQuiz/quizAttempt and could no-op or double-fire).
  const quizAttemptRef = useRef(null);
  const quizLockMessageRef = useRef(null);
  // currentQuizRef mirrors currentQuiz so finalizeQuizFailure (called from
  // event listeners registered once) always reads the latest assignment
  // instead of a stale React state value captured at registration time.
  const currentQuizRef = useRef(null);
  
  // Placement Training
  const [trainingType, setTrainingType] = useState(null); // 'technical' or 'non-technical'
  const [trainingModalOpen, setTrainingModalOpen] = useState(false);
  const [trainingQuestions, setTrainingQuestions] = useState([]);
  const [currentTrainingIndex, setCurrentTrainingIndex] = useState(0);
  const [trainingAnswer, setTrainingAnswer] = useState('');
  const [trainingFeedback, setTrainingFeedback] = useState([]);
  const [trainingLoading, setTrainingLoading] = useState(false);
  const [trainingComplete, setTrainingComplete] = useState(false);
  const [showAptitudeTraining, setShowAptitudeTraining] = useState(false);
  
  // GD Round (Group Discussion)
  const [gdRoundOpen, setGdRoundOpen] = useState(false);
  const [gdRoundLoading, setGdRoundLoading] = useState(false);
  const [currentGDRound, setCurrentGDRound] = useState(null);
  const [submittingAssignments, setSubmittingAssignments] = useState({});
  // eslint-disable-next-line no-unused-vars
  const [gdNotifications, setGdNotifications] = useState([]);
  // eslint-disable-next-line no-unused-vars
  const [gdResults, setGdResults] = useState([]);
  
  // Coding Practice
  const [codingInterfaceOpen, setCodingInterfaceOpen] = useState(false);
  // eslint-disable-next-line no-unused-vars
  const [codingLanguage, setCodingLanguage] = useState('python');
  const [showProgrammingLanguages, setShowProgrammingLanguages] = useState(false); // 'python' or 'c';
  
  // Settings
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordChangeLoading, setPasswordChangeLoading] = useState(false);
  const [passwordChangeMessage, setPasswordChangeMessage] = useState('');
  const [passwordChangeError, setPasswordChangeError] = useState('');
  
  // Profile Edit Settings
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileName, setProfileName] = useState(currentStudent.name || '');
  const [profileDepartment, setProfileDepartment] = useState(currentStudent.department || '');
  const [profileEmail, setProfileEmail] = useState(currentStudent.email || '');
  const [profileUpdateLoading, setProfileUpdateLoading] = useState(false);
  const [profileUpdateMessage, setProfileUpdateMessage] = useState('');
  const [profileUpdateError, setProfileUpdateError] = useState('');
  
  // Notification Settings
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [assignmentNotifications, setAssignmentNotifications] = useState(true);
  const [interviewNotifications, setInterviewNotifications] = useState(true);
  const [notificationLoading, setNotificationLoading] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');
  const [notificationModalOpen, setNotificationModalOpen] = useState(false);
  
  // Active settings section
  const [activeSettingsSection, setActiveSettingsSection] = useState('password');
  
  // Speech recognition and synthesis
  const recognitionRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  // Voice-mode interview capture: MediaRecorder -> shared /gd/transcribe
  // endpoint (faster-whisper singleton in stt_service.py). No second Whisper
  // implementation is created - the GD endpoint and its model are REUSED.
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const interviewStreamRef = useRef(null);
  const voiceTranscriptRef = useRef(null);        // Whisper transcript for the current turn
  const voiceTranscribePromiseRef = useRef(null); // in-flight transcription request
  // STT quality of the current turn's transcript (VALID / LOW_CONFIDENCE /
  // NO_SPEECH / INVALID) captured from /gd/transcribe. Empty/low-confidence
  // turns must never be saved or evaluated as meaningful answers.
  const voiceTranscriptStatusRef = useRef(null);
  // Sync mirror of the recording state: browser SpeechRecognition errors and
  // React's async setState can desync `isRecording`, and a stale value here
  // previously let a second MediaRecorder be created on the same stream (an
  // orphaned recorder -> corrupt/undecodable audio -> backend 422
  // "Audio could not be decoded"). The ref is the authoritative guard.
  const isRecordingRef = useRef(false);

  useEffect(() => {
    fetchAllData();
    loadStudentData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // AI Interview resume-status check (runs ONCE on mount, independent of the
  // dashboard data load): reads the REAL database state (resumeUploaded from
  // the progress endpoint) before the Interview tab is allowed to claim
  // anything. Until this resolves the tab shows a neutral "checking" card -
  // never a fabricated "Resume on file" banner.
  useEffect(() => {
    let cancelled = false;
    const checkResumeStatus = async () => {
      try {
        const res = await studentAPI.getProgress(currentStudent.id);
        if (!cancelled) {
          setInterviewResumeReady(res.data?.resumeUploaded === true);
        }
      } catch (error) {
        console.error('Error checking resume status:', error);
        // Unknown state: stay null so the UI keeps showing "checking";
        // starting an interview will hit the backend RESUME_REQUIRED gate.
      } finally {
        if (!cancelled) setInterviewCheckingResume(false);
      }
    };
    checkResumeStatus();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timerActive, timeRemaining]);

  const loadStudentData = async () => {
    try {
      const [assignmentsRes, progressRes] = await Promise.all([
        studentAPI.getAssignments(currentStudent.id),
        studentAPI.getProgress(currentStudent.id),
      ]);
      setStudentAssignments(assignmentsRes.data);
      setProgress(progressRes.data);
      // Resume gatekeeper state: reflect whether a resume is already on file
      // (backend stores resume_text/resume_filename on upload).
      setInterviewResumeReady(progressRes.data?.resumeUploaded === true);
      // The dashboard always renders what the backend just returned: the
      // progress endpoint reads the user document fresh from Mongo, so a
      // refresh / re-login shows the latest persisted interview result.
      console.log('[DASHBOARD] Interview result fetched:',
        progressRes.data?.interviewScore != null
          ? `score=${progressRes.data.interviewScore} status=${progressRes.data.interviewStatus}`
          : 'no result yet');
    } catch (error) {
      console.error('Error loading student data:', error);
    }
  };

  const getStudentNotifications = () => {
    const list = [];
    
    // Assignment notifications
    (studentAssignments || []).forEach(asm => {
      if (!asm.submitted) {
        list.push({
          id: `asm-${asm.id}`,
          type: 'assignment',
          title: `New ${asm.type || 'Assignment'} Assigned`,
          message: `${asm.title}: ${asm.description}`,
          time: asm.dueDate ? `Due: ${asm.dueDate}` : 'Pending'
        });
      }
    });

    // HR Activity & Profile notifications
    if (progress?.resumeScore) {
      list.push({
        id: 'hr-ats-score',
        type: 'hr',
        title: 'HR Profile Activity: ATS Resume Analysis',
        message: `Your resume matched with a score of ${progress.resumeScore}%. Profile updated for HR recruiters.`,
        time: 'Recently'
      });
    }

    // != null (not truthiness): a 0 score is still a recorded result.
    if (progress?.interviewScore != null) {
      list.push({
        id: 'hr-interview-score',
        type: 'hr',
        title: 'HR Activity: AI Interview Evaluation',
        message: `Your AI interview score of ${progress.interviewScore}% has been recorded on your HR candidate profile.`,
        time: 'Recently'
      });
    }

    list.push({
      id: 'hr-view-status',
      type: 'hr',
      title: 'HR Activity: Candidate Profile Status',
      message: 'Your student profile is active and visible to HR recruiters for placement opportunities.',
      time: 'Today'
    });

    return list;
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

    setSubmittingAssignments(prev => ({ ...prev, [assignmentId]: true }));

    try {
      await studentAPI.submitAssignment(currentStudent.id, assignmentId, formData);
      alert('Assignment submitted successfully!');
      fileInput.value = '';
      await loadStudentData();
    } catch (error) {
      console.error('Error submitting assignment:', error);
      alert('Failed to submit assignment.');
    } finally {
      setSubmittingAssignments(prev => ({ ...prev, [assignmentId]: false }));
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

  const handleStartQuiz = async (assignment, retake = false) => {
    setCurrentQuiz(assignment);
    // Ref keeps pace with state so closures registered once (visibilitychange,
    // timer ticks) always read the live assignment without re-registering.
    currentQuizRef.current = assignment;
    setQuizAnswers({});
    setQuizResults(null);
    setQuizLockMessage(null);
    quizLockMessageRef.current = null;
    setQuizModalOpen(true);
    setQuizAttempt(null);
    quizAttemptRef.current = null;
    setQuizTimeRemaining(0);
    quizFinalizedRef.current = false;
    // DYNAMIC POOLING: reset to the assignment bank as the initial fallback;
    // the authoritative per-attempt paper replaces it once start returns.
    setQuizQuestions(assignment.quiz_questions || []);
    // Retake flow: archive the finished attempt server-side and start fresh.
    setQuizRetaking(retake);

    // Ask the backend to start (or resume) the attempt. The expiry time is
    // generated server-side, so refreshing can never reset the timer.
    try {
      let response;
      try {
        if (retake) {
          // Explicit retake: archive finished attempt + create a new one.
          response = await assessmentAPI.startTeacherQuiz(assignment.id, currentStudent.id, true);
        } else {
          // Resume-safe: reuse an existing attempt when there is one.
          response = await assessmentAPI.teacherQuizStatus(assignment.id, currentStudent.id);
          if (!response.data?.attempt) {
            // Never started: create the attempt (server timestamps).
            response = await assessmentAPI.startTeacherQuiz(assignment.id, currentStudent.id);
          }
        }
      } catch (statusErr) {
        // Status lookup failed (network blip etc.) - fall back to start/resume.
        response = await assessmentAPI.startTeacherQuiz(assignment.id, currentStudent.id, retake);
      }
      const data = response.data || {};
      const attempt = data.attempt;
      setQuizAttempt(attempt);
      quizAttemptRef.current = attempt;

      // The backend serves this attempt's own randomized paper - always the
      // authority for what is rendered (a retake gets a fresh selection).
      if (Array.isArray(data.questions) && data.questions.length > 0) {
        setQuizQuestions(data.questions);
      } else if (attempt && attempt.status !== 'IN_PROGRESS') {
        // No active paper (attempt finished): the lock screen shows instead.
        setQuizQuestions([]);
      }

      if (attempt && attempt.status !== 'IN_PROGRESS') {
        // Finished attempt WITHOUT an explicit retake: no longer a dead end -
        // surface the last result AND a Retake Assessment button.
        const msg = buildQuizLockMessage(attempt);
        setQuizLockMessage(msg);
        quizLockMessageRef.current = msg;
        return;
      }
      setQuizRetaking(false);
      setQuizTimeRemaining(attempt?.remainingSeconds || 0);
    } catch (error) {
      console.error('Error starting quiz assessment:', error);
      alert('Failed to start the quiz assessment.');
      setQuizModalOpen(false);
    }
  };

  // Retake from the lock/result state: archive the old attempt and start a
  // clean one (server re-validates; finished attempts are archived, history
  // and scores are preserved).
  const handleRetakeQuiz = () => {
    if (!currentQuiz) return;
    setQuizLockMessage(null);
    quizLockMessageRef.current = null;
    setQuizResults(null);
    setQuizAnswers({});
    quizFinalizedRef.current = false;
    setQuizQuestions([]); // fresh randomized paper arrives from the backend
    handleStartQuiz(currentQuiz, true);
  };

  // Detailed answer review for an already-submitted quiz (from the stored
  // evaluation returned by the assignments endpoint).
  const handleViewQuizResult = (assignment) => {
    const evaluation = assignment.quiz_evaluation || {};
    setCurrentQuiz(assignment);
    currentQuizRef.current = assignment;
    setQuizAnswers({});
    setQuizLockMessage(null);
    quizLockMessageRef.current = null;
    setQuizAttempt(null);
    quizAttemptRef.current = null;
    setQuizTimeRemaining(0);
    quizFinalizedRef.current = false;      setQuizResults({
        score: Math.round(evaluation.score ?? assignment.quiz_score ?? 0),
        passed: evaluation.passed ?? assignment.quiz_passed,
        questionFeedback: (evaluation.results || []).map(r => ({
          question: r.question,
          answer: r.user_answer || 'No answer provided',
          correctAnswer: r.correct_answer,
          category: r.category,
          isCorrect: r.status === 'correct',
          status: r.status,
        })),
        overallFeedback: evaluation.performance?.message ||
          `You scored ${Math.round(evaluation.score ?? assignment.quiz_score ?? 0)}%.`,
      });
    setQuizModalOpen(true);
  };

  const buildQuizLockMessage = (attempt) => {
    if (!attempt) return 'This assessment is no longer available.';
    if (attempt.failureReason === 'TAB_SWITCH') {
      return 'Assessment failed because you switched to another browser tab or window.';
    }
    if (attempt.failureReason === 'TIME_EXPIRED') {
      return 'Assessment Failed - Time Expired.';
    }
    if (attempt.status === 'PASS' || attempt.status === 'COMPLETED') {
      return `Assessment already submitted. Score: ${attempt.score ?? 'N/A'}%`;
    }
    if (attempt.status === 'FAIL') {
      return `Assessment already submitted. You scored ${attempt.score ?? 'N/A'}% - below the pass mark.`;
    }
    return 'This assessment is already finished.';
  };

  // Server-authoritative finalization for tab switches and timer expiry.
  // Reads the latest quiz/attempt from refs so it is safe to call from event
  // listeners registered once (visibilitychange) or from interval ticks.
  // Uses currentQuizRef.current (not the React state currentQuiz) because
  // this function is called from event handlers that close over a stale
  // render's state — the ref always reflects the latest assignment.
  const finalizeQuizFailure = async (reason) => {
    if (quizFinalizedRef.current || !currentQuizRef.current || !quizAttemptRef.current) return;
    quizFinalizedRef.current = true;
    if (quizTimerRef.current) clearInterval(quizTimerRef.current);
    try {
      const response = await assessmentAPI.failTeacherQuiz(currentQuizRef.current.id, currentStudent.id, reason);
      const attempt = response.data?.attempt || quizAttemptRef.current;
      quizAttemptRef.current = attempt;
      setQuizAttempt(attempt);
      const msg = buildQuizLockMessage(attempt);
      quizLockMessageRef.current = msg;
      setQuizLockMessage(msg);
    } catch (error) {
      console.error('Error recording assessment failure:', error);
      const msg = buildQuizLockMessage({ status: 'FAILED', failureReason: reason });
      quizLockMessageRef.current = msg;
      setQuizLockMessage(msg);
    }
  };

  // Tab/window switch detection: any switch while the assessment is active
  // immediately fails it via the backend (server stores the failure).
  // NOTE: this is the browser-supported mechanism - visibilitychange fires
  // when the TAB or BROWSER WINDOW is hidden (other tab, other app window,
  // minimize on most desktop browsers). OS-level events the browser does not
  // expose cannot be detected, which is a platform limitation.
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden' && quizModalOpen
          && quizAttemptRef.current?.status === 'IN_PROGRESS'
          && !quizFinalizedRef.current) {
        finalizeQuizFailure('TAB_SWITCH');
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quizModalOpen]);

  // Display-only countdown. The SERVER expiry remains the authority: the
  // countdown is anchored to the attempt's remainingSeconds (computed by the
  // backend at load time), ticks down locally for display, and self-corrects
  // when the tab is throttled (browsers pause timers in background tabs) or
  // the wall clock changes. The backend re-validates expiry on every
  // status/fail/submit call, so this display can never extend the attempt.
  useEffect(() => {
    if (!quizModalOpen) return;
    const attempt = quizAttemptRef.current;
    if (!attempt || attempt.status !== 'IN_PROGRESS') return;

    // Anchor once from the server's remainingSeconds; never re-derive from
    // Date.now() against expiresAt (browser clock skew) and never reset when
    // this effect re-runs mid-attempt.
    const anchored = Math.max(0, Math.floor(attempt.remainingSeconds ?? 0));
    if (anchored <= 0) {
      setQuizTimeRemaining(0);
      finalizeQuizFailure('TIME_EXPIRED');
      return;
    }

    const anchorEpochMs = Date.now();
    const tick = () => {
      // Elapsed is measured locally so wall-clock changes can't stretch it;
      // throttled background tabs self-correct on the next visible tick.
      const elapsed = Math.floor((Date.now() - anchorEpochMs) / 1000);
      const remaining = Math.max(0, anchored - elapsed);
      setQuizTimeRemaining(remaining);
      if (remaining <= 0) {
        finalizeQuizFailure('TIME_EXPIRED');
      }
    };

    setQuizTimeRemaining(anchored);
    quizTimerRef.current = setInterval(tick, 1000);
    return () => clearInterval(quizTimerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quizModalOpen, quizAttempt]);

  const handleQuizAnswerChange = (questionIndex, answer) => {
    setQuizAnswers(prev => ({
      ...prev,
      [questionIndex]: answer
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!currentQuiz || !quizAttemptRef.current) return;
    if (quizAttemptRef.current.status !== 'IN_PROGRESS') return;
    if (quizFinalizedRef.current) return;

    // Check if all questions are answered (against the attempt's own paper)
    const totalQuestions = quizQuestions.length;
    const answeredQuestions = Object.keys(quizAnswers).length;
    
    if (answeredQuestions < totalQuestions) {
      const proceed = window.confirm(`You have answered ${answeredQuestions} out of ${totalQuestions} questions. Do you want to submit anyway?`);
      if (!proceed) return;
    }

    setQuizSubmitting(true);
    
    try {
      quizFinalizedRef.current = true;
      if (quizTimerRef.current) clearInterval(quizTimerRef.current);

      // Backend validates: active attempt, not already submitted, before expiry.
      // It computes the score, decides PASS/FAIL (70% pass mark) and stores
      // ONE authoritative result record.
      const response = await assessmentAPI.submitTeacherQuiz(currentQuiz.id, {
        student_id: currentStudent.id,
        answers: quizAnswers,
      });

      const result = response.data?.result || {};
      const evaluation = result.evaluation || {};

      quizAttemptRef.current = result;
      setQuizAttempt(result);
      setQuizResults({
        score: Math.round(evaluation.score ?? result.score ?? 0),
        passed: evaluation.passed ?? result.passed,
        questionFeedback: (evaluation.results || []).map(r => ({
          question: r.question,
          answer: r.user_answer || 'No answer provided',
          correctAnswer: r.correct_answer,
          category: r.category,
          isCorrect: r.status === 'correct',
          status: r.status,
        })),
        overallFeedback: evaluation.performance?.message || `You scored ${Math.round(evaluation.score ?? 0)}%.`,
      });
      await loadStudentData();
    } catch (error) {
      const data = error.response?.data || {};
      if (error.response?.status === 409) {
        // Backend rejected the submission: expired, failed (tab switch) or
        // already submitted. The attempt is terminal - show the locked state
        // and never allow a retry (BUG 8: a submission that arrives after the
        // server deadline is stored as FAILED/TIME_EXPIRED by the backend).
        if (data.attempt) {
          quizAttemptRef.current = data.attempt;
          setQuizAttempt(data.attempt);
        }
        const expired = data.failureReason === 'TIME_EXPIRED'
          || data.attempt?.failureReason === 'TIME_EXPIRED';
        const msg = expired
          ? 'Assessment Failed - Time Expired.'
          : (data.error || data.failureReason === 'TAB_SWITCH'
            ? 'Assessment failed because you switched to another browser tab or window.'
            : (data.error || 'This assessment has already been submitted.'));
        quizLockMessageRef.current = msg;
        setQuizLockMessage(msg);
      } else {
        console.error('Error submitting quiz:', error);
        // Transient error (network/server): allow retry ONLY if the backend
        // could not have finalized the attempt.
        quizFinalizedRef.current = false;
        alert('Failed to submit quiz. Please try again.');
      }
    } finally {
      setQuizSubmitting(false);
    }
  };

  const handlePasswordChange = async () => {
    // Reset messages
    setPasswordChangeMessage('');
    setPasswordChangeError('');

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordChangeError('All fields are required');
      return;
    }

    if (newPassword.length < 6) {
      setPasswordChangeError('New password must be at least 6 characters long');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordChangeError('New passwords do not match');
      return;
    }

    if (currentPassword === newPassword) {
      setPasswordChangeError('New password must be different from current password');
      return;
    }

    setPasswordChangeLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/student/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          student_id: currentStudent.id,
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      const data = await response.json();

      if (response.ok) {
        setPasswordChangeMessage('Password changed successfully!');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      } else {
        setPasswordChangeError(data.message || 'Failed to change password');
      }
    } catch (error) {
      console.error('Error changing password:', error);
      setPasswordChangeError('Failed to change password. Please try again.');
    } finally {
      setPasswordChangeLoading(false);
    }
  };

  const handleProfileUpdate = async () => {
    setProfileUpdateMessage('');
    setProfileUpdateError('');

    if (!profileName || !profileEmail || !profileDepartment) {
      setProfileUpdateError('All fields are required');
      return;
    }

    if (!/\S+@\S+\.\S+/.test(profileEmail)) {
      setProfileUpdateError('Please enter a valid email address');
      return;
    }

    setProfileUpdateLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/student/update-profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          student_id: currentStudent.id,
          name: profileName,
          email: profileEmail,
          department: profileDepartment
        })
      });

      const data = await response.json();

      if (response.ok) {
        setProfileUpdateMessage('Profile updated successfully!');
        setEditingProfile(false);
        
        // Update localStorage
        const updatedUser = {
          ...currentStudent,
          name: profileName,
          email: profileEmail,
          department: profileDepartment
        };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      } else {
        setProfileUpdateError(data.message || 'Failed to update profile');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      setProfileUpdateError('Failed to update profile. Please try again.');
    } finally {
      setProfileUpdateLoading(false);
    }
  };

  const handleNotificationUpdate = async () => {
    setNotificationMessage('');
    setNotificationLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/student/update-notifications`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          student_id: currentStudent.id,
          email_notifications: emailNotifications,
          assignment_notifications: assignmentNotifications,
          interview_notifications: interviewNotifications
        })
      });

      // eslint-disable-next-line no-unused-vars
      const data = await response.json();

      if (response.ok) {
        setNotificationMessage('Notification preferences saved successfully!');
        setTimeout(() => setNotificationMessage(''), 3000);
      } else {
        setNotificationMessage('Failed to save preferences');
      }
    } catch (error) {
      console.error('Error updating notifications:', error);
      setNotificationMessage('Failed to save preferences');
    } finally {
      setNotificationLoading(false);
    }
  };

  const closeQuizModal = () => {
    if (quizTimerRef.current) clearInterval(quizTimerRef.current);
    setQuizModalOpen(false);
    setCurrentQuiz(null);
    currentQuizRef.current = null;
    setQuizQuestions([]);
    setQuizAnswers({});
    setQuizResults(null);
    setQuizAttempt(null);
    quizAttemptRef.current = null;
    setQuizLockMessage(null);
    quizLockMessageRef.current = null;
    quizFinalizedRef.current = false;
  };

  const programmingLanguages = [
    { id: 'python', name: 'Python Programming', icon: Code, description: 'Practice Python coding problems and algorithms' },
  ];

  const technicalCategories = [
    { 
      id: 'programming', 
      name: 'Programming and Coding', 
      icon: Code, 
      description: 'Practice coding problems in Python or C'
    },
    { id: 'databases', name: 'Database & SQL', icon: Database, description: 'Master database concepts and queries' },
    { id: 'webdev', name: 'Web Development', icon: Globe, description: 'Learn frontend and backend technologies' },
    { id: 'dsa', name: 'Data Structures & Algorithms', icon: BarChart3, description: 'Strengthen problem-solving skills' },
    { id: 'system-design', name: 'System Design', icon: Network, description: 'Learn to design scalable systems' },
    { id: 'devops', name: 'DevOps & Cloud', icon: Cloud, description: 'Master deployment and cloud platforms' },
  ];

  const nonTechnicalCategories = [
    { id: 'communication', name: 'Communication Skills', icon: MessageCircle, description: 'Improve verbal and written communication' },
    { id: 'gd-round', name: 'AI Group Discussion', icon: Users, description: 'Practice GD with AI agents' },
    { id: 'leadership', name: 'Leadership & Management', icon: Users2, description: 'Develop leadership qualities' },
    { id: 'teamwork', name: 'Teamwork & Collaboration', icon: Users2, description: 'Learn to work effectively in teams' },
    { id: 'problem-solving', name: 'Problem Solving', icon: Brain, description: 'Enhance analytical thinking' },
    { id: 'time-management', name: 'Time Management', icon: Clock, description: 'Learn to manage time efficiently' },
    { id: 'aptitude', name: 'Aptitude & Reasoning', icon: Target, description: 'Practice logical reasoning' },
  ];

  const startTraining = async (category) => {
    // Special handling for Programming & Coding categories
    if (category === 'programming') {
      setShowProgrammingLanguages(true);
      return;
    }

    // Special handling for Aptitude & Reasoning
    if (category === 'aptitude') {
      setShowAptitudeTraining(true);
      return;
    }

    // Special handling for GD Round
    if (category === 'gd-round') {
      startGDRound();
      return;
    }

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

  const selectProgrammingLanguage = () => {
    setCodingInterfaceOpen(true);
    setShowProgrammingLanguages(false);
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
    setTrainingQuestions([]);
    setCurrentTrainingIndex(0);
    setTrainingAnswer('');
    setTrainingFeedback([]);
    setTrainingComplete(false);
  };

  // GD Round Functions
  const startGDRound = async () => {
    setGdRoundLoading(true);
    try {
      const response = await gdAPI.getTopics();
      const data = response.data;
      
      if (data.success) {
        // Schedule a practice round on the backend so it gets a valid Mongo ObjectId
        const scheduleResp = await gdAPI.schedulePracticeRound({
          title: 'Practice GD Round',
          duration: 20,
          allow_topic_selection: true,
          available_topics: data.topics || [],
          num_ai_agents: 7,
          ai_agent_voices: ['male', 'female', 'male', 'female', 'male', 'female', 'male'],
          evaluation_criteria: {
            communication_skills: { weight: 25, description: "Clarity, articulation, and language proficiency" },
            leadership: { weight: 20, description: "Initiative taking and group steering ability" },
            logical_reasoning: { weight: 20, description: "Quality of arguments and critical thinking" },
            content_relevance: { weight: 20, description: "Knowledge and relevance of points made" },
            listening_team_dynamics: { weight: 15, description: "Active listening and team collaboration" }
          }
        });

        if (scheduleResp.data.success) {
          setCurrentGDRound(scheduleResp.data.gd_round);
          setGdRoundOpen(true);
        }
      }
    } catch (error) {
      console.error('Error starting GD round:', error);
      alert(error.response?.data?.error || 'Failed to start GD round. Please try again.');
    } finally {
      setGdRoundLoading(false);
    }
  };

  const handleGDComplete = async (results) => {
    // Save results locally
    setGdResults(prev => [...prev, results]);
    
    // Could also save to backend here
    try {
      // Optional: send results to backend for permanent storage
      console.log('GD Round completed with results:', results);
    } catch (error) {
      console.error('Error saving GD results:', error);
    }
  };

  const closeGDRound = () => {
    setGdRoundOpen(false);
    setCurrentGDRound(null);
  };

  const speakText = (text) => {
    if (synthRef.current && interviewMode === 'voice') {
      // Cancel any ongoing speech so the previous question's TTS never
      // overlaps or repeats when moving to the next question.
      synthRef.current.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 1;

      synthRef.current.speak(utterance);
    }
  };

  // The interviewer speaks ONLY the actual question - no greetings, no
  // introductions, no "Question N" prefixes, no AI feedback boilerplate
  // (removed at the source: what is passed here is exactly what is spoken).
  const speakQuestion = (questionText) => {
    if (!questionText) return;
    console.log('[INTERVIEW] TTS input:', questionText);
    speakText(questionText);
  };  // RESUME GATEKEEPER: mandatory resume upload step before any interview
  // session starts. The file must upload AND parse successfully (the backend
  // extracts the text server-side and fails the request when it cannot) -
  // only then is the interview unlocked. Optional auto-start continues
  // straight into the interview the student clicked.
  const handleInterviewResumeUpload = async (autoStartMode = null) => {
    const fileInput = interviewResumeInputRef.current;
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      alert('Please select your resume file (PDF or DOCX) to continue.');
      return;
    }
    const formData = new FormData();
    formData.append('resume', fileInput.files[0]);
    setInterviewResumeUploading(true);
    try {
      await studentAPI.uploadResume(currentStudent.id, formData);
      setInterviewResumeReady(true);
      setInterviewResumeGate(false);
      // Reset the input so re-uploading a DIFFERENT file later is picked up
      // (a still-attached File object would silently reuse the old file).
      fileInput.value = '';
      const mode = pendingInterviewMode;
      setPendingInterviewMode(null);
      // Refresh dashboard state (resume score etc.) and WAIT for it: the
      // profile cards and the interview gate must reflect the just-uploaded
      // resume before the interview modal opens. Firing without await here
      // raced the interview start and left the dashboard stale.
      await loadStudentData();
      if (autoStartMode || mode) {
        await startInterview(autoStartMode || mode);
      }
    } catch (error) {
      console.error('Error uploading resume for interview:', error);
      // The upload endpoint 500s when the file could not be parsed (e.g. a
      // scanned/image-only PDF). Surface that clearly instead of a generic
      // "upload failed" so the student can pick a text-based resume.
      const detail = error.response?.data?.error;
      alert(detail
        ? `Resume upload failed: ${detail}`
        : 'Resume upload failed. Please try again.');
    } finally {
      setInterviewResumeUploading(false);
    }
  };

  // Entry point for both Start buttons: holds the student at the mandatory
  // "Upload Resume First" modal until a resume is actually on file.
  const openInterviewWithResumeGate = (mode) => {
    if (interviewResumeReady === false) {
      setPendingInterviewMode(mode);
      setInterviewResumeGate(true);
      return;
    }
    startInterview(mode);
  };

  const startInterview = async (mode) => {
    // GATE: no resume on file -> force the upload step first.
    if (interviewResumeReady === false) {
      setInterviewResumeGate(true);
      return;
    }
    setInterviewStarting(true);
    setInterviewMode(mode);
    setInterviewModalOpen(true);
    setInterviewResults(null);
    interviewFinalizedRef.current = false;

    // Refresh-safe: an unfinished session for this student is resumed
    // (questions + answered turns come back from the server) instead of
    // starting a brand-new interview.
    const savedSessionId = localStorage.getItem('activeInterviewSessionId');
    if (savedSessionId) {
      try {
        const sessionRes = await interviewAPI.getSession(savedSessionId);
        const session = sessionRes.data?.session;
        if (session && session.status === 'in_progress') {
          setInterviewSessionId(session.sessionId);
          setInterviewQuestions(session.questions || []);
          setUserAnswers(session.answers || []);
          setCurrentQuestionIndex(session.currentQuestionIndex || 0);
          setInterviewResuming(true);
          setInterviewStarting(false);
          setTimeRemaining(interviewDuration * 60);
          setTimerActive(true);
          return;
        }
        if (session && session.status === 'completed') {
          localStorage.removeItem('activeInterviewSessionId');
        }
      } catch (error) {
        // Session is gone/expired - fall through and start a fresh one.
        localStorage.removeItem('activeInterviewSessionId');
      }
    }

    setCurrentQuestionIndex(0);
    setUserAnswers([]);
    setCurrentAnswer('');
    setInterviewResuming(false);
    
    try {
      // Bounded start request: question generation is synchronous server-side
      // (parse resume -> LLM -> fallback deck). An unbounded axios wait used
      // to leave the popup spinning forever when the backend LLM chain was
      // slow; 75s bounds the wait while the backend's own 90s generation
      // budget + offline fallback deck still resolves first in practice.
      const response = await interviewAPI.startInterview({
        user_id: currentStudent.id,
        mode,
        session_id: null,
      }, { timeout: 75000 });
      const data = response.data || {};
      const questions = data.questions || data.session?.questions || [];
      const sessionId = data.session?.sessionId || null;
      setInterviewQuestions(questions);
      setInterviewSessionId(sessionId);
      if (sessionId) {
        localStorage.setItem('activeInterviewSessionId', sessionId);
      }
      setTimeRemaining(interviewDuration * 60);
      setTimerActive(true);
      
      if (mode === 'voice') {
        // [INTERVIEW] Browser SpeechRecognition is deliberately NOT used for
        // the Mock Interview: it produced 'Speech recognition error: network'
        // and is cloud-dependent. The Whisper pipeline (MediaRecorder ->
        // /gd/transcribe -> faster-whisper) is the sole STT authority here.
        // Speak ONLY the first actual question - no greeting/introduction.
        setTimeout(() => {
          if (questions.length > 0) {
            speakQuestion(questions[0]);
          }
        }, 500);
      }
    } catch (error) {
      console.error('Error starting interview:', error);
      // Server-side RESUME GATEWAY: if the backend rejects the start because
      // no resume is on file (code RESUME_REQUIRED), flip to the mandatory
      // upload step instead of a dead-end alert.
      if (error.response?.status === 400 && error.response?.data?.code === 'RESUME_REQUIRED') {
        setInterviewResumeReady(false);
        setInterviewResumeGate(true);
        setInterviewModalOpen(false);
        setInterviewMode(null);
      } else {
        alert(error.response?.data?.error || 'Failed to start interview.');
        setInterviewModalOpen(false);
      }
    } finally {
      setInterviewStarting(false);
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
      // Browser STT failure must NOT touch the recording state: the
      // MediaRecorder + Whisper pipeline is the authority. Previously this
      // handler called setIsRecording(false) while the recorder kept
      // capturing, desyncing the Start/Stop button and allowing a second
      // recorder to be created (the corrupt-blob source behind the 422).
      console.warn('Speech recognition error:', event.error);
    };
  };

  const transcribeInterviewAudio = async (audioBlob) => {
    // Blob validation: the backend returns HTTP 422 ONLY for audio it cannot
    // decode (stt_service.transcribe -> AudioValidationError). A corrupt/empty
    // blob must never reach the API.
    if (!audioBlob || audioBlob.size === 0) {
      console.warn('[INTERVIEW] transcription aborted - empty audio blob (size 0)');
      return;
    }
    console.log('[INTERVIEW] sending audio to /gd/transcribe');
    console.log('[INTERVIEW] blob type:', audioBlob.type);
    console.log('[INTERVIEW] blob size:', audioBlob.size, 'bytes');
    voiceTranscribePromiseRef.current = (async () => {
      try {
        // REUSES the existing /gd/transcribe endpoint and its shared
        // faster-whisper model singleton (stt_service.py).
        const response = await interviewAPI.transcribeAudio(audioBlob);
        const data = response.data || {};
        console.log('[INTERVIEW] transcription response:', data);
        const text = (data.text || data.transcript || '').trim();
        console.log('[INTERVIEW] transcript:', text || '(empty)');
        // Track the STT quality for this turn (VALID / LOW_CONFIDENCE /
        // NO_SPEECH / INVALID) so empty or low-confidence transcripts are
        // never saved or evaluated as a meaningful answer.
        voiceTranscriptStatusRef.current = text ? (data.status || 'VALID') : (data.status || 'NO_SPEECH');
        if (text) {
          // The Whisper transcript REPLACES any partial browser speech text
          // (same approach as GDRound) and becomes the user's answer (BUG 13).
          voiceTranscriptRef.current = text;
          setCurrentAnswer(text);
          if (data.status === 'LOW_CONFIDENCE' && data.warning) {
            alert(data.warning);
          }
        } else {
          // No usable speech: keep the answer EMPTY (never substitute text).
          voiceTranscriptRef.current = null;
          setCurrentAnswer('');
          alert(data.message || 'No clear speech was detected. Please try again.');
        }
      } catch (error) {
        console.error('[INTERVIEW] Error transcribing interview audio:', error);
        const detail = error.response?.data?.message || error.response?.data?.error;
        alert(detail || 'Speech transcription failed. Please try recording again.');
      } finally {
        voiceTranscribePromiseRef.current = null;
      }
    })();
    return voiceTranscribePromiseRef.current;
  };

  const stopInterviewRecording = () => {
    // Stop the MediaRecorder only. We deliberately do NOT call
    // recognitionRef.current.stop() here: stopping a SpeechRecognition
    // instance that is already stopped (or was never started for the
    // interview) fires onerror with event.error === 'network', which is
    // the source of the "Speech recognition error: network" console message.
    // The Mock Interview uses the Whisper pipeline exclusively — browser
    // SpeechRecognition is not used and must not be touched here.
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop(); } catch (e) { /* already stopped */ }
    }
    // Do NOT null the ref here: onstop fires asynchronously AFTER stop()
    // returns. The onstop closure captures the local `recorder` variable so
    // it still works correctly — setting the ref to null immediately is safe
    // for the ref bookkeeping but was previously causing confusion. Keep the
    // null assignment so the ref is cleaned up, but after the async flush.
    mediaRecorderRef.current = null;
    // NOTE: recognitionRef.current is intentionally NOT stopped here.
    // See comment above. If a SpeechRecognition instance exists from an
    // earlier feature, it will be stopped only in closeInterviewModal().
  };

  const releaseInterviewStream = () => {
    if (interviewStreamRef.current) {
      interviewStreamRef.current.getTracks().forEach(t => t.stop());
      interviewStreamRef.current = null;
    }
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
  };

  const toggleRecording = async () => {
    // Guard on the SYNC ref, not the async `isRecording` state: a rapid
    // double-click previously passed the state check twice and created TWO
    // concurrent MediaRecorders on one stream - the orphaned recorder produced
    // corrupt webm that the backend rejected with HTTP 422.
    if (isRecordingRef.current) {
      isRecordingRef.current = false;
      setIsRecording(false);
      console.log('[INTERVIEW] recording stopped');
      stopInterviewRecording();
      return;
    }
    if (isRecordingRef.current === false && mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      // Stale recorder from a desynced previous turn: discard it cleanly
      // before starting a fresh one (never two live recorders at once).
      try { mediaRecorderRef.current.onstop = null; mediaRecorderRef.current.stop(); } catch (e) { /* already stopped */ }
      mediaRecorderRef.current = null;
    }
    isRecordingRef.current = true;

    // New turn: reset any previous transcript.
    voiceTranscriptRef.current = null;
    voiceTranscriptStatusRef.current = null;
    setCurrentAnswer('');

    // 1. Request microphone permission and record the user's speech.
    //    Independent getUserMedia: the app mic does NOT depend on Google Meet
    //    or any other app's microphone state - only on browser permission.
    let stream = interviewStreamRef.current;
    if (stream && stream.getAudioTracks().every(t => t.readyState !== 'live')) {
      // Dead stream from a previous turn: release it and acquire a fresh one.
      releaseInterviewStream();
      stream = null;
    }
    if (!stream) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        interviewStreamRef.current = stream;
      } catch (error) {
        console.error('[INTERVIEW] Microphone permission error:', error);
        isRecordingRef.current = false;
        setIsRecording(false);
        alert('Microphone access is required for the voice interview. Please allow microphone access and try again.');
        return;
      }
    }

    // 2. Record with MediaRecorder (the audio is transcribed server-side on stop).
    //    IMPORTANT: recorder.start(250) uses a 250ms timeslice so ondataavailable
    //    fires every 250ms, producing many small valid chunks. This matches
    //    GDRound.js (recorder.start(250)) which works reliably with /gd/transcribe.
    //    WITHOUT a timeslice, ondataavailable fires only once on .stop(), and the
    //    single-chunk WebM can be corrupt/undecodable -> backend HTTP 422.
    if (window.MediaRecorder) {
      try {
        const chunks = [];
        audioChunksRef.current = chunks;
        const mimeUsed = window.MediaRecorder.isTypeSupported
          ? ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus']
              .find(m => window.MediaRecorder.isTypeSupported(m))
          : null;
        let recorder;
        try {
          recorder = new MediaRecorder(stream, mimeUsed ? { mimeType: mimeUsed } : undefined);
        } catch (recErr) {
          recorder = new MediaRecorder(stream);
        }
        recorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.push(e.data); };
        recorder.onstop = () => {
          // Use the recorder's ACTUAL output mime type for the Blob - building
          // the blob from a mismatched type can produce an undecodable file.
          const blob = new Blob(chunks, { type: recorder.mimeType || mimeUsed || 'audio/webm' });
          transcribeInterviewAudio(blob);
        };
        mediaRecorderRef.current = recorder;
        // Use 250ms timeslice (matching GDRound.js recorder.start(250)) so that
        // ondataavailable fires every 250ms. This produces many small valid WebM
        // chunks instead of a single potentially-corrupt chunk, preventing the
        // backend HTTP 422 "Audio could not be decoded" error.
        recorder.start(250);
        console.log('[INTERVIEW] recording started');
      } catch (recError) {
        console.error('[INTERVIEW] MediaRecorder initialization failed:', recError);
        isRecordingRef.current = false;
        setIsRecording(false);
        return;
      }
    }

    // 3. Browser speech recognition is DISABLED for the Mock Interview
    //    (requirement: no 'Speech recognition error: network'). The Whisper
    //    transcript returned by /gd/transcribe is the one and only transcript
    //    used as the interview answer.
    setIsRecording(true);
  };

  const submitAnswer = async () => {
    // Voice mode: wait for any in-flight Whisper transcription to land and
    // use the ACTUAL transcript as the answer (BUG 13).
    if (interviewMode === 'voice' && voiceTranscribePromiseRef.current) {
      try { await voiceTranscribePromiseRef.current; } catch (e) { /* handled */ }
    }
    const answer = ((interviewMode === 'voice' && voiceTranscriptRef.current) || currentAnswer).trim();
    const transcriptStatus = interviewMode === 'voice' ? voiceTranscriptStatusRef.current : null;
    voiceTranscriptRef.current = null;
    voiceTranscriptStatusRef.current = null;

    // An empty transcript is NOT an answer: block submission (both modes) so
    // the turn is retried instead of being saved as a fake "No answer provided"
    // turn that could pollute the evaluation.
    if (!answer) {
      alert(interviewMode === 'voice'
        ? 'No clear speech was detected. Please try again.'
        : 'Please provide an answer before submitting.');
      return;
    }

    const newAnswers = [...userAnswers, answer];
    setUserAnswers(newAnswers);
    setCurrentAnswer('');
    
    if (isRecording || isRecordingRef.current) {
      // Stop the WHOLE recording pipeline (recorder + recognition). Stopping
      // only recognition previously left the MediaRecorder capturing across
      // the question transition, polluting the next answer's audio.
      isRecordingRef.current = false;
      setIsRecording(false);
      stopInterviewRecording();
    }

    // Persist the turn server-side so a refresh mid-interview keeps progress.
    // The payload carries the question index and STT status so the backend can
    // store a structured per-question turn (never conflating questions).
    if (interviewSessionId) {
      console.log('[INTERVIEW] saving answer: question', currentQuestionIndex,
        'status:', transcriptStatus || 'text');
      interviewAPI.saveAnswer({
        session_id: interviewSessionId,
        user_id: currentStudent.id,
        question_index: currentQuestionIndex,
        answer,
        transcript_status: transcriptStatus || undefined,
      })
        .then((res) => console.log('[INTERVIEW] answer save response:', res.data?.success))
        .catch(err => {
          console.error('[INTERVIEW] answer save failed:',
            err.response?.status, err.response?.data?.error || err.message);
        });
    }

    if (currentQuestionIndex < interviewQuestions.length - 1) {
      const nextIndex = currentQuestionIndex + 1;

      // Voice mode: speak ONLY the next question. The old flow injected AI
      // feedback ("Great answer! Now, question 2. ...") into the TTS - that
      // boilerplate is removed at the source per the TTS requirement.
      if (interviewMode === 'voice') {
        speakQuestion(interviewQuestions[nextIndex]);
      }

      setCurrentQuestionIndex(nextIndex);
    } else {
      // Voice mode: stop any remaining speech; no closing chatter is spoken.
      if (interviewMode === 'voice') {
        if (synthRef.current) synthRef.current.cancel();
      }
      handleFinishInterview(newAnswers);
    }
  };

  const skipQuestion = () => {
    submitAnswer();
  };

  const handleFinishInterview = async (answers = userAnswers) => {
    if (interviewFinalizedRef.current) return;
    interviewFinalizedRef.current = true;
    setInterviewEvaluating(true);
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }
    setTimerActive(false);
    
    // Stop recording pipeline first, then stop recognition (order matters:
    // stopping recognition while recorder is active causes 'network' error).
    isRecordingRef.current = false;
    setIsRecording(false);
    stopInterviewRecording();
    releaseInterviewStream();

    try {
      // Bounded evaluate request: evaluation is synchronous evidence-based
      // scoring server-side; never leave the student on an endless spinner.
      const response = await interviewAPI.submitAnswers({
        questions: interviewQuestions,
        answers: answers,
        studentId: currentStudent.id,
        user_id: currentStudent.id,
        session_id: interviewSessionId,
      }, { timeout: 60000 });
      
      const data = response.data || {};
      console.log(`[INTERVIEW] Evaluation completed. Final score: ${data.score}. ` +
        `Final status: ${data.status || (data.passed ? 'PASS' : 'FAIL')}`);
      setInterviewResults(data);
      localStorage.removeItem('activeInterviewSessionId');
      // Re-fetch student data so the Profile/progress section reflects the
      // freshly persisted score/status immediately (no stale state).
      await loadStudentData();
    } catch (error) {
      console.error('Error evaluating interview:', error);
      alert('Failed to evaluate interview.');
      interviewFinalizedRef.current = false; // allow retry on transient errors
    } finally {
      setInterviewEvaluating(false);
    }
  };

  const closeInterviewModal = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }
    setTimerActive(false);
    
    // Stop browser SpeechRecognition cleanly here (not during recording) so
    // it does NOT fire 'network' error while the MediaRecorder is active.
    // After closing the modal we also null the ref to prevent stale state
    // across modal open/close cycles.
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) { /* already stopped - ignore */ }
      recognitionRef.current = null;
    }
    if (isRecording) {
      setIsRecording(false);
    }
    isRecordingRef.current = false;
    stopInterviewRecording();
    releaseInterviewStream();
    voiceTranscriptRef.current = null;
    voiceTranscriptStatusRef.current = null;
    
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
    setInterviewSessionId(null);
    setInterviewResuming(false);
    interviewFinalizedRef.current = false;
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
    { id: 'ai-training', label: 'AI Skill Training', icon: <Brain size={20} /> },
    { id: 'settings', label: 'Settings', icon: <Settings size={20} /> },
  ];

  // If coding interface is open, show it in full screen instead of main content
  if (codingInterfaceOpen) {
    return (
      <CodingInterface 
        onClose={() => setCodingInterfaceOpen(false)}
      />
    );
  }

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Floating Menu Button for Mobile */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="floating-menu-btn md:hidden"
      >
        <Menu size={24} className="text-gray-700" />
      </button>

      <div className="h-screen">
        <div className="bg-gray-100 shadow-lg border-b-4 border-blue-500 overflow-hidden flex h-full">
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
            {/* Top Bar with Notification Bell */}
            <div className="flex justify-between items-center mb-6 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
              <div>
                <h1 className="text-xl font-bold text-gray-800">Student Portal</h1>
                <p className="text-xs text-gray-500">Track assignments, HR profile activities, and placement training</p>
              </div>
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setNotificationModalOpen(true)}
                  className="relative p-2 text-gray-600 hover:text-blue-600 rounded-full hover:bg-blue-50 transition-colors"
                  title="Notifications & HR Activity"
                >
                  <Bell size={24} />
                  {getStudentNotifications().length > 0 && (
                    <span className="absolute top-0 right-0 bg-red-500 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center animate-pulse">
                      {getStudentNotifications().length}
                    </span>
                  )}
                </button>
              </div>
            </div>

            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">My Profile</h2>
                
                <div className="bg-white p-8 rounded-xl shadow-md mb-6">
                  <div className="flex items-center space-x-6 mb-8">
                    <div className="w-24 h-24 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center text-white text-4xl font-bold shadow-lg">
                      {currentStudent.name?.charAt(0).toUpperCase() || 'S'}
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold text-gray-800">{currentStudent.name || 'Student'}</h3>
                      <p className="text-gray-600 capitalize">{currentStudent.role || 'student'}</p>
                      {currentStudent.department && (
                        <p className="text-sm text-gray-500 mt-1">{currentStudent.department}</p>
                      )}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {currentStudent.id && (
                      <div className="border-l-4 border-blue-500 pl-4 bg-blue-50 p-3 rounded-r-lg">
                        <p className="text-sm font-medium text-gray-600">Student ID</p>
                        <p className="text-lg text-gray-800 font-semibold">{currentStudent.id}</p>
                      </div>
                    )}
                    
                    {currentStudent.registerNumber && (
                      <div className="border-l-4 border-indigo-500 pl-4 bg-indigo-50 p-3 rounded-r-lg">
                        <p className="text-sm font-medium text-gray-600">Register Number</p>
                        <p className="text-lg text-gray-800 font-semibold">{currentStudent.registerNumber}</p>
                      </div>
                    )}
                    
                    {currentStudent.email && (
                      <div className="border-l-4 border-purple-500 pl-4 bg-purple-50 p-3 rounded-r-lg">
                        <p className="text-sm font-medium text-gray-600">Email</p>
                        <p className="text-lg text-gray-800">{currentStudent.email}</p>
                      </div>
                    )}
                    
                    {currentStudent.department && (
                      <div className="border-l-4 border-green-500 pl-4 bg-green-50 p-3 rounded-r-lg">
                        <p className="text-sm font-medium text-gray-600">Department</p>
                        <p className="text-lg text-gray-800">{currentStudent.department}</p>
                      </div>
                    )}
                    
                    {!currentStudent.registerNumber && !currentStudent.department && (
                      <div className="border-l-4 border-blue-500 pl-4 bg-blue-50 p-3 rounded-r-lg">
                        <p className="text-sm font-medium text-gray-600">Email</p>
                        <p className="text-lg text-gray-800">{currentStudent.email || 'student@example.com'}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Progress Stats */}
                <h3 className="text-2xl font-bold mb-4 text-gray-800">My Progress</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-blue-500">
                    <h4 className="text-lg font-semibold text-gray-600">Assignments Submitted</h4>
                    <p className="text-4xl font-bold text-blue-600 mt-2">
                      {progress?.submittedAssignments || 0}
                    </p>
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-green-500">
                    <h4 className="text-lg font-semibold text-gray-600">Interview Score</h4>
                    <p className="text-4xl font-bold text-green-600 mt-2">
                      {/* != null check (not truthiness): a completed interview
                          that scored 0 is a REAL score, never 'N/A'. */}
                      {progress?.interviewScore != null ? `${progress.interviewScore}%` : 'N/A'}
                    </p>
                    {/* PASS/FAIL recorded by /api/interview/evaluate - shown
                        only when a result actually exists (no-result state
                        stays clean). */}
                    {progress?.interviewStatus && (
                      <p className={`text-sm font-bold mt-1 ${
                        progress.interviewStatus === 'PASS'
                          ? 'text-green-700'
                          : 'text-red-600'
                      }`}>
                        {progress.interviewStatus === 'PASS' ? '✓ PASSED' : '✗ FAILED'}
                      </p>
                    )}
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-purple-500">
                    <h4 className="text-lg font-semibold text-gray-600">Resume Match Score</h4>
                    <p className="text-4xl font-bold text-purple-600 mt-2">
                      {progress?.resumeScore ? `${progress.resumeScore}%` : 'N/A'}
                    </p>
                    {!progress?.resumeScore && (
                      <p className="text-sm text-gray-500 mt-1">Upload your resume to get an ATS score</p>
                    )}
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-orange-500">
                    <h4 className="text-lg font-semibold text-gray-600">Quiz Average</h4>
                    <p className="text-4xl font-bold text-orange-600 mt-2">
                      {progress?.quizScore || progress?.averageQuizScore ? `${Math.round(progress.quizScore || progress.averageQuizScore)}%` : 'N/A'}
                    </p>
                    {progress?.totalQuizzes > 0 && (
                      <p className="text-sm text-gray-500 mt-1">{progress.totalQuizzes} test{progress.totalQuizzes !== 1 ? 's' : ''} taken</p>
                    )}
                  </div>

                  {/* Aptitude test average - synced from the training-section
                      attempts (server-persisted on every submit/fail). */}
                  <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-teal-500">
                    <h4 className="text-lg font-semibold text-gray-600">Aptitude Test Score</h4>
                    <p className="text-4xl font-bold text-teal-600 mt-2">
                      {progress?.aptitudeScore ? `${Math.round(progress.aptitudeScore)}%` : 'N/A'}
                    </p>
                    {progress?.totalAptitudeTests > 0 && (
                      <p className="text-sm text-gray-500 mt-1">
                        {progress.totalAptitudeTests} test{progress.totalAptitudeTests !== 1 ? 's' : ''} taken
                        {progress.aptitudeBestScore != null && ` • best ${Math.round(progress.aptitudeBestScore)}%`}
                      </p>
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
                                disabled={submittingAssignments[assignment.id]}
                              />
                              <button
                                onClick={() => handleSubmitAssignment(assignment.id)}
                                disabled={submittingAssignments[assignment.id]}
                                className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                              >
                                {submittingAssignments[assignment.id] ? (
                                  <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                                    Submitting...
                                  </>
                                ) : 'Submit'}
                              </button>
                            </div>
                          )
                        ) : (
                          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                            <p className="text-sm text-gray-700">
                              <span className="font-medium">Status:</span>{' '}
                              {assignment.type === 'Quiz'
                                ? (assignment.quiz_failure_reason === 'TAB_SWITCH'
                                  ? 'Assessment failed - tab switch detected'
                                  : assignment.quiz_failure_reason === 'TIME_EXPIRED'
                                  ? 'Assessment failed - time expired'
                                  : assignment.quiz_status === 'PASS' || assignment.quiz_passed === true
                                  ? 'Quiz completed - PASSED'
                                  : assignment.quiz_status === 'FAIL' || assignment.quiz_passed === false
                                  ? 'Quiz completed - FAILED'
                                  : 'Quiz submitted')
                                : 'Assignment submitted successfully'}
                              {assignment.submittedAt && (
                                <span className="text-gray-500"> on {new Date(assignment.submittedAt).toLocaleDateString()}</span>
                              )}
                            </p>

                            {/* Quiz result actions: review answers and/or
                                retake (a retake archives the old attempt
                                server-side and starts clean). */}
                            {assignment.type === 'Quiz' && (
                              <div className="mt-3 flex flex-wrap gap-3">
                                {assignment.quiz_evaluation?.results?.length > 0 && (
                                  <button
                                    onClick={() => handleViewQuizResult(assignment)}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
                                  >
                                    View Answer Review
                                  </button>
                                )}
                                <button
                                  onClick={() => handleStartQuiz(assignment, true)}
                                  className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700"
                                >
                                  🔄 Retake Quiz
                                </button>
                              </div>
                            )}
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
                      {/* != null check (not truthiness): a completed interview
                          that scored 0 is a REAL score, never 'N/A'. */}
                      {progress?.interviewScore != null ? `${progress.interviewScore}%` : 'N/A'}
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

                {/* =====================================================
                    RESUME UPLOAD GATEWAY - MANDATORY STEP 1
                    The duration/type selection and Start buttons are NOT
                    rendered until a resume is on file. Questions are
                    generated from the resume text (context injection into
                    the LLM prompt), so this is a hard prerequisite.
                    Three REAL states: checking (null) / upload required
                    (false) / ready (true). No fake success banner.
                    ===================================================== */}
                {interviewCheckingResume ? (
                  <div className="bg-gray-50 border border-gray-200 p-6 rounded-xl mb-6 flex items-center gap-3">
                    <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-500 border-t-transparent"></div>
                    <p className="text-sm text-gray-600 font-medium">Checking resume status...</p>
                  </div>
                ) : interviewResumeReady === false ? (
                  <div className="bg-amber-50 border-2 border-amber-300 p-6 rounded-xl mb-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="bg-amber-100 p-3 rounded-full">
                        <Upload size={26} className="text-amber-600" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-gray-800">
                          Step 1: Upload Your Resume (Required)
                        </h3>
                        <p className="text-sm text-amber-700 font-medium">
                          You must complete this step before you can choose an interview duration or type.
                        </p>
                      </div>
                    </div>
                    <p className="text-gray-700 mb-4">
                      Your AI interview questions are generated from your resume —
                      projects, skills, education and experience. Upload it once
                      and your mock interview will be tailored to YOU instead of
                      generic questions.
                    </p>
                    <ul className="text-sm text-gray-600 mb-5 list-disc list-inside space-y-1">
                      <li>Accepted formats: PDF or DOCX</li>
                      <li>The resume text is parsed and passed to the AI interviewer</li>
                      <li>You'll also get an ATS match score for your profile</li>
                    </ul>
                    <input
                      type="file"
                      ref={interviewResumeInputRef}
                      accept=".pdf,.docx"
                      className="w-full text-sm text-gray-600 mb-3 file:mr-4 file:py-3 file:px-6 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-amber-100 file:text-amber-800 hover:file:bg-amber-200"
                    />
                    <button
                      onClick={handleInterviewResumeUpload}
                      disabled={interviewResumeUploading}
                      className="bg-amber-500 hover:bg-amber-600 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {interviewResumeUploading ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                          Uploading &amp; Analyzing...
                        </>
                      ) : 'Upload Resume to Unlock Interview'}
                    </button>
                  </div>
                ) : (
                  <>
                    {/* Step 1 complete - shown ONLY after the database check
                        (or a fresh upload) confirmed a resume exists. This
                        banner is backed by the resumeUploaded flag, never
                        fabricated. */}
                    {interviewResumeReady === true && (
                      <div className="bg-green-50 border border-green-300 p-4 rounded-xl mb-6 flex items-center gap-3">
                        <CheckCircle size={20} className="text-green-600" />
                        <p className="text-sm text-green-800">
                          <span className="font-semibold">Resume on file.</span>{' '}
                          Interview questions will be generated from your resume. You can re-upload an updated resume anytime from the Resume Analysis tab.
                        </p>
                      </div>
                    )}

                    {/* STEP 2: duration + type selection (locked until Step 1) */}
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
                          onClick={() => openInterviewWithResumeGate('text')}
                          disabled={interviewStarting}
                          className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mx-auto"
                        >
                          {interviewStarting ? (
                            <>
                              <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                              Starting...
                            </>
                          ) : 'Start Text Interview'}
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
                          onClick={() => openInterviewWithResumeGate('voice')}
                          disabled={interviewStarting}
                          className="bg-green-500 hover:bg-green-600 text-white px-8 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mx-auto"
                        >
                          {interviewStarting ? (
                            <>
                              <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                              Starting...
                            </>
                          ) : 'Start Voice Interview'}
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Placement Training Tab */}
            {activeTab === 'training' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Placement Training</h2>

                {/* SkillRack-style topic-wise skill cards: XP, badges and
                    progress are persisted server-side and computed on the API. */}
                <div className="mb-10">
                  <SkillCardDashboard currentStudent={currentStudent} />
                </div>
              </div>
            )}

            {/* AI Training Paths (kept as a second training tab) */}
            {activeTab === 'ai-training' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">AI Skill Training</h2>
                
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
                    {showProgrammingLanguages ? (
                      <div>
                        <button
                          onClick={() => setShowProgrammingLanguages(false)}
                          className="mb-6 text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2"
                        >
                          <ArrowLeft size={20} />
                          Back to Categories
                        </button>

                        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl shadow-md mb-6">
                          <div className="flex items-center gap-3 mb-2">
                            <Code className="text-blue-600" size={28} />
                            <h3 className="text-xl font-bold text-gray-800">Select Programming Language</h3>
                          </div>
                          <p className="text-gray-600">Choose a programming language to practice coding problems and improve your skills.</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                          {programmingLanguages.map(language => (
                            <div
                              key={language.id}
                              className="bg-white p-6 rounded-xl shadow-md hover:shadow-xl transition-all cursor-pointer border-2 border-transparent hover:border-blue-500 transform hover:-translate-y-1"
                              onClick={() => selectProgrammingLanguage(language.id)}
                            >
                              <div className="flex justify-center mb-3">
                                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-full">
                                  <language.icon className="text-blue-600" size={40} />
                                </div>
                              </div>
                              <h4 className="text-lg font-bold text-gray-800 mb-2 text-center">{language.name}</h4>
                              <p className="text-sm text-gray-600 text-center mb-4">{language.description}</p>
                              <div className="flex justify-center">
                                <button className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white px-4 py-2 rounded-lg font-medium transition-colors text-sm">
                                  Start Coding
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : showAptitudeTraining ? (
                      <div>
                        <button
                          onClick={() => setShowAptitudeTraining(false)}
                          className="mb-6 text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2"
                        >
                          <ArrowLeft size={20} />
                          Back to Categories
                        </button>
                        <AptitudeTraining currentStudent={currentStudent} />
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
                              onClick={() => !trainingLoading && !gdRoundLoading && startTraining(category.id)}
                            >
                              <div className="flex justify-center mb-4">
                                <div className="bg-gradient-to-br from-blue-100 to-indigo-100 p-5 rounded-full">
                                  <category.icon className="text-blue-600" size={40} />
                                </div>
                              </div>
                              <h4 className="text-lg font-bold text-gray-800 mb-2 text-center">{category.name}</h4>
                              <p className="text-sm text-gray-600 text-center">{category.description}</p>
                              {(category.id === 'gd-round' && gdRoundLoading) && (
                                <div className="flex items-center justify-center gap-2 mt-4 text-blue-600">
                                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent"></div>
                                  <span className="text-sm">Loading...</span>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <div className="fade-in">
                <h2 className="text-3xl font-bold mb-6 text-gray-800">Settings</h2>
                
                {/* Settings Navigation */}
                <div className="flex gap-2 mb-6 border-b border-gray-200 overflow-x-auto">
                  <button
                    onClick={() => setActiveSettingsSection('password')}
                    className={`px-4 py-2 font-medium whitespace-nowrap transition-colors ${
                      activeSettingsSection === 'password'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    <Lock size={18} className="inline mr-2" />
                    Password
                  </button>
                  <button
                    onClick={() => setActiveSettingsSection('profile')}
                    className={`px-4 py-2 font-medium whitespace-nowrap transition-colors ${
                      activeSettingsSection === 'profile'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    <UserCircle size={18} className="inline mr-2" />
                    Profile
                  </button>
                  <button
                    onClick={() => setActiveSettingsSection('notifications')}
                    className={`px-4 py-2 font-medium whitespace-nowrap transition-colors ${
                      activeSettingsSection === 'notifications'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    <Bell size={18} className="inline mr-2" />
                    Notifications
                  </button>
                  <button
                    onClick={() => setActiveSettingsSection('account')}
                    className={`px-4 py-2 font-medium whitespace-nowrap transition-colors ${
                      activeSettingsSection === 'account'
                        ? 'text-blue-600 border-b-2 border-blue-600'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    <Info size={18} className="inline mr-2" />
                    Account Info
                  </button>
                </div>

                {/* Password Change Section */}
                {activeSettingsSection === 'password' && (
                  <div className="bg-white p-6 rounded-xl shadow-md">
                    <h3 className="text-xl font-bold mb-4 text-gray-700 flex items-center gap-2">
                      <Lock size={24} />
                      Change Password
                    </h3>
                    
                    <div className="max-w-md space-y-4">
                      {passwordChangeMessage && (
                        <div className="p-4 rounded-lg bg-green-50 border border-green-200 text-green-800 flex items-center gap-2">
                          <CheckCircle size={20} />
                          {passwordChangeMessage}
                        </div>
                      )}
                      
                      {passwordChangeError && (
                        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 flex items-center gap-2">
                          <AlertCircle size={20} />
                          {passwordChangeError}
                        </div>
                      )}
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Current Password
                        </label>
                        <input
                          type="password"
                          value={currentPassword}
                          onChange={(e) => setCurrentPassword(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Enter current password"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          New Password
                        </label>
                        <input
                          type="password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Enter new password (min 6 characters)"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Confirm New Password
                        </label>
                        <input
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Confirm new password"
                        />
                      </div>
                      
                      <button
                        onClick={handlePasswordChange}
                        disabled={passwordChangeLoading}
                        className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 font-medium"
                      >
                        {passwordChangeLoading ? 'Changing Password...' : 'Change Password'}
                      </button>
                    </div>
                  </div>
                )}

                {/* Profile Edit Section */}
                {activeSettingsSection === 'profile' && (
                  <div className="bg-white p-6 rounded-xl shadow-md">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-gray-700 flex items-center gap-2">
                        <UserCircle size={24} />
                        Profile Information
                      </h3>
                      {!editingProfile && (
                        <button
                          onClick={() => setEditingProfile(true)}
                          className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        >
                          <Edit2 size={18} />
                          Edit Profile
                        </button>
                      )}
                    </div>
                    
                    <div className="max-w-md space-y-4">
                      {profileUpdateMessage && (
                        <div className="p-4 rounded-lg bg-green-50 border border-green-200 text-green-800 flex items-center gap-2">
                          <CheckCircle size={20} />
                          {profileUpdateMessage}
                        </div>
                      )}
                      
                      {profileUpdateError && (
                        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 flex items-center gap-2">
                          <AlertCircle size={20} />
                          {profileUpdateError}
                        </div>
                      )}
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Full Name
                        </label>
                        <input
                          type="text"
                          value={profileName}
                          onChange={(e) => setProfileName(e.target.value)}
                          disabled={!editingProfile}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-600"
                          placeholder="Enter your full name"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Email
                        </label>
                        <input
                          type="email"
                          value={profileEmail}
                          onChange={(e) => setProfileEmail(e.target.value)}
                          disabled={!editingProfile}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-600"
                          placeholder="Enter your email"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Department
                        </label>
                        <input
                          type="text"
                          value={profileDepartment}
                          onChange={(e) => setProfileDepartment(e.target.value)}
                          disabled={!editingProfile}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-600"
                          placeholder="Enter your department"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Register Number
                        </label>
                        <input
                          type="text"
                          value={currentStudent.registerNumber || 'N/A'}
                          disabled
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                        />
                        <p className="text-xs text-gray-500 mt-1">Register number cannot be changed</p>
                      </div>
                      
                      {editingProfile && (
                        <div className="flex gap-3">
                          <button
                            onClick={handleProfileUpdate}
                            disabled={profileUpdateLoading}
                            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 font-medium flex items-center justify-center gap-2"
                          >
                            <Save size={18} />
                            {profileUpdateLoading ? 'Saving...' : 'Save Changes'}
                          </button>
                          <button
                            onClick={() => {
                              setEditingProfile(false);
                              setProfileName(currentStudent.name || '');
                              setProfileEmail(currentStudent.email || '');
                              setProfileDepartment(currentStudent.department || '');
                              setProfileUpdateError('');
                            }}
                            className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors duration-200 font-medium"
                          >
                            Cancel
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Notification Preferences Section */}
                {activeSettingsSection === 'notifications' && (
                  <div className="bg-white p-6 rounded-xl shadow-md">
                    <h3 className="text-xl font-bold mb-4 text-gray-700 flex items-center gap-2">
                      <Bell size={24} />
                      Notification Preferences
                    </h3>
                    
                    <div className="max-w-md space-y-4">
                      {notificationMessage && (
                        <div className="p-4 rounded-lg bg-green-50 border border-green-200 text-green-800 flex items-center gap-2">
                          <CheckCircle size={20} />
                          {notificationMessage}
                        </div>
                      )}
                      
                      <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                          <div>
                            <p className="font-medium text-gray-800">Email Notifications</p>
                            <p className="text-sm text-gray-600">Receive updates via email</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={emailNotifications}
                              onChange={(e) => setEmailNotifications(e.target.checked)}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                          </label>
                        </div>
                        
                        <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                          <div>
                            <p className="font-medium text-gray-800">Assignment Updates</p>
                            <p className="text-sm text-gray-600">Get notified about new assignments</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={assignmentNotifications}
                              onChange={(e) => setAssignmentNotifications(e.target.checked)}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                          </label>
                        </div>
                        
                        <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                          <div>
                            <p className="font-medium text-gray-800">Interview Notifications</p>
                            <p className="text-sm text-gray-600">Alerts for interview schedules</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={interviewNotifications}
                              onChange={(e) => setInterviewNotifications(e.target.checked)}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                          </label>
                        </div>
                      </div>
                      
                      <button
                        onClick={handleNotificationUpdate}
                        disabled={notificationLoading}
                        className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 font-medium flex items-center justify-center gap-2"
                      >
                        <Save size={18} />
                        {notificationLoading ? 'Saving...' : 'Save Preferences'}
                      </button>
                    </div>
                  </div>
                )}

                {/* Account Information Section */}
                {activeSettingsSection === 'account' && (
                  <div className="bg-white p-6 rounded-xl shadow-md">
                    <h3 className="text-xl font-bold mb-4 text-gray-700 flex items-center gap-2">
                      <Info size={24} />
                      Account Information
                    </h3>
                    
                    <div className="max-w-md space-y-4">
                      <div className="p-4 border border-gray-200 rounded-lg">
                        <p className="text-sm text-gray-600 mb-1">Student ID</p>
                        <p className="font-medium text-gray-800">{currentStudent.id}</p>
                      </div>
                      
                      <div className="p-4 border border-gray-200 rounded-lg">
                        <p className="text-sm text-gray-600 mb-1">Register Number</p>
                        <p className="font-medium text-gray-800">{currentStudent.registerNumber || 'N/A'}</p>
                      </div>
                      
                      <div className="p-4 border border-gray-200 rounded-lg">
                        <p className="text-sm text-gray-600 mb-1">Email Address</p>
                        <p className="font-medium text-gray-800">{currentStudent.email}</p>
                      </div>
                      
                      <div className="p-4 border border-gray-200 rounded-lg">
                        <p className="text-sm text-gray-600 mb-1">Department</p>
                        <p className="font-medium text-gray-800">{currentStudent.department || 'N/A'}</p>
                      </div>
                      
                      <div className="p-4 border border-gray-200 rounded-lg">
                        <p className="text-sm text-gray-600 mb-1">Role</p>
                        <p className="font-medium text-gray-800 capitalize">{currentStudent.role || 'Student'}</p>
                      </div>
                      
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm text-blue-600 mb-2">💡 Need Help?</p>
                        <p className="text-sm text-gray-700">
                          If you need to change your register number or have any account issues, 
                          please contact your administrator.
                        </p>
                      </div>
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

      {/* Quiz Modal - full-screen: the assessment occupies the whole
          viewport instead of a narrow centered card (assessment UI overhaul).
          Other modals keep their normal sizing. */}
      <Modal
        isOpen={quizModalOpen}
        onClose={closeQuizModal}
        fullScreen={true}
        title={quizResults ? 'Quiz Results' : `${currentQuiz?.title || 'Quiz'}`}
      >
        {!quizResults ? (
          <div className="space-y-6">
            {/* Server-authoritative countdown (display only) */}
            {quizAttempt && quizAttempt.status === 'IN_PROGRESS' && (
              <div className={`p-4 rounded-lg text-center ${quizTimeRemaining < 60 ? 'bg-red-50' : 'bg-blue-50'}`}>
                <p className="text-sm font-medium text-gray-600 mb-1">Time Remaining</p>
                <p className={`text-3xl font-bold ${quizTimeRemaining < 60 ? 'text-red-600 animate-pulse' : 'text-blue-600'}`}>
                  {formatTime(quizTimeRemaining)}
                </p>
              </div>
            )}

            {/* Lock/result state: failed (tab switch / expiry) or already
                submitted. NOT a dead end anymore - a Retake Assessment
                button archives the old attempt and starts a clean one. */}
            {quizLockMessage && (
              <div className="bg-red-50 border-2 border-red-300 p-6 rounded-lg text-center">
                <p className="text-2xl mb-2">🔒</p>
                <p className="text-lg font-bold text-red-700">{quizLockMessage}</p>
                <p className="text-sm text-gray-600 mt-2">
                  You can retake this assessment - a fresh attempt will be started.
                </p>
                <div className="mt-4 flex flex-col sm:flex-row gap-3 justify-center">
                  <button
                    onClick={handleRetakeQuiz}
                    disabled={quizRetaking}
                    className="px-6 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {quizRetaking ? 'Preparing retake...' : '🔄 Retake Assessment'}
                  </button>
                  <button
                    onClick={closeQuizModal}
                    className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300"
                  >
                    Back
                  </button>
                </div>
              </div>
            )}

            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-700">
                <span className="font-bold">Instructions:</span> Answer all questions to the best of your ability.
                Your quiz will be evaluated once submitted.
              </p>
              <p className="text-sm text-red-600 mt-2 font-medium">
                ⚠️ Switching to another browser tab or window will automatically fail this assessment.
              </p>
              <p className="text-sm text-gray-600 mt-2">
                Total Questions: {quizQuestions.length}
              </p>
            </div>

            <div className="space-y-6 max-h-96 overflow-y-auto">
              {quizQuestions.map((question, index) => {
                // Normalize both legacy string questions and object questions
                const questionText = typeof question === 'string'
                  ? question
                  : question?.question || JSON.stringify(question);
                const options = question?.options || [];
                const hasOptions = Array.isArray(options) && options.length > 0;
                const category = question?.category;

                return (
                  <div key={index} className="bg-white p-4 rounded-lg border border-gray-200">
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <h4 className="font-bold text-gray-800">
                        {index + 1}. {questionText}
                      </h4>
                      {/* Category tag (Grammar / General Knowledge / Technical /
                          Logical Reasoning) when the bank provides one. */}
                      {category && (
                        <span className="shrink-0 px-2 py-1 text-xs rounded-full bg-indigo-100 text-indigo-700 font-medium">
                          {category}
                        </span>
                      )}
                    </div>
                    {hasOptions ? (
                      <div className="space-y-2">
                        {options.map((option, optIndex) => (
                          <label 
                            key={optIndex}
                            className={`flex items-center p-3 rounded-lg border-2 transition-all ${
                              quizLockMessage
                                ? 'opacity-50 cursor-not-allowed border-gray-200'
                                : quizAnswers[index] === option
                                ? 'border-purple-500 bg-purple-50 cursor-pointer'
                                : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50 cursor-pointer'
                            }`}
                          >
                            <input
                              type="radio"
                              name={`question-${index}`}
                              value={option}
                              checked={quizAnswers[index] === option}
                              onChange={(e) => handleQuizAnswerChange(index, e.target.value)}
                              disabled={!!quizLockMessage || quizSubmitting}
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
                        disabled={!!quizLockMessage || quizSubmitting}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
                      />
                    )}
                  </div>
                );
              })}
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSubmitQuiz}
                disabled={quizSubmitting || !!quizLockMessage || !quizAttempt || quizAttempt.status !== 'IN_PROGRESS'}
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
              <p className={`text-5xl font-bold mb-2 ${
                quizResults.passed === false ? 'text-red-600' : 'text-purple-600'
              }`}>
                {quizResults.score}%
              </p>
              {quizResults.passed != null && (
                <p className={`text-lg font-bold mb-2 ${quizResults.passed ? 'text-green-700' : 'text-red-700'}`}>
                  {quizResults.passed ? '✓ PASSED' : '✗ FAILED'}
                </p>
              )}
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
                      {feedback.category && (
                        <span className="ml-2 shrink-0 px-2 py-0.5 text-xs rounded-full bg-indigo-100 text-indigo-700 font-medium">
                          {feedback.category}
                        </span>
                      )}
                      <span className={`ml-2 px-3 py-1 rounded-full text-sm font-bold flex items-center gap-1 ${
                        feedback.isCorrect 
                          ? 'bg-green-200 text-green-800'
                          : feedback.status === 'unanswered'
                          ? 'bg-yellow-200 text-yellow-800'
                          : 'bg-red-200 text-red-800'
                      }`}>
                        {feedback.isCorrect ? (
                          <><Check size={16} /> Correct</>
                        ) : feedback.status === 'unanswered' ? (
                          <><AlertCircle size={16} /> Unanswered</>
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

      {/* MANDATORY "Upload Resume First" gate: rendered when the student
          clicks Start Text/Voice Interview with no resume on file. Starting
          the interview is impossible until the upload + parse succeeds. */}
      <Modal
        isOpen={interviewResumeGate}
        onClose={() => { setInterviewResumeGate(false); setPendingInterviewMode(null); }}
        title="Upload Resume First"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="bg-amber-100 p-3 rounded-full">
              <Upload size={26} className="text-amber-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-800">A resume is required before the AI Interview can start.</p>
              <p className="text-sm text-gray-600">Your interview questions will be generated from your resume's actual projects, skills and experience.</p>
            </div>
          </div>
          <ul className="text-sm text-gray-600 list-disc list-inside space-y-1 bg-gray-50 p-4 rounded-lg">
            <li>Accepted formats: PDF or DOCX</li>
            <li>The resume must parse successfully (text extraction) before the interview unlocks</li>
            <li>You'll also get an ATS match score for your profile</li>
          </ul>
          <input
            type="file"
            ref={interviewResumeInputRef}
            accept=".pdf,.docx"
            className="w-full text-sm text-gray-600 file:mr-4 file:py-3 file:px-6 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-amber-100 file:text-amber-800 hover:file:bg-amber-200"
          />
          <div className="flex justify-end gap-3">
            <button
              onClick={() => { setInterviewResumeGate(false); setPendingInterviewMode(null); }}
              disabled={interviewResumeUploading}
              className="px-5 py-2.5 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 font-medium transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={() => handleInterviewResumeUpload(true)}
              disabled={interviewResumeUploading}
              className="bg-amber-500 hover:bg-amber-600 text-white px-6 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {interviewResumeUploading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                  Uploading &amp; Parsing...
                </>
              ) : 'Upload & Start Interview'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Interview Modal - fullScreen: the assessment occupies the whole
          viewport (other modals keep their normal card sizing) */}
      <Modal
        isOpen={interviewModalOpen}
        onClose={closeInterviewModal}
        fullScreen={true}
        title={interviewResults ? 'Interview Results' : `Question ${currentQuestionIndex + 1} of ${interviewQuestions.length}`}
      >
        {!interviewResults ? (
          <div className="space-y-6">
            {interviewResuming && (
              <div className="bg-amber-50 border border-amber-300 p-3 rounded-lg text-center">
                <p className="text-sm text-amber-800 font-medium">
                  ↩️ Previous interview session restored — continuing from Question {currentQuestionIndex + 1}.
                </p>
              </div>
            )}

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
                disabled={interviewEvaluating}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {interviewEvaluating ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    {currentQuestionIndex < interviewQuestions.length - 1 ? 'Processing...' : 'Evaluating...'}
                  </>
                ) : (
                  currentQuestionIndex < interviewQuestions.length - 1 ? 'Next Question' : 'Finish Interview'
                )}
              </button>
              <button
                onClick={skipQuestion}
                disabled={interviewEvaluating}
                className="px-6 py-3 bg-gray-300 hover:bg-gray-400 text-gray-700 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
              {/* Pass/Fail straight from the backend evaluation result. */}
              {interviewResults.status && (
                <p className={`text-lg font-bold mb-2 ${
                  interviewResults.status === 'PASS' ? 'text-green-700' : 'text-red-700'
                }`}>
                  {interviewResults.status === 'PASS' ? '✓ PASSED' : '✗ FAILED'}
                </p>
              )}
              <p className="text-gray-700">{interviewResults.feedback || 'Interview completed successfully!'}</p>
            </div>

            {interviewResults.details && (
              <div className="space-y-3">
                <h4 className="font-bold text-gray-800">Detailed Feedback:</h4>
                {interviewResults.details.map((detail, index) => (
                  <div key={index} className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex justify-between items-start gap-2">
                      <p className="font-medium text-gray-800">{detail.question}</p>
                      {detail.classification && (
                        <span className={`px-2 py-0.5 text-xs rounded-full whitespace-nowrap ${
                          detail.classification === 'RELEVANT'
                            ? 'bg-green-100 text-green-800'
                            : detail.classification === 'PARTIALLY_RELEVANT'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {detail.classification.replace('_', ' ')}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-2">
                      {detail.relevance_reason || detail.feedback || ''}
                    </p>
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

      {/* Student Notifications & HR Activity Modal */}
      <Modal
        isOpen={notificationModalOpen}
        onClose={() => setNotificationModalOpen(false)}
        title="Notifications & HR Activity"
      >
        <div className="space-y-4 max-h-96 overflow-y-auto pr-1">
          {getStudentNotifications().length > 0 ? (
            getStudentNotifications().map(notif => (
              <div
                key={notif.id}
                className={`p-4 rounded-lg border transition-colors ${
                  notif.type === 'hr' ? 'bg-purple-50 border-purple-200' : 'bg-blue-50 border-blue-200'
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                    notif.type === 'hr' ? 'bg-purple-200 text-purple-800' : 'bg-blue-200 text-blue-800'
                  }`}>
                    {notif.type === 'hr' ? 'HR Activity' : 'Assignment'}
                  </span>
                  <span className="text-xs text-gray-500">{notif.time}</span>
                </div>
                <h4 className="font-bold text-gray-800 mt-2">{notif.title}</h4>
                <p className="text-sm text-gray-600 mt-1">{notif.message}</p>
              </div>
            ))
          ) : (
            <p className="text-center text-gray-500 py-6">No new notifications at this time.</p>
          )}
        </div>
      </Modal>

      {/* GD Round Component */}
      {gdRoundOpen && currentGDRound && (
        <GDRound
          gdRound={currentGDRound}
          studentId={currentStudent.id}
          onClose={closeGDRound}
          onComplete={handleGDComplete}
        />
      )}
    </div>
  );
};

export default StudentPage;
