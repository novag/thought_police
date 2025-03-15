'use client';

import React, { useState, useEffect } from 'react';
import { ApolloProvider } from '@apollo/client';
import { ReactFlowProvider } from '@xyflow/react';
import apolloClient from '@/lib/apollo-client';
import ActionFlow from '@/components/ActionFlow';
import TraceSelector from '@/components/TraceSelector';
import '@xyflow/react/dist/style.css';
import { Activity, Info, Github, ExternalLink } from 'lucide-react';

export default function Home() {
  const [selectedTraceId, setSelectedTraceId] = useState<number | null>(null);
  const [showInfo, setShowInfo] = useState(false);

  // Add console logging for debugging
  console.log('Home render:', { selectedTraceId });

  const handleTraceSelect = (traceId: number) => {
    console.log('Home handleTraceSelect:', traceId);
    setSelectedTraceId(traceId);
  };

  return (
    <main className="flex min-h-screen flex-col bg-slate-50">
      <header className="bg-slate-800 text-white p-4 flex justify-between items-center shadow-md">
        <div>
          <div className="flex items-center">
            <Activity className="h-6 w-6 mr-2 text-blue-400" />
            <h1 className="text-2xl font-bold">AI Agent Action Tracker</h1>
          </div>
          <p className="text-sm text-slate-300 mt-1">Visualize the decision tree of AI agent actions</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => setShowInfo(!showInfo)}
            className="p-2 rounded-full hover:bg-slate-700 transition-colors"
            title="About this app"
          >
            <Info className="h-5 w-5" />
          </button>
          <a 
            href="https://github.com/cursor-ai" 
            target="_blank" 
            rel="noopener noreferrer"
            className="p-2 rounded-full hover:bg-slate-700 transition-colors"
            title="GitHub Repository"
          >
            <Github className="h-5 w-5" />
          </a>
        </div>
      </header>
      
      {showInfo && (
        <div className="bg-white border-b border-slate-200 p-4 shadow-sm">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-lg font-semibold mb-2">About AI Agent Action Tracker</h2>
            <p className="mb-2">
              This application visualizes the actions performed by the Cursor AI agent as a tree graph. 
              Each node in the graph represents an action taken by the agent during its execution.
            </p>
            <p className="mb-2">
              <strong>Node Types:</strong>
            </p>
            <ul className="list-disc pl-5 mb-2 space-y-1">
              <li><span className="text-blue-600 font-medium">Logging</span> - Information logged during agent execution</li>
              <li><span className="text-purple-600 font-medium">Decision</span> - Decision points where the agent chose between options</li>
              <li><span className="text-green-600 font-medium">Tool Call</span> - External tools or functions called by the agent</li>
            </ul>
            <p>
              Use the trace selector to choose different agent runs, and the controls in the top-right corner 
              to change the layout, filter nodes, or search for specific content.
            </p>
            <div className="flex justify-end mt-2">
              <button 
                onClick={() => setShowInfo(false)}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      
      <div className="flex-1 flex flex-col">
        <ApolloProvider client={apolloClient}>
          <TraceSelector 
            selectedTraceId={selectedTraceId} 
            onSelectTrace={handleTraceSelect} 
          />
          
          <ReactFlowProvider>
            <div className="flex-1" style={{ 
              height: 'calc(100vh - 160px)', 
              width: '100%', 
              position: 'relative',
              overflow: 'hidden'
            }}>
              {selectedTraceId !== null && (
                <ActionFlow key={`trace-${selectedTraceId}`} traceId={selectedTraceId} />
              )}
            </div>
          </ReactFlowProvider>
        </ApolloProvider>
      </div>
      
      <footer className="bg-slate-800 text-slate-400 text-xs p-3 text-center">
        <p>
          Built with Next.js, React Flow, and GraphQL. 
          <a 
            href="https://cursor.sh" 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center ml-2 text-blue-400 hover:text-blue-300"
          >
            Cursor AI <ExternalLink className="h-3 w-3 ml-1" />
          </a>
        </p>
      </footer>
    </main>
  );
}
