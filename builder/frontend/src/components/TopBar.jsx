import React, { useState, useCallback } from 'react';
import { useStore } from '../store';

const TopBar = () => {
  // --- Option 2: Select individual pieces of state/functions ---
  const projects = useStore((state) => state.projects);
  const currentProjectId = useStore((state) => state.currentProjectId);
  const loadProject = useStore((state) => state.loadProject);
  const createProject = useStore((state) => state.createProject);
  const deleteProject = useStore((state) => state.deleteProject);
  const saveCurrentProject = useStore((state) => state.saveCurrentProject);
  const runFlow = useStore((state) => state.runFlow);
  const isRunning = useStore((state) => state.isRunning);
  // -------------------------------------------------------------

  const [newProjectName, setNewProjectName] = useState('');

  const handleCreateProject = useCallback(() => {
    if (newProjectName.trim()) {
      createProject(newProjectName.trim());
      setNewProjectName(''); // Clear input after creation
    } else {
        // Optionally create with a default name if empty
         createProject(); // Create with default name
    }
    // Add createProject as dependency if it might change,
    // but Zustand actions are usually stable references.
  }, [createProject, newProjectName]);

  const handleProjectChange = (event) => {
    loadProject(event.target.value);
  };

   const handleDeleteClick = () => {
        if (currentProjectId) {
            deleteProject(currentProjectId);
        }
    };


  return (
    <div className="h-16 bg-gray-800 border-b border-gray-700 flex items-center justify-between px-4 shadow-md">
      {/* Project Controls */}
      <div className="flex items-center space-x-4">
         <span className="text-lg font-semibold text-gray-100">Flow Runner</span>
        {/* Project Selector */}
        <select
          value={currentProjectId || ''}
          onChange={handleProjectChange}
          className="bg-gray-700 border border-gray-600 text-gray-200 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2"
          disabled={isRunning}
        >
          <option value="" disabled>Select Project</option>
          {Object.entries(projects).map(([id, project]) => (
            <option key={id} value={id}>
              {project.name}
            </option>
          ))}
        </select>

         {/* Create New Project */}
        <div className="flex items-center space-x-2">
            <input
                type="text"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="New Project Name"
                className="bg-gray-700 border border-gray-600 text-gray-200 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 w-40"
                disabled={isRunning}
            />
            <button
                onClick={handleCreateProject}
                className="px-3 py-2 text-sm font-medium text-center text-white bg-green-600 rounded-lg hover:bg-green-700 focus:ring-4 focus:outline-none focus:ring-green-300 disabled:opacity-50"
                disabled={isRunning}
            >
                Create
            </button>
            <button
                onClick={handleDeleteClick}
                title="Delete Current Project"
                className="px-3 py-2 text-sm font-medium text-center text-white bg-red-600 rounded-lg hover:bg-red-700 focus:ring-4 focus:outline-none focus:ring-red-300 disabled:opacity-50"
                disabled={isRunning || Object.keys(projects).length <= 1} // Disable if only one project
            >
               🗑️ Delete
            </button>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center space-x-3">
         <button
            onClick={saveCurrentProject}
            className="px-4 py-2 text-sm font-medium text-center text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-300 disabled:opacity-50"
             disabled={isRunning}
        >
            💾 Save Project
        </button>
        <button
          onClick={runFlow}
          className={`px-6 py-2 font-semibold text-center text-white rounded-lg focus:ring-4 focus:outline-none focus:ring-purple-300 transition-colors duration-150 ease-in-out ${
            isRunning ? 'bg-gray-500 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'
          }`}
          disabled={isRunning}
        >
          {isRunning ? 'Running...' : '▶️ Run Flow'}
        </button>
      </div>
    </div>
  );
};

export default TopBar;