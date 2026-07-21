import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Mail, Lock, Eye, EyeOff, ChevronRight, CheckCircle, AlertCircle, Hash, Building2, GraduationCap } from 'lucide-react';
import { API_URL } from '../services/api';

const StudentRegistration = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    fullName: '',
    registerNumber: '',
    email: '',
    department: '',
    password: '',
    confirmPassword: '',
    agreeToTerms: false,
  });

  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Common departments list
  const departments = [
    "Computer Science Engineering",
    "Information Technology",
    "Electronics & Communication",
    "Mechanical Engineering",
    "Civil Engineering",
    "Electrical & Electronics",
    "Biotechnology",
    "Business Administration",
    "Science & Humanities"
  ];

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.fullName.trim()) newErrors.fullName = 'Full name is required';
    
    if (!formData.registerNumber.trim()) {
      newErrors.registerNumber = 'Register Number is required';
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.department) {
      newErrors.department = 'Please select your department';
    }

    if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (!formData.agreeToTerms) {
      newErrors.agreeToTerms = 'You must agree to the Terms of Service';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (validateForm()) {
      setIsLoading(true);
      setErrors({});
      
      try {
        const response = await fetch(`${API_URL}/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            fullName: formData.fullName,
            registerNumber: formData.registerNumber,
            email: formData.email,
            department: formData.department,
            password: formData.password,
          }),
        });

        const data = await response.json();

        if (data.success) {
          // Store JWT token in localStorage
          localStorage.setItem('authToken', data.token);
          localStorage.setItem('user', JSON.stringify(data.user));
          
          setIsLoading(false);
          setIsSuccess(true);
        } else {
          setIsLoading(false);
          setErrors({ submit: data.message || 'Registration failed. Please try again.' });
        }
      } catch (error) {
        setIsLoading(false);
        setErrors({ submit: 'Network error. Please check your connection and try again.' });
        console.error('Registration error:', error);
      }
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4 font-sans">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center space-y-6 animate-in fade-in zoom-in duration-300 border border-slate-100">
          <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto shadow-inner">
            <CheckCircle size={40} />
          </div>
          <h2 className="text-3xl font-bold text-slate-800">Registration Successful!</h2>
          <p className="text-slate-600">
            Welcome to the student portal. Your account has been created successfully.
          </p>
          <button 
            onClick={() => window.location.href = '/login'}
            className="w-full py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg transform transition hover:-translate-y-0.5 duration-200"
          >
            Go to Student Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4 font-sans relative overflow-hidden">
      {/* Background Decorative Elements for Desktop */}
      <div className="hidden md:block absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute -top-[10%] -left-[5%] w-[40%] h-[40%] rounded-full bg-gradient-to-br from-indigo-200/40 to-purple-200/40 blur-3xl animate-pulse" />
        <div className="absolute bottom-[10%] -right-[5%] w-[30%] h-[30%] rounded-full bg-gradient-to-br from-blue-200/40 to-teal-200/40 blur-3xl animate-pulse" style={{animationDelay: '1s'}} />
      </div>

      <div className="w-full max-w-lg bg-white rounded-2xl shadow-2xl overflow-hidden z-10 animate-in fade-in zoom-in duration-300 border border-slate-100">
        
        {/* Professional Header Section */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-700 px-8 py-8 text-white text-center relative overflow-hidden">
            {/* Decorative white lines */}
            <div className="absolute top-0 left-0 w-full h-full bg-white/5 skew-y-6 scale-150 translate-y-12"></div>
            
            <div className="relative z-10 flex flex-col items-center">
                <div className="bg-white/20 p-3 rounded-full mb-3 backdrop-blur-sm">
                    <GraduationCap size={32} className="text-white" />
                </div>
                <h2 className="text-3xl font-bold tracking-tight">Student Portal</h2>
                <p className="text-indigo-100 text-sm mt-2 font-medium">Create your academic account</p>
            </div>
        </div>

        <div className="p-8 md:p-10">
            <form onSubmit={handleSubmit} className="space-y-5">
            
            <div className="space-y-5">
                {/* Full Name */}
                <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5 ml-1">Full Name</label>
                <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <User size={18} className="text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                    </div>
                    <input
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleChange}
                    className={`block w-full pl-11 pr-4 py-3 bg-slate-50 border ${errors.fullName ? 'border-red-500 ring-red-100' : 'border-slate-200 focus:border-indigo-500 focus:ring-indigo-100'} rounded-xl shadow-sm focus:outline-none focus:ring-4 transition-all duration-200 text-slate-800 placeholder:text-slate-400`}
                    placeholder="Enter your full name"
                    />
                </div>
                {errors.fullName && <p className="mt-1.5 text-xs text-red-500 flex items-center font-medium animate-in slide-in-from-left-1"><AlertCircle size={12} className="mr-1"/>{errors.fullName}</p>}
                </div>

                {/* Register Number */}
                <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5 ml-1">Register Number</label>
                <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Hash size={18} className="text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                    </div>
                    <input
                    type="text"
                    name="registerNumber"
                    value={formData.registerNumber}
                    onChange={handleChange}
                    className={`block w-full pl-11 pr-4 py-3 bg-slate-50 border ${errors.registerNumber ? 'border-red-500 ring-red-100' : 'border-slate-200 focus:border-indigo-500 focus:ring-indigo-100'} rounded-xl shadow-sm focus:outline-none focus:ring-4 transition-all duration-200 text-slate-800 placeholder:text-slate-400`}
                    placeholder="e.g. REG2024001"
                    />
                </div>
                {errors.registerNumber && <p className="mt-1.5 text-xs text-red-500 flex items-center font-medium animate-in slide-in-from-left-1"><AlertCircle size={12} className="mr-1"/>{errors.registerNumber}</p>}
                </div>

                {/* Email */}
                <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5 ml-1">Email Address</label>
                <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Mail size={18} className="text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                    </div>
                    <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className={`block w-full pl-11 pr-4 py-3 bg-slate-50 border ${errors.email ? 'border-red-500 ring-red-100' : 'border-slate-200 focus:border-indigo-500 focus:ring-indigo-100'} rounded-xl shadow-sm focus:outline-none focus:ring-4 transition-all duration-200 text-slate-800 placeholder:text-slate-400`}
                    placeholder="student@college.edu"
                    />
                </div>
                {errors.email && <p className="mt-1.5 text-xs text-red-500 flex items-center font-medium animate-in slide-in-from-left-1"><AlertCircle size={12} className="mr-1"/>{errors.email}</p>}
                </div>

                {/* Department Selection */}
                <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5 ml-1">Department</label>
                <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Building2 size={18} className="text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                    </div>
                    <select
                    name="department"
                    value={formData.department}
                    onChange={handleChange}
                    className={`block w-full pl-11 pr-10 py-3 bg-slate-50 border ${errors.department ? 'border-red-500 ring-red-100' : 'border-slate-200 focus:border-indigo-500 focus:ring-indigo-100'} rounded-xl shadow-sm focus:outline-none focus:ring-4 transition-all duration-200 text-slate-800 appearance-none cursor-pointer`}
                    >
                    <option value="" className="text-slate-400">Select Department</option>
                    {departments.map((dept) => (
                        <option key={dept} value={dept}>{dept}</option>
                    ))}
                    </select>
                    <div className="absolute inset-y-0 right-0 flex items-center px-3 pointer-events-none">
                    <ChevronRight size={18} className="text-slate-400 rotate-90" />
                    </div>
                </div>
                {errors.department && <p className="mt-1.5 text-xs text-red-500 flex items-center font-medium animate-in slide-in-from-left-1"><AlertCircle size={12} className="mr-1"/>{errors.department}</p>}
                </div>

                {/* Password Fields Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5 ml-1">Password</label>
                    <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                        <Lock size={18} className="text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                    </div>
                    <input
                        type={showPassword ? "text" : "password"}
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        className={`block w-full pl-11 pr-10 py-3 bg-slate-50 border ${errors.password ? 'border-red-500 ring-red-100' : 'border-slate-200 focus:border-indigo-500 focus:ring-indigo-100'} rounded-xl shadow-sm focus:outline-none focus:ring-4 transition-all duration-200 text-slate-800 placeholder:text-slate-400`}
                        placeholder="••••••••"
                    />
                    <div 
                        className="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer text-slate-400 hover:text-indigo-600 transition-colors"
                        onClick={() => setShowPassword(!showPassword)}
                    >
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </div>
                    </div>
                    {errors.password && <p className="mt-1.5 text-xs text-red-500 flex items-center font-medium animate-in slide-in-from-left-1"><AlertCircle size={12} className="mr-1"/>{errors.password}</p>}
                </div>

                <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5 ml-1">Confirm Password</label>
                    <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                        <Lock size={18} className="text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                    </div>
                    <input
                        type={showPassword ? "text" : "password"}
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        className={`block w-full pl-11 pr-4 py-3 bg-slate-50 border ${errors.confirmPassword ? 'border-red-500 ring-red-100' : 'border-slate-200 focus:border-indigo-500 focus:ring-indigo-100'} rounded-xl shadow-sm focus:outline-none focus:ring-4 transition-all duration-200 text-slate-800 placeholder:text-slate-400`}
                        placeholder="••••••••"
                    />
                    </div>
                    {errors.confirmPassword && <p className="mt-1.5 text-xs text-red-500 flex items-center font-medium animate-in slide-in-from-left-1"><AlertCircle size={12} className="mr-1"/>{errors.confirmPassword}</p>}
                </div>
                </div>
            </div>

            {/* Terms Checkbox */}
            <div className="flex items-start pt-2">
                <div className="flex items-center h-5">
                <input
                    id="agreeToTerms"
                    name="agreeToTerms"
                    type="checkbox"
                    checked={formData.agreeToTerms}
                    onChange={handleChange}
                    className="h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded cursor-pointer transition-all duration-200"
                />
                </div>
                <div className="ml-3 text-sm">
                <label htmlFor="agreeToTerms" className="font-medium text-slate-600 cursor-pointer select-none">
                    I agree to the <button type="button" className="text-indigo-600 hover:text-indigo-700 underline decoration-indigo-200 hover:decoration-indigo-600 transition-all bg-transparent border-0 p-0 cursor-pointer">Terms of Service</button> and <button type="button" className="text-indigo-600 hover:text-indigo-700 underline decoration-indigo-200 hover:decoration-indigo-600 transition-all bg-transparent border-0 p-0 cursor-pointer">Privacy Policy</button>
                </label>
                {errors.agreeToTerms && <p className="mt-1.5 text-xs text-red-500 flex items-center font-medium animate-in slide-in-from-left-1"><AlertCircle size={12} className="mr-1"/>{errors.agreeToTerms}</p>}
                </div>
            </div>

            {/* Server Error Display */}
            {errors.submit && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-3 flex items-start">
                <AlertCircle size={18} className="text-red-500 mr-2 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-600 font-medium">{errors.submit}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
                type="submit"
                disabled={isLoading}
                className="group relative w-full flex justify-center py-3.5 px-4 border border-transparent text-sm font-bold rounded-xl text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 shadow-lg shadow-indigo-500/30 hover:shadow-xl hover:shadow-indigo-500/40 transform transition hover:-translate-y-0.5 duration-200 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none"
            >
                {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                ) : (
                <>
                    Create Account
                    <ChevronRight size={18} className="ml-2 group-hover:translate-x-1 transition-transform" />
                </>
                )}
            </button>
            
            <div className="text-center pt-2">
                <p className="text-sm text-slate-500">
                    Already have an account?{' '}
                    <a href="/login" className="font-bold text-indigo-600 hover:text-indigo-500 transition-colors">
                        Sign in here
                    </a>
                </p>
            </div>
            </form>
        </div>
      </div>
    </div>
  );
};

export default StudentRegistration;
