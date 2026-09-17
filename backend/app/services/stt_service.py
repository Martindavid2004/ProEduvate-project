"""
stt_service.py — Faster-Whisper STT service with transcript validation.

Changes vs original:
  - validate_transcript() layer: rejects garbage/repetitive/empty output
  - Per-segment quality signals returned in meta (avg_logprob, no_speech, cr)
  - Minimum-duration guard before inference (skip <0.3s blobs)
  - Audio probe always returned for diagnostic use
  - Status field: VALID / LOW_CONFIDENCE / INVALID / NO_SPEECH
  - All original Whisper parameters preserved
"""
import os
import re
import time
import logging
import threading
import traceback

logger = logging.getLogger("stt")


def _ensure_cuda_dll_paths():
    """Make cuBLAS/cuDNN DLLs from the pip 'nvidia-*' wheels visible to
    ctranslate2 on Windows. Without this, CUDA inference fails with
    'RuntimeError: Library cublas64_12.dll is not found or cannot be loaded'
    even though the GPU is detected. Must run BEFORE ctranslate2 loads a
    CUDA model. Harmless on CPU-only machines (dirs simply don't exist)."""
    import glob
    try:
        import ctranslate2  # noqa: F401 - ensure matching install exists
        site = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "..", "..", "..", ".venv", "Lib", "site-packages"))
        dll_dirs = []
        for pkg in ("nvidia.cublas", "nvidia.cudnn", "nvidia.cuda_nvrtc"):
            dll_dirs += glob.glob(os.path.join(site, pkg.replace(".", os.sep), "bin"))
        if dll_dirs:
            os.environ["PATH"] = ";".join(dll_dirs) + ";" + os.environ.get("PATH", "")
            logger.info("[STT] CUDA DLL paths added from pip wheels: %d dir(s)", len(dll_dirs))
    except Exception as e:
        logger.debug("[STT] CUDA DLL path bootstrap skipped: %s", e)


_ensure_cuda_dll_paths()

try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    WhisperModel = None
    HAS_FASTER_WHISPER = False


class AudioValidationError(ValueError):
    """Raised when the uploaded audio cannot be decoded (HTTP 422)."""
    pass


class ModelUnavailableError(RuntimeError):
    """Raised when the Whisper model cannot be loaded (HTTP 503)."""


# Transcript validation status values
TRANSCRIPT_VALID        = "VALID"
TRANSCRIPT_LOW_CONF     = "LOW_CONFIDENCE"
TRANSCRIPT_INVALID      = "INVALID"
TRANSCRIPT_NO_SPEECH    = "NO_SPEECH"

# Whitelist of extensions the pipeline can realistically handle.
ALLOWED_AUDIO_EXTENSIONS = {'.webm', '.wav', '.ogg', '.mp4', '.mp3', '.m4a', '.mpga', '.mpeg'}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


# ---------------------------------------------------------------------------
# Transcript validation layer
# ---------------------------------------------------------------------------

def _count_repeated_pattern(words):
    """Return the fraction of words that are exact copies of the previous word.
    E.g. ['9','9','9','9'] -> 0.75  (3 out of 4 are repeats of the prior).
    A legitimate speaker like 'I think AI, AI, AI is changing' -> 0.27 (2/7).
    Threshold for 'garbage': > 0.50."""
    if len(words) <= 1:
        return 0.0
    repeats = sum(1 for i in range(1, len(words)) if words[i] == words[i - 1])
    return repeats / (len(words) - 1)


def _is_pure_numeric_sequence(words):
    """Return True if the transcript is entirely (or almost entirely) numeric
    tokens with very high repetition — e.g. '9 9 9 9 9 9 9'."""
    if not words:
        return False
    numeric = [w for w in words if re.match(r'^\d+$', w)]
    # ≥80% numeric AND repetition fraction > 0.5
    if len(numeric) / len(words) >= 0.8:
        rep = _count_repeated_pattern(words)
        if rep > 0.5:
            return True
    return False


