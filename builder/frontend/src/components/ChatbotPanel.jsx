// src/components/ChatbotPanel.jsx
import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '../store';

const ChatbotPanel = () => {
  const [inputMessage, setInputMessage] = useState('');

  // --- CORRECTED STATE SELECTION ---
  // Select each piece of state or action individually
  const chatHistory = useStore((state) => state.chatHistory);
  const sendChatMessage = useStore((state) => state.sendChatMessage);
  const isChatbotLoading = useStore((state) => state.isChatbotLoading);
  const clearChatHistory = useStore((state) => state.clearChatHistory);
  // ---------------------------------

  const messagesEndRef = useRef(null); // To auto-scroll

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]); // Dependency is correct

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (inputMessage.trim() && !isChatbotLoading) {
      sendChatMessage(inputMessage.trim());
      setInputMessage('');
    }
  };

  return (
    <div className="flex flex-col h-full p-2">
      {/* Chat History */}
      <div className="flex-grow overflow-y-auto mb-2 bg-gray-900 rounded p-2 space-y-3">
        {chatHistory.map((msg, index) => (
          <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] p-2 rounded-lg text-sm whitespace-pre-wrap break-words ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white'
                  : msg.type === 'error'
                  ? 'bg-red-800 text-red-100'
                  : 'bg-gray-600 text-gray-200'
              }`}
            >
              {msg.message}
            </div>
          </div>
        ))}
         {isChatbotLoading && (
             <div className="flex justify-start">
                 <div className="max-w-[80%] p-2 rounded-lg text-sm bg-gray-600 text-gray-400 animate-pulse">
                    Thinking...
                 </div>
             </div>
         )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSendMessage} className="flex-shrink-0 flex items-center space-x-2">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Describe the flow..."
          className="flex-grow node-input !mt-0"
          disabled={isChatbotLoading}
          aria-label="Chat input"
        />
        <button
          type="submit"
          disabled={isChatbotLoading || !inputMessage.trim()}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
         <button
            type="button"
            onClick={clearChatHistory}
            disabled={isChatbotLoading || chatHistory.length === 0}
            className="p-2 text-xs font-medium text-white bg-yellow-600 rounded-lg hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Clear Chat"
        >
            🗑️
        </button>
      </form>
    </div>
  );
};

export default ChatbotPanel;