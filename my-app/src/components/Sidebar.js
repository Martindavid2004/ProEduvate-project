import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, X } from 'lucide-react';

const Sidebar = ({ items, activeTab, onTabChange, isOpen, onClose }) => {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const handleTabClick = (tabName) => {
    onTabChange(tabName);
    if (window.innerWidth <= 768) {
      onClose();
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="sidebar-overlay active"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`sidebar w-64 bg-gradient-to-b from-gray-900 to-black border-r border-gray-800 flex flex-col shadow-xl ${isOpen ? 'active' : ''}`}>
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <img 
            src="/static/WhatsApp_Image_2025-12-02_at_14.51.15__1_-removebg-preview.png" 
            alt="ProeduVate Logo" 
            className="h-17 w-auto"
          />
          <button
            onClick={onClose}
            className="md:hidden text-white hover:text-gray-300 p-2"
          >
            <X size={24} />
          </button>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {items.map((item) => (
            <button
              key={item.id}
              onClick={() => handleTabClick(item.id)}
              className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-all duration-200 flex items-center ${
                activeTab === item.id
                  ? 'bg-white text-gray-900 shadow-lg'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              {item.icon && <span className="mr-3">{item.icon}</span>}
              {item.label}
            </button>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-700">
          {/* User Info Section */}
          <div className="mb-4 px-4 py-3 bg-gray-800 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white font-semibold capitalize">
                {user?.role || 'User'}
              </span>
              <span className="flex items-center text-xs text-green-400">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                Online
              </span>
            </div>
            {user?.name && (
              <p className="text-gray-400 text-sm truncate">{user.name}</p>
            )}
          </div>
          
          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full text-left px-4 py-3 rounded-lg font-medium transition-all duration-200 flex items-center text-gray-300 hover:bg-red-600 hover:text-white"
          >
            <LogOut className="mr-3" size={20} />
            Logout
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
