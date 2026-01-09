import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_URL, BACKEND_URL } from '../services/api';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(false);
    setErrorMessage('');

    // Check if input looks like an email (for registered users) or username (for demo)
    const isEmail = email.includes('@');
    
    if (isEmail) {
      // Try database authentication for registered users
      try {
        const response = await fetch(`${API_URL}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ email, password }),
        });

        const data = await response.json();

        if (data.success) {
          // Store JWT token and user data
          localStorage.setItem('authToken', data.token);
          localStorage.setItem('user', JSON.stringify(data.user));
          
          login(data.user.name, data.user.role);
          navigate(data.redirect);
          return;
        } else {
          setError(true);
          setErrorMessage(data.message || 'Invalid email or password');
          setPassword('');
          return;
        }
      } catch (err) {
        setError(true);
        setErrorMessage('Network error. Please check your connection.');
        setPassword('');
        return;
      }
    } else {
      // Try demo authentication for username-based login
      try {
        const demoResponse = await fetch(`${BACKEND_URL}/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ username: email, password }),
        });

        const demoData = await demoResponse.json();

        if (demoData.success) {
          // Store minimal user data for demo accounts
          const demoUser = {
            name: email.charAt(0).toUpperCase() + email.slice(1),
            email: `${email}@demo.com`,
            role: email,
            id: email
          };
          localStorage.setItem('user', JSON.stringify(demoUser));
          
          login(email, email);
          navigate(demoData.redirect);
          return;
        } else {
          setError(true);
          setErrorMessage('Invalid credentials. Please check your username and password.');
          setPassword('');
          return;
        }
      } catch (fallbackErr) {
        setError(true);
        setErrorMessage('Network error. Please check your connection.');
        setPassword('');
        return;
      }
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
                Email / Username
              </label>
              <input
                type="text"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email or username"
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
                {errorMessage || 'Invalid email or password'}
              </div>
            )}

            <button
              type="submit"
              className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition duration-200 font-semibold"
            >
              Login
            </button>
          </form>

          <div className="mt-4 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <button
                onClick={() => navigate('/register')}
                className="font-bold text-indigo-600 hover:text-indigo-700 underline transition-colors"
              >
                Register here
              </button>
            </p>
          </div>

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
