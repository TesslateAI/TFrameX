import React, { useState, useEffect } from 'react';
import axios from 'axios'; // Make sure axios is installed: npm install axios

const DraggableNode = ({ type, label, description }) => {
  const onDragStart = (event, nodeType, nodeLabel) => {
    // Pass the type and potentially default data structure or label
    const nodeInfo = { type: nodeType, label: nodeLabel };
    event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeInfo));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      className="p-3 mb-3 border border-gray-600 rounded-md cursor-grab bg-gray-700 hover:bg-gray-600 hover:border-blue-500 transition-colors duration-150 ease-in-out text-left"
      onDragStart={(event) => onDragStart(event, type, label)}
      draggable
      title={description} // Add tooltip for description
    >
      <div className="font-semibold">{label}</div>
      <div className="text-xs text-gray-400 mt-1">{description}</div>
    </div>
  );
};

const Sidebar = () => {
  const [agentDefs, setAgentDefs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAgentDefinitions = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await axios.get('http://localhost:5001/api/agents'); // Use correct backend URL/port
        if (response.data && Array.isArray(response.data)) {
            setAgentDefs(response.data);
        } else {
            setError("Invalid response format from server.");
            setAgentDefs([]); // Clear definitions on error
        }
      } catch (err) {
        console.error("Failed to fetch agent definitions:", err);
        setError("Could not load nodes. Is the backend running?");
        setAgentDefs([]); // Clear definitions on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchAgentDefinitions();
  }, []); // Empty dependency array means run once on mount

  return (
    <aside className="w-72 p-4 bg-gray-800 border-r border-gray-700 h-full overflow-y-auto flex flex-col">
      <h2 className="text-xl font-semibold mb-1 text-center text-gray-100">Nodes</h2>
      <p className="text-xs text-gray-400 mb-4 text-center">Drag nodes onto the canvas</p>

      {isLoading && <div className="text-center text-gray-400">Loading nodes...</div>}
      {error && <div className="text-center text-red-400 p-2 bg-red-900 rounded">{error}</div>}

      {!isLoading && !error && agentDefs.length === 0 && (
        <div className="text-center text-gray-500">No nodes available.</div>
      )}

      {!isLoading && !error && agentDefs.map((def) => (
        <DraggableNode
          key={def.id}
          type={def.id} // Use the registered ID as the node type
          label={def.name}
          description={def.description}
        />
      ))}
    </aside>
  );
};

export default Sidebar;