def _exceeds_repetition_threshold(words, threshold=0.55):
    """Return True if consecutive word-repetition fraction exceeds threshold.
    A deliberate stutter like 'I I I think' won't exceed 0.55 unless the
    recording is a true loop of one word."""
    return _count_repeated_pattern(words) > threshold


def _has_invalid_characters(text):
    """Detect transcripts that contain only symbols/numbers/nonsense with no
    alphabetic content — a sign of decoder garbage output."""
    letters = sum(1 for c in text if c.isalpha())
    return len(text) > 10 and letters / max(len(text), 1) < 0.4


def _word_count_vs_duration_plausible(word_count, duration_seconds):
    """Human speech is roughly 100-200 words per minute (1.7-3.3 wpm).
    A 3s clip with 80 words is impossible — flag as suspicious hallucination.
    A 30s clip with 0 words means silence."""
    if duration_seconds is None or duration_seconds <= 0:
        return True  # can't check — give benefit of the doubt
    wpm = (word_count / duration_seconds) * 60
    # Allow 0 wpm (silence) up to 300 wpm (very fast speech with pauses)
    return 0 <= wpm <= 300


def validate_transcript(text, audio_duration=None):
    """Validate transcript quality. Returns (status, reason).

    STATUS values:
      VALID          — transcript looks genuine, use for AI evaluation
      LOW_CONFIDENCE — borderline, surface to user but don't score blindly
      INVALID        — garbage/repetition/hallucination, reject
      NO_SPEECH      — empty or effectively empty, ask user to retry

    This does NOT correct or rewrite the text — it only classifies it.
    """
    if not text or not text.strip():
        return TRANSCRIPT_NO_SPEECH, "Empty transcript"

    stripped = text.strip()
    words = stripped.lower().split()
    word_count = len(words)

    # 1. Extremely short (single word or very few characters)
    if word_count < 2 or len(stripped) < 4:
        # A single word (like "Agreed" or "Yes") could be a legitimate short answer.
        # Strip trailing punctuation for the alpha check.
        clean_word = re.sub(r'[^a-zA-Z]', '', words[0]) if words else ''
        if word_count == 1 and clean_word and len(clean_word) >= 2:
            return TRANSCRIPT_LOW_CONF, f"Single word response ({clean_word!r}) — may be valid but unverifiable"
        return TRANSCRIPT_NO_SPEECH, f"Transcript too short ({word_count} word(s))"

    # 2. Pure numeric repetition loop: "9 9 9 9 9" / "1 2 1 2 1 2"
    if _is_pure_numeric_sequence(words):
        return TRANSCRIPT_INVALID, "Transcript consists of repeated numeric tokens (decoder loop)"

    # 3. Consecutive word repetition above threshold
    rep_frac = _count_repeated_pattern(words)
    if rep_frac > 0.55:
        return TRANSCRIPT_INVALID, (
            f"Transcript has {rep_frac:.0%} consecutive word repetition — "
            "likely a decoder hallucination loop"
        )

    # 4. Invalid characters / non-alphabetic dominance
    if _has_invalid_characters(stripped):
        return TRANSCRIPT_INVALID, "Transcript contains insufficient alphabetic content"

    # 5. Word count vs audio duration plausibility
    if not _word_count_vs_duration_plausible(word_count, audio_duration):
        wpm = (word_count / audio_duration) * 60 if audio_duration else 0
        return TRANSCRIPT_INVALID, (
            f"Implausible word rate ({wpm:.0f} wpm for {audio_duration:.1f}s clip) — "
            "possible hallucination"
        )

    # 6. Borderline short (2-4 words) — mark as LOW_CONFIDENCE so caller
    #    can decide whether to accept it (might be a genuine short answer).
    if word_count <= 4:
        return TRANSCRIPT_LOW_CONF, f"Very short transcript ({word_count} words)"

    # 7. Moderately high repetition (0.35-0.55) — LOW_CONFIDENCE, not INVALID.
    #    Genuine stammering / GD filler "I think, I think, I think" can happen.
    if rep_frac > 0.35:
        return TRANSCRIPT_LOW_CONF, (
            f"Moderate word repetition ({rep_frac:.0%}) — "
            "may be genuine hesitation or decoder artifact"
        )

    return TRANSCRIPT_VALID, "OK"


