import { create } from 'zustand';
import {
  applyNodeChanges,
  applyEdgeChanges,
} from 'reactflow';
import { nanoid } from 'nanoid'; // For unique IDs
import axios from 'axios';


// Helper function to load state from localStorage
const loadState = (key) => {
  try {
    const serializedState = localStorage.getItem(key);
    if (serializedState === null) {
      return undefined; // No state saved
    }
    return JSON.parse(serializedState);
  } catch (err) {
    console.error("Could not load state from localStorage", err);
    return undefined;
  }
};

// Helper function to save state to localStorage
const saveState = (key, state) => {
  try {
    const serializedState = JSON.stringify(state);
    localStorage.setItem(key, serializedState);
  } catch (err) {
    console.error("Could not save state to localStorage", err);
  }
};

// --- Example Project Data ---
// Read content from backend files (context.txt, longtext.txt)
// In a real app, you might fetch this or provide it differently.
// For simplicity here, we'll hardcode placeholders or assume they exist.
// You should manually copy/paste the content into these constants
// if you don't set up a fetch mechanism.

const exampleContextContent = `The user is interested in Python programming best practices, especially regarding code cleanliness, performance, and concurrency. They are working with potentially large codebases and interacting with external APIs.`; // Replace with actual context.txt content

const exampleLongTextContent = `Python is dynamically typed, which offers flexibility but can lead to runtime errors if not carefully managed. This means variables can change type during execution. Static analysis tools like MyPy help mitigate this by adding optional type hints (PEP 484) and checking them before runtime, catching potential type errors early in the development cycle. This improves code reliability and maintainability, especially in larger projects.

Another key aspect is its extensive standard library, often called "batteries included". It covers areas from web protocols (HTTP, email) to GUI development (Tkinter), data processing (CSV, JSON, XML), operating system interfaces, and more. This reduces the need for external packages for common tasks.

The Global Interpreter Lock (GIL) in CPython, the most common Python implementation, is a mutex that protects access to Python objects, preventing multiple threads from executing Python bytecode simultaneously within a single process. While it simplifies memory management (making C extensions easier to write), it can limit the performance of CPU-bound multithreaded programs on multi-core processors, as only one thread runs Python code at a time. However, it doesn't significantly impact I/O-bound tasks, where threads spend most of their time waiting for external operations (like network requests or disk reads).

Asynchronous programming with the \`asyncio\` library provides concurrency for I/O-bound tasks without needing multiple OS threads. It uses an event loop and \`async\`/\`await\` syntax to manage coroutines, allowing the program to switch between tasks when one is waiting for I/O, leading to efficient handling of many concurrent connections or operations. This is particularly useful for web servers, network clients, and applications involving significant waiting time. Libraries like \`aiohttp\` build upon asyncio for asynchronous web development.`; // Replace with actual longtext.txt content

const initialProjects = {
  'example1': {
    name: "Example 1: Basic Agent",
    nodes: [
      { id: 'basic-1', type: 'basicAgent', position: { x: 100, y: 100 }, data: { label: 'Basic Agent', prompt: 'Explain the difference between synchronous and asynchronous programming using a simple analogy.', maxTokens: 300 } },
    ],
    edges: [],
  },
  'example2': {
    name: "Example 2: Context Agent",
    nodes: [
      { id: 'context-1', type: 'contextAgent', position: { x: 100, y: 100 }, data: { label: 'Context Agent', context: exampleContextContent, prompt: 'What are 3 key recommendations for writing clean Python code based on the context?' } },
    ],
    edges: [],
  },
  'example3': {
    name: "Example 3: Chain of Agents",
    nodes: [
      { id: 'chain-1', type: 'chainOfAgents', position: { x: 100, y: 100 }, data: { label: 'Chain Summarizer', initialPrompt: "Based on the provided text, explain the implications of Python's dynamic typing and the GIL.", longText: exampleLongTextContent, chunkSize: 2000, chunkOverlap: 200, maxTokens: 500 } }, // Adjusted chunk size
    ],
    edges: [],
  },
   'example4': {
    name: "Example 4: Multi Call System",
    nodes: [
      { id: 'multi-1', type: 'multiCallSystem', position: { x: 100, y: 100 }, data: { label: 'Website Generator', prompt: 'Make the best looking website for a html css js tailwind coffee shop landing page.', numCalls: 5, baseFilename: 'website_call', maxTokens: 35000, outputDir: 'example_outputs/ex4_multi_call_outputs' } }, // Reduced num_calls for quick test
    ],
    edges: [],
  },
   'example5': {
    name: "Example 5: Software Builder",
    nodes: [
       { id: 'builder-1', type: 'softwareBuilder', position: { x: 100, y: 100 }, data: { label: 'Website Builder', userRequest: 'Create a simple single-page website for a local coffee shop called "The Daily Grind". It should have a header with the name, a brief welcome section, a menu section (listing 3 coffees with prices), and a simple footer with contact info. Use HTML, basic CSS (no frameworks initially), and maybe a placeholder image.' } },
    ],
    edges: [],
   },
    'new_project': {
        name: "New Project",
        nodes: [],
        edges: [],
    }
};

