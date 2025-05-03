// src/components/Sidebar.jsx
import React, { useState, useEffect } from 'react';
// No need for axios here anymore, fetching is handled in store
import NodesPanel from './NodesPanel';
import ChatbotPanel from './ChatbotPanel';
import { useStore } from '../store';

const Sidebar = () => {
  const [activeTab, setActiveTab] = useState('nodes'); // 'nodes' or 'chatbot'

  // --- Corrected State Selection: Select individual pieces ---
  const agentDefinitions = useStore((state) => state.agentDefinitions);
  const fetchAgentDefinitions = useStore((state) => state.fetchAgentDefinitions);
  const isLoading = useStore((state) => state.isDefinitionLoading);
  const error = useStore((state) => state.definitionError);
  // -----------------------------------------------------------

  useEffect(() => {
      // Fetch definitions once on mount if not already loaded/loading
      // Ensure we don't fetch repeatedly if definitions array exists but is empty due to error
      if (agentDefinitions.length === 0 && !isLoading && !error) {
          fetchAgentDefinitions();
      }
      // Dependencies: Only re-run if these specific functions/values change.
      // fetchAgentDefinitions is stable from Zustand.
  }, [fetchAgentDefinitions, agentDefinitions.length, isLoading, error]);

  const tabButtonStyle = (tabName) => `
    flex-1 px-4 py-2 text-center text-sm font-medium rounded-t-lg focus:outline-none transition-colors duration-150 ease-in-out
    ${activeTab === tabName
      ? 'bg-gray-700 text-white border-b-2 border-blue-500'
      : 'text-gray-400 hover:bg-gray-700/50 hover:text-gray-200'}
  `;

  return (
    <aside className="w-72 flex flex-col bg-gray-800 border-r border-gray-700 h-full">
      {/* Tabs */}
      <div className="flex flex-shrink-0 border-b border-gray-700">
        <button onClick={() => setActiveTab('nodes')} className={tabButtonStyle('nodes')}>
          Nodes
        </button>
        <button onClick={() => setActiveTab('chatbot')} className={tabButtonStyle('chatbot')}>
          Chatbot
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-grow overflow-hidden"> {/* Prevent content overflow */}
        {activeTab === 'nodes' && (
          // Pass the selected state down as props
          <NodesPanel agentDefs={agentDefinitions} isLoading={isLoading} error={error} />
        )}
        {activeTab === 'chatbot' && (
          <ChatbotPanel />
        )}
      </div>
    </aside>
  );
};

export default Sidebar;