# Quick Commands Reference

## ❌ Wrong Command (You Used)
```bash
npm run dev
```

## ✅ Correct Commands

### Start React App (Development)
```bash
npm start
```
This will:
- Start the development server
- Open browser at http://localhost:3000
- Enable hot reloading

### Other Useful Commands

#### Build for Production
```bash
npm run build
```
Creates optimized production build in `build/` folder

#### Run Tests
```bash
npm test
```
Launches test runner

#### View All Available Scripts
```bash
npm run
```

## 🚀 Complete Startup Process

### Terminal 1 - Backend (Flask)
```bash
cd C:\Users\kitty\Downloads\ProeduVate-main\ProeduVate-main\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```
Backend runs on: **http://127.0.0.1:5001**

### Terminal 2 - Frontend (React)
```bash
cd C:\Users\kitty\Downloads\ProeduVate-main\my-app
npm start
```
Frontend runs on: **http://localhost:3000**

## 📝 Note

- `npm run dev` is used in Vite projects
- `npm start` is used in Create React App projects (this one)
- Your project uses **Create React App**, so use `npm start`

## 🔍 Troubleshooting

If `npm start` fails:
1. Ensure you're in the correct directory: `my-app/`
2. Check if `node_modules/` exists
3. If missing, run: `npm install`
4. Then try: `npm start` again

## 🌐 Access the App

Once both servers are running:
- **Frontend**: http://localhost:3000
- **Backend API**: http://127.0.0.1:5001/api

Login with:
- Admin: `admin` / `password`
- Teacher: `teacher` / `password`
- Student: `student` / `password`
- HR: `hr` / `password`
