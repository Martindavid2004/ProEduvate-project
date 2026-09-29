import React, { useEffect } from 'react';
import { X } from 'lucide-react';

const Modal = ({ isOpen, onClose, title, children, maxWidth = '600px', fullScreen = false }) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className={fullScreen ? 'interview-modal interview-modal-fullscreen' : 'interview-modal'}>
      {/* fullScreen (used ONLY by the Mock Interview) removes the 600px card
          constraint so the assessment occupies the whole viewport. All other
          modals keep their original sizing. */}
      <div
        className="interview-modal-content"
        style={fullScreen ? undefined : { maxWidth }}
      >
        <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-lg flex justify-between items-center z-10">
          <h3 className="text-xl font-bold text-gray-800">{title}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X size={24} />
          </button>
        </div>
        <div className="p-6 interview-modal-body">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Modal;