# ---------------------------------------------------------------------------
# Audio probe
# ---------------------------------------------------------------------------

def _probe_audio(path):
    """Probe decoded audio properties with ffprobe."""
    info = {"file_size": os.path.getsize(path) if os.path.exists(path) else 0,
            "duration": None, "sample_rate": None, "channels": None, "format": None}
    try:
        import json
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=format_name,duration:stream=sample_rate,channels',
             '-of', 'json', path],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout or '{}')
        fmt = data.get('format') or {}
        streams = data.get('streams') or []
        info['format'] = fmt.get('format_name')
        try:
            info['duration'] = round(float(fmt.get('duration')), 2)
        except (TypeError, ValueError):
            pass
        if streams:
            st = streams[0]
            info['sample_rate'] = st.get('sample_rate')
            info['channels'] = st.get('channels')
    except Exception as e:
        logger.warning("ffprobe unavailable/failed: %s", e)
    return info


# ---------------------------------------------------------------------------
# Device/compute detection
# ---------------------------------------------------------------------------

def _detect_device_and_compute_type():
    """Detect available hardware and pick a safe compute type."""
    env_device = (os.getenv("WHISPER_DEVICE") or "").strip().lower()
    env_compute = (os.getenv("WHISPER_COMPUTE_TYPE") or "").strip().lower()

    cuda_requested = env_device in ("cuda", "auto", "gpu")
    cuda_ok = False
    if cuda_requested:
        try:
            import ctranslate2
            if ctranslate2.get_cuda_device_count() > 0:
                ctranslate2.get_supported_compute_types("cuda")
                cuda_ok = True
        except Exception as e:
            logger.warning("[STT] CUDA requested but unavailable (%s). Falling back to CPU.", e)

    if cuda_ok and env_device in ("cuda", "auto", "gpu"):
        device = "cuda"
        compute = env_compute if env_compute in ("int8_float16", "float16", "int8") else "int8_float16"
    elif env_device == "cpu":
        device = "cpu"
        compute = env_compute if env_compute in ("int8", "float32") else "int8"
    else:
        device = "cpu"
        compute = "int8"

    return device, compute


# ---------------------------------------------------------------------------
# STTService
# ---------------------------------------------------------------------------

