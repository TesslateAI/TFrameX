import React from 'react';
import { useStore } from '../store';

const OutputPanel = () => {
  const output = useStore((state) => state.output);
  const clearOutput = useStore((state) => state.clearOutput);
  const isRunning = useStore((state) => state.isRunning);


  return (
    <div className="w-[450px] flex flex-col bg-gray-800 border-l border-gray-700 h-full">
       <div className="flex justify-between items-center p-3 border-b border-gray-700">
            <h2 className="text-xl font-semibold text-gray-100">Output</h2>
            <button
                onClick={clearOutput}
                disabled={isRunning}
                className="px-3 py-1 text-xs font-medium text-center text-white bg-yellow-600 rounded-lg hover:bg-yellow-700 focus:ring-4 focus:outline-none focus:ring-yellow-300 disabled:opacity-50"
            >
                Clear
            </button>
       </div>

      <div className="flex-grow p-4 overflow-y-auto">
        <pre className="text-sm text-gray-200 whitespace-pre-wrap break-words">
            {output}
        </pre>
      </div>
    </div>
  );
};

export default OutputPanel;