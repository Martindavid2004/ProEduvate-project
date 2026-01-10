import React, { useState, useEffect, useRef } from 'react';
import { Brain, BookOpen, Target, Trophy, Clock, Camera, AlertCircle, CheckCircle, XCircle, Play, Pause, Video } from 'lucide-react';
import { API_URL } from '../services/api';

const AptitudeTraining = ({ currentStudent }) => {
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [topics, setTopics] = useState([]);
  const [mode, setMode] = useState('select'); // select, learn, practice, test, results
  const [concepts, setConcepts] = useState(null);
  const [practiceQuestions, setPracticeQuestions] = useState([]);
  const [testQuestions, setTestQuestions] = useState([]);
  const [testId, setTestId] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [timeRemaining, setTimeRemaining] = useState(3600); // 60 minutes in seconds
  const [testStarted, setTestStarted] = useState(false);
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(null);
  
  const videoRef = useRef(null);
  const timerIntervalRef = useRef(null);

  // Fetch topics on mount
  useEffect(() => {
    fetchTopics();
    fetchProgress();
  }, []);

  // Timer for test
  useEffect(() => {
    if (testStarted && timeRemaining > 0) {
      timerIntervalRef.current = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            clearInterval(timerIntervalRef.current);
            handleSubmitTest();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timerIntervalRef.current);
  }, [testStarted]);

  // Camera monitoring
  useEffect(() => {
    if (cameraEnabled && mode === 'test') {
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
  }, [cameraEnabled, mode]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      alert('Camera access denied. Please enable camera for test monitoring.');
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
  };

  const fetchTopics = async () => {
    try {
      const response = await fetch(`${API_URL}/aptitude/topics`);
      const data = await response.json();
      if (data.success) {
        setTopics(data.topics);
      }
    } catch (error) {
      console.error('Error fetching topics:', error);
    }
  };

  const fetchProgress = async () => {
    try {
      const response = await fetch(`${API_URL}/aptitude/progress/${currentStudent.id}`);
      const data = await response.json();
      if (data.success) {
        setProgress(data);
      }
    } catch (error) {
      console.error('Error fetching progress:', error);
    }
  };

  const handleTopicSelect = (topic) => {
    setSelectedTopic(topic);
    setMode('options');
  };

  const handleLearnConcepts = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/aptitude/concepts/${selectedTopic.name}`);
      const data = await response.json();
      if (data.success) {
        setConcepts(data.data);
        setMode('learn');
      }
    } catch (error) {
      console.error('Error fetching concepts:', error);
    }
    setLoading(false);
  };

  const handlePractice = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/aptitude/practice/${selectedTopic.name}?count=10`);
      const data = await response.json();
      if (data.success) {
        setPracticeQuestions(data.data.practice_questions || []);
        setMode('practice');
      }
    } catch (error) {
      console.error('Error fetching practice questions:', error);
    }
    setLoading(false);
  };

  const handleStartTest = async (difficulty = 'medium') => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/aptitude/test/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: selectedTopic.name,
          difficulty,
          num_questions: 50
        })
      });
      const data = await response.json();
      if (data.success) {
        setTestId(data.test_id);
        setTestQuestions(data.questions);
        setCurrentQuestionIndex(0);
        setUserAnswers({});
        setTimeRemaining(3600);
        setMode('test');
        setTestStarted(true);
        setCameraEnabled(true);
      }
    } catch (error) {
      console.error('Error generating test:', error);
    }
    setLoading(false);
  };

  const handleAnswerSelect = (questionIndex, answer) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionIndex]: answer
    }));
  };

  const handleSubmitTest = async () => {
    clearInterval(timerIntervalRef.current);
    setTestStarted(false);
    setCameraEnabled(false);
    setLoading(true);

    try {
      const timeTaken = 3600 - timeRemaining;
      const response = await fetch(`${API_URL}/aptitude/test/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: currentStudent.id,
          test_id: testId,
          topic: selectedTopic.name,
          questions: testQuestions,
          answers: userAnswers,
          time_taken: timeTaken
        })
      });
      const data = await response.json();
      if (data.success) {
        setTestResults(data.evaluation);
        setMode('results');
        fetchProgress();
      }
    } catch (error) {
      console.error('Error submitting test:', error);
    }
    setLoading(false);
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Topic Selection View
  if (mode === 'select') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Brain size={28} className="text-purple-600" />
            AI-Based Aptitude Training
          </h3>
        </div>

        {progress && progress.statistics.total_tests > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="text-blue-600 text-sm font-medium">Total Tests</div>
              <div className="text-2xl font-bold text-blue-700">{progress.statistics.total_tests}</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="text-green-600 text-sm font-medium">Average Score</div>
              <div className="text-2xl font-bold text-green-700">{progress.statistics.average_score}%</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
              <div className="text-purple-600 text-sm font-medium">Best Score</div>
              <div className="text-2xl font-bold text-purple-700">{progress.statistics.best_score}%</div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {topics.map((topic, index) => (
            <button
              key={index}
              onClick={() => handleTopicSelect(topic)}
              className="p-6 bg-white border-2 border-gray-200 rounded-xl hover:border-purple-500 hover:shadow-lg transition-all text-left group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center group-hover:bg-purple-200 transition-colors">
                  <Brain size={24} className="text-purple-600" />
                </div>
                {progress?.statistics.topic_performance[topic.name] && (
                  <div className="text-sm font-bold text-green-600">
                    {Math.round(progress.statistics.topic_performance[topic.name].avg_score)}%
                  </div>
                )}
              </div>
              <h4 className="font-bold text-gray-800 mb-2">{topic.name}</h4>
              <p className="text-sm text-gray-600">{topic.description}</p>
            </button>
          ))}
        </div>
      </div>
    );
  }

  // Options View (Learn, Practice, Test)
  if (mode === 'options') {
    return (
      <div className="space-y-6 relative">
        {/* Loading Overlay */}
        {loading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-8 rounded-xl shadow-2xl text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-600 mx-auto mb-4"></div>
              <p className="text-lg font-semibold text-gray-800 mb-2">Loading...</p>
              <p className="text-sm text-gray-600">AI is preparing your content</p>
            </div>
          </div>
        )}

        <button
          onClick={() => setMode('select')}
          className="text-purple-600 hover:text-purple-800 font-medium flex items-center gap-2"
        >
          ← Back to Topics
        </button>

        <h3 className="text-2xl font-bold text-gray-800">{selectedTopic.name}</h3>
        <p className="text-gray-600">{selectedTopic.description}</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <button
            onClick={handleLearnConcepts}
            className="p-8 bg-blue-50 border-2 border-blue-200 rounded-xl hover:border-blue-500 hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loading}
          >
            <BookOpen size={48} className="text-blue-600 mb-4" />
            <h4 className="text-xl font-bold text-gray-800 mb-2">Learn Concepts</h4>
            <p className="text-gray-600">Study fundamental concepts, formulas, and tricks</p>
          </button>

          <button
            onClick={handlePractice}
            className="p-8 bg-green-50 border-2 border-green-200 rounded-xl hover:border-green-500 hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loading}
          >
            <Target size={48} className="text-green-600 mb-4" />
            <h4 className="text-xl font-bold text-gray-800 mb-2">Practice Questions</h4>
            <p className="text-gray-600">Solve sample problems with detailed solutions</p>
          </button>

          <button
            onClick={() => handleStartTest('medium')}
            className="p-8 bg-purple-50 border-2 border-purple-200 rounded-xl hover:border-purple-500 hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loading}
          >
            <Trophy size={48} className="text-purple-600 mb-4" />
            <h4 className="text-xl font-bold text-gray-800 mb-2">Take Test</h4>
            <p className="text-gray-600">50 questions • 60 minutes • AI proctored</p>
          </button>
        </div>
      </div>
    );
  }

  // Learn View
  if (mode === 'learn' && concepts) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => setMode('options')}
          className="text-purple-600 hover:text-purple-800 font-medium flex items-center gap-2 mb-2"
        >
          ← Back to Options
        </button>

        {/* Header Section */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-400 p-8 rounded-2xl shadow-lg text-white">
          <div className="flex items-center gap-4 mb-3">
            <div className="bg-white bg-opacity-20 p-3 rounded-xl">
              <BookOpen size={32} className="text-white" />
            </div>
            <div>
              <h3 className="text-3xl font-bold">{concepts.topic}</h3>
              <p className="text-blue-100 text-sm mt-1">Master the fundamentals with structured learning</p>
            </div>
          </div>
        </div>

        {/* Video Tutorial Section */}
        {selectedTopic.video_url && (
          <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                <div className="bg-red-100 p-2 rounded-lg">
                  <Video size={20} className="text-red-600" />
                </div>
                Video Tutorial
              </h4>
              <span className="text-sm bg-blue-50 text-blue-600 px-3 py-1 rounded-full font-medium">Recommended</span>
            </div>
            <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl overflow-hidden shadow-inner">
              <iframe
                width="100%"
                height="100%"
                src={selectedTopic.video_url}
                title="Video tutorial"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="w-full h-full"
              />
            </div>
          </div>
        )}

        {/* Key Concepts Section */}
        {concepts.concepts && concepts.concepts.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="h-1 w-12 bg-blue-600 rounded"></div>
              <h4 className="text-xl font-bold text-gray-800">Key Concepts</h4>
            </div>
            {concepts.concepts.map((concept, index) => (
              <div key={index} className="bg-white p-6 rounded-2xl shadow-md border border-gray-100 hover:shadow-lg transition-shadow">
                <div className="flex items-start gap-4">
                  <div className="bg-blue-100 text-blue-600 font-bold text-lg w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <h5 className="text-xl font-bold text-gray-800 mb-3">{concept.title}</h5>
                    <p className="text-gray-700 leading-relaxed mb-4">{concept.description}</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {concept.formula && (
                        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-200">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="text-blue-600 font-semibold text-sm">📐 Formula</div>
                          </div>
                          <div className="font-mono text-blue-900 text-sm bg-white p-3 rounded-lg">{concept.formula}</div>
                        </div>
                      )}
                      {concept.example && (
                        <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-xl border border-green-200">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="text-green-600 font-semibold text-sm">💡 Example</div>
                          </div>
                          <div className="text-gray-700 text-sm bg-white p-3 rounded-lg leading-relaxed">{concept.example}</div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tips & Tricks Section */}
        {concepts.tips_and_tricks && concepts.tips_and_tricks.length > 0 && (
          <div className="bg-gradient-to-br from-yellow-50 to-amber-50 p-6 rounded-2xl border-2 border-yellow-300 shadow-md">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-yellow-400 p-2 rounded-lg">
                <span className="text-2xl">💡</span>
              </div>
              <h4 className="text-xl font-bold text-gray-800">Pro Tips & Shortcuts</h4>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {concepts.tips_and_tricks.map((tip, index) => (
                <div key={index} className="bg-white p-4 rounded-lg shadow-sm flex gap-3">
                  <div className="text-yellow-600 font-bold flex-shrink-0">✓</div>
                  <p className="text-gray-700 text-sm leading-relaxed">{tip}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Practice Action */}
        <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-6 rounded-2xl shadow-lg text-white flex items-center justify-between">
          <div>
            <h4 className="text-xl font-bold mb-1">Ready to Practice?</h4>
            <p className="text-green-100 text-sm">Test your understanding with sample problems</p>
          </div>
          <button
            onClick={() => setMode('options')}
            className="bg-white text-green-600 px-6 py-3 rounded-xl font-bold hover:bg-green-50 transition-colors shadow-lg"
          >
            Start Practice →
          </button>
        </div>
      </div>
    );
  }

  // Practice View
  if (mode === 'practice' && practiceQuestions.length > 0) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => setMode('options')}
          className="text-purple-600 hover:text-purple-800 font-medium flex items-center gap-2 mb-2"
        >
          ← Back to Options
        </button>

        {/* Header Section */}
        <div className="bg-gradient-to-r from-green-600 to-emerald-500 p-8 rounded-2xl shadow-lg text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-white bg-opacity-20 p-3 rounded-xl">
                <Target size={32} className="text-white" />
              </div>
              <div>
                <h3 className="text-3xl font-bold">Practice Questions</h3>
                <p className="text-green-100 text-sm mt-1">{selectedTopic.name} • {practiceQuestions.length} Questions</p>
              </div>
            </div>
            <div className="bg-white bg-opacity-20 px-4 py-2 rounded-xl">
              <div className="text-2xl font-bold">{practiceQuestions.length}</div>
              <div className="text-xs text-green-100">Problems</div>
            </div>
          </div>
        </div>

        {/* Progress Indicator */}
        <div className="bg-white p-4 rounded-xl shadow-md border border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Practice Progress</span>
            <span className="text-sm font-bold text-green-600">{practiceQuestions.length} / {practiceQuestions.length}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-green-600 h-2 rounded-full" style={{width: '100%'}}></div>
          </div>
        </div>

        {/* Questions */}
        {practiceQuestions.map((question, index) => (
          <div key={index} className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl transition-shadow">
            {/* Question Header */}
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 border-b border-green-100">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="bg-green-600 text-white font-bold text-lg w-10 h-10 rounded-xl flex items-center justify-center">
                    {index + 1}
                  </div>
                  <h4 className="text-xl font-bold text-gray-800">Question {index + 1} of {practiceQuestions.length}</h4>
                </div>
                <span className={`px-4 py-2 rounded-xl text-sm font-bold shadow-sm ${
                  question.difficulty === 'easy' ? 'bg-green-100 text-green-700 border border-green-300' :
                  question.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700 border border-yellow-300' :
                  'bg-red-100 text-red-700 border border-red-300'
                }`}>
                  {question.difficulty?.toUpperCase() || 'MEDIUM'}
                </span>
              </div>
              <p className="text-gray-800 text-lg leading-relaxed">{question.question}</p>
            </div>

            {/* Options */}
            <div className="p-6">
              <h5 className="text-sm font-semibold text-gray-500 uppercase mb-3">Options:</h5>
              <div className="space-y-3 mb-6">
                {question.options && question.options.map((option, optIndex) => (
                  <div
                    key={optIndex}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      option === question.correct_answer
                        ? 'border-green-500 bg-green-50 shadow-md'
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                          option === question.correct_answer
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-300 text-gray-700'
                        }`}>
                          {String.fromCharCode(65 + optIndex)}
                        </div>
                        <span className="text-gray-800">{option}</span>
                      </div>
                      {option === question.correct_answer && (
                        <div className="flex items-center gap-2 bg-green-600 text-white px-3 py-1 rounded-full text-xs font-bold">
                          <CheckCircle size={16} />
                          Correct
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Solution Section */}
              <div className="space-y-4">
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-5 rounded-xl border-l-4 border-blue-500">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="bg-blue-600 p-1.5 rounded-lg">
                      <BookOpen size={16} className="text-white" />
                    </div>
                    <h5 className="text-sm font-bold text-blue-900 uppercase">Step-by-Step Solution</h5>
                  </div>
                  <div className="text-gray-700 leading-relaxed whitespace-pre-line bg-white p-4 rounded-lg">
                    {question.step_by_step_solution}
                  </div>
                </div>

                {question.tips_and_tricks && (
                  <div className="bg-gradient-to-r from-yellow-50 to-amber-50 p-5 rounded-xl border-l-4 border-yellow-500">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xl">💡</span>
                      <h5 className="text-sm font-bold text-yellow-900 uppercase">Quick Tip</h5>
                    </div>
                    <div className="text-gray-700 leading-relaxed bg-white p-4 rounded-lg">
                      {question.tips_and_tricks}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Take Test CTA */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 p-6 rounded-2xl shadow-lg text-white flex items-center justify-between">
          <div>
            <h4 className="text-xl font-bold mb-1">Feeling Confident?</h4>
            <p className="text-purple-100 text-sm">Take the full test with 50 questions and timer</p>
          </div>
          <button
            onClick={() => setMode('options')}
            className="bg-white text-purple-600 px-6 py-3 rounded-xl font-bold hover:bg-purple-50 transition-colors shadow-lg"
          >
            Take Test →
          </button>
        </div>
      </div>
    );
  }

  // Test View
  if (mode === 'test' && testQuestions.length > 0) {
    const currentQuestion = testQuestions[currentQuestionIndex];
    const answeredCount = Object.keys(userAnswers).length;
    const progressPercentage = (answeredCount / testQuestions.length) * 100;
    
    return (
      <div className="space-y-4">
        {/* Test Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 p-6 rounded-2xl shadow-lg text-white">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="bg-white bg-opacity-20 p-2 rounded-xl">
                <Trophy size={24} className="text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold">{selectedTopic.name} Test</h3>
                <p className="text-purple-100 text-sm">AI Proctored Assessment</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className={`flex items-center gap-2 px-5 py-3 rounded-xl shadow-lg font-bold text-lg ${
                timeRemaining < 300 ? 'bg-red-600 text-white animate-pulse' : 'bg-white bg-opacity-20 text-white'
              }`}>
                <Clock size={24} />
                <span>{formatTime(timeRemaining)}</span>
              </div>
              
              {cameraEnabled && (
                <div className="flex items-center gap-2 bg-green-500 px-4 py-3 rounded-xl shadow-lg">
                  <Camera size={20} />
                  <span className="text-sm font-bold">Monitoring</span>
                </div>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-purple-100">Question {currentQuestionIndex + 1} of {testQuestions.length}</span>
              <span className="font-bold">Answered: {answeredCount} / {testQuestions.length}</span>
            </div>
            <div className="w-full bg-white bg-opacity-20 rounded-full h-3">
              <div 
                className="bg-white h-3 rounded-full transition-all duration-300"
                style={{width: `${progressPercentage}%`}}
              ></div>
            </div>
          </div>
        </div>

        {/* Camera Feed (small preview) */}
        {cameraEnabled && (
          <div className="fixed bottom-4 right-4 w-48 h-36 rounded-lg overflow-hidden shadow-lg border-2 border-green-500 z-50">
            <video ref={videoRef} autoPlay muted className="w-full h-full object-cover" />
            <div className="absolute top-2 left-2 bg-red-600 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
              <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              REC
            </div>
          </div>
        )}

        {/* Question Card */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-6 border-b border-purple-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-purple-600 text-white font-bold text-lg w-12 h-12 rounded-xl flex items-center justify-center shadow-lg">
                {currentQuestionIndex + 1}
              </div>
              <div className="text-sm text-gray-600">of {testQuestions.length} questions</div>
            </div>
            <p className="text-gray-800 text-lg leading-relaxed">{currentQuestion.question}</p>
          </div>
          
          <div className="p-6">
            <h5 className="text-sm font-semibold text-gray-500 uppercase mb-4">Select your answer:</h5>
            <div className="space-y-3">
              {currentQuestion.options && currentQuestion.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleAnswerSelect(currentQuestionIndex, option)}
                  className={`w-full p-5 text-left rounded-xl border-2 transition-all group ${
                    userAnswers[currentQuestionIndex] === option
                      ? 'border-purple-500 bg-purple-50 shadow-md'
                      : 'border-gray-200 bg-white hover:border-purple-300 hover:bg-purple-50'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm transition-colors ${
                      userAnswers[currentQuestionIndex] === option
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-200 text-gray-700 group-hover:bg-purple-200'
                    }`}>
                      {String.fromCharCode(65 + index)}
                    </div>
                    <span className="text-gray-800 flex-1">{option}</span>
                    {userAnswers[currentQuestionIndex] === option && (
                      <CheckCircle size={24} className="text-purple-600" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between bg-white p-4 rounded-xl shadow-md">
          <button
            onClick={() => setCurrentQuestionIndex(prev => Math.max(0, prev - 1))}
            disabled={currentQuestionIndex === 0}
            className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          {currentQuestionIndex === testQuestions.length - 1 ? (
            <button
              onClick={handleSubmitTest}
              className="px-8 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
            >
              Submit Test
            </button>
          ) : (
            <button
              onClick={() => setCurrentQuestionIndex(prev => Math.min(testQuestions.length - 1, prev + 1))}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              Next
            </button>
          )}
        </div>

        {/* Question Grid */}
        <div className="bg-white p-4 rounded-xl shadow-md">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Question Navigator:</h4>
          <div className="grid grid-cols-10 gap-2">
            {testQuestions.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentQuestionIndex(index)}
                className={`w-10 h-10 rounded-lg font-medium text-sm ${
                  index === currentQuestionIndex
                    ? 'bg-purple-600 text-white'
                    : userAnswers[index]
                    ? 'bg-green-100 text-green-700 border-2 border-green-500'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {index + 1}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Results View
  if (mode === 'results' && testResults) {
    return (
      <div className="space-y-6">
        <h3 className="text-2xl font-bold text-gray-800">Test Results - {selectedTopic.name}</h3>

        {/* Score Card */}
        <div className="bg-gradient-to-r from-purple-500 to-blue-500 p-8 rounded-xl shadow-lg text-white">
          <div className="text-center">
            <div className="text-6xl font-bold mb-2">{testResults.score}%</div>
            <div className="text-xl mb-4">{testResults.performance.level}</div>
            <div className="text-lg opacity-90">{testResults.performance.message}</div>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow-md">
            <div className="text-gray-600 text-sm mb-1">Total Questions</div>
            <div className="text-2xl font-bold text-gray-800">{testResults.total_questions}</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg shadow-md border border-green-200">
            <div className="text-green-600 text-sm mb-1">Correct</div>
            <div className="text-2xl font-bold text-green-700">{testResults.correct_answers}</div>
          </div>
          <div className="bg-red-50 p-4 rounded-lg shadow-md border border-red-200">
            <div className="text-red-600 text-sm mb-1">Incorrect</div>
            <div className="text-2xl font-bold text-red-700">{testResults.incorrect_answers}</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg shadow-md border border-yellow-200">
            <div className="text-yellow-600 text-sm mb-1">Unanswered</div>
            <div className="text-2xl font-bold text-yellow-700">{testResults.unanswered}</div>
          </div>
        </div>

        {/* Recommendation */}
        <div className="bg-blue-50 p-6 rounded-xl border border-blue-200">
          <h4 className="font-bold text-blue-800 mb-2">💡 Recommendation</h4>
          <p className="text-blue-700">{testResults.performance.recommendation}</p>
        </div>

        {/* Detailed Results */}
        <div className="space-y-4">
          <h4 className="text-xl font-bold text-gray-800">Detailed Answer Review</h4>
          {testResults.results.map((result, index) => (
            <div
              key={index}
              className={`bg-white p-6 rounded-xl shadow-md border-l-4 ${
                result.status === 'correct'
                  ? 'border-green-500'
                  : result.status === 'incorrect'
                  ? 'border-red-500'
                  : 'border-yellow-500'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <h5 className="font-semibold text-gray-800">Question {result.question_number}</h5>
                <span className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-2 ${
                  result.status === 'correct'
                    ? 'bg-green-100 text-green-700'
                    : result.status === 'incorrect'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {result.status === 'correct' && <CheckCircle size={16} />}
                  {result.status === 'incorrect' && <XCircle size={16} />}
                  {result.status === 'unanswered' && <AlertCircle size={16} />}
                  {result.status.charAt(0).toUpperCase() + result.status.slice(1)}
                </span>
              </div>

              <p className="text-gray-700 mb-4">{result.question}</p>

              <div className="space-y-2 mb-4">
                {result.options && result.options.map((option, optIndex) => (
                  <div
                    key={optIndex}
                    className={`p-3 rounded-lg border-2 ${
                      option === result.correct_answer
                        ? 'border-green-500 bg-green-50'
                        : option === result.user_answer && result.status === 'incorrect'
                        ? 'border-red-500 bg-red-50'
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    {option}
                    {option === result.correct_answer && (
                      <CheckCircle size={18} className="inline ml-2 text-green-600" />
                    )}
                    {option === result.user_answer && result.status === 'incorrect' && (
                      <XCircle size={18} className="inline ml-2 text-red-600" />
                    )}
                  </div>
                ))}
              </div>

              {result.explanation && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-sm font-medium text-blue-600 mb-2">Explanation:</div>
                  <div className="text-gray-700">{result.explanation}</div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button
            onClick={() => setMode('select')}
            className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium"
          >
            Back to Topics
          </button>
          <button
            onClick={() => handleStartTest('medium')}
            className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium"
          >
            Retake Test
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center p-12">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  );
};

export default AptitudeTraining;
