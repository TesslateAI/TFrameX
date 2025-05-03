import React, { useCallback, useRef } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  Controls,
  Background,
  addEdge,
  MiniMap,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { nanoid } from 'nanoid';

import { useStore } from './store';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import OutputPanel from './components/OutputPanel';

// Import Custom Nodes
import BasicAgentNode from './nodes/BasicAgentNode';
import ContextAgentNode from './nodes/ContextAgentNode';
import ChainOfAgentsNode from './nodes/ChainOfAgentsNode';
import MultiCallSystemNode from './nodes/MultiCallSystemNode';
import SoftwareBuilderNode from './nodes/SoftwareBuilderNode';

// --- Define node types mapping OUTSIDE the component ---
const nodeTypes = {
  basicAgent: BasicAgentNode,
  contextAgent: ContextAgentNode,
  chainOfAgents: ChainOfAgentsNode,
  multiCallSystem: MultiCallSystemNode,
  softwareBuilder: SoftwareBuilderNode,
  // Add other custom nodes here
};
// ----------------------------------------------------

const FlowEditor = () => {
  const reactFlowWrapper = useRef(null); // Ref for converting screen coords to flow coords
   // Get state and setters from Zustand store (using individual selectors now implicit via TopBar fix)
   const nodes = useStore((state) => state.nodes);
   const edges = useStore((state) => state.edges);
   const onNodesChange = useStore((state) => state.onNodesChange);
   const onEdgesChange = useStore((state) => state.onEdgesChange);
   const addNode = useStore((state) => state.addNode);
   const setEdges = useStore((state) => state.setEdges);

  const onConnect = useCallback(
    (params) => setEdges(addEdge(params, edges)),
    [edges, setEdges],
  );

  // Handle dropping nodes from the sidebar
  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const currentRef = reactFlowWrapper.current; // Capture ref value
       if (!currentRef) {
          console.error("React Flow wrapper ref not available");
          return;
      }

      const reactFlowBounds = currentRef.getBoundingClientRect();
      const nodeInfoString = event.dataTransfer.getData('application/reactflow');

       if (!nodeInfoString) {
           console.warn("No node info found in dataTransfer");
           return;
       }

      try {
          const {type, label} = JSON.parse(nodeInfoString);

          // check if the dropped element is valid
          if (typeof type === 'undefined' || !type) {
            return;
          }

          // Calculate position relative to the flow pane
           const position = {
             x: event.clientX - reactFlowBounds.left,
             y: event.clientY - reactFlowBounds.top,
           };
           // Adjust position using the React Flow instance's project method if needed
           // This requires getting the instance, often via useReactFlow() hook
           // For simplicity, direct calculation is often sufficient initially.
           // const position = project({ x: event.clientX, y: event.clientY });


          const newNode = {
            id: `${type}-${nanoid(6)}`, // Unique ID
            type,
            position,
            // Initialize data with a label; specific nodes might need more
            data: { label: label || `${type} Node` },
          };

          console.log("Adding node:", newNode);
          addNode(newNode);
      } catch (e) {
          console.error("Failed to parse dropped node data:", e);
      }

    },
    [addNode], // Dependency on addNode action
  );

  return (
    <div className="flex h-screen w-screen bg-gray-900" ref={reactFlowWrapper}>
      <Sidebar />
      <div className="flex-grow flex flex-col h-full">
        <TopBar />
        <div className="flex-grow relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes} // Use the constant defined outside
            fitView
            className="bg-gray-900"
          >
            <Controls className="react-flow__controls" />
            <Background variant="dots" gap={16} size={1} color="#4A5568" />
             <MiniMap nodeStrokeWidth={3} nodeColor={(n) => {
                 switch (n.type) {
                     case 'basicAgent': return '#3b82f6';
                     case 'contextAgent': return '#10b981';
                     case 'chainOfAgents': return '#f97316';
                     case 'multiCallSystem': return '#a855f7';
                     case 'softwareBuilder': return '#ef4444';
                     default: return '#6b7280';
                 }
             }} />
          </ReactFlow>
        </div>
      </div>
      <OutputPanel />
    </div>
  );
};

// Wrap with ReactFlowProvider
function App() {
  return (
    <ReactFlowProvider>
      <FlowEditor />
    </ReactFlowProvider>
  );
}

export default App;