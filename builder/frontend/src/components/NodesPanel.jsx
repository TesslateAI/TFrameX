// src/components/NodesPanel.jsx
import React from 'react';

const DraggableNode = ({ type, label, description }) => {
  const onDragStart = (event, nodeType, nodeLabel) => {
    const nodeInfo = { type: nodeType, label: nodeLabel };
    event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeInfo));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      className="p-3 mb-3 border border-gray-600 rounded-md cursor-grab bg-gray-700 hover:bg-gray-600 hover:border-blue-500 transition-colors duration-150 ease-in-out text-left"
      onDragStart={(event) => onDragStart(event, type, label)}
      draggable
      title={description}
    >
      <div className="font-semibold text-sm">{label}</div>
      {description && <div className="text-xs text-gray-400 mt-1">{description}</div>}
    </div>
  );
};


const NodesPanel = ({ agentDefs, isLoading, error }) => {
    return (
        <div className="flex-grow overflow-y-auto p-1"> {/* Add padding */}
            {isLoading && <div className="text-center text-gray-400 py-4">Loading nodes...</div>}
            {error && <div className="text-center text-red-400 p-2 bg-red-900/50 rounded mx-2">{error}</div>}
            {!isLoading && !error && agentDefs.length === 0 && (
                <div className="text-center text-gray-500 py-4">No nodes available.</div>
            )}
            {!isLoading && !error && agentDefs.map((def) => (
                <DraggableNode
                key={def.id}
                type={def.id}
                label={def.name}
                description={def.description}
                />
            ))}
        </div>
    );
};

export default NodesPanel;