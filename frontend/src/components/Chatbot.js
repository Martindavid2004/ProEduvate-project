import React, { useState, useRef, useEffect } from 'react';
import { X, Send } from 'lucide-react';
import { chatbotAPI } from '../services/api';

const Chatbot = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I\'m your AI learning assistant. Ask me anything about your courses, assignments, or request a custom quiz!' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatResponse = (text) => {
    let html = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/^# (.*$)/gim, '<h4 class="font-bold text-lg mb-2 text-indigo-800">$1</h4>')
      .replace(/^## (.*$)/gim, '<h5 class="font-semibold text-md mb-1 text-gray-700">$1</h5>')
      .replace(/\n/g, '<br>');

    if (html.includes('<br>* ')) {
      let listHtml = '<ul class="list-disc list-inside space-y-1 my-2">';
      const items = html.split('<br>* ');
      items.slice(1).forEach(item => {
        listHtml += `<li>${item.replace(/<br>/g, '')}</li>`;
      });
      listHtml += '</ul>';
      html = html.substring(0, html.indexOf('<br>* ')) + listHtml;
    }

    return html;
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await chatbotAPI.sendMessage(userMessage);
      const answer = response.data.answer?.text || response.data.answer || response.data.response || "Sorry, I couldn't generate a response.";
      
      setMessages(prev => [...prev, { role: 'assistant', content: answer }]);
    } catch (error) {
      console.error('Chatbot error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Sorry, I couldn't process that request. ${error.message}` 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="chatbot-window">
      <div className="bg-white rounded-lg shadow-xl border h-full flex flex-col">
        <div className="bg-indigo-500 text-white p-4 rounded-t-lg flex justify-between items-center">
          <h3 className="font-bold">AI Learning Assistant</h3>
          <button onClick={onClose} className="hover:bg-indigo-600 rounded p-1">
            <X size={20} />
          </button>
        </div>
        
        <div className="flex-1 p-4 overflow-y-auto" style={{ maxHeight: '500px' }}>
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`chat-message mb-3 ${msg.role === 'user' ? 'text-right' : ''}`}
            >
              <div className={`inline-block max-w-[80%] ${
                msg.role === 'user' 
                  ? 'bg-blue-500 text-white rounded-lg px-4 py-2' 
                  : 'bg-gray-100 text-gray-800 rounded-lg px-4 py-2'
              }`}>
                <strong className="block mb-1">
                  {msg.role === 'user' ? 'You' : 'AI Assistant'}:
                </strong>
                {msg.role === 'assistant' ? (
                  <div dangerouslySetInnerHTML={{ __html: formatResponse(msg.content) }} />
                ) : (
                  <div>{msg.content}</div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="chat-message mb-3">
              <div className="inline-block bg-gray-100 text-gray-800 rounded-lg px-4 py-2">
                <strong>AI Assistant:</strong> Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="p-4 border-t">
          <div className="flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="bg-indigo-500 hover:bg-indigo-600 text-white p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
