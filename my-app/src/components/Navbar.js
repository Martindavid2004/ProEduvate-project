import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Menu, Sun, Moon } from 'lucide-react';

const Navbar = ({ onMenuClick }) => {
  const { user, theme, toggleTheme } = useAuth();

  return (
    <nav className="bg-gray-300 shadow-lg border-b-4 border-blue-500">
      <div className="max-w-7xl mx-auto px-2 sm:px-4">
        <div className="flex justify-between items-center py-3 sm:py-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={onMenuClick}
              className="mobile-menu-btn text-gray-700 hover:text-gray-900 p-2"
            >
              <Menu size={24} />
            </button>
            <img 
              src="/static/WhatsApp_Image_2025-12-02_at_14.51.15__1_-removebg-preview.png" 
              alt="ProEduvate Logo" 
              className="h-10 sm:h-12 w-auto"
            />
            <h1 className="text-xl sm:text-2xl font-bold text-gray-800">
              ProEduvate
            </h1>
          </div>
          
          <div className="flex items-center space-x-2 sm:space-x-4">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-gray-200 transition-colors"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <Sun size={20} className="text-yellow-500" />
              ) : (
                <Moon size={20} className="text-gray-700" />
              )}
            </button>
            
            <span className="hidden sm:inline text-gray-700 font-medium">
              {user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)} Portal
            </span>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
