import React, { useState, useEffect, useRef } from 'react';
import { Users, Mic, Video, Clock, Award, MessageCircle, X, Check, AlertCircle, Volume2, VolumeX } from 'lucide-react';

const GDRound = ({ gdRound, studentId, onClose, onComplete }) => {
  const [phase, setPhase] = useState('pre-start'); // pre-start, topic-selection, preparation, active, completed
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [topicSelectionTimer, setTopicSelectionTimer] = useState(30);
  const [preparationTimer, setPreparationTimer] = useState(180); // 3 minutes
  const [gdTimer, setGdTimer] = useState(gdRound?.duration * 60 || 1200); // Convert minutes to seconds
  const [isRecording, setIsRecording] = useState(false);
  const [userResponse, setUserResponse] = useState('');
  const [allResponses, setAllResponses] = useState([]);
  const [currentSpeaker, setCurrentSpeaker] = useState(null);
  const [aiAgents, setAiAgents] = useState([]);
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [micEnabled, setMicEnabled] = useState(false);
  const [volumeEnabled, setVolumeEnabled] = useState(true);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [recognitionActive, setRecognitionActive] = useState(false);
  
  const videoRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);
  const speakingTimeoutRef = useRef(null);
  
  // Initialize AI agents
  useEffect(() => {
    if (gdRound) {
      const numAgents = gdRound.num_ai_agents || 7;
      const agents = [];
      const personalities = ['analytical', 'creative', 'diplomatic', 'aggressive', 'supportive'];
      
      for (let i = 0; i < numAgents; i++) {
        const gender = gdRound.ai_agent_voices?.[i] || (Math.random() > 0.5 ? 'male' : 'female');
        agents.push({
          id: `ai_agent_${i + 1}`,
          name: `AI Agent ${i + 1}`,
          gender: gender,
          personality: personalities[i % personalities.length],
          hasSpoken: false,
          speakCount: 0
        });
      }
      
      setAiAgents(agents);
    }
  }, [gdRound]);
  
  // Handle phase timers
  useEffect(() => {
    let interval;
    
    if (phase === 'topic-selection' && topicSelectionTimer > 0) {
      interval = setInterval(() => {
        setTopicSelectionTimer(prev => {
          if (prev <= 1) {
            // Auto-select first topic if time runs out
            if (!selectedTopic && gdRound.available_topics?.length > 0) {
              setSelectedTopic(gdRound.available_topics[0]);
            }
            setPhase('preparation');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    if (phase === 'preparation' && preparationTimer > 0) {
      interval = setInterval(() => {
        setPreparationTimer(prev => {
          if (prev <= 1) {
            setPhase('active');
            startGDRound();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    if (phase === 'active' && gdTimer > 0) {
      interval = setInterval(() => {
        setGdTimer(prev => {
          if (prev <= 1) {
            endGDRound();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    return () => clearInterval(interval);
  }, [phase, topicSelectionTimer, preparationTimer, gdTimer]);
  
  // Initialize camera and microphone
  const initializeMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      
      mediaStreamRef.current = stream;
      setCameraEnabled(true);
      setMicEnabled(true);
    } catch (error) {
      console.error('Error accessing media devices:', error);
      alert('Please allow camera and microphone access to participate in the GD round.');
    }
  };
  
  // Initialize speech recognition
  const initializeSpeechRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      
      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        
        if (finalTranscript) {
          setUserResponse(prev => prev + ' ' + finalTranscript);
        }
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setRecognitionActive(false);
      };
      
      recognitionRef.current.onend = () => {
        setRecognitionActive(false);
      };
    }
  };
  
  const handleStartGD = () => {
    if (gdRound.allow_topic_selection) {
      setPhase('topic-selection');
    } else {
      setSelectedTopic(gdRound.topic);
      setPhase('preparation');
    }
    initializeMedia();
    initializeSpeechRecognition();
  };
  
  const handleTopicSelection = (topic) => {
    setSelectedTopic(topic);
    setPhase('preparation');
  };
  
  const startGDRound = () => {
    // Start with random AI agent or user
    const shouldUserStart = Math.random() > 0.5;
    
    if (shouldUserStart) {
      setCurrentSpeaker('user');
      startUserSpeaking();
    } else {
      scheduleNextSpeaker();
    }
  };
  
  const startUserSpeaking = () => {
    setCurrentSpeaker('user');
    setIsRecording(true);
    
    if (recognitionRef.current && micEnabled && !recognitionActive) {
      try {
        recognitionRef.current.start();
        setRecognitionActive(true);
      } catch (error) {
        console.error('Error starting speech recognition:', error);
      }
    }
    
    // User has 30-60 seconds to speak
    const speakingTime = 30000 + Math.random() * 30000; // 30-60 seconds
    
    speakingTimeoutRef.current = setTimeout(() => {
      stopUserSpeaking();
    }, speakingTime);
  };
  
  const stopUserSpeaking = () => {
    setIsRecording(false);
    
    if (recognitionRef.current && recognitionActive) {
      try {
        recognitionRef.current.stop();
        setRecognitionActive(false);
      } catch (error) {
        console.error('Error stopping speech recognition:', error);
      }
    }
    
    if (userResponse.trim()) {
      const response = {
        participant: 'user',
        name: 'You',
        text: userResponse,
        timestamp: new Date().toISOString()
      };
      
      setAllResponses(prev => [...prev, response]);
      setUserResponse('');
    }
    
    setCurrentSpeaker(null);
    
    // Schedule next speaker after 2 seconds
    setTimeout(() => {
      scheduleNextSpeaker();
    }, 2000);
  };
  
  const scheduleNextSpeaker = () => {
    if (gdTimer <= 0) {
      endGDRound();
      return;
    }
    
    // 40% chance user speaks, 60% chance AI agent speaks
    const shouldUserSpeak = Math.random() < 0.4;
    
    if (shouldUserSpeak) {
      startUserSpeaking();
    } else {
      speakAIAgent();
    }
  };
  
  const speakAIAgent = () => {
    // Select AI agent that has spoken least
    const sortedAgents = [...aiAgents].sort((a, b) => a.speakCount - b.speakCount);
    const agent = sortedAgents[Math.floor(Math.random() * Math.min(3, sortedAgents.length))];
    
    setCurrentSpeaker(agent.id);
    
    // Generate AI response (in production, call backend API)
    const aiResponse = generateAIResponse(agent);
    
    // Update agent speak count
    setAiAgents(prev => prev.map(a => 
      a.id === agent.id ? { ...a, speakCount: a.speakCount + 1, hasSpoken: true } : a
    ));
    
    const response = {
      participant: agent.id,
      name: agent.name,
      text: aiResponse,
      timestamp: new Date().toISOString()
    };
    
    setAllResponses(prev => [...prev, response]);
    
    // Speak using text-to-speech
    if (volumeEnabled) {
      speakText(aiResponse, agent.gender);
    }
    
    // AI speaks for 15-30 seconds
    const speakingTime = 15000 + Math.random() * 15000;
    
    setTimeout(() => {
      setCurrentSpeaker(null);
      
      // Schedule next speaker after 2 seconds
      setTimeout(() => {
        scheduleNextSpeaker();
      }, 2000);
    }, speakingTime);
  };
  
  const generateAIResponse = (agent) => {
    // Mock AI responses - in production, call backend API
    const responses = {
      analytical: [
        `Looking at ${selectedTopic} from a data perspective, research shows significant trends we should consider.`,
        `The empirical evidence regarding ${selectedTopic} suggests we need a systematic approach.`,
        `Statistical analysis reveals interesting patterns in ${selectedTopic} that warrant discussion.`
      ],
      creative: [
        `What if we approached ${selectedTopic} from a completely different angle?`,
        `I think ${selectedTopic} presents a unique opportunity for innovation.`,
        `Let me share an unconventional perspective on ${selectedTopic}.`
      ],
      diplomatic: [
        `I appreciate the various viewpoints on ${selectedTopic}. Perhaps we can find common ground.`,
        `While there are different opinions, I believe both sides have merit regarding ${selectedTopic}.`,
        `Considering all perspectives, we might reach a balanced conclusion on ${selectedTopic}.`
      ],
      aggressive: [
        `I strongly believe that ${selectedTopic} requires immediate and decisive action.`,
        `The facts clearly support a particular stance on ${selectedTopic}.`,
        `Let's be honest about ${selectedTopic} - the evidence is compelling.`
      ],
      supportive: [
        `That's an excellent point. Let me build on that regarding ${selectedTopic}.`,
        `I agree with the previous observation and would like to add something about ${selectedTopic}.`,
        `Great insights. This reminds me of related aspects of ${selectedTopic}.`
      ]
    };
    
    const personalityResponses = responses[agent.personality] || responses.analytical;
    return personalityResponses[Math.floor(Math.random() * personalityResponses.length)];
  };
  
  const speakText = (text, gender) => {
    if (!synthRef.current) return;
    
    const utterance = new SpeechSynthesisUtterance(text);
    const voices = synthRef.current.getVoices();
    
    // Select voice based on gender
    const voice = voices.find(v => 
      gender === 'female' 
        ? v.name.includes('female') || v.name.includes('Female') || v.name.includes('Zira')
        : v.name.includes('male') || v.name.includes('Male') || v.name.includes('David')
    );
    
    if (voice) {
      utterance.voice = voice;
    }
    
    utterance.rate = 1.0;
    utterance.pitch = gender === 'female' ? 1.1 : 0.9;
    
    synthRef.current.speak(utterance);
  };
  
  const endGDRound = async () => {
    setPhase('evaluating');
    setLoading(true);
    
    // Stop all media
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
    }
    
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    
    // Call backend to evaluate
    try {
      const response = await fetch(`http://localhost:5000/api/gd/round/${gdRound._id}/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          responses: allResponses,
          evaluation_criteria: gdRound.evaluation_criteria,
          num_ai_agents: aiAgents.length
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setResults(data.results);
        setPhase('completed');
      }
    } catch (error) {
      console.error('Error evaluating GD:', error);
      alert('Error evaluating GD round. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const toggleCamera = () => {
    if (mediaStreamRef.current) {
      const videoTrack = mediaStreamRef.current.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setCameraEnabled(videoTrack.enabled);
      }
    }
  };
  
  const toggleMic = () => {
    if (mediaStreamRef.current) {
      const audioTrack = mediaStreamRef.current.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setMicEnabled(audioTrack.enabled);
      }
    }
  };
  
  const toggleVolume = () => {
    setVolumeEnabled(prev => !prev);
    if (synthRef.current) {
      synthRef.current.cancel();
    }
  };
  
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  const handleForceSubmit = () => {
    if (window.confirm('Are you sure you want to end the GD round early?')) {
      if (isRecording) {
        stopUserSpeaking();
      }
      endGDRound();
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Users className="h-6 w-6" />
              AI-Based Group Discussion
            </h2>
            <p className="text-blue-100 mt-1">
              {selectedTopic || 'Preparing for Group Discussion...'}
            </p>
          </div>
          <button onClick={onClose} className="hover:bg-white/20 p-2 rounded-lg transition">
            <X className="h-6 w-6" />
          </button>
        </div>
        
        {/* Pre-start Phase */}
        {phase === 'pre-start' && (
          <div className="p-8 text-center">
            <Users className="h-16 w-16 text-blue-600 mx-auto mb-4" />
            <h3 className="text-2xl font-bold mb-4">Welcome to AI-Based GD Round</h3>
            <div className="bg-blue-50 p-6 rounded-lg mb-6 text-left max-w-2xl mx-auto">
              <h4 className="font-bold mb-3 flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-blue-600" />
                Round Details:
              </h4>
              <ul className="space-y-2 text-gray-700">
                <li>• Duration: {gdRound?.duration || 20} minutes</li>
                <li>• AI Competitors: {gdRound?.num_ai_agents || 7} AI agents</li>
                <li>• Topic: {gdRound?.allow_topic_selection ? 'You can select' : gdRound?.topic}</li>
                <li>• Camera and microphone access required</li>
                <li>• Your performance will be evaluated on multiple criteria</li>
              </ul>
            </div>
            <button
              onClick={handleStartGD}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition flex items-center gap-2 mx-auto"
            >
              <Check className="h-5 w-5" />
              Start GD Round
            </button>
          </div>
        )}
        
        {/* Topic Selection Phase */}
        {phase === 'topic-selection' && (
          <div className="p-8">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold mb-2">Select Your Topic</h3>
              <p className="text-gray-600">Time remaining: <span className="font-bold text-red-600">{topicSelectionTimer}s</span></p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
              {gdRound?.available_topics?.map((topic, index) => (
                <button
                  key={index}
                  onClick={() => handleTopicSelection(topic)}
                  className={`p-4 rounded-lg border-2 transition text-left ${
                    selectedTopic === topic
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-400 hover:bg-blue-50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`mt-1 h-5 w-5 rounded-full border-2 flex items-center justify-center ${
                      selectedTopic === topic ? 'border-blue-600 bg-blue-600' : 'border-gray-300'
                    }`}>
                      {selectedTopic === topic && <Check className="h-3 w-3 text-white" />}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{topic}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Preparation Phase */}
        {phase === 'preparation' && (
          <div className="p-8 text-center">
            <Clock className="h-16 w-16 text-orange-600 mx-auto mb-4 animate-pulse" />
            <h3 className="text-2xl font-bold mb-2">Preparation Time</h3>
            <p className="text-gray-600 mb-4">Think about your points on the topic</p>
            <div className="text-6xl font-bold text-orange-600 mb-6">{formatTime(preparationTimer)}</div>
            <div className="bg-orange-50 p-6 rounded-lg max-w-2xl mx-auto">
              <h4 className="font-bold mb-3">Topic:</h4>
              <p className="text-xl text-gray-800">{selectedTopic}</p>
            </div>
          </div>
        )}
        
        {/* Active GD Phase */}
        {phase === 'active' && (
          <div className="p-6">
            {/* Timer and Controls */}
            <div className="flex justify-between items-center mb-6 bg-gray-100 p-4 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="text-2xl font-bold text-red-600 flex items-center gap-2">
                  <Clock className="h-6 w-6" />
                  {formatTime(gdTimer)}
                </div>
                <div className="text-sm text-gray-600">
                  Responses: {allResponses.length}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={toggleCamera}
                  className={`p-2 rounded-lg transition ${cameraEnabled ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'}`}
                  title={cameraEnabled ? 'Turn off camera' : 'Turn on camera'}
                >
                  <Video className="h-5 w-5" />
                </button>
                <button
                  onClick={toggleMic}
                  className={`p-2 rounded-lg transition ${micEnabled ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'}`}
                  title={micEnabled ? 'Mute microphone' : 'Unmute microphone'}
                >
                  <Mic className="h-5 w-5" />
                </button>
                <button
                  onClick={toggleVolume}
                  className={`p-2 rounded-lg transition ${volumeEnabled ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'}`}
                  title={volumeEnabled ? 'Mute AI voices' : 'Unmute AI voices'}
                >
                  {volumeEnabled ? <Volume2 className="h-5 w-5" /> : <VolumeX className="h-5 w-5" />}
                </button>
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Video Section */}
              <div className="lg:col-span-2">
                <div className="bg-gray-900 rounded-lg overflow-hidden aspect-video mb-4">
                  <video
                    ref={videoRef}
                    autoPlay
                    muted
                    className="w-full h-full object-cover"
                  />
                </div>
                
                {/* Current Speaker Indicator */}
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-bold mb-2 flex items-center gap-2">
                    <MessageCircle className="h-5 w-5 text-blue-600" />
                    Current Speaker:
                  </h4>
                  {currentSpeaker === 'user' ? (
                    <div className="flex items-center gap-3">
                      <div className="h-3 w-3 bg-red-600 rounded-full animate-pulse"></div>
                      <span className="font-medium">You are speaking...</span>
                      {isRecording && <span className="text-sm text-gray-600">(Recording)</span>}
                    </div>
                  ) : currentSpeaker ? (
                    <div className="flex items-center gap-3">
                      <div className="h-3 w-3 bg-green-600 rounded-full animate-pulse"></div>
                      <span className="font-medium">
                        {aiAgents.find(a => a.id === currentSpeaker)?.name}
                      </span>
                    </div>
                  ) : (
                    <span className="text-gray-600">Waiting for next speaker...</span>
                  )}
                </div>
                
                {/* User Response Input (when speaking) */}
                {currentSpeaker === 'user' && (
                  <div className="mt-4 bg-white p-4 rounded-lg border-2 border-blue-600">
                    <label className="block text-sm font-medium mb-2">Your Response:</label>
                    <textarea
                      value={userResponse}
                      onChange={(e) => setUserResponse(e.target.value)}
                      className="w-full p-3 border rounded-lg"
                      rows="3"
                      placeholder="Speak or type your response..."
                    />
                    <button
                      onClick={stopUserSpeaking}
                      className="mt-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition"
                    >
                      Stop Speaking
                    </button>
                  </div>
                )}
              </div>
              
              {/* Participants Panel */}
              <div>
                <div className="bg-white rounded-lg border p-4 max-h-[600px] overflow-y-auto">
                  <h4 className="font-bold mb-4 flex items-center gap-2">
                    <Users className="h-5 w-5 text-blue-600" />
                    Participants
                  </h4>
                  
                  {/* User */}
                  <div className={`p-3 rounded-lg mb-2 ${currentSpeaker === 'user' ? 'bg-blue-100 border-2 border-blue-600' : 'bg-gray-50'}`}>
                    <div className="flex items-center gap-2">
                      <div className="h-8 w-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                        Y
                      </div>
                      <div>
                        <p className="font-medium">You</p>
                        <p className="text-xs text-gray-600">Student</p>
                      </div>
                    </div>
                  </div>
                  
                  {/* AI Agents */}
                  {aiAgents.map((agent, index) => (
                    <div
                      key={agent.id}
                      className={`p-3 rounded-lg mb-2 ${currentSpeaker === agent.id ? 'bg-green-100 border-2 border-green-600' : 'bg-gray-50'}`}
                    >
                      <div className="flex items-center gap-2">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center text-white font-bold ${
                          agent.gender === 'female' ? 'bg-pink-500' : 'bg-indigo-500'
                        }`}>
                          A{index + 1}
                        </div>
                        <div>
                          <p className="font-medium">{agent.name}</p>
                          <p className="text-xs text-gray-600 capitalize">{agent.personality}</p>
                        </div>
                        {agent.hasSpoken && (
                          <Check className="h-4 w-4 text-green-600 ml-auto" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                
                <button
                  onClick={handleForceSubmit}
                  className="w-full mt-4 bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition"
                >
                  End GD Early
                </button>
              </div>
            </div>
            
            {/* Recent Responses */}
            <div className="mt-6 bg-gray-50 p-4 rounded-lg">
              <h4 className="font-bold mb-3">Recent Discussion Points:</h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {allResponses.slice(-5).reverse().map((response, index) => (
                  <div key={index} className="bg-white p-3 rounded-lg border">
                    <p className="text-sm font-medium text-blue-600">{response.name}</p>
                    <p className="text-sm text-gray-700 mt-1">{response.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {/* Evaluating Phase */}
        {phase === 'evaluating' && (
          <div className="p-8 text-center">
            <div className="animate-spin h-16 w-16 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <h3 className="text-2xl font-bold mb-2">Evaluating Performance...</h3>
            <p className="text-gray-600">AI is analyzing the discussion and calculating results</p>
          </div>
        )}
        
        {/* Results Phase */}
        {phase === 'completed' && results && (
          <div className="p-8">
            <div className="text-center mb-8">
              <Award className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
              <h3 className="text-3xl font-bold mb-2">GD Round Completed!</h3>
              <p className="text-gray-600">Here are your results</p>
            </div>
            
            {/* Your Rank */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg mb-6 max-w-2xl mx-auto">
              <h4 className="text-xl font-bold mb-2">Your Rank</h4>
              <div className="text-6xl font-bold">#{results.student_rank}</div>
              <p className="mt-2 opacity-90">out of {results.all_participants.length} participants</p>
            </div>
            
            {/* Top 3 Performers */}
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-center">Top 3 Performers</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
                {results.top_3.map((participant, index) => (
                  <div
                    key={participant.id}
                    className={`p-6 rounded-lg border-2 text-center ${
                      participant.type === 'student'
                        ? 'border-blue-600 bg-blue-50'
                        : 'border-gray-300 bg-white'
                    }`}
                  >
                    <div className={`text-4xl font-bold mb-2 ${
                      index === 0 ? 'text-yellow-500' : index === 1 ? 'text-gray-400' : 'text-orange-600'
                    }`}>
                      #{index + 1}
                    </div>
                    <p className="font-bold text-lg mb-1">{participant.name}</p>
                    <p className="text-sm text-gray-600 mb-3">{participant.type === 'student' ? 'You' : 'AI Agent'}</p>
                    <div className="text-2xl font-bold text-blue-600">{participant.total_score.toFixed(2)}</div>
                    <p className="text-sm text-gray-600">Total Score</p>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Your Detailed Scores */}
            <div className="max-w-3xl mx-auto">
              <h4 className="text-xl font-bold mb-4">Your Detailed Performance</h4>
              <div className="bg-white rounded-lg border p-6">
                {Object.entries(results.all_participants.find(p => p.type === 'student').scores).map(([criterion, data]) => (
                  <div key={criterion} className="mb-4 last:mb-0">
                    <div className="flex justify-between mb-2">
                      <span className="font-medium capitalize">{criterion.replace(/_/g, ' ')}</span>
                      <span className="font-bold text-blue-600">{data.score}/100</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-blue-600 h-3 rounded-full transition-all"
                        style={{ width: `${data.score}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">Weight: {data.weight}%</p>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="text-center mt-8">
              <button
                onClick={() => {
                  onComplete(results);
                  onClose();
                }}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition"
              >
                Complete & Return to Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GDRound;