class STTService:
    """Singleton service owning the one WhisperModel instance."""

    def __init__(self):
        self.model = None
        self._load_error = None
        self._lock = threading.Lock()
        self._infer_lock = threading.Lock()
        self.device = None
        self.compute_type = None
        self.model_size = (os.getenv("WHISPER_MODEL") or "base").strip().lower()
        self._transcription_count = 0

    # ------------- model lifecycle -------------

    @staticmethod
    def _cuda_smoke_test(model):
        import io
        import numpy as np
        import av
        buf = io.BytesIO()
        with av.open(buf, mode='w', format='wav') as container:
            stream = container.add_stream('pcm_s16le', rate=16000)
            stream.layout = 'mono'
            frame = av.AudioFrame.from_ndarray(
                np.zeros((1, 8000), dtype='int16'), format='s16', layout='mono')
            frame.sample_rate = 16000
            frame.pts = None
            for packet in stream.encode(frame):
                packet.stream = stream
                container.mux(packet)
            for packet in stream.encode(None):
                packet.stream = stream
                container.mux(packet)
        buf.seek(0)
        segments, _ = model.transcribe(buf, language="en", beam_size=1)
        list(segments)

    def _create_model(self):
        if not HAS_FASTER_WHISPER:
            raise ModelUnavailableError(
                "faster-whisper is not installed in the active Python environment."
            )
        device, compute = _detect_device_and_compute_type()
        logger.info("[STT] Model: %s", self.model_size)
        logger.info("[STT] Device: %s", device)
        logger.info("[STT] Compute type: %s", compute)
        try:
            model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute,
                download_root=os.getenv("WHISPER_DOWNLOAD_ROOT") or None,
            )
            if device == "cuda":
                self._cuda_smoke_test(model)
                logger.info("[STT] CUDA smoke test passed.")
        except Exception as e:
            if device == "cuda":
                logger.warning("[STT] CUDA unavailable (%s: %s). Falling back to CPU/int8.",
                               type(e).__name__, e)
                device, compute = "cpu", "int8"
                model = WhisperModel(self.model_size, device=device, compute_type=compute)
            else:
                raise
        self.device = device
        self.compute_type = compute
        return model

    def load_model(self):
        if self.model is not None:
            return self.model
        with self._lock:
            if self.model is not None:
                return self.model
            if self._load_error:
                raise ModelUnavailableError(self._load_error)
            try:
                self.model = self._create_model()
            except ModelUnavailableError:
                raise
            except Exception as e:
                self._load_error = None
                logger.error("[STT ERROR] Model load failed: %s\n%s", e, traceback.format_exc())
                raise ModelUnavailableError(
                    f"Whisper model could not be loaded: {type(e).__name__}: {e}"
                ) from e
        return self.model

    def warmup(self):
        try:
            import numpy as np
            import av
            import io
            buf = io.BytesIO()
            with av.open(buf, mode='w', format='wav') as container:
                stream = container.add_stream('pcm_s16le', rate=16000)
                stream.layout = 'mono'
                for _ in range(16):
                    frame = av.AudioFrame.from_ndarray(
                        np.zeros((1, 1600), dtype='int16'), format='s16', layout='mono')
                    frame.sample_rate = 16000
                    frame.pts = None
                    for packet in stream.encode(frame):
                        packet.stream = stream
                        container.mux(packet)
                for packet in stream.encode(None):
                    packet.stream = stream
                    container.mux(packet)
            buf.seek(0)
            import tempfile
            fd, path = tempfile.mkstemp(suffix='.wav')
            with os.fdopen(fd, 'wb') as f:
                f.write(buf.read())
            try:
                model = self.model
                if model is not None:
                    segments, _ = model.transcribe(path, language="en", beam_size=1)
                    list(segments)
            finally:
                if os.path.exists(path):
                    os.remove(path)
            logger.info("[STT] Warmup transcription completed.")
        except Exception as e:
            logger.warning("[STT] Warmup skipped: %s", e)

    # ------------- audio prep -------------

    def _convert_to_wav(self, input_path):
        base = os.path.splitext(input_path)[0]
        output_path = base + '_conv.wav'
        try:
            import subprocess
            subprocess.run([
                'ffmpeg', '-y', '-i', input_path,
                '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
                output_path
            ], check=True, capture_output=True, timeout=60)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info("[STT] Audio conversion completed: %s (%d bytes)",
                            os.path.basename(output_path), os.path.getsize(output_path))
                return output_path, True
            logger.warning("[STT] ffmpeg produced no output; will try direct PyAV decode")
            return input_path, False
        except FileNotFoundError:
            logger.warning("[STT] ffmpeg not found on PATH - relying on faster-whisper's built-in PyAV decoder")
            return input_path, False
        except Exception as e:
            logger.warning("[STT] ffmpeg conversion failed (%s) - relying on PyAV decode", e)
            return input_path, False

    # ------------- transcription -------------

    def transcribe(self, audio_file_path):
        """Transcribe an audio file with faster-whisper, English-optimized.

        Returns (text, metadata_dict).
        metadata_dict includes:
          - status: VALID / LOW_CONFIDENCE / INVALID / NO_SPEECH
          - validation_reason: human-readable reason for status
          - quality: {avg_logprob, max_no_speech_prob, max_compression_ratio, segment_count}
          - audio: {duration, sample_rate, channels, format, file_size}
          - device, model, infer_ms, total_ms, convert_ms

        Raises:
          AudioValidationError  -> HTTP 422
          ModelUnavailableError -> HTTP 503
          Other exceptions      -> HTTP 500
        """
        t_start = time.time()

        if not audio_file_path or not os.path.exists(audio_file_path):
            raise AudioValidationError("Audio file does not exist or invalid path.")

        size = os.path.getsize(audio_file_path)
        if size == 0:
            raise AudioValidationError("Audio file is empty.")

        # Probe audio before inference
        probe = _probe_audio(audio_file_path)
        logger.info(
            "[STT] Audio probe: size=%d bytes format=%s duration=%ss sample_rate=%s channels=%s",
            probe['file_size'], probe['format'], probe['duration'],
            probe['sample_rate'], probe['channels']
        )

        audio_duration = probe.get('duration')

        # Hard guard: audio with near-zero decoded duration is silence/corrupt
        if audio_duration is not None and audio_duration <= 0.05:
            raise AudioValidationError("Audio contains no decodable content (duration ~0).")

        # Soft guard: very short blobs (<0.3s) — skip inference, return NO_SPEECH
        if audio_duration is not None and audio_duration < 0.3:
            logger.info("[STT] Skipping inference: audio too short (%.2fs)", audio_duration)
            return "", {
                "status": TRANSCRIPT_NO_SPEECH,
                "validation_reason": f"Audio is too short ({audio_duration:.2f}s) to contain speech",
                "audio": probe,
                "device": self.device,
                "model": self.model_size,
                "infer_ms": 0,
                "total_ms": int((time.time() - t_start) * 1000),
                "convert_ms": 0,
                "quality": None,
            }

        model = self.load_model()

        t_convert = time.time()
        converted_path = None
        needs_conversion = not audio_file_path.lower().endswith('.wav')
        try:
            if needs_conversion:
                converted_path, _ = self._convert_to_wav(audio_file_path)
            target_path = converted_path if (converted_path and os.path.exists(converted_path)) else audio_file_path
            convert_ms = int((time.time() - t_convert) * 1000)

            if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
                raise AudioValidationError("Audio file is empty after conversion.")

            with self._infer_lock:
                t_infer = time.time()
                logger.info(
                    "[STT] Transcription started (model=%s device=%s compute=%s language=en)",
                    self.model_size, self.device, self.compute_type
                )

                params = dict(
                    language="en",
                    task="transcribe",
                    beam_size=5,
                    temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                    vad_filter=True,
                    vad_parameters={"min_silence_duration_ms": 2000},
                    condition_on_previous_text=False,
                    no_speech_threshold=0.6,
                    log_prob_threshold=-1.0,
                    compression_ratio_threshold=2.4,
                )

                def _run_transcribe(m):
                    segs, inf = m.transcribe(target_path, **params)
                    parts, logs = [], []
                    logprobs, no_speech_probs, compression_ratios = [], [], []
                    for seg in segs:
                        txt = seg.text.strip()
                        if txt:
                            parts.append(txt)
                        logprobs.append(seg.avg_logprob)
                        no_speech_probs.append(seg.no_speech_prob)
                        compression_ratios.append(seg.compression_ratio)
                        logs.append(
                            f"[{seg.start:.1f}s->{seg.end:.1f}s] "
                            f"lp={seg.avg_logprob:.2f} nsp={seg.no_speech_prob:.2f} "
                            f"cr={seg.compression_ratio:.2f} {txt!r}"
                        )
                    quality = {
                        "segment_count": len(logs),
                        "avg_logprob": round(sum(logprobs) / len(logprobs), 3) if logprobs else None,
                        "max_no_speech_prob": round(max(no_speech_probs), 3) if no_speech_probs else None,
                        "max_compression_ratio": round(max(compression_ratios), 3) if compression_ratios else None,
                    }
                    return " ".join(parts).strip(), inf, logs, quality

                try:
                    text, info, seg_logs, quality = _run_transcribe(model)
                except RuntimeError as rt_err:
                    msg = str(rt_err).lower()
                    if self.device == "cuda" and any(k in msg for k in ("cublas", "cudnn", "cuda", "vram", "gpu")):
                        logger.warning("[STT] CUDA inference failed (%s). Rebuilding on CPU.", rt_err)
                        with self._lock:
                            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                            self.device, self.compute_type = "cpu", "int8"
                        model = self.model
                        text, info, seg_logs, quality = _run_transcribe(model)
                    elif type(rt_err).__module__.startswith("av.") or "invalid data" in msg:
                        raise AudioValidationError(
                            f"Audio could not be decoded ({rt_err})."
                        ) from rt_err
                    else:
                        raise
                except Exception as other_err:
                    if type(other_err).__module__.startswith("av.") or "invalid data" in str(other_err).lower():
                        raise AudioValidationError(
                            f"Audio could not be decoded ({other_err})."
                        ) from other_err
                    raise

            self._transcription_count += 1
            infer_ms = int((time.time() - t_infer) * 1000)
            total_ms = int((time.time() - t_start) * 1000)

            logger.info(
                "[STT] Raw transcript completed: chars=%d segments=%d audio_duration=%ss infer=%dms total=%dms",
                len(text), len(seg_logs), getattr(info, 'duration', None), infer_ms, total_ms
            )
            logger.info("[STT] Raw transcript: %r", text)
            for line in seg_logs:
                logger.debug("  %s", line)

            # ---- Transcript validation ----
            audio_dur = audio_duration or getattr(info, 'duration', None)
            status, reason = validate_transcript(text, audio_duration=audio_dur)

            # Quality-signal downgrade: high no_speech_prob across all segments
            # suggests the audio had almost no voice activity but Whisper still
            # generated tokens (a known hallucination mode).
            if (status == TRANSCRIPT_VALID
                    and quality.get("max_no_speech_prob") is not None
                    and quality["max_no_speech_prob"] > 0.85):
                status = TRANSCRIPT_LOW_CONF
                reason = f"High no-speech probability ({quality['max_no_speech_prob']:.2f}) — possible hallucination"

            # Low average log probability means the model was very uncertain
            if (status == TRANSCRIPT_VALID
                    and quality.get("avg_logprob") is not None
                    and quality["avg_logprob"] < -1.2):
                status = TRANSCRIPT_LOW_CONF
                reason = f"Low average log probability ({quality['avg_logprob']:.2f}) — low confidence transcription"

            logger.info("[STT] Validation result: status=%s reason=%s", status, reason)

            meta = {
                "status": status,
                "validation_reason": reason,
                "device": self.device,
                "compute_type": self.compute_type,
                "model": self.model_size,
                "language": getattr(info, "language", "en"),
                "audio": probe,
                "quality": quality,
                "convert_ms": convert_ms,
                "infer_ms": infer_ms,
                "total_ms": total_ms,
            }

            # For INVALID/NO_SPEECH return empty text so callers don't use the text
            if status in (TRANSCRIPT_INVALID, TRANSCRIPT_NO_SPEECH):
                logger.info("[STT] Transcript rejected: %s — %s", status, reason)
                return "", meta

            return text, meta

        finally:
            if converted_path and converted_path != audio_file_path and os.path.exists(converted_path):
                try:
                    os.remove(converted_path)
                except Exception as e:
                    logger.warning("Error removing temp converted file %s: %s", converted_path, e)


# Singleton STTService instance shared across all requests
stt_service = STTService()