const savedProjects = loadState('reactFlowProjects') || initialProjects;
const initialProjectId = loadState('reactFlowCurrentProject') || 'example1'; // Default to first example

export const useStore = create((set, get) => ({
  // === React Flow State ===
  nodes: savedProjects[initialProjectId]?.nodes || [],
  edges: savedProjects[initialProjectId]?.edges || [],
  onNodesChange: (changes) => {
    set((state) => ({ nodes: applyNodeChanges(changes, state.nodes) }));
  },
  onEdgesChange: (changes) => {
    set((state) => ({ edges: applyEdgeChanges(changes, state.edges) }));
  },
  addNode: (newNode) => {
    set((state) => ({ nodes: [...state.nodes, newNode] }));
  },
  setNodes: (nodes) => {
    set({ nodes });
  },
  setEdges: (edges) => {
    set({ edges });
  },
  // Update data within a specific node
  updateNodeData: (nodeId, data) => {
      set((state) => ({
          nodes: state.nodes.map((node) =>
              node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
          ),
      }));
  },

  // === Project Management State ===
  projects: savedProjects,
  currentProjectId: initialProjectId,

  saveCurrentProject: () => {
    const { nodes, edges, currentProjectId, projects } = get();
    const currentProject = projects[currentProjectId];
    if (currentProject) {
        const updatedProjects = {
            ...projects,
            [currentProjectId]: { ...currentProject, nodes, edges }
        };
        set({ projects: updatedProjects });
        saveState('reactFlowProjects', updatedProjects); // Persist projects
        console.log(`Project '${currentProject.name}' saved.`);
    }
  },

  loadProject: (projectId) => {
    const { projects, saveCurrentProject } = get();
    // Save the current state before switching
    saveCurrentProject();

    const projectToLoad = projects[projectId];
    if (projectToLoad) {
      set({
        nodes: projectToLoad.nodes || [],
        edges: projectToLoad.edges || [],
        currentProjectId: projectId,
      });
      saveState('reactFlowCurrentProject', projectId); // Persist current project ID
      console.log(`Project '${projectToLoad.name}' loaded.`);
    } else {
        console.warn(`Project with ID ${projectId} not found.`);
    }
  },

  createProject: (name) => {
    const { projects, saveCurrentProject } = get();
    // Save the current state before creating
    saveCurrentProject();

    const newProjectId = `project_${nanoid(8)}`;
    const newProject = {
        name: name || `New Project ${Object.keys(projects).length + 1}`,
        nodes: [],
        edges: []
    };
    const updatedProjects = { ...projects, [newProjectId]: newProject };
    set({
        projects: updatedProjects,
        nodes: [], // Clear canvas for new project
        edges: [],
        currentProjectId: newProjectId,
    });
    saveState('reactFlowProjects', updatedProjects); // Persist projects
    saveState('reactFlowCurrentProject', newProjectId); // Persist current project ID
    console.log(`Project '${newProject.name}' created.`);
  },

  deleteProject: (projectId) => {
      const { projects, currentProjectId, loadProject } = get();
      if (!projects[projectId]) return;
      if (Object.keys(projects).length <= 1) {
          alert("Cannot delete the last project.");
          return; // Don't delete the last project
      }
       if (!confirm(`Are you sure you want to delete project "${projects[projectId].name}"? This cannot be undone.`)) {
           return;
       }


      const updatedProjects = { ...projects };
      delete updatedProjects[projectId];

      // If deleting the current project, load another one (e.g., the first available)
      let nextProjectId = currentProjectId;
      if (currentProjectId === projectId) {
          nextProjectId = Object.keys(updatedProjects)[0];
      }

      set({ projects: updatedProjects });
      saveState('reactFlowProjects', updatedProjects);

      // Load the next project AFTER state is updated
       if (currentProjectId === projectId) {
           loadProject(nextProjectId);
       }

      console.log(`Project "${projects[projectId].name}" deleted.`);
  },


  // === Execution State ===
  output: "Output will appear here...",
  isRunning: false,
  runFlow: async () => {
    const { nodes, edges, saveCurrentProject } = get();
     // Save before running
    saveCurrentProject();

    set({ isRunning: true, output: "Executing flow..." });
    console.log("Sending to backend:", { nodes, edges });

    try {
      // Use the correct backend URL (ensure backend runs on port 5001 or change here)
      const response = await axios.post('http://localhost:5001/api/run', { nodes, edges });
      console.log("Received from backend:", response.data);
      set({ output: response.data.output || "Execution finished, but no output received." });
    } catch (error) {
      console.error("Error running flow:", error);
      let errorMessage = "Failed to run flow.";
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error("Backend Error Data:", error.response.data);
        console.error("Backend Error Status:", error.response.status);
        errorMessage = `Backend Error (${error.response.status}): ${error.response.data?.error || 'Unknown error'}`;
      } else if (error.request) {
        // The request was made but no response was received
        console.error("No response received:", error.request);
        errorMessage = "Network Error: Could not connect to the backend. Is it running?";
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error('Error', error.message);
        errorMessage = `Request Error: ${error.message}`;
      }
      set({ output: errorMessage });
    } finally {
      set({ isRunning: false });
    }
  },
  clearOutput: () => {
      set({ output: "" });
  },
}));