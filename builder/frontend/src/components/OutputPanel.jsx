import React from 'react';
import { useStore } from '../store';

const OutputPanel = () => {
  const output = useStore((state) => state.output);
  const clearOutput = useStore((state) => state.clearOutput);
  const isRunning = useStore((state) => state.isRunning);

  // Basic check if the output looks like the initial message or empty
  const hasContent = output && output !== "Output will appear here..." && output.trim() !== "";

  return (
    // Fixed width, flex column layout
    <div className="w-[450px] flex flex-col bg-gray-800 border-l border-gray-700 h-full">
      {/* Header */}
       <div className="flex justify-between items-center p-3 border-b border-gray-700 flex-shrink-0"> {/* Prevent header shrinking */}
            <h2 className="text-xl font-semibold text-gray-100">Output</h2>
            <button
                onClick={clearOutput}
                disabled={isRunning || !hasContent} // Disable if running or no content
                className="px-3 py-1 text-xs font-medium text-center text-white bg-yellow-600 rounded-lg hover:bg-yellow-700 focus:ring-4 focus:outline-none focus:ring-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                Clear
            </button>
       </div>

      {/* Scrollable Content Area */}
      <div className="flex-grow p-4 overflow-y-auto"> {/* Take remaining space and scroll */}
        <pre className="text-sm text-gray-200 whitespace-pre-wrap break-words font-mono"> {/* Ensure monospaced font */}
            {/* Display placeholder if no real output yet */}
            {hasContent ? output : <span className="text-gray-500">Output will appear here...</span>}
        </pre>
      </div>
    </div>
  );
};

export default OutputPanel;