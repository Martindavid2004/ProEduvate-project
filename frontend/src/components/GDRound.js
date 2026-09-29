import React, { useState, useEffect, useRef } from 'react';
import { Users, Mic, Video, Clock, Award, MessageCircle, X, Check, AlertCircle, Volume2, VolumeX, WifiOff, Loader2, MicOff } from 'lucide-react';
import { gdAPI } from '../services/api';

// Canonical sentence the AI agent says when the participant's latest statement
// is unrelated to the topic. Must match backend GDService.OFF_TOPIC_REPLY.
const OFF_TOPIC_SENTENCE = 'This is not related to the topic. Please speak points related to the topic.';

const GDRound = ({ gdRound, studentId, onClose, onComplete }) => {
  const [phase, setPhase] = useState('pre-start');
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [topicSelectionTimer, setTopicSelectionTimer] = useState(30);
  const [preparationTimer, setPreparationTimer] = useState(60);
  const [gdTimer, setGdTimer] = useState(gdRound?.duration * 60 || 1200);
  const [isRecording, setIsRecording] = useState(false);
  const [userResponse, setUserResponse] = useState('');
  const [allResponses, setAllResponses] = useState([]);
  const [currentSpeaker, setCurrentSpeaker] = useState(null);
  const [aiAgents, setAiAgents] = useState([]);
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [micEnabled, setMicEnabled] = useState(false);
  const [volumeEnabled, setVolumeEnabled] = useState(true);
  const [results, setResults] = useState(null);
  // STT States: 'IDLE' | 'LISTENING' | 'PROCESSING' | 'SUCCESS' | 'ERROR' | 'FALLBACK' | 'WAITING_USER_RETRY'
  const [sttState, setSttState] = useState('IDLE');
  // STT Engine Modes: 'browser' (Web Speech API) | 'whisper' (MediaRecorder + faster-whisper fallback)
  const [sttMode, setSttMode] = useState('browser');
  const [sttError, setSttError] = useState(null);
  const [aiUnavailable, setAiUnavailable] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');

  // eslint-disable-next-line no-unused-vars
  const [loading, setLoading] = useState(false);
  const [recognitionActive, setRecognitionActive] = useState(false);
  const [isGeneratingAIResponse, setIsGeneratingAIResponse] = useState(false);


  const videoRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioStreamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);
  const speakingTimeoutRef = useRef(null);
  const aiSpeakingTimeoutRef = useRef(null);
  const nextSpeakerTimerRef = useRef(null);
  const ttsFallbackTimerRef = useRef(null);

  // Refs mirroring state so timer callbacks never read stale values
  const userResponseRef = useRef('');
  const finalTranscriptRef = useRef('');
  const browserSTTFailedRef = useRef(false);
  const browserNetworkRetryRef = useRef(0);
  const mediaRecorderRef = useRef(null);
  const recognitionActiveRef = useRef(false);
  const sttStateRef = useRef('IDLE');
  const sttModeRef = useRef('browser');
  const gdTimerRef = useRef(gdRound?.duration * 60 || 1200);
  const allResponsesRef = useRef([]);
  const aiAgentsRef = useRef([]);
  const transcribeDoneRef = useRef(null);
  const turnEpochRef = useRef(0);
  const currentSpeakerRef = useRef(null);
  const micEnabledRef = useRef(false);
  const volumeEnabledRef = useRef(true);
  const selectedMimeTypeRef = useRef('');

  // ---- Authoritative turn state machine ----
  // User turn : IDLE -> RECORDING_USER -> PROCESSING_STT -> (transcript) -> IDLE
  // AI turn   : IDLE -> PROCESSING_AI -> PLAYING_TTS -> IDLE
  // Only ONE turn (user or AI) may be active at a time. startUserSpeaking()
  // may ONLY begin from 'IDLE'; any other state logs DUPLICATE_START_BLOCKED.
  const turnStateRef = useRef('IDLE');
  const activeTurnIdRef = useRef(0);
  const gdRoundStartedRef = useRef(false);
  const roundEndedRef = useRef(false);
  // Empty-transcript retry budget: consecutive failed attempts before the
  // system releases the floor instead of looping empty->retry forever.
  const MAX_EMPTY_RETRIES = 3;
  const userRetryCountRef = useRef(0);
  // Off-topic intervention budget: after an off-topic reply, the floor is
  // handed BACK to the speaker so they can continue with topic points.
  // Capped so an off-topic -> intervention -> off-topic loop cannot continue
  // forever; after MAX consecutive interventions the discussion moves on.
  const MAX_OFF_TOPIC_INTERVENTIONS = 3;
  const offTopicInterventionsRef = useRef(0);
  const [offTopicHint, setOffTopicHint] = useState(false);

  // ---- Microphone state ----
  // IMPORTANT: the previous "mic health / conflict detection" layer (silence
  // watchdog + track.mute/ended banner) blamed Google Meet/Zoom/Teams for the
  // mic failing even when getUserMedia succeeded and the track was live — a
  // 20 s quiet period or a benign track.muted event was treated as "another
  // app holds the mic". That false banner is REMOVED. The UI now only shows
  // an error when the browser microphone API actually fails, and shows the
  // REAL error (NotAllowedError / NotFoundError / NotReadableError / etc.).
  const [micIssue, setMicIssue] = useState(null);
  const micRecoveringRef = useRef(false);
  // Mic device selection: the user-chosen deviceId is stored in a ref (never
  // hardcoded). If that device disappears, getUserMedia falls back to the
  // default microphone instead of failing the GD.
  const selectedMicDeviceIdRef = useRef('');
  const micAcquirePromiseRef = useRef(null); // in-flight acquisition promise (awaitable)

  // Track turn metadata for speaker-aware flow: who spoke last, so agents can
  // respond to another AGENT instead of always addressing the user.
  const previousSpeakerRef = useRef(null);      // { id, name, type: 'user'|'agent' }
  const [micDevices, setMicDevices] = useState([]);       // available inputs
  const [selectedMicDeviceId, setSelectedMicDeviceId] = useState('');
  // Turn IDs whose user response was already added/submitted - prevents the
  // same transcript being stored twice (e.g. a late Whisper result re-entering
  // the submit flow for a turn that already completed).
  const submittedTurnIdsRef = useRef(new Set());

  useEffect(() => { userResponseRef.current = userResponse; }, [userResponse]);
  useEffect(() => { micEnabledRef.current = micEnabled; }, [micEnabled]);
  useEffect(() => { selectedMicDeviceIdRef.current = selectedMicDeviceId; }, [selectedMicDeviceId]);
  useEffect(() => { volumeEnabledRef.current = volumeEnabled; }, [volumeEnabled]);
  useEffect(() => { recognitionActiveRef.current = recognitionActive; }, [recognitionActive]);
  useEffect(() => { sttStateRef.current = sttState; }, [sttState]);
  useEffect(() => { sttModeRef.current = sttMode; }, [sttMode]);
  useEffect(() => { gdTimerRef.current = gdTimer; }, [gdTimer]);
  useEffect(() => { allResponsesRef.current = allResponses; }, [allResponses]);
  useEffect(() => { aiAgentsRef.current = aiAgents; }, [aiAgents]);
  useEffect(() => { currentSpeakerRef.current = currentSpeaker; }, [currentSpeaker]);

  // Completely release and stop all microphone, camera, and recognition resources
  const stopAllMediaTracks = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop(); } catch (e) {}
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => {
        try { track.stop(); } catch (e) {}
      });
      mediaStreamRef.current = null;
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => {
        try { track.stop(); } catch (e) {}
      });
      audioStreamRef.current = null;
    }
    mediaRecorderRef.current = null;
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }
    setRecognitionActive(false);
    recognitionActiveRef.current = false;
    setIsRecording(false);
    console.log('[Mic] Stream released');
  };

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
          gender,
          personality: personalities[i % personalities.length],
          hasSpoken: false,
          speakCount: 0
        });
      }
      setAiAgents(agents);
    }
  }, [gdRound]);

  // Handle phase timers — the setState updaters MUST stay pure. React
  // StrictMode double-invokes updater functions in development, so any side
  // effect inside them (startGDRound, endGDRound, setSelectedTopic) ran
  // TWICE — that was the root cause of the duplicate round start and the
  // "Turn already in progress" log. Timers only tick numbers down here;
  // transitions fire from the dedicated effects below.
  useEffect(() => {
    let interval;
    if (phase === 'topic-selection' && topicSelectionTimer > 0) {
      interval = setInterval(() => {
        setTopicSelectionTimer(prev => (prev <= 1 ? 0 : prev - 1));
      }, 1000);
    }
    if (phase === 'preparation' && preparationTimer > 0) {
      interval = setInterval(() => {
        setPreparationTimer(prev => (prev <= 1 ? 0 : prev - 1));
      }, 1000);
    }
    if (phase === 'active' && gdTimer > 0) {
      interval = setInterval(() => {
        setGdTimer(prev => (prev <= 1 ? 0 : prev - 1));
      }, 1000);
    }
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, topicSelectionTimer, preparationTimer, gdTimer]);

  // Phase transitions - fire exactly once per state change, in effect scope
  // (never inside a setState updater). startGDRound/endGDRound carry their
  // own once-guards as a second line of defense.
  useEffect(() => {
    if (phase === 'topic-selection' && topicSelectionTimer === 0) {
      if (!selectedTopic && gdRound?.available_topics?.length > 0) {
        const autoTopic = gdRound.available_topics[0];
        setSelectedTopic(autoTopic);
        // Persist the auto-selected topic to the backend (same as a manual
        // selection). Without this the round is evaluated with topic: null,
        // the LLM judges the speech against "None" and every criterion
        // scores 0 with "evidence: none" - the static/zero-score bug.
        if (gdRound?._id && !gdRound._id.startsWith('practice_')) {
          gdAPI.selectTopic(gdRound._id, autoTopic).catch(err =>
            console.error('Error persisting auto-selected topic:', err));
        }
      }
      setPhase('preparation');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, topicSelectionTimer]);

  useEffect(() => {
    if (phase === 'preparation' && preparationTimer === 0) {
      setPhase('active');
      startGDRound();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, preparationTimer]);

  useEffect(() => {
    if (phase === 'active' && gdTimer === 0) {
      endGDRound();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, gdTimer]);

  // Cleanup on unmount
  useEffect(() => {
    // Capture ref values at effect time for use in cleanup
    const synth = synthRef.current;
    return () => {
      stopAllMediaTracks();
      if (speakingTimeoutRef.current) clearTimeout(speakingTimeoutRef.current);
      if (aiSpeakingTimeoutRef.current) clearTimeout(aiSpeakingTimeoutRef.current);
      if (nextSpeakerTimerRef.current) clearTimeout(nextSpeakerTimerRef.current);
      if (ttsFallbackTimerRef.current) clearTimeout(ttsFallbackTimerRef.current);
      if (synth) synth.cancel();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- MediaRecorder lifecycle (a FRESH recorder per speaking turn) ----
  // Chrome throws NotSupportedError ("There was an error starting the
  // MediaRecorder") when a stopped recorder instance is started again, so we
  // never reuse an instance across turns: every turn gets a brand-new one.

  const handleRecorderStop = async (recorder, mimeUsed) => {
    console.log(`[TURN ${activeTurnIdRef.current}] RECORDER_ONSTOP`);
    try {
      const chunks = [...audioChunksRef.current];
      audioChunksRef.current = [];
      console.log(`[TURN ${activeTurnIdRef.current}] chunks: ${chunks.length}`);

      // ONLY invoke Whisper fallback if:
      // 1. Fallback mode is active (browser STT failed/unavailable), OR
      // 2. Browser STT didn't produce usable final text despite user speaking
      const browserSTTSuccess =
        sttModeRef.current === 'browser' &&
        !browserSTTFailedRef.current &&
        finalTranscriptRef.current.trim().length > 0;

      if (!browserSTTSuccess) {
        if (chunks.length > 0) {
          const mime = (recorder && recorder.mimeType) || mimeUsed || 'audio/webm';
          const audioBlob = new Blob(chunks, { type: mime });
          console.log(`[Mic] Recording stopped`);
          console.log(`[Mic] Audio blob created: ${audioBlob.size} bytes (${audioBlob.type})`);
          console.log(`[TURN ${activeTurnIdRef.current}] audio blob: ${audioBlob.size} bytes (${audioBlob.type})`);
          console.log(`[TURN ${activeTurnIdRef.current}] STT_STARTED -> POST /api/gd/transcribe`);
          await transcribeAudioBlob(audioBlob);
        } else {
          console.warn('[GD-MIC] No audio chunks captured - empty recording');
          console.warn('[STT] No audio chunks available in MediaRecorder for transcription');
        }
      } else {
        console.log('[STT] Skipped Whisper fallback because browser STT succeeded with text:', finalTranscriptRef.current.trim());
      }
    } finally {
      if (transcribeDoneRef.current) {
        const done = transcribeDoneRef.current;
        transcribeDoneRef.current = null;
        done();
      }
    }
  };

  const createRecorder = (mimeUsed) => {
    let recorder = null;
    // Higher Opus bitrate (~96 kbps) preserves consonants ('t'/'d', 's'/'sh')
    // that lower default bitrates smear - a direct input to Whisper accuracy.
    const recorderOptions = mimeUsed ? { mimeType: mimeUsed, audioBitsPerSecond: 96000 } : { audioBitsPerSecond: 96000 };
    try {
      recorder = new MediaRecorder(audioStreamRef.current, recorderOptions);
    } catch (recErr) {
      console.warn('[Mic] MediaRecorder with custom mimeType failed, trying default:', recErr);
      try {
        recorder = new MediaRecorder(audioStreamRef.current);
      } catch (recErr2) {
        console.error('[Mic] MediaRecorder initialization failed:', recErr2);
        return null;
      }
    }
    console.log('[Mic] MediaRecorder created', { state: recorder.state, mimeType: recorder.mimeType });

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        audioChunksRef.current.push(e.data);
      }
    };
    recorder.onstop = () => handleRecorderStop(recorder, mimeUsed);
    recorder.onerror = (event) => {
      console.error('MediaRecorder error:', event.error);
      setSttState('ERROR');
      setSttError('Microphone recording error occurred. Please type manually.');
    };
    return recorder;
  };

  const ensureRecorderStarted = () => {
    if (!window.MediaRecorder || !audioStreamRef.current) {
      console.warn('[STT] MediaRecorder unavailable for Whisper fallback:', mediaRecorderRef.current ? mediaRecorderRef.current.state : 'null');
      return false;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      console.log(`[TURN ${activeTurnIdRef.current}] MediaRecorder already recording for this turn - Whisper will transcribe THE SAME recording when you finish speaking (no second recorder, no second turn).`);
      return true;
    }
    try {
      audioChunksRef.current = [];
      const recorder = createRecorder(selectedMimeTypeRef.current || '');
      if (!recorder) {
        setSttError('Audio recording unavailable. Please type your response manually.');
        return false;
      }
      mediaRecorderRef.current = recorder;
      recorder.start(250);
      console.log('[Mic] Recording started, state:', recorder.state);
      console.log('[STT] MediaRecorder started, state:', recorder.state);
      return true;
    } catch (error) {
      console.warn('[STT] MediaRecorder start failed:', error);
      setSttError('Audio recording unavailable. Please type your response manually.');
      return false;
    }
  };

  // ---- Microphone stream acquisition ----

  // Acquire a fresh microphone stream. The REAL browser error is surfaced
  // (never guessed): permission denied, no device, device busy, bad device
  // selection etc. map 1:1 to their DOMException names.
  const acquireMicStream = async () => {
    console.log('[Mic] Requesting getUserMedia');
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('This browser does not expose navigator.mediaDevices.getUserMedia. Use HTTPS or localhost.');
      }
      if (selectedMicDeviceIdRef.current) {
        console.log(`[Mic] Selected device: ${selectedMicDeviceIdRef.current}`);
        try {
          return await navigator.mediaDevices.getUserMedia({
            audio: { deviceId: { ideal: selectedMicDeviceIdRef.current } },
          });
        } catch (deviceErr) {
          // The specifically selected device failed (vanished / unsupported
          // constraints): log the REAL error, then fall back to the default mic.
          console.log('[Mic] getUserMedia failed');
          console.log(`[Mic] Error name: ${deviceErr?.name}`);
          console.log(`[Mic] Error message: ${deviceErr?.message || deviceErr}`);
          if (deviceErr?.name === 'OverconstrainedError' || deviceErr?.name === 'NotFoundError') {
            selectedMicDeviceIdRef.current = '';
            setSelectedMicDeviceId('');
          } else {
            throw deviceErr;  // NotAllowedError etc. - report as-is
          }
        }
      }
      console.log('[Mic] getUserMedia({ audio: true }) (default microphone)');
      return await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      console.log('[Mic] getUserMedia failed');
      console.log(`[Mic] Error name: ${err?.name}`);
      console.log(`[Mic] Error message: ${err?.message || err}`);
      throw err;
    }
  };

  // Tear down old stream/watchers and swap in a fresh mic stream. Safe to
  // call mid-turn; if the recorder died with the old track, a new one is
  // started so the CURRENT turn keeps recording.
  // Acquire a fresh mic stream and swap it in. The old AUDIO tracks are
  // stopped ONLY after the new stream is in hand (never lose the mic); a
  // live CAMERA track is preserved untouched. The active turn's recorder is
  // re-created from the NEW active stream so the current turn keeps
  // capturing; nothing else about the GD state is touched.
  const restoreMicrophone = async () => {
    if (micRecoveringRef.current) {
      console.log('[Mic] Acquisition already in progress - awaiting it');
      if (micAcquirePromiseRef.current) {
        try { await micAcquirePromiseRef.current; } catch (e) {}
      }
      return;
    }
    const acquire = async () => {
      try {
        console.log('[Mic] Initializing microphone');
        const newStream = await acquireMicStream();
        console.log('[Mic] getUserMedia succeeded');

        // Stop the recorder FIRST so it never records from a dying stream,
        // then stop the old AUDIO tracks only AFTER the new stream is in hand.
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
          try { mediaRecorderRef.current.stop(); } catch (e) {}
          mediaRecorderRef.current = null;
        }
        audioStreamRef.current?.getTracks().forEach(t => { try { t.stop(); } catch (e) {} });
        mediaStreamRef.current?.getAudioTracks().forEach(t => { try { t.stop(); } catch (e) {} });

        // Preserve a live camera track from the previous combined stream.
        const liveVideoTrack = mediaStreamRef.current?.getVideoTracks().find(t => t.readyState === 'live') || null;

        mediaStreamRef.current = newStream;
        console.log('[Mic] Stream obtained');
        const audioTracks = newStream.getAudioTracks();
        console.log(`[Mic] Audio tracks: ${audioTracks.length}`, audioTracks.map(t => `${t.label || 'mic'} (${t.readyState})`));
        audioStreamRef.current = audioTracks.length > 0 ? new MediaStream(audioTracks) : null;

        if (liveVideoTrack) {
          mediaStreamRef.current.addTrack(liveVideoTrack);
        }
        if (videoRef.current && mediaStreamRef.current.getVideoTracks().length > 0) {
          videoRef.current.srcObject = mediaStreamRef.current;
        }

        // Best-effort CAMERA (audio is the critical path): requested
        // SEPARATELY so a busy camera can never block or break microphone
        // capture. Camera failure is non-fatal and never surfaces as a mic error.
        if (mediaStreamRef.current.getVideoTracks().length === 0) {
          try {
            const camStream = await navigator.mediaDevices.getUserMedia({ video: true });
            camStream.getVideoTracks().forEach(t => { try { mediaStreamRef.current.addTrack(t); } catch (e) {} });
            console.log('[Mic] Camera acquired (best-effort)');
          } catch (camErr) {
            console.log('[Mic] Camera unavailable (non-blocking):', camErr?.name);
          }
        }
        setMicEnabled(audioTracks.length > 0);
        setCameraEnabled(mediaStreamRef.current.getVideoTracks().length > 0);

        // Mid-turn: build a FRESH MediaRecorder on the fresh active stream so
        // the current turn keeps capturing. (A recorder is never reused after
        // it has stopped, and never attached to a stream whose tracks died.)
        if (turnStateRef.current === 'RECORDING_USER' && currentSpeakerRef.current === 'user') {
          const ok = ensureRecorderStarted();
          console.log(`[Mic] Mid-turn recorder restart: ${ok ? 'OK' : 'FAILED'}`);
          if (sttModeRef.current === 'browser' && recognitionRef.current && !browserSTTFailedRef.current) {
            try { recognitionRef.current.start(); setRecognitionActive(true); recognitionActiveRef.current = true; } catch (e) {}
          }
        }

        setMicIssue(null);
        setSttError(null);
        console.log('[Mic] Microphone ready');
      } catch (err) {
        console.error('[Mic] getUserMedia failed:', err);
        console.log(`[Mic] Error name: ${err?.name}`);
        console.log(`[Mic] Error message: ${err?.message || err}`);
        // Show the REAL error only - never a guessed "another app holds the mic".
        setMicIssue(describeMicError(err));
        setSttError(describeMicError(err));
      }
    };

    micRecoveringRef.current = true;
    const acquirePromise = acquire();
    micAcquirePromiseRef.current = acquirePromise;
    try {
      await acquirePromise;
    } finally {
      micRecoveringRef.current = false;
      micAcquirePromiseRef.current = null;
    }
  };

  // ---- Microphone device selection ----
  // Enumerate available audio input devices so the user's chosen mic (stored
  // by deviceId in a ref - never hardcoded) is passed through getUserMedia.
  // If the selected device later disappears, acquisition falls back to the
  // default microphone instead of failing the GD session.
  const refreshMicDevices = async () => {
    try {
      if (!navigator.mediaDevices?.enumerateDevices) return;
      const devices = await navigator.mediaDevices.enumerateDevices();
      const mics = devices.filter(d => d.kind === 'audioinput');
      setMicDevices(mics);
      console.log(`[Mic] Available audio inputs: ${mics.length}`, mics.map(d => d.label || (d.deviceId || '').slice(0, 8) || 'default'));
      // If the previously selected device no longer exists, drop it so the
      // next getUserMedia gracefully falls back to the default microphone.
      const sel = selectedMicDeviceIdRef.current;
      if (sel && !mics.some(d => d.deviceId === sel)) {
        console.warn(`[GD-MIC] Selected device ${sel.slice(0, 8)}... no longer available - falling back to default mic`);
        selectedMicDeviceIdRef.current = '';
        setSelectedMicDeviceId('');
      }
    } catch (e) {
      console.warn('[GD-MIC] Device enumeration failed:', e);
    }
  };

  // Re-enumerate when the OS swaps devices (headset plugged/unplugged etc.)
  useEffect(() => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.addEventListener) return undefined;
    const onChange = () => { console.log('[GD-MIC] devicechange - refreshing mic list'); refreshMicDevices(); };
    navigator.mediaDevices.addEventListener('devicechange', onChange);
    return () => navigator.mediaDevices.removeEventListener('devicechange', onChange);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Map the REAL getUserMedia failure (DOMException) to a human-readable
  // message. Every message is derived from an actual browser error name -
  // the cause is never guessed or invented.
  const describeMicError = (error) => {
    switch (error?.name) {
      case 'NotAllowedError':
      case 'PermissionDeniedError':
        return 'Microphone permission denied by the browser. Allow microphone access for this site in your browser settings, then try again.';
      case 'NotFoundError':
      case 'DevicesNotFoundError':
        return 'No microphone was found. Connect a microphone and try again.';
      case 'NotReadableError':
      case 'TrackStartError':
        return 'The browser could not read from your microphone (NotReadableError). The device may be in use by another application or disabled in system audio settings.';
      case 'OverconstrainedError':
        return 'The selected microphone does not support the requested settings (OverconstrainedError). Choose "Default microphone" or pick another device.';
      case 'SecurityError':
        return 'Microphone access is blocked because the page is not in a secure context. Use HTTPS or localhost.';
      case 'AbortError':
        return 'The microphone request was aborted. Please try again.';
      default:
        return error?.message || 'Could not access the microphone. Check your audio settings.';
    }
  };

  // Initialize camera and microphone.
  // NOTE: mic acquisition follows the browser contract directly:
  //   getUserMedia() -> live stream -> fresh MediaRecorder per turn -> Blob
  //   -> existing /api/gd/transcribe STT pipeline.
  // No "health" heuristics: if the mic fails, the REAL browser error is
  // shown (NotAllowedError / NotFoundError / NotReadableError /
  // OverconstrainedError / AbortError) - the cause is never guessed.
  const initializeMedia = async () => {
    console.log('[Mic] Initializing microphone');
    // Single acquisition path (shared with mid-turn restores / device swaps).
    await restoreMicrophone();

    if (!audioStreamRef.current) {
      setSttError('Microphone unavailable. Check the microphone error shown above.');
      return;
    }

    const mimeTypes = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/ogg',
      'audio/mp4',
      'audio/wav'
    ];
    let selectedMimeType = '';
    if (window.MediaRecorder && MediaRecorder.isTypeSupported) {
      for (const mime of mimeTypes) {
        if (MediaRecorder.isTypeSupported(mime)) {
          selectedMimeType = mime;
          break;
        }
      }
    }
    selectedMimeTypeRef.current = selectedMimeType;

    if (!window.MediaRecorder) {
      console.warn('MediaRecorder not supported on this browser');
      setSttError('Audio recording is not supported in this browser.');
    }

    // Enumerate available mics (after permission, labels are populated)
    refreshMicDevices();
    // NOTE: a fresh MediaRecorder is created for every speaking turn via
    // ensureRecorderStarted() (see below). Do NOT construct one here.
  };

  // Attach the media stream to the <video> element once it is rendered in the
  // active phase (getUserMedia may resolve before phase === 'active')
  useEffect(() => {
    if (phase === 'active' && mediaStreamRef.current && videoRef.current && !videoRef.current.srcObject) {
      videoRef.current.srcObject = mediaStreamRef.current;
    }
  }, [phase, cameraEnabled]);

  // Initialize browser speech recognition (Web Speech API)
  const initializeSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('SpeechRecognition API not supported in this browser. Activating Whisper fallback.');
      sttModeRef.current = 'whisper';
      setSttMode('whisper');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setRecognitionActive(true);
        recognitionActiveRef.current = true;
        if (sttModeRef.current === 'browser') {
          sttStateRef.current = 'LISTENING';
          setSttState('LISTENING');
          setSttError(null);
        }
      };

      recognition.onresult = (event) => {
        let interim = '';
        let finalizedThisBatch = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          const transcriptPiece = result[0]?.transcript || '';
          if (result.isFinal) {
            finalizedThisBatch += transcriptPiece;
          } else {
            interim += transcriptPiece;
          }
        }

        if (finalizedThisBatch) {
          finalTranscriptRef.current = (finalTranscriptRef.current + ' ' + finalizedThisBatch).trim();
        }

        const combined = (finalTranscriptRef.current + (interim ? ' ' + interim : '')).trim();
        setInterimTranscript(interim);
        setUserResponse(combined);
        userResponseRef.current = combined;
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition error encountered:', event.error);
        const fatalErrors = ['network', 'service-not-allowed', 'not-allowed', 'audio-capture'];

        // Transient Chrome STT network blips are common: retry ONCE before
        // permanently switching to the offline Whisper fallback.
        if (event.error === 'network' && !browserSTTFailedRef.current && browserNetworkRetryRef.current < 1) {
          browserNetworkRetryRef.current += 1;
          console.warn(`[TURN ${activeTurnIdRef.current}] BROWSER_STT_NETWORK_ERROR - retrying browser STT once (same turn, same recording; no new recorder, no second Whisper call)`);
          try { recognition.stop(); } catch (e) {} // onend restarts it while the turn is active
          return;
        }

        if (fatalErrors.includes(event.error)) {
          console.warn(`[TURN ${activeTurnIdRef.current}] BROWSER_STT_FATAL (${event.error}) -> transcription method switches to offline Whisper fallback; the SAME MediaRecorder recording continues`);
          browserSTTFailedRef.current = true;
          sttModeRef.current = 'whisper';
          setSttMode('whisper');
          sttStateRef.current = 'FALLBACK';
          setSttState('FALLBACK');

          // Keep the ONE recorder of this turn capturing for Whisper. If (and
          // only if) it is not already recording, start it - never a second one.
          ensureRecorderStarted();

          if (event.error === 'network') {
            setSttError('Online speech recognition unavailable. Switched to offline Whisper fallback.');
          } else if (event.error === 'not-allowed') {
            setSttError('Microphone permission denied by browser.');
          } else {
            setSttError(`Speech recognition error (${event.error}). Using offline Whisper fallback.`);
          }
          try { recognition.stop(); } catch (e) {}
        } else if (event.error === 'no-speech') {
          // Normal silence detection — non-fatal
        } else {
          setSttError(`Speech recognition error: ${event.error}`);
        }
      };

      recognition.onend = () => {
        setRecognitionActive(false);
        recognitionActiveRef.current = false;

        // Restart recognition only while THIS turn is still RECORDING_USER.
        // During stopUserSpeaking's async window the speaker ref still reads
        // 'user', so the turn state machine is the authority here.
        if (
          turnStateRef.current === 'RECORDING_USER' &&
          currentSpeakerRef.current === 'user' &&
          sttModeRef.current === 'browser' &&
          !browserSTTFailedRef.current
        ) {
          try {
            recognition.start();
          } catch (e) {
            browserSTTFailedRef.current = true;
            sttModeRef.current = 'whisper';
            setSttMode('whisper');
            sttStateRef.current = 'FALLBACK';
            setSttState('FALLBACK');
          }
        }
      };

      recognitionRef.current = recognition;
    } catch (e) {
      console.error('Failed to initialize speech recognition:', e);
      sttModeRef.current = 'whisper';
      setSttMode('whisper');
    }
  };

  // Transcribe audio using backend faster-whisper API
  const transcribeAudioBlob = async (audioBlob) => {
    const tid = activeTurnIdRef.current;
    console.log(`[TURN ${tid}] STT_REQUEST (blob size: ${audioBlob ? audioBlob.size : 0})`);
    if (!audioBlob || audioBlob.size === 0) {
      console.warn(`[TURN ${tid}] STT_REQUEST aborted - empty audio blob`);
      return;
    }
    // AUDIO_SENT diagnostic: exact payload handed to /api/gd/transcribe so
    // truncation/decoding issues can be separated from Whisper accuracy issues.
    console.log(`[TURN ${tid}] AUDIO_SENT -> POST /api/gd/transcribe (${audioBlob.size} bytes, type: ${audioBlob.type || 'unknown'})`);
    const epoch = turnEpochRef.current;
    sttStateRef.current = 'PROCESSING';
    setSttState('PROCESSING');

    try {
      console.log(`[TURN ${tid}] STT_AWAITING (faster-whisper inference running)`);
      const response = await gdAPI.transcribeAudio(audioBlob);
      console.log(`[TURN ${tid}] STT_RESPONSE received`);

      if (epoch !== turnEpochRef.current) {
        // The turn moved on before this transcription arrived (slow inference,
        // manual submit, etc.). Never throw the user's speech away: surface it
        // in the transcript and submit it to the backend anyway.
        const lateText = (response.data?.text || '').trim();
        if (lateText) {
          console.warn('[STT] Transcription arrived after turn ended - applying it late and submitting:', lateText);
          console.log(`[AI_DEBUG] LATE_STT_APPLIED: ${JSON.stringify(lateText)}`);
          const lateResponse = {
            participant: 'user',
            name: 'You',
            text: lateText,
            timestamp: new Date().toISOString()
          };
          setAllResponses(prev => [...prev, lateResponse]);
          previousSpeakerRef.current = { id: 'user', name: 'You', type: 'user' };
          if (gdRound?._id && !gdRound._id.startsWith('practice_') && gdRound._id.length > 10) {
            gdAPI.submitResponse(gdRound._id, lateText).catch(err =>
              console.error('Error submitting late response to backend:', err)
            );
          }
        } else {
          console.warn('[STT] Late transcription arrived but contained no text');
        }
        return;
      }

      if (response.data && response.data.success) {
        const text = (response.data.text || '').trim();
        // [AI_DEBUG] full transcript (no 80-char preview): shows EXACTLY what
        // the AI will receive, so STT vs AI-prompting problems are separable.
        console.log(`[AI_DEBUG] CURRENT_USER_TRANSCRIPT: ${JSON.stringify(text)}`);
        if (text) {
          // Replace any partial/broken browser text with the complete Whisper transcription
          userResponseRef.current = text;
          setUserResponse(text);
          finalTranscriptRef.current = text;
          sttStateRef.current = 'SUCCESS';
          setSttState('SUCCESS');
          setSttError(null);
          console.log(`[TURN ${tid}] STT_RESULT: "${text.substring(0, 80)}"`);
        } else {
          // Whisper heard nothing usable - prefer the backend's specific
          // diagnosis (silence detected via loudness probe) when provided.
          console.warn(`[TURN ${tid}] STT_RESULT: empty transcript (no speech detected in audio)`);
          sttStateRef.current = 'IDLE';
          setSttState('IDLE');
          setSttError(response.data?.warning || 'No speech detected in your audio. Make sure the mic is not muted, no other app (Zoom/Meet/Teams) is using it, and speak a little louder.');
        }
      } else {
        const errMsg = response.data?.error || 'Transcription failed';
        sttStateRef.current = 'ERROR';
        setSttState('ERROR');
        setSttError(errMsg);
      }
    } catch (error) {
      if (epoch === turnEpochRef.current) {
        console.error('Backend Whisper transcription failed:', error);
        sttStateRef.current = 'ERROR';
        setSttState('ERROR');
        const errMsg = error.response?.data?.error || 'Offline Whisper transcription failed. Please type your response manually.';
        setSttError(errMsg);
      }
    }
  };



  const handleStartGD = () => {
    if (gdRound?.allow_topic_selection) {
      setPhase('topic-selection');
    } else {
      setSelectedTopic(gdRound?.topic);
      setPhase('preparation');
    }
    initializeMedia();
    initializeSpeechRecognition();
  };

  const handleTopicSelection = async (topic) => {
    setSelectedTopic(topic);
    setPhase('preparation');
    if (gdRound?._id && !gdRound._id.startsWith('practice_')) {
      try { await gdAPI.selectTopic(gdRound._id, topic); } catch (err) {
        console.error('Error selecting topic on backend:', err);
      }
    }
  };

  // Manual retry after a no-speech turn is handled directly by the UI via
  // startUserSpeaking('retry') - a fresh turn started ONLY by a user click,
  // so an empty -> retry cycle can never run without explicit user action.

  const startGDRound = async () => {
    // Once-guard: the preparation-timer effect (or any re-entry) must never
    // start the round - and with it the first turn - twice.
    if (gdRoundStartedRef.current) {
      console.log('[TURN] startGDRound ignored - round already started');
      return;
    }
    gdRoundStartedRef.current = true;
    if (gdRound?._id && !gdRound._id.startsWith('practice_')) {
      try { await gdAPI.startRound(gdRound._id); } catch (err) {
        console.error('Error starting round on backend:', err);
      }
    }
    const shouldUserStart = Math.random() > 0.5;
    console.log(`[TURN] Round started -> first speaker: ${shouldUserStart ? 'USER' : 'AI_AGENT'}`);
    if (shouldUserStart) {
      startUserSpeaking('round-start');
    } else {
      scheduleNextSpeaker('round-start');
    }
  };

  const startUserSpeaking = async (source = 'unknown') => {
    // Cancel any ongoing TTS immediately
    if (synthRef.current) synthRef.current.cancel();
    if (speakingTimeoutRef.current) {
      clearTimeout(speakingTimeoutRef.current);
      speakingTimeoutRef.current = null;
    }
    if (aiSpeakingTimeoutRef.current) {
      clearTimeout(aiSpeakingTimeoutRef.current);
      aiSpeakingTimeoutRef.current = null;
    }
    // SINGLE AUTHORITY GATE: a user turn may only begin from IDLE.
    if (turnStateRef.current !== 'IDLE') {
      console.warn(`[TURN ${activeTurnIdRef.current}] DUPLICATE_START_BLOCKED (source: ${source}) - turn state: ${turnStateRef.current}`);
      return;
    }
    activeTurnIdRef.current += 1;
    const tid = activeTurnIdRef.current;
    turnStateRef.current = 'RECORDING_USER';
    turnEpochRef.current += 1;
    console.log(`[TURN ${tid}] USER_START (source: ${source})`);
    console.log(`[GD-TURN] Current speaker: user`);
    console.log(`[GD-TURN] Previous speaker: ${previousSpeakerRef.current ? `${previousSpeakerRef.current.id} (${previousSpeakerRef.current.type})` : 'none'}`);
    browserNetworkRetryRef.current = 0; // fresh retry budget per speaking turn

    setCurrentSpeaker('user');
    setIsRecording(true);
    setSttError(null);
    setOffTopicHint(false);
    setInterimTranscript('');
    finalTranscriptRef.current = '';
    audioChunksRef.current = [];
    // NOTE: userResponse is deliberately NOT cleared here - if the previous
    // turn ended with "no speech detected", anything the user typed as a
    // fallback must survive into the retry turn.

    // ---- BASIC MIC GUARANTEE (runs EVERY turn) ----
    // The MediaRecorder must ALWAYS be created from a LIVE stream. If the
    // previous turn released the stream, the stream died, or the mic was
    // never acquired, acquire a fresh one NOW and AWAIT it, so recording
    // starts from real audio. Per turn: getUserMedia -> stream -> fresh
    // MediaRecorder -> chunks -> Blob -> existing STT pipeline.
    const liveAudioTracks = (audioStreamRef.current?.getAudioTracks() || [])
      .filter(t => t.readyState === 'live');
    if (liveAudioTracks.length === 0) {
      console.log(`[TURN ${tid}] No live mic stream at turn start - acquiring a fresh microphone stream`);
      await restoreMicrophone();
    }
    // Refresh the mic mirror immediately: state setters above resolve on the
    // NEXT render, but the browser-STT decision below runs NOW.
    micEnabledRef.current = (audioStreamRef.current?.getAudioTracks() || [])
      .some(t => t.readyState === 'live' && t.enabled);

    const useBrowserSTT =
      sttModeRef.current === 'browser' &&
      recognitionRef.current &&
      micEnabledRef.current &&
      !browserSTTFailedRef.current;

    if (useBrowserSTT) {
      try {
        recognitionRef.current.start();
        setRecognitionActive(true);
        recognitionActiveRef.current = true;
        sttStateRef.current = 'LISTENING';
        setSttState('LISTENING');
        console.log(`[TURN ${tid}] BROWSER_STT_STARTED`);
      } catch (error) {
        console.warn('Error starting speech recognition:', error);
        browserSTTFailedRef.current = true;
        sttModeRef.current = 'whisper';
        setSttMode('whisper');
        sttStateRef.current = 'FALLBACK';
        setSttState('FALLBACK');
      }
    } else {
      sttStateRef.current = sttModeRef.current === 'whisper' ? 'FALLBACK' : 'LISTENING';
      setSttState(sttStateRef.current);
    }

    // Always run a fresh MediaRecorder as safety net/fallback (ONE per turn:
    // create once, start once, stop once, transcribe once). Created from the
    // ACTIVE audio stream only.
    ensureRecorderStarted();
    console.log(`[TURN ${tid}] RECORDING_STARTED (recorder: ${mediaRecorderRef.current?.state || 'unavailable'})`);

    const speakingTime = 30000 + Math.random() * 30000;
    speakingTimeoutRef.current = setTimeout(() => {
      speakingTimeoutRef.current = null;
      stopUserSpeaking('turn-timer');
    }, speakingTime);
  };

  const stopUserSpeaking = async (source = 'unknown') => {
    if (speakingTimeoutRef.current) {
      clearTimeout(speakingTimeoutRef.current);
      speakingTimeoutRef.current = null;
    }
    // Only a turn that is actively RECORDING_USER can be stopped; stale or
    // duplicate stop requests (double-click, round-end + manual) are ignored.
    if (turnStateRef.current !== 'RECORDING_USER' || currentSpeakerRef.current !== 'user') return;
    const tid = activeTurnIdRef.current;
    console.log(`[TURN ${tid}] RECORDING_STOPPING (source: ${source})`);
    turnStateRef.current = 'PROCESSING_STT';
    setIsRecording(false);

    // Stop browser SpeechRecognition if active
    if (recognitionRef.current && recognitionActiveRef.current) {
      try {
        recognitionRef.current.stop();
        setRecognitionActive(false);
        recognitionActiveRef.current = false;
      } catch (error) {
        console.warn('Error stopping speech recognition:', error);
      }
    }

    // Check if Browser STT produced a usable, finalized transcript without failing
    const browserSucceeded =
      sttModeRef.current === 'browser' &&
      !browserSTTFailedRef.current &&
      finalTranscriptRef.current.trim().length > 0;

    console.log(`[TURN ${tid}] STT_MODE_RESOLVED (recorder: ${mediaRecorderRef.current?.state}, mode: ${sttModeRef.current}, browserSucceeded: ${browserSucceeded})`);

    let transcriptionWait = null;

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      if (!browserSucceeded) {
        // Fallback needed: register wait promise before stopping MediaRecorder
        sttStateRef.current = 'PROCESSING';
        setSttState('PROCESSING');
        transcriptionWait = new Promise(resolve => { transcribeDoneRef.current = resolve; });
      }
      try {
        // stop() flushes all pending chunks to ondataavailable before onstop fires
        mediaRecorderRef.current.stop();
        console.log(`[TURN ${tid}] RECORDING_STOPPED`);
        console.log('[Mic] Recording stopped');
      } catch (error) {
        console.warn('[Mic] MediaRecorder stop failed:', error);
        transcriptionWait = null;
        transcribeDoneRef.current = null;
      }
    } else if (!browserSucceeded && audioChunksRef.current.length > 0) {
      // Audio chunks exist even if recorder was not in recording state
      const mime = mediaRecorderRef.current?.mimeType || 'audio/webm';
      const audioBlob = new Blob(audioChunksRef.current, { type: mime });
      audioChunksRef.current = [];
      console.log('[STT] Direct fallback transcribe from existing chunks, blob size:', audioBlob.size);
      if (audioBlob.size > 0) {
        await transcribeAudioBlob(audioBlob);
      }
    }

    if (browserSucceeded) {
      // Browser STT succeeded: use its text directly without duplicate Whisper call
      const cleanText = finalTranscriptRef.current.trim();
      userResponseRef.current = cleanText;
      setUserResponse(cleanText);
      sttStateRef.current = 'SUCCESS';
      setSttState('SUCCESS');
    } else if (transcriptionWait) {
      // Await Whisper transcription from onstop
      try {
        // Wait generously: offline Whisper on CPU can take a while for long
        // turns (and the model may still be downloading on first run). If this
        // races out, the late response would be discarded as a stale epoch and
        // the user's speech would be lost entirely.
        await Promise.race([
          transcriptionWait,
          new Promise(resolve => setTimeout(resolve, 90000))
        ]);
      } catch (e) {
        console.warn('Transcription wait error:', e);
      }
      transcribeDoneRef.current = null;
    }

    setInterimTranscript('');

    const textToSubmit = userResponseRef.current.trim();
    console.log(`[TURN ${tid}] TRANSCRIPT_READY${textToSubmit ? `: "${textToSubmit.substring(0, 80)}"` : ' (empty)'}`);

    // ---- EMPTY-TRANSCRIPT GUARD ----
    // An empty/whitespace transcript is NOT a valid user response: never
    // submit it, never advance to an AI turn, never start TTS because of it.
    // Enter WAITING_USER_RETRY so the user gets another opportunity to speak
    // (bounded retries - no automatic infinite loop). currentSpeaker stays
    // 'user' so the response box remains visible with retry/submit actions;
    // nothing is scheduled automatically, the user drives the next step.
    if (!textToSubmit) {
      userRetryCountRef.current += 1;
      const attempt = userRetryCountRef.current;
      console.log(`[TURN ${tid}] EMPTY_TRANSCRIPT (attempt ${attempt}/${MAX_EMPTY_RETRIES})`);
      if (attempt < MAX_EMPTY_RETRIES) {
        sttStateRef.current = 'WAITING_USER_RETRY';
        setSttState('WAITING_USER_RETRY');
        setSttError(`No speech detected. Please try speaking again. (Attempt ${attempt} of ${MAX_EMPTY_RETRIES} - you can also type your response below.)`);
        turnStateRef.current = 'IDLE';
        console.log(`[TURN ${tid}] WAITING_FOR_USER_RETRY (no submit, no AI request, no TTS, no auto-advance)`);
        return;
      }
      // Retry budget exhausted: hand the floor back to the discussion instead
      // of trapping the user. The scheduler's own AI guard keeps AI turns
      // honest about whether a user response actually exists.
      console.warn(`[TURN ${tid}] RETRY_LIMIT_REACHED - releasing floor to the discussion`);
      userRetryCountRef.current = 0;
    }

    if (textToSubmit) {
      // Duplicate-submission guard: transcribeAudioBlob can resolve late and
      // re-enter this flow after the turn epoch moved on; without this check
      // the same text could be added/submitted twice for one turn.
      if (submittedTurnIdsRef.current.has(tid)) {
        console.warn(`[TURN ${tid}] DUPLICATE_SUBMIT_BLOCKED - this turn was already submitted`);
        return;
      }
      submittedTurnIdsRef.current.add(tid);
      const response = {
        participant: 'user',
        name: 'You',
        text: textToSubmit,
        timestamp: new Date().toISOString()
      };
      setAllResponses(prev => [...prev, response]);
      // Speaker tracking: the user is now the previous speaker, so the next
      // agent knows whom it is responding to.
      previousSpeakerRef.current = { id: 'user', name: 'You', type: 'user' };
      setUserResponse('');
      userResponseRef.current = '';
      finalTranscriptRef.current = '';
      if (gdRound?._id && gdRound._id.length > 10) {
        try {
          console.log(`[TURN ${tid}] SUBMIT_STARTED -> POST /gd/round/:id/submit-response`);
          await gdAPI.submitResponse(gdRound._id, textToSubmit);
          console.log(`[TURN ${tid}] SUBMIT_DONE`);
        } catch (err) {
          console.error('Error submitting response to backend:', err);
        }
      }
    }

    // A submitted response resets the consecutive empty-retry budget
    userRetryCountRef.current = 0;
    setOffTopicHint(false);

    sttStateRef.current = 'IDLE';
    setSttState('IDLE');
    setCurrentSpeaker(null);
    turnStateRef.current = 'IDLE';
    console.log(`[TURN ${tid}] COMPLETE`);

    if (roundEndedRef.current) {
      console.log('[TURN] Round ended - no next speaker will be scheduled');
      return;
    }
    if (nextSpeakerTimerRef.current) clearTimeout(nextSpeakerTimerRef.current);
    nextSpeakerTimerRef.current = setTimeout(() => {
      nextSpeakerTimerRef.current = null;
      scheduleNextSpeaker('user-turn-complete');
    }, 2000);
  };


  // Submit a manually-typed response while in WAITING_USER_RETRY, then hand
  // the floor back to the scheduler exactly like a spoken turn would.
  const submitTypedResponse = async () => {
    if (turnStateRef.current !== 'IDLE' || currentSpeakerRef.current !== 'user') return;
    const text = userResponseRef.current.trim();
    if (!text) return;
    const tid = activeTurnIdRef.current;
    console.log(`[TURN ${tid}] TYPED_SUBMIT (manual response while waiting)`);
    setAllResponses(prev => [...prev, { participant: 'user', name: 'You', text, timestamp: new Date().toISOString() }]);
    previousSpeakerRef.current = { id: 'user', name: 'You', type: 'user' };
    setUserResponse('');
    userResponseRef.current = '';
    finalTranscriptRef.current = '';
    userRetryCountRef.current = 0;
    setOffTopicHint(false);
    if (gdRound?._id && gdRound._id.length > 10) {
      try {
        console.log(`[TURN ${tid}] SUBMIT_STARTED -> POST /gd/round/:id/submit-response`);
        await gdAPI.submitResponse(gdRound._id, text);
        console.log(`[TURN ${tid}] SUBMIT_DONE`);
      } catch (err) {
        console.error('Error submitting response to backend:', err);
      }
    }
    sttStateRef.current = 'IDLE';
    setSttState('IDLE');
    setSttError(null);
    setCurrentSpeaker(null);
    if (roundEndedRef.current) return;
    if (nextSpeakerTimerRef.current) clearTimeout(nextSpeakerTimerRef.current);
    nextSpeakerTimerRef.current = setTimeout(() => {
      nextSpeakerTimerRef.current = null;
      scheduleNextSpeaker('user-typed-submit');
    }, 2000);
  };

  const scheduleNextSpeaker = (source = 'unknown') => {
    if (nextSpeakerTimerRef.current) {
      clearTimeout(nextSpeakerTimerRef.current);
      nextSpeakerTimerRef.current = null;
    }
    // Never start a new speaker while a turn is still in progress
    if (turnStateRef.current !== 'IDLE') {
      console.warn(`[TURN] scheduleNextSpeaker skipped (source: ${source}) - turn state: ${turnStateRef.current}`);
      return;
    }
    if (roundEndedRef.current) return;
    if (gdTimerRef.current <= 0) { endGDRound(); return; }
    const shouldUserSpeak = Math.random() < 0.4;
    console.log(`[TURN] scheduleNextSpeaker (source: ${source}) -> next: ${shouldUserSpeak ? 'USER' : 'AI_AGENT'}`);
    if (shouldUserSpeak) {
      startUserSpeaking('scheduleNextSpeaker');
    } else {
      speakAIAgent('scheduleNextSpeaker');
    }
  };

  const speakAIAgent = async (source = 'unknown') => {
    // Cancel any ongoing TTS immediately
    if (synthRef.current) synthRef.current.cancel();
    if (speakingTimeoutRef.current) {
      clearTimeout(speakingTimeoutRef.current);
      speakingTimeoutRef.current = null;
    }
    if (turnStateRef.current !== 'IDLE') {
      console.warn(`[TURN] DUPLICATE_AI_START_BLOCKED (source: ${source}) - turn state: ${turnStateRef.current}`);
      return;
    }
    turnStateRef.current = 'PROCESSING_AI';

    const sortedAgents = [...aiAgentsRef.current].sort((a, b) => a.speakCount - b.speakCount);
    const agent = sortedAgents[Math.floor(Math.random() * Math.min(3, sortedAgents.length))];
    if (!agent) {
      turnStateRef.current = 'IDLE';
      return;
    }
    activeTurnIdRef.current += 1;
    const tid = activeTurnIdRef.current;
    console.log(`[TURN ${tid}] AI_START (source: ${source}, agent: ${agent.name})`);

    // DEFENSIVE GUARD: /gd/agent-response must never be called because of an
    // empty user transcript. If any user response exists in the discussion,
    // the latest one must be non-empty. (The round-opening AI turn
    // legitimately has no user history yet - that case is allowed.)
    const lastUserResponse = [...allResponsesRef.current].reverse().find(r => r.participant === 'user');
    const hasUserHistory = allResponsesRef.current.some(r => r.participant === 'user');
    if (hasUserHistory && !(lastUserResponse && typeof lastUserResponse.text === 'string' && lastUserResponse.text.trim())) {
      console.log(`[TURN ${tid}] AI_SKIPPED: empty user transcript`);
      setIsGeneratingAIResponse(false);
      turnStateRef.current = 'IDLE';
      if (roundEndedRef.current) {
        setCurrentSpeaker(null);
        return;
      }
      // Hand control BACK to the user - never auto-start another recording
      // (an automatic empty -> retry -> empty loop is forbidden). The user
      // explicitly clicks "Try Speaking Again" or types a response.
      setSttError('No speech detected. Please try speaking again.');
      sttStateRef.current = 'WAITING_USER_RETRY';
      setSttState('WAITING_USER_RETRY');
      setCurrentSpeaker('user');
      console.log(`[TURN ${tid}] WAITING_FOR_USER_RETRY (no AI request, no TTS, no auto-advance)`);
      return;
    }
    console.log(`[TURN ${tid}] AI_REQUEST -> POST /gd/agent-response`);

    setCurrentSpeaker(agent.id);
    setIsGeneratingAIResponse(true);
    setAiUnavailable(false);

    console.log(`[GD-TURN] Current speaker: ${agent.id}`);
    console.log(`[GD-TURN] Previous speaker: ${previousSpeakerRef.current ? `${previousSpeakerRef.current.id} (${previousSpeakerRef.current.type})` : 'none'}`);

    // ---- Speaker-aware response target ----
    // The agent responds to the PREVIOUS speaker, whoever that was: another
    // agent (agent->agent discussion) or the user. The user is targeted when
    // they spoke last OR when no one has spoken yet. Otherwise the discussion
    // continues between agents instead of every agent addressing the user.
    const prev = previousSpeakerRef.current;
    const respondToType = (!prev || prev.type === 'user' || prev.id === agent.id) ? 'user' : 'agent';
    const respondToName = prev ? prev.name : 'You';
    const respondToText = prev ? prev.text : '';
    console.log(`[GD-TURN] Next speaker: ${agent.id}`);
    console.log(`[GD-TURN] Response target: ${respondToType === 'agent' ? respondToName : 'user'}`);

    // The agent must react to what was JUST said by the previous speaker -
    // pass the exact latest statements alongside the recent discussion context.
    const recentContext = allResponsesRef.current.slice(-5).map(r => `${r.name}: ${r.text}`).join('\n');
    let aiResponse;
    let isOffTopicReply = false;
    try {
      // For user-directed turns the agent reacts to the exact latest user
      // transcript (never stale state). For agent-directed turns it reacts to
      // the previous agent's actual last statement.
      const currentUserTranscript = respondToType === 'user' && lastUserResponse ? lastUserResponse.text : '';
      console.log(`[TURN ${tid}] [AI_DEBUG] TRANSCRIPT_SENT_TO_AI: ${JSON.stringify(respondToType === 'agent' ? respondToText : currentUserTranscript)}`);
      const response = await gdAPI.getAgentResponse({
        round_id: gdRound?._id,
        topic: selectedTopic,
        context: recentContext,
        agent_personality: agent.personality,
        agent_gender: agent.gender,
        latest_user_text: currentUserTranscript,
        respond_to_type: respondToType,
        respond_to_name: respondToType === 'agent' ? respondToName : undefined,
        respond_to_text: respondToType === 'agent' ? respondToText : undefined,
        agent_name: agent.name,
      });
      if (response.data && response.data.agent_response_available === false) {
        // Backend explicitly reports no AI provider available - show a clear
        // notice instead of speaking something unrelated to the discussion.
        console.warn('[AI] Agent service unavailable:', response.data.error);
        setAiUnavailable(true);
        aiResponse = generateAIResponse(agent);
        isOffTopicReply = aiResponse === OFF_TOPIC_SENTENCE;
      } else {
        aiResponse = response.data.response;
        // Backend flags its canonical off-topic intervention explicitly.
        isOffTopicReply = !!(response.data && response.data.off_topic_reply === true);
      }
    } catch (error) {
      console.error('Backend AI response failed, using on-topic fallback:', error);
      setAiUnavailable(true);
      aiResponse = generateAIResponse(agent);
      isOffTopicReply = aiResponse === OFF_TOPIC_SENTENCE;
    }

    console.log(`[TURN ${tid}] AI_RESULT: "${(aiResponse || '').substring(0, 70)}"`);

    // ---- TTS SAFETY GUARD (layer 3) ----
    // Never speak (and never record into the discussion) an empty/invalid AI
    // response, and never speak a response that no longer belongs to the
    // current turn (the round ended while the AI request was in flight).
    if (!aiResponse || aiResponse.trim().length === 0 || roundEndedRef.current) {
      console.warn(`[TURN ${tid}] TTS_SKIPPED (${!aiResponse || aiResponse.trim().length === 0 ? 'empty AI response' : 'round no longer active'})`);
      setIsGeneratingAIResponse(false);
      turnStateRef.current = 'IDLE';
      setCurrentSpeaker(null);
      if (roundEndedRef.current) return;
      if (nextSpeakerTimerRef.current) clearTimeout(nextSpeakerTimerRef.current);
      nextSpeakerTimerRef.current = setTimeout(() => {
        nextSpeakerTimerRef.current = null;
        scheduleNextSpeaker('ai-turn-complete');
      }, 1500);
      return;
    }

    setIsGeneratingAIResponse(false);
    setAiAgents(prev => prev.map(a =>
      a.id === agent.id ? { ...a, speakCount: a.speakCount + 1, hasSpoken: true } : a
    ));

    // A normal (on-topic) agent turn resets the off-topic intervention budget
    if (!isOffTopicReply) offTopicInterventionsRef.current = 0;

    setAllResponses(prev => [...prev, {
      participant: agent.id,
      name: agent.name,
      text: aiResponse,
      timestamp: new Date().toISOString()
    }]);
    // Speaker tracking: this agent is now the previous speaker, so the NEXT
    // agent can respond to it (agent->agent flow) instead of the user.
    previousSpeakerRef.current = { id: agent.id, name: agent.name, type: 'agent', text: aiResponse };

    const finishAgentTurn = () => {
      if (aiSpeakingTimeoutRef.current) {
        clearTimeout(aiSpeakingTimeoutRef.current);
        aiSpeakingTimeoutRef.current = null;
      }
      if (ttsFallbackTimerRef.current) {
        clearTimeout(ttsFallbackTimerRef.current);
        ttsFallbackTimerRef.current = null;
      }
      turnStateRef.current = 'IDLE';
      console.log(`[TURN ${tid}] TTS_FINISHED`);
      console.log(`[TURN ${tid}] COMPLETE`);
      if (roundEndedRef.current) {
        setCurrentSpeaker(null);
        return;
      }

      // ---- OFF-TOPIC HAND-BACK ----
      // After an off-topic intervention, the agent has asked the speaker to
      // continue with topic points - so hand the floor BACK to the speaker
      // instead of scheduling the next participant. A budget caps consecutive
      // interventions so the round cannot loop forever on off-topic speech.
      if (isOffTopicReply) {
        offTopicInterventionsRef.current += 1;
        const interventions = offTopicInterventionsRef.current;
        console.log(`[TURN ${tid}] OFF_TOPIC_INTERVENTION (${interventions}/${MAX_OFF_TOPIC_INTERVENTIONS}) - handing floor back to speaker`);
        if (interventions >= MAX_OFF_TOPIC_INTERVENTIONS) {
          // Budget exhausted: move the discussion on instead of trapping the
          // speaker; the budget resets after any on-topic turn.
          console.warn(`[TURN ${tid}] OFF_TOPIC_BUDGET_EXHAUSTED - discussion continues without hand-back`);
          offTopicInterventionsRef.current = 0;
          setCurrentSpeaker(null);
          if (nextSpeakerTimerRef.current) clearTimeout(nextSpeakerTimerRef.current);
          nextSpeakerTimerRef.current = setTimeout(() => {
            nextSpeakerTimerRef.current = null;
            scheduleNextSpeaker('off-topic-budget-exhausted');
          }, 1500);
          return;
        }
        // Hand the floor back: user keeps the mic, gets a hint, and can
        // continue immediately with topic points. No auto-recording starts.
        setIsGeneratingAIResponse(false);
        setOffTopicHint(true);
        setSttError('That was not related to the topic. Please continue with points related to the topic.');
        sttStateRef.current = 'WAITING_USER_RETRY';
        setSttState('WAITING_USER_RETRY');
        setCurrentSpeaker('user');
        userRetryCountRef.current = 0; // fresh retry budget for the continuation turn
        console.log(`[TURN ${tid}] WAITING_FOR_USER_CONTINUATION (floor returned to speaker)`);
        return;
      }

      setCurrentSpeaker(null);
      if (nextSpeakerTimerRef.current) clearTimeout(nextSpeakerTimerRef.current);
      nextSpeakerTimerRef.current = setTimeout(() => {
        nextSpeakerTimerRef.current = null;
        scheduleNextSpeaker('ai-turn-complete');
      }, 1500);
    };

    if (volumeEnabledRef.current) {
      console.log(`[TURN ${tid}] TTS_STARTED (browser speech synthesis)`);
      turnStateRef.current = 'PLAYING_TTS';
      speakText(aiResponse, agent.gender, finishAgentTurn);
    } else {
      console.log(`[TURN ${tid}] TTS_SKIPPED (volume muted)`);
      turnStateRef.current = 'PLAYING_TTS';
      const wordCount = (aiResponse || '').split(/\s+/).length;
      aiSpeakingTimeoutRef.current = setTimeout(finishAgentTurn, Math.max(3000, wordCount * 350));
    }
  };

  // Client-side topic relevance check used ONLY for the offline fallback
  // responses (when the AI backend is unreachable). Mirrors the backend gate:
  // if the user's latest statement has no genuine connection to the topic,
  // the agent must NOT force an indirect connection - it must say so.
  const isUserTextRelatedToTopic = (text, topic) => {
    if (!text || !text.trim()) return true; // nothing said yet - nothing to flag
    const STOP = new Set(['the', 'a', 'an', 'in', 'on', 'of', 'and', 'or', 'is', 'are', 'was', 'were', 'be', 'to', 'for', 'with', 'vs', 'that', 'this', 'it', 'its', 'as', 'not', 'but', 'we', 'i', 'you', 'they', 'will', 'would', 'should', 'can', 'could', 'have', 'has', 'had', 'about', 'think', 'believe', 'feel', 'point', 'view', 'opinion', 'agree', 'because', 'really', 'very', 'just', 'some', 'many', 'more', 'most', 'other', 'people', 'today', 'now']);
    const words = new Set((text.toLowerCase().match(/[a-z']+/g) || []));
    const topicWords = (topic || '').toLowerCase().match(/[a-z']+/g) || [];
    const meaningful = [...words].filter(w => !STOP.has(w));
    let matches = 0;
    for (const tw of new Set(topicWords)) {
      if (STOP.has(tw)) continue;
      const stem = tw.length > 4 ? tw.slice(0, Math.ceil(tw.length * 0.7)) : tw;
      if (words.has(tw) || meaningful.some(w => w.startsWith(stem))) matches += 1;
    }
    // At least one real topic-concept match (or two short-topic matches)
    const shortTopicWords = topicWords.filter(tw => !STOP.has(tw) && tw.length <= 4);
    const shortMatches = shortTopicWords.filter(tw => words.has(tw)).length;
    return matches >= 1 || shortMatches >= 2;
  };

  const generateAIResponse = (agent) => {
    // Offline fallback: if the user's latest statement is unrelated to the
    // topic, the agent calls it out instead of indirectly connecting it.
    const lastUserTurn = [...allResponsesRef.current].reverse().find(r => r.participant === 'user');
    if (lastUserTurn && !isUserTextRelatedToTopic(lastUserTurn.text, selectedTopic)) {
      return 'This is not related to the topic. Please speak points related to the topic.';
    }
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

  const speakText = (text, gender, onEndCallback) => {
    if (!synthRef.current) {
      if (onEndCallback) onEndCallback();
      return;
    }
    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const voices = synthRef.current.getVoices();
    const voice = voices.find(v =>
      gender === 'female'
        ? v.name.includes('female') || v.name.includes('Female') || v.name.includes('Zira')
        : v.name.includes('male') || v.name.includes('Male') || v.name.includes('David')
    );
    if (voice) utterance.voice = voice;
    utterance.rate = 1.0;
    utterance.pitch = gender === 'female' ? 1.1 : 0.9;

    let hasEnded = false;
    // handleEnd must run EXACTLY once: utterance.onend/onerror and the fallback
    // timer can both fire, which previously double-ran finishAgentTurn.
    const handleEnd = () => {
      if (hasEnded) return;
      hasEnded = true;
      if (ttsFallbackTimerRef.current) {
        clearTimeout(ttsFallbackTimerRef.current);
        ttsFallbackTimerRef.current = null;
      }
      if (onEndCallback) onEndCallback();
    };
    utterance.onend = handleEnd;
    utterance.onerror = handleEnd;

    // Fallback timer in case browser doesn't fire onend
    if (ttsFallbackTimerRef.current) clearTimeout(ttsFallbackTimerRef.current);
    const wordCount = (text || '').split(/\s+/).length;
    ttsFallbackTimerRef.current = setTimeout(() => {
      ttsFallbackTimerRef.current = null;
      handleEnd();
    }, Math.max(4000, (wordCount * 450) + 2000));

    synthRef.current.speak(utterance);
  };

  const endGDRound = async () => {
    // Once-guard: the gd-timer effect must not end the round twice (double
    // evaluate POST) nor race with a manual end.
    if (roundEndedRef.current) {
      console.log('[TURN] endGDRound ignored - round already ended');
      return;
    }
    roundEndedRef.current = true;
    // If the user is mid-turn, close their turn first so the final transcript is captured
    if (turnStateRef.current === 'RECORDING_USER' && currentSpeakerRef.current === 'user') {
      try { await stopUserSpeaking('round-end'); } catch (e) { console.warn('Failed to close user turn:', e); }
    }
    setPhase('evaluating');
    setLoading(true);
    stopAllMediaTracks();
    if (synthRef.current) synthRef.current.cancel();
    if (speakingTimeoutRef.current) clearTimeout(speakingTimeoutRef.current);
    if (aiSpeakingTimeoutRef.current) clearTimeout(aiSpeakingTimeoutRef.current);
    if (nextSpeakerTimerRef.current) clearTimeout(nextSpeakerTimerRef.current);
    if (ttsFallbackTimerRef.current) clearTimeout(ttsFallbackTimerRef.current);
    turnStateRef.current = 'IDLE';

    try {
      if (gdRound?._id && !gdRound._id.startsWith('practice_')) {
        const response = await gdAPI.evaluateRound(gdRound._id);
        if (response.data.success) {
          setResults(response.data.results);
          setPhase('completed');
        } else {
          alert(response.data.error || 'Failed to evaluate GD round.');
        }
      } else {
        setPhase('completed');
      }
    } catch (error) {
      console.error('Error evaluating GD:', error);
      alert(error.response?.data?.error || 'Error evaluating GD round. Please try again.');
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
    if (synthRef.current) synthRef.current.cancel();
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleForceSubmit = async () => {
    if (window.confirm('Are you sure you want to end the GD round early?')) {
      if (turnStateRef.current === 'RECORDING_USER' && currentSpeakerRef.current === 'user') {
        try { await stopUserSpeaking('force-submit'); } catch (e) { console.warn('Failed to close user turn:', e); }
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
          <button onClick={() => { stopAllMediaTracks(); onClose(); }} className="hover:bg-white/20 p-2 rounded-lg transition">
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
                <div className="bg-gray-900 rounded-lg overflow-hidden aspect-video mb-4 relative">
                  {mediaStreamRef.current ? (
                    <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-500 flex-col">
                      <Video className="h-12 w-12 mx-auto mb-2" />
                      <p>Camera initializing...</p>
                    </div>
                  )}
                  {!cameraEnabled && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                      <Video className="h-12 w-12 text-white/50" />
                    </div>
                  )}
                </div>

                {/* Mic conflict / health banner - ALWAYS visible in the active phase
                    (not just during the user's turn): another app taking the mic can
                    happen while an AI agent is speaking too. */}
                {micIssue && (
                  <div className="mb-4 p-4 bg-red-50 border-2 border-red-300 rounded-lg flex items-start gap-3 text-red-900">
                    <MicOff className="h-5 w-5 flex-shrink-0 text-red-600 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-bold">Microphone problem detected</p>
                      <p className="text-sm mt-0.5">{micIssue}</p>
                      <button
                        type="button"
                        onClick={restoreMicrophone}
                        className="mt-2 flex items-center gap-2 px-3 py-1.5 rounded-lg text-white font-medium text-xs transition bg-red-600 hover:bg-red-700 active:scale-95"
                      >
                        <Mic className="h-3.5 w-3.5" />
                        Restore Microphone
                      </button>
                    </div>
                  </div>
                )}

                {/* Current Speaker Indicator */}
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-bold mb-2 flex items-center gap-2 text-gray-800">
                    <MessageCircle className="h-5 w-5 text-blue-600" />
                    Current Speaker:
                  </h4>
                  {currentSpeaker === 'user' ? (
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="flex items-center gap-2">
                        <div className="h-3 w-3 bg-red-600 rounded-full animate-pulse"></div>
                        <span className="font-semibold text-gray-900">You are speaking...</span>
                        {isRecording && <span className="text-xs text-red-600 font-medium animate-pulse">(Mic Live)</span>}
                        {sttState === 'WAITING_USER_RETRY' && (
                          <span className="text-xs text-orange-700 font-semibold animate-pulse">No speech detected - waiting for you to try again</span>
                        )}
                      </div>

                      {/* Active Engine Badge */}
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium flex items-center gap-1.5 ${
                        sttMode === 'browser'
                          ? 'bg-blue-100 text-blue-800 border border-blue-200'
                          : 'bg-amber-100 text-amber-800 border border-amber-200'
                      }`}>
                        {sttMode === 'browser' ? (
                          <>
                            <Mic className="h-3.5 w-3.5 text-blue-600" />
                            Browser Speech Recognition (Live)
                          </>
                        ) : (
                          <>
                            <WifiOff className="h-3.5 w-3.5 text-amber-600" />
                            Offline Whisper Fallback (Server AI)
                          </>
                        )}
                      </span>

                      {/* Transcribing State Pill */}
                      {sttState === 'PROCESSING' && (
                        <span className="text-xs bg-indigo-100 text-indigo-800 border border-indigo-200 px-2.5 py-1 rounded-full font-medium flex items-center gap-1.5 animate-pulse">
                          <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-600" />
                          Transcribing audio with Whisper AI...
                        </span>
                      )}
                    </div>
                  ) : currentSpeaker ? (
                    <div className="flex items-center gap-3">
                      <div className="h-3 w-3 bg-green-600 rounded-full animate-pulse"></div>
                      <span className="font-medium">
                        {isGeneratingAIResponse ? 'AI agent thinking...' : aiAgents.find(a => a.id === currentSpeaker)?.name}
                      </span>
                      {isGeneratingAIResponse && <Loader2 className="h-4 w-4 animate-spin" />}
                    </div>
                  ) : (
                    <span className="text-gray-600">Waiting for next speaker...</span>
                  )}
                </div>

                {/* User Response Input (when speaking) */}
                {currentSpeaker === 'user' && (
                  <div className="mt-4 bg-white p-4 rounded-lg border-2 border-blue-600 shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-semibold text-gray-700">Your Response:</label>
                      <div className="text-xs text-gray-500 flex items-center gap-2">
                        {sttState === 'LISTENING' && (
                          <span className="flex items-center gap-1 text-green-700 font-medium">
                            <span className="h-2 w-2 rounded-full bg-green-500 animate-ping"></span>
                            Listening & Recording
                          </span>
                        )}
                        {sttState === 'PROCESSING' && (
                          <span className="flex items-center gap-1 text-indigo-700 font-medium">
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            Transcribing...
                          </span>
                        )}
                        {sttState === 'FALLBACK' && (
                          <span className="flex items-center gap-1 text-amber-700 font-medium">
                            <WifiOff className="h-3.5 w-3.5" />
                            Offline Mode Active
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Informative notification banner when in Fallback mode */}
                    {aiUnavailable && (
                      <div className="mb-3 p-3 rounded-lg bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm">
                        AI agent voice is unavailable right now (AI service not configured or unreachable). Add a working GOOGLE_API_KEY to backend/.env and restart the backend. Agents will keep to the topic with scripted points meanwhile.
                      </div>
                    )}
                    {sttState === 'FALLBACK' && sttError && (
                      <div className="mb-3 p-2.5 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2 text-amber-800 text-xs">
                        <WifiOff className="h-4 w-4 flex-shrink-0 text-amber-600" />
                        <span>{sttError}</span>
                      </div>
                    )}

                    {/* No-speech retry banner - the user gets another opportunity to speak */}
                    {sttState === 'WAITING_USER_RETRY' && sttError && !offTopicHint && (
                      <div className="mb-3 p-3 bg-orange-50 border border-orange-300 rounded-lg flex items-start gap-2 text-orange-800 text-sm">
                        <AlertCircle className="h-4 w-4 flex-shrink-0 text-orange-600 mt-0.5" />
                        <span>{sttError}</span>
                      </div>
                    )}

                    {/* Off-topic continuation banner - the floor was handed back so the
                        speaker can continue with points related to the topic */}
                    {offTopicHint && (
                      <div className="mb-3 p-3 bg-orange-50 border-2 border-orange-400 rounded-lg flex items-start gap-2 text-orange-900 text-sm">
                        <AlertCircle className="h-5 w-5 flex-shrink-0 text-orange-600 mt-0.5" />
                        <div>
                          <p className="font-bold">That was not related to the topic.</p>
                          <p className="mt-0.5">Please continue with points related to the topic — the mic is yours again.</p>
                        </div>
                      </div>
                    )}

                    {/* Error Banner */}
                    {sttState === 'ERROR' && sttError && (
                      <div className="mb-3 p-2.5 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-800 text-xs">
                        <AlertCircle className="h-4 w-4 flex-shrink-0 text-red-600" />
                        <span>{sttError}</span>
                      </div>
                    )}

                    <textarea
                      value={userResponse}
                      onChange={(e) => {
                        setUserResponse(e.target.value);
                        userResponseRef.current = e.target.value;
                      }}
                      className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-gray-800 text-sm leading-relaxed"
                      rows="3"
                      placeholder={
                        sttMode === 'whisper'
                          ? "Recording speech... your words will be transcribed by Whisper when you finish speaking (or type here directly)."
                          : "Start speaking... live transcript appears here automatically (or type manually)."
                      }
                      disabled={sttState === 'PROCESSING'}
                    />

                    {interimTranscript && sttMode === 'browser' && (
                      <p className="mt-1.5 text-xs text-blue-600 italic">
                        Live speech: &quot;{interimTranscript}&quot;
                      </p>
                    )}

                    <div className="mt-3 flex items-center justify-between">
                      {sttState === 'WAITING_USER_RETRY' ? (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => startUserSpeaking('retry')}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg text-white font-medium text-sm transition bg-blue-600 hover:bg-blue-700 active:scale-95"
                          >
                            <Mic className="h-4 w-4" />
                            Try Speaking Again
                          </button>
                          {userResponse.trim() && (
                            <button
                              onClick={submitTypedResponse}
                              className="flex items-center gap-2 px-4 py-2 rounded-lg text-white font-medium text-sm transition bg-green-600 hover:bg-green-700 active:scale-95"
                            >
                              <Check className="h-4 w-4" />
                              Submit Response
                            </button>
                          )}
                        </div>
                      ) : (
                        <button
                          onClick={() => stopUserSpeaking('manual-stop')}
                          disabled={sttState === 'PROCESSING'}
                          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-white font-medium text-sm transition ${
                            sttState === 'PROCESSING'
                              ? 'bg-gray-400 cursor-not-allowed'
                              : 'bg-red-600 hover:bg-red-700 active:scale-95'
                          }`}
                        >
                          {sttState === 'PROCESSING' ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              Transcribing...
                            </>
                          ) : (
                            <>
                              <MicOff className="h-4 w-4" />
                              Stop Speaking
                            </>
                          )}
                        </button>
                      )}

                      {userResponse && (
                        <button
                          type="button"
                          onClick={() => {
                            setUserResponse('');
                            userResponseRef.current = '';
                            finalTranscriptRef.current = '';
                            setInterimTranscript('');
                          }}
                          className="text-xs text-gray-500 hover:text-red-600 underline"
                        >
                          Clear Text
                        </button>
                      )}
                    </div>
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
                      <div className="h-8 w-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">Y</div>
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
                        {agent.hasSpoken && <Check className="h-4 w-4 text-green-600 ml-auto" />}
                      </div>
                    </div>
                  ))}
                </div>
                {/* Microphone selection - the chosen deviceId is passed through
                    getUserMedia with graceful fallback to the default mic. */}
                {micDevices.length > 1 && (
                  <div className="mt-4 bg-white rounded-lg border p-3">
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Microphone</label>
                    <select
                      value={selectedMicDeviceId}
                      onChange={(e) => {
                        const deviceId = e.target.value;
                        setSelectedMicDeviceId(deviceId);
                        selectedMicDeviceIdRef.current = deviceId;
                        console.log(`[Mic] Selected device: ${deviceId || 'default microphone'}`);
                        // Store the new deviceId; the NEXT recording uses the
                        // newly selected device. Stop the old stream now so no
                        // stale capture keeps running, but do NOT touch the
                        // current turn state: if a turn is active, the turn-start
                        // mic guarantee re-acquires a live stream from the new
                        // device before recording continues.
                        if (mediaStreamRef.current || audioStreamRef.current) {
                          mediaStreamRef.current?.getTracks().forEach(t => { try { t.stop(); } catch (err) {} });
                          audioStreamRef.current?.getTracks().forEach(t => { try { t.stop(); } catch (err) {} });
                          mediaStreamRef.current = null;
                          audioStreamRef.current = null;
                        }
                        if (!(turnStateRef.current === 'RECORDING_USER' && currentSpeakerRef.current === 'user')) {
                          restoreMicrophone();
                        }
                      }}
                      className="w-full text-xs border rounded-lg px-2 py-1.5 bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    >
                      <option value="">Default microphone</option>
                      {micDevices.map((d) => (
                        <option key={d.deviceId} value={d.deviceId}>
                          {d.label || `Microphone ${d.deviceId.slice(0, 6)}`}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
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
              <p className="mt-2 opacity-90">out of {results.all_participants?.length} participants</p>
              {(() => {
                const me = results.all_participants?.find(p => p.type === 'student');
                const pct = me ? Math.round(me.total_score) : 0;
                return (
                  <div className="mt-4 bg-white/15 rounded-lg p-3">
                    <div className="text-sm opacity-90">Final Score (exact, weighted)</div>
                    <div className="text-3xl font-bold">{me?.total_score?.toFixed(2) ?? '0.00'} / 100</div>
                    <div className="text-sm opacity-90">Score Percentage: <span className="font-bold">{pct}%</span></div>
                  </div>
                );
              })()}
            </div>

            {/* Topic relevance verdict - off-topic speech is explicitly flagged */}
            {results.topic_related === false && (
              <div className="max-w-2xl mx-auto mb-6 p-4 bg-red-50 border-2 border-red-300 rounded-lg text-red-800">
                <p className="font-bold flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  Your speech was NOT related to the topic.
                </p>
                <p className="text-sm mt-1">
                  Your points did not relate to the discussion topic, so the score is heavily reduced.
                  Next time, speak points that are directly related to the topic.
                </p>
              </div>
            )}

            {/* Top 3 Performers */}
            <div className="mb-8">
              <h4 className="text-xl font-bold mb-4 text-center">Top 3 Performers</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
                {results.top_3?.map((participant, index) => (
                  <div
                    key={participant.id}
                    className={`p-6 rounded-lg border-2 text-center ${
                      participant.type === 'student' ? 'border-blue-600 bg-blue-50' : 'border-gray-300 bg-white'
                    }`}
                  >
                    <div className={`text-4xl font-bold mb-2 ${
                      index === 0 ? 'text-yellow-500' : index === 1 ? 'text-gray-400' : 'text-orange-600'
                    }`}>
                      #{index + 1}
                    </div>
                    <p className="font-bold text-lg mb-1">{participant.name}</p>
                    <p className="text-sm text-gray-600 mb-3">{participant.type === 'student' ? 'You' : 'AI Agent'}</p>
                    <div className="text-2xl font-bold text-blue-600">{participant.total_score?.toFixed(2)}</div>
                    <p className="text-sm text-gray-600">Total Score</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Your Detailed Scores */}
            {results.all_participants?.find(p => p.type === 'student') && (
              <div className="max-w-3xl mx-auto">
                <h4 className="text-xl font-bold mb-4">Your Detailed Performance</h4>
                <div className="bg-white rounded-lg border p-6">
                  {Object.entries(results.all_participants.find(p => p.type === 'student').scores || {}).map(([criterion, data]) => (
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
                      <p className="text-xs text-gray-600 mt-1">
                        Weight: {data.weight}% · Weighted contribution: {((data.score * data.weight) / 100).toFixed(2)} points
                      </p>

                      {/* Evaluator evidence quote + reason (transparent scoring) */}
                      {(() => {
                        const fb = (results.criterion_feedback || {})[criterion];
                        if (!fb || (!fb.evidence && !fb.reason)) return null;
                        const evidenceNone = !fb.evidence || fb.evidence.toLowerCase() === 'none';
                        return (
                          <div className="mt-2 bg-gray-50 border-l-4 border-blue-400 pl-3 py-2 rounded-r">
                            <p className="text-xs text-gray-700">
                              <span className="font-semibold">Evidence:</span>{' '}
                              {evidenceNone
                                ? <span className="italic text-gray-500">No relevant quote found in your speech</span>
                                : <span className="italic">“{fb.evidence}”</span>}
                            </p>
                            {fb.reason && (
                              <p className="text-xs text-gray-600 mt-1">
                                <span className="font-semibold">Reason:</span> {fb.reason}
                              </p>
                            )}
                          </div>
                        );
                      })()}
                    </div>
                  ))}
                  {(() => {
                    const me = results.all_participants.find(p => p.type === 'student');
                    // Backend-authoritative total: the weighted total is
                    // calculated ONCE in the backend (and validated there).
                    // Recomputing it here could drift from the backend value
                    // and from the rank that was derived from it.
                    const weighted = typeof me?.total_score === 'number'
                      ? me.total_score
                      : Object.values(me?.scores || {}).reduce((acc, d) => acc + (d.score * d.weight) / 100, 0);
                    return (
                      <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between items-center">
                        <span className="font-bold text-gray-800">Exact Total (weighted)</span>
                        <span className="text-2xl font-bold text-blue-600">
                          {weighted.toFixed(2)} / 100 ({Math.round(weighted)}%)
                        </span>
                      </div>
                    );
                  })()}
                </div>
              </div>
            )}

            <div className="text-center mt-8">
              <button
                onClick={() => { stopAllMediaTracks(); onComplete(results); onClose(); }}
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
