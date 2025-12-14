import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BACKEND_URL } from '../services/api';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(false);

    try {
      const response = await fetch(`${BACKEND_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (data.success) {
        login(username, username); // Using username as role for demo
        navigate(data.redirect);
      } else {
        setError(true);
        setPassword('');
      }
    } catch (err) {
      setError(true);
      setPassword('');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-100 via-blue-50 to-indigo-100">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg overflow-hidden fade-in">
        <div className="p-8 bg-gray-500 text-center">
          <div className="flex items-center justify-center mb-3">
            <img 
              src="/logo.png" 
              alt="ProEduvate Logo" 
              className="h-24 sm:h-28 md:h-32 w-auto"
            />
          </div>
          <p className="text-black">Learning Management System</p>
        </div>

        <div className="p-8 bg-gray-400">
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Username
              </label>
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
              <label className="block text-gray-700 text-sm font-bold mb-2">
                Password
              </label>
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

            <button
              type="submit"
              className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition duration-200 font-semibold"
            >
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
