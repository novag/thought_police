import React, { useState } from 'react';
import { Handle, Position } from '@xyflow/react';
import { NodeType } from '@/lib/types';
import { ChevronDown, ChevronUp, Clock, FileText, Wrench, GitBranch, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';

interface ActionNodeProps {
  data: {
    node: {
      id: number;
      type: NodeType;
      label: string;
      content?: string;
      timestamp: string;
      toolName?: string;
      decisionOutcome?: string;
      logLevel?: string;
      termination_reason?: string;
    };
  };
  selected: boolean;
}

const getNodeColor = (type: NodeType) => {
  switch (type) {
    case NodeType.LOGGING:
      return {
        bg: 'bg-blue-100',
        border: 'border-blue-500',
        text: 'text-blue-800',
        hover: 'hover:bg-blue-50',
        detail: 'bg-blue-50'
      };
    case NodeType.DECISION:
      return {
        bg: 'bg-purple-100',
        border: 'border-purple-500',
        text: 'text-purple-800',
        hover: 'hover:bg-purple-50',
        detail: 'bg-purple-50'
      };
    case NodeType.TOOL_CALL:
      return {
        bg: 'bg-green-100',
        border: 'border-green-500',
        text: 'text-green-800',
        hover: 'hover:bg-green-50',
        detail: 'bg-green-50'
      };
    case NodeType.TERMINAL:
      return {
        bg: 'bg-red-100',
        border: 'border-red-500',
        text: 'text-red-800',
        hover: 'hover:bg-red-50',
        detail: 'bg-red-50'
      };
    default:
      return {
        bg: 'bg-gray-100',
        border: 'border-gray-500',
        text: 'text-gray-800',
        hover: 'hover:bg-gray-50',
        detail: 'bg-gray-50'
      };
  }
};

const getNodeIcon = (type: NodeType) => {
  switch (type) {
    case NodeType.LOGGING:
      return <FileText className="h-4 w-4" />;
    case NodeType.DECISION:
      return <GitBranch className="h-4 w-4" />;
    case NodeType.TOOL_CALL:
      return <Wrench className="h-4 w-4" />;
    case NodeType.TERMINAL:
      return <AlertTriangle className="h-4 w-4" />;
    default:
      return <FileText className="h-4 w-4" />;
  }
};

const formatTimestamp = (timestamp: string) => {
  try {
    return format(new Date(timestamp), 'MMM d, yyyy h:mm:ss a');
  } catch (e) {
    return timestamp;
  }
};

const ActionNode: React.FC<ActionNodeProps> = ({ data, selected }) => {
  const { node } = data;
  const nodeColors = getNodeColor(node.type);
  const nodeIcon = getNodeIcon(node.type);
  const [expanded, setExpanded] = useState(false);
  
  const toggleExpanded = (e: React.MouseEvent) => {
    e.stopPropagation();
    setExpanded(!expanded);
  };
  
  return (
    <div 
      className={`rounded-lg border-2 shadow-md w-72 transition-all duration-200 ${nodeColors.border} ${selected ? 'ring-2 ring-blue-400' : ''}`}
    >
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      
      <div className={`p-3 ${nodeColors.bg} rounded-t-md`}>
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center">
            <span className={`mr-2 ${nodeColors.text} flex items-center justify-center`}>
              {nodeIcon}
            </span>
            <h3 className="font-bold text-sm truncate">{node.label}</h3>
          </div>
          <button 
            onClick={toggleExpanded}
            className={`p-1 rounded-full ${nodeColors.hover}`}
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
        
        <div className="flex items-center text-xs text-gray-500">
          <Clock className="h-3 w-3 mr-1" />
          <span>{formatTimestamp(node.timestamp)}</span>
        </div>
      </div>
      
      <div className="p-3 bg-white rounded-b-md">
        {node.type === NodeType.DECISION && node.decisionOutcome && (
          <div className="mb-2">
            <div className="text-xs font-semibold text-gray-500 mb-1">Outcome:</div>
            <div className={`text-xs p-1.5 rounded ${nodeColors.detail}`}>
              {node.decisionOutcome}
            </div>
          </div>
        )}
        
        {node.type === NodeType.TOOL_CALL && node.toolName && (
          <div className="mb-2">
            <div className="text-xs font-semibold text-gray-500 mb-1">Tool:</div>
            <div className={`text-xs p-1.5 rounded ${nodeColors.detail}`}>
              {node.toolName}
            </div>
          </div>
        )}
        
        {node.type === NodeType.LOGGING && node.logLevel && (
          <div className="mb-2">
            <div className="text-xs font-semibold text-gray-500 mb-1">Level:</div>
            <div className={`text-xs p-1.5 rounded ${nodeColors.detail}`}>
              {node.logLevel}
            </div>
          </div>
        )}
        
        {node.type === NodeType.TERMINAL && node.termination_reason && (
          <div className="mb-2">
            <div className="text-xs font-semibold text-gray-500 mb-1">Reason:</div>
            <div className={`text-xs p-1.5 rounded ${nodeColors.detail}`}>
              {node.termination_reason}
            </div>
          </div>
        )}
        
        {node.content && (
          <p className={`text-xs text-gray-600 mb-2 ${expanded ? '' : 'line-clamp-2'}`}>
            {node.content}
          </p>
        )}
        
        {expanded && (
          <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
            <div>ID: {node.id}</div>
          </div>
        )}
      </div>
      
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
};

export default ActionNode; 