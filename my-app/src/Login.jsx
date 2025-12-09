import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Using a placeholder since the local asset cannot be resolved during this build step.
// You can replace this string with your local import later: 
// import logo from './assets/WhatsApp_Image_2025-12-02_at_14.51.15__1_-removebg-preview.png';
const logo = "https://placehold.co/200x80?text=ProEduvate";

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await response.json();
      
      if (data.success) {
        localStorage.setItem('userRole', username);
        navigate('/dashboard'); 
      } else {
        setError(true);
        setPassword('');
      }
    } catch (err) {
      // Fallback for demo purposes
      const demoCreds = { 'admin': 'password', 'teacher': 'password', 'student': 'password', 'hr': 'password' };
      if (demoCreds[username] === password) {
        localStorage.setItem('userRole', username);
        navigate('/dashboard');
      } else {
        setError(true);
        setPassword('');
      }
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-indigo-500 to-blue-600 fade-in">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="p-8 bg-indigo-600 text-white text-center">
          <div className="mx-auto flex justify-center mb-4">
            <img src={logo} alt="ProEduvate Logo" className="h-20 w-auto" />
          </div>
          <h2 className="text-2xl font-bold mb-2">ProEduvate</h2>
          <p className="text-indigo-100">Learning Management System</p>
        </div>
        
        <div className="p-8">
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2">Username</label>
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your role (admin/teacher/student/hr)" 
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500" 
                required 
              />
            </div>
            
            <div className="mb-6">
              <label className="block text-gray-700 text-sm font-bold mb-2">Password</label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password" 
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500" 
                required 
              />
            </div>
            
            {error && (
              <div className="mb-4 text-red-500 text-sm text-center bg-red-50 p-2 rounded">
                Invalid username or password
              </div>
            )}
            
            <button type="submit" className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition duration-200 font-semibold">
              Login
            </button>
          </form>
          
          <div className="mt-6 text-center text-sm text-gray-600 bg-gray-50 p-3 rounded">
            <p className="font-semibold mb-1">Demo Credentials:</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <p><strong>admin</strong> / password</p>
              <p><strong>teacher</strong> / password</p>
              <p><strong>student</strong> / password</p>
              <p><strong>hr</strong> / password</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;