import React from 'react';

const DraggableNode = ({ type, label }) => {
  const onDragStart = (event, nodeType) => {
    const nodeInfo = { type: nodeType, label: label };
    event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeInfo));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      className="p-3 mb-3 border border-gray-600 rounded-md cursor-grab bg-gray-700 hover:bg-gray-600 hover:border-blue-500 transition-colors duration-150 ease-in-out text-center"
      onDragStart={(event) => onDragStart(event, type)}
      draggable
    >
      {label}
    </div>
  );
};

const Sidebar = () => {
  return (
    <aside className="w-64 p-4 bg-gray-800 border-r border-gray-700 h-full overflow-y-auto">
      <h2 className="text-xl font-semibold mb-4 text-center text-gray-100">Nodes</h2>
       <p className="text-xs text-gray-400 mb-4 text-center">Drag nodes onto the canvas</p>
       <DraggableNode type="basicAgent" label="Basic Agent" />
       <DraggableNode type="contextAgent" label="Context Agent" />
       <DraggableNode type="chainOfAgents" label="Chain of Agents" />
       <DraggableNode type="multiCallSystem" label="Multi Call System" />
       <DraggableNode type="softwareBuilder" label="Software Builder" />
       {/* Add more node types here */}
    </aside>
  );
};

export default Sidebar;