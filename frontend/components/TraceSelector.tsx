import React, { useState, useEffect } from 'react';
import { useQuery, useSubscription } from '@apollo/client';
import { GET_TRACES, TRACE_CREATED_SUBSCRIPTION } from '@/lib/graphql/queries';
import { Trace } from '@/lib/types';
import { Search, X, Calendar, Clock } from 'lucide-react';
import { format } from 'date-fns';

interface TraceSelectorProps {
  selectedTraceId: number | null;
  onSelectTrace: (traceId: number) => void;
}

const TraceSelector: React.FC<TraceSelectorProps> = ({ selectedTraceId, onSelectTrace }) => {
  const { data, loading, error, refetch } = useQuery(GET_TRACES, {
    fetchPolicy: 'network-only' // Don't use cache, always fetch from server
  });
  
  // Subscribe to new traces
  const { data: subscriptionData } = useSubscription(TRACE_CREATED_SUBSCRIPTION);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'name'>('newest');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [traces, setTraces] = useState<Trace[]>([]);
  
  // Update traces when query data changes
  useEffect(() => {
    if (data?.traces) {
      setTraces(data.traces);
    }
  }, [data]);
  
  // Update traces when subscription data is received
  useEffect(() => {
    if (subscriptionData?.traceCreated) {
      console.log('New trace received:', subscriptionData.traceCreated);
      // Add the new trace to the list if it doesn't already exist
      setTraces(prevTraces => {
        const newTrace = subscriptionData.traceCreated;
        const exists = prevTraces.some(trace => trace.id === newTrace.id);
        if (exists) {
          return prevTraces;
        }
        return [newTrace, ...prevTraces];
      });
    }
  }, [subscriptionData]);
  
  // Add console logging for debugging
  console.log('TraceSelector render:', { 
    selectedTraceId, 
    tracesCount: traces.length,
    subscriptionReceived: !!subscriptionData
  });
  
  const handleSelectTrace = (id: number) => {
    console.log('Selecting trace:', id);
    onSelectTrace(id);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return format(date, 'MMM d, yyyy h:mm a');
  };
  
  if (loading && traces.length === 0) return <div className="p-4">Loading traces...</div>;
  if (error) return <div className="p-4 text-red-500">Error loading traces: {error.message}</div>;
  
  let filteredTraces = [...traces];
  
  // Filter traces based on search term
  if (searchTerm) {
    filteredTraces = filteredTraces.filter(trace => 
      trace.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
      (trace.description && trace.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  }
  
  // Sort traces
  filteredTraces = filteredTraces.sort((a, b) => {
    if (sortBy === 'newest') {
      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
    } else if (sortBy === 'oldest') {
      return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
    } else {
      return a.name.localeCompare(b.name);
    }
  });
  
  return (
    <div className={`bg-slate-100 border-b border-slate-200 transition-all duration-300 ${isCollapsed ? 'h-16' : ''}`}>
      <div className="flex justify-between items-center p-4">
        <div className="flex items-center">
          <h2 className="text-lg font-semibold mr-2">Traces</h2>
          <button 
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-slate-500 hover:text-slate-700"
          >
            {isCollapsed ? 'Expand' : 'Collapse'}
          </button>
        </div>
        
        {!isCollapsed && (
          <div className="flex space-x-2">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search traces..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 pr-4 py-2 rounded-md border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
              {searchTerm && (
                <button 
                  onClick={() => setSearchTerm('')}
                  className="absolute right-2 top-2.5"
                >
                  <X className="h-4 w-4 text-slate-400" />
                </button>
              )}
            </div>
            
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'newest' | 'oldest' | 'name')}
              className="px-3 py-2 rounded-md border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option value="newest">Newest first</option>
              <option value="oldest">Oldest first</option>
              <option value="name">Name (A-Z)</option>
            </select>
          </div>
        )}
      </div>
      
      {!isCollapsed && (
        <div className="px-4 pb-4">
          {filteredTraces.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              {searchTerm ? 'No traces match your search' : 'No traces available'}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[300px] overflow-y-auto pr-2">
              {filteredTraces.map((trace) => (
                <div
                  key={trace.id}
                  onClick={() => handleSelectTrace(trace.id)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedTraceId === trace.id
                      ? 'border-blue-500 bg-blue-50 shadow-sm'
                      : 'border-slate-200 bg-white hover:border-blue-300 hover:shadow-sm'
                  }`}
                >
                  <h3 className="font-medium text-slate-800 mb-1 truncate">{trace.name}</h3>
                  {trace.description && (
                    <p className="text-sm text-slate-600 mb-2 line-clamp-2">{trace.description}</p>
                  )}
                  <div className="flex items-center text-xs text-slate-500 mt-2">
                    <Calendar className="h-3 w-3 mr-1" />
                    <span>{formatDate(trace.createdAt)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TraceSelector; 