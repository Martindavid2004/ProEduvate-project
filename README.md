# ProEduVate — AI-Powered Learning & Career Preparation Platform

[![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB?logo=react&logoColor=black)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask%203.0-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB%20Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Gemini AI](https://img.shields.io/badge/AI%20Engine-Google%20Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styles-Tailwind%20CSS-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

**ProEduVate** is an advanced, end-to-end Learning Management and Campus Placement Preparation platform. Designed for students, educators, and administrators, ProEduVate integrates cutting-edge generative AI to deliver realistic mock interviews, interactive Group Discussion simulations, intelligent aptitude training, ATS resume scoring, and coding execution sandboxes.

---

## 🚀 Key Modules & Features

### 🎙️ 1. AI Group Discussion (GD) Simulator
- **Interactive Multi-Agent Environment**: Engage with AI peer participants powered by Google Gemini and OpenAI.
- **Dual-Engine Speech Recognition**:
  - **Browser Web Speech API**: Fast, real-time client-side live transcription.
  - **Offline Whisper Fallback**: Robust server-side transcription using `faster-whisper` (handles browser network blocks, Brave shields, or offline states automatically).
- **Live Video & Audio Feed**: Realistic virtual GD conference room with turn-taking logic, countdown timers, and live speaking visualizer.
- **Detailed Evaluation Matrix**: Instant feedback on communication skills, logical reasoning, team dynamics, leadership, and actionable improvement pointers.

### 🧠 2. Aptitude & Reasoning Training
- Comprehensive repository of quantitative aptitude, logical reasoning, and verbal topics.
- Concept notes, practice question sets, and real-time timed assessments with score tracking.

### 💼 3. AI Mock Interviews (Technical & HR)
- Adaptive question generation tailored to the candidate's target job role and experience.
- Instant scoring, answer critique, and behavioral feedback.

### 📄 4. ATS Resume Analyzer & Study Chatbot
- **ATS Resume Parser**: Uses PyMuPDF and Gemini to evaluate resumes against industry job descriptions, highlighting keyword matches and missing skills.
- **AI Academic Tutor**: 24/7 contextual assistant for clearing student doubts across programming, engineering, and career prep.

### 💻 5. Coding Sandbox & Judge
- Multi-language code editor with syntax highlighting.
- Code execution powered by self-hosted **Judge0** (Docker) or **AWS Lambda**.

### 👥 6. Role-Based Management Portals
- **Dual-mode Authentication**: Login using either email or username with secure JWT and bcrypt hashing.
- **Student Portal**: Manage learning paths, take assessments, view GD evaluation cards, and track placement readiness.
- **Teacher & Admin Portal**: Manage students, assignments, batch performance analytics, and GD round configurations.

---

## 🏗️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, React Router v6, Tailwind CSS, Lucide Icons, Recharts, Axios |
| **Backend** | Python (3.10 - 3.14), Flask 3.0, PyMongo, PyJWT, Werkzeug |
| **AI & ML** | Google Generative AI (`google-generativeai`), Faster-Whisper, OpenAI API |
| **Database** | MongoDB Atlas / Local MongoDB |
| **Execution Engine** | Judge0 (PostgreSQL, Redis, Docker), AWS Lambda (optional) |
| **Deployment** | Netlify (Frontend SPA), Render / VPS (Backend API) |

---

## 📂 Project Structure

```plaintext
ProEduvate-project/
├── backend/
│   ├── app/
│   │   ├── models/           # Data models and schemas
│   │   ├── routes/           # Flask API route blueprints (auth, gd, student, teacher, admin, etc.)
│   │   ├── services/         # Business logic (ai_service, gd_service, stt_service, etc.)
│   │   └── database.py       # MongoDB client initialization
│   ├── uploads/              # Uploaded resumes and audio blobs
│   ├── .env.example          # Environment variables template
│   ├── requirements.txt      # Python dependencies
│   └── run.py                # Flask server entry point
├── frontend/
│   ├── public/               # HTML template and static assets
│   ├── src/
│   │   ├── components/       # Reusable components (GDRound, Navbar, etc.)
│   │   ├── context/          # React Context (AuthContext, DataContext)
│   │   ├── pages/            # Page views (StudentPage, TeacherDashboard, Login, etc.)
│   │   └── services/         # API service wrappers (Axios)
│   ├── package.json          # Node dependencies and scripts
│   └── tailwind.config.js    # Tailwind CSS configuration
├── whisper.cpp/              # Vendored whisper.cpp source (optional native STT engine)
├── docker-compose.yml        # Self-hosted Judge0 code runner
├── netlify.toml              # Netlify SPA redirect rules
├── make_backup_zip.py        # Project backup zip helper (light/full modes)
└── README.md
```

---

## ⚙️ Getting Started

### Prerequisites
- **Python**: Version `3.10` to `3.14` installed.
- **Node.js**: Version `18.x` or higher and `npm`.
- **MongoDB**: Active MongoDB Atlas cluster or local MongoDB instance.
- **Google Gemini API Key**: Obtainable from [Google AI Studio](https://aistudio.google.com/).
- *(Optional)* **FFmpeg**: Recommended for audio format conversion in offline speech recognition.

---

### 1. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment** *(recommended)*:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   > **Note for Python 3.14**: Ensure `protobuf>=5.29.0` is installed (already included in `requirements.txt`).

4. **Configure environment variables**:
   Create a `.env` file in the `backend/` directory by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Configure your keys:
   ```ini
   MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/proeduvate?retryWrites=true&w=majority
   GOOGLE_API_KEY=your_google_gemini_api_key
   JWT_SECRET=your_secret_jwt_key
   SECRET_KEY=your_flask_secret_key
   WHISPER_DEVICE=cpu
   WHISPER_COMPUTE_TYPE=int8
   ```

5. **Start the backend development server**:
   ```bash
   python run.py
   ```
   *The API will start at `http://127.0.0.1:5000`.*

---

### 2. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Install Node modules**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   Create a `.env` file in the `frontend/` directory:
   ```ini
   REACT_APP_API_URL=http://127.0.0.1:5000/api
   ```

4. **Start the React dev server**:
   ```bash
   npm start
   ```
   *The application will open at `http://localhost:3000`.*

---

### 3. Code Execution Sandbox (Optional)

If running the local coding playground with Judge0:
```bash
# In the root project directory:
docker-compose up -d
```
The Judge0 server will listen on port `2358`.

---

### 4. whisper.cpp (Optional — vendored native STT engine)

The repository vendors [whisper.cpp](https://github.com/ggml-org/whisper.cpp) under `whisper.cpp/`. The backend's offline speech-to-text fallback uses the Python `faster-whisper` package (installed via `requirements.txt`), so **building whisper.cpp is not required** for normal use. Build it only if you want to test the native engine or regenerate its tooling.

**Prerequisites**: [CMake](https://cmake.org/download/) ≥ 3.14 and a C/C++ compiler (MSVC on Windows, `build-essential` on Linux, Xcode CLT on macOS).

1. **Build from the repo root**:
   ```bash
   cd whisper.cpp
   cmake -B build
   cmake --build build --config Release -j
   ```
   Binaries land in `whisper.cpp/build/bin/` (e.g. `whisper-cli`).

2. **Download a model** *(the ggml model binaries are not committed — `whisper.cpp/models/` ships only download/convert scripts)*:
   ```bash
   # Windows (PowerShell / cmd)
   models\download-ggml-model.cmd base.en

   # macOS / Linux
   bash models/download-ggml-model.sh base.en
   ```
   Choose `tiny.en`/`base.en` for fast CPU tests, `small`/`medium` for higher accuracy.

3. **Sanity-check the build**:
   ```bash
   ./build/bin/whisper-cli -m models/ggml-base.en.bin -f samples/jfk.wav
   ```

> **Tip**: clean a previous build with `cmake --build build --target clean` or just delete `whisper.cpp/build/`.

---

## 🔍 Speech Recognition & Offline Fallback Details

In the Group Discussion module, speech-to-text operates with a resilient hybrid architecture:

1. **Browser Web Speech API (`webkitSpeechRecognition`)**:
   - Used for immediate, interactive transcript display.
   - In some browsers (such as Brave, Chromium with strict network restrictions, or offline setups), the browser may emit:
     ```
     Speech recognition error: network
     Speech recognition network error - using offline transcription fallback
     ```
2. **Backend Whisper Fallback (`faster-whisper`)**:
   - When the browser speech service is unreachable, the system automatically captures audio via the HTML5 `MediaRecorder` API.
   - Upon releasing the microphone or finishing a turn, the recorded audio chunk is dispatched to `/api/gd/transcribe`.
   - The backend processes the audio on CPU or GPU with `faster-whisper` and returns high-accuracy transcriptions without requiring external speech cloud connections.

---

## 🌐 Production Deployment

### Frontend (Netlify)
The frontend includes a pre-configured `netlify.toml` with Single Page Application (SPA) routing rewrites.
- Set Build command: `npm run build`
- Set Publish directory: `build`
- Add environment variable: `REACT_APP_API_URL=https://your-backend-api.onrender.com/api`

### Backend (Render / VPS)
- Set Environment to Python 3.
- Set Build command: `pip install -r requirements.txt`
- Set Start command: `gunicorn -w 4 -b 0.0.0.0:$PORT run:app`
- Provide production environment variables (`MONGO_URI`, `GOOGLE_API_KEY`, `JWT_SECRET`, `SECRET_KEY`).

---

## 💾 Project Backup Zip

A helper script creates portable zip archives of the whole project:

```bash
# From the repo root (uses any Python 3.10+):
python make_backup_zip.py                    # light: source only, ~15 MB
python make_backup_zip.py --mode full        # full offline: deps + builds + models (multi-GB)
python make_backup_zip.py --out D:\backups\proj.zip
python make_backup_zip.py --out - > proj.zip # stream to stdout
```

| Mode | Includes | Excludes | Output (default) |
| :--- | :--- | :--- | :--- |
| `light` *(default)* | All source, configs, test assets | venvs, `node_modules`, `build/` outputs, `whisper.cpp/models` binaries, caches, logs, `.env` secrets | `../project-backup.zip` |
| `full` | Everything to run offline: `node_modules`, `.venv`, `backend/venv`, build artifacts, models | Only `.git`, `.freebuff`, `.uv-cache2`, `__pycache__`, `*.pyc` | `../project-full-backup.zip` |

**Notes**
- The script never follows symlinks/junctions, supports Windows long paths (>260 chars), and skips unreadable files — exiting with code `2` and listing skipped paths on stderr.
- After extracting a **light** zip, run `npm install`, `pip install -r backend/requirements.txt`, and follow [Section 4](#4-whispercpp-optional--vendored-native-stt-engine) to restore the offline STT engine.

---

## 📄 License
This project is licensed under the MIT License.
