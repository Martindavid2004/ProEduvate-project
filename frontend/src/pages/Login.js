import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_URL, BACKEND_URL } from '../services/api';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(false);
    setErrorMessage('');
    setIsLoading(true);

    const isEmail = email.includes('@');
    
    try {
      if (isEmail) {
        // Try database authentication for registered users
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
          console.log('[Login] Email token stored:', data.token.substring(0, 30) + '...');
          
          login(data.user);
          navigate(data.redirect);
          return;
        } else {
          setError(true);
          setErrorMessage(data.message || 'Invalid email or password');
          setPassword('');
        }
      } else {
        // Try demo authentication for username-based login
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
          
          // Store JWT token for demo accounts too
          if (demoData.token) {
            localStorage.setItem('authToken', demoData.token);
            // SECURITY: never log JWT tokens (even partially) to the console.
            console.log('[Login] Demo token stored: <redacted>');
          } else {
            console.error('[Login] WARNING: No token received from demo login!');
          }
          
          login(demoUser);
          navigate(demoData.redirect);
          return;
        } else {
          setError(true);
          setErrorMessage('Invalid credentials. Please check your username and password.');
          setPassword('');
        }
      }
    } catch (err) {
      setError(true);
      setErrorMessage('Network error. Please check your connection.');
      setPassword('');
    } finally {
      setIsLoading(false);
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
          <p className="text-black font-semibold">Learning Management System</p>
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
                disabled={isLoading}
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
                disabled={isLoading}
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
              disabled={isLoading}
              className={`w-full bg-indigo-600 text-white py-2.5 px-4 rounded-md hover:bg-indigo-700 transition duration-200 font-semibold flex items-center justify-center gap-2 ${
                isLoading ? 'opacity-75 cursor-not-allowed' : ''
              }`}
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Logging in...</span>
                </>
              ) : (
                <span>Login</span>
              )}
            </button>
          </form>

          <div className="mt-4 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <button
                onClick={() => navigate('/register')}
                disabled={isLoading}
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
