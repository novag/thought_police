import React, { useMemo, useState, useCallback, useEffect } from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  Panel, 
  useReactFlow, 
  Node as FlowNodeType,
  MiniMap,
  ConnectionLineType,
  Edge
} from '@xyflow/react';
import { useQuery, useSubscription } from '@apollo/client';
import { GET_NODES, NODE_CREATED_SUBSCRIPTION } from '@/lib/graphql/queries';
import { Node, FlowNode, FlowEdge, NodeType } from '@/lib/types';
import ActionNode from './ActionNode';
import dagre from 'dagre';
import { ZoomIn, ZoomOut, Maximize, LayoutGrid, ArrowRightLeft, ArrowDownUp, Filter, Search, X } from 'lucide-react';

interface ActionFlowProps {
  traceId: number | null;
}

const nodeTypes = {
  actionNode: ActionNode,
};

// Helper function to create a tree layout
const getLayoutedElements = (nodes: FlowNode[], edges: FlowEdge[], direction = 'TB') => {
  if (!nodes.length) return { nodes, edges };
  
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ 
    rankdir: direction,
    nodesep: 100, // Horizontal spacing between nodes (was default 50)
    ranksep: 150, // Vertical spacing between nodes (was default 50)
    edgesep: 10,  // Minimum separation between adjacent edges
    ranker: 'network-simplex' // Use network simplex for better spacing
  });
  
  // Add nodes to the graph
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 300, height: 150 });
  });
  
  // Add edges to the graph
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });
  
  // Calculate the layout
  dagre.layout(dagreGraph);
  
  // Apply the layout to the nodes
  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 150, // Center the node (half of width)
        y: nodeWithPosition.y - 75,  // Center the node (half of height)
      },
    };
  });
  
  return { nodes: layoutedNodes, edges };
};

// Create flow elements from API nodes
const createFlowElements = (apiNodes: Node[]) => {
  const flowNodes: FlowNode[] = [];
  const flowEdges: FlowEdge[] = [];
  const nodeMap: Record<number, Node> = {};
  
  // First, create a map of all nodes by ID for easy lookup
  apiNodes.forEach(node => {
    nodeMap[node.id] = node;
  });
  
  // Create flow nodes for all nodes
  apiNodes.forEach(node => {
    const nodeId = `node-${node.id}`;
    
    flowNodes.push({
      id: nodeId,
      type: 'actionNode',
      data: { node },
      position: { x: 0, y: 0 }, // Initial position, will be recalculated by layout
    });
  });
  
  // Create edges based on parent-child relationships
  apiNodes.forEach(node => {
    if (node.parentId) {
      const sourceId = `node-${node.parentId}`;
      const targetId = `node-${node.id}`;
      
      flowEdges.push({
        id: `edge-${sourceId}-${targetId}`,
        source: sourceId,
        target: targetId,
        type: 'smoothstep'
      });
    }
  });
  
  return { nodes: flowNodes, edges: flowEdges };
};

const ActionFlow: React.FC<ActionFlowProps> = ({ traceId }) => {
  // Ensure traceId is a number for the GraphQL query
  const traceIdNumber = traceId !== null ? Number(traceId) : null;
  
  const { data, loading, error, refetch } = useQuery(GET_NODES, {
    variables: { traceId: traceIdNumber },
    skip: traceIdNumber === null,
    fetchPolicy: 'network-only', // Don't use cache, always fetch from server
  });
  
  // Subscribe to new nodes for this trace
  const { data: subscriptionData } = useSubscription(NODE_CREATED_SUBSCRIPTION, {
    variables: { traceId: traceIdNumber },
    skip: traceIdNumber === null,
  });
  
  // Add console logging for debugging
  console.log('ActionFlow render:', { 
    traceId, 
    traceIdNumber, 
    loading, 
    error, 
    hasData: !!data, 
    nodesCount: data?.nodes?.length,
    subscriptionReceived: !!subscriptionData
  });
  
  const [nodes, setNodes] = useState<FlowNode[]>([]);
  const [edges, setEdges] = useState<FlowEdge[]>([]);
  const [layoutDirection, setLayoutDirection] = useState<'TB' | 'LR'>('TB');
  const [nodeTypeFilter, setNodeTypeFilter] = useState<NodeType | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [allApiNodes, setAllApiNodes] = useState<Node[]>([]);
  
  const reactFlowInstance = useReactFlow();
  
  // Force refetch when traceId changes
  useEffect(() => {
    if (traceIdNumber !== null) {
      refetch({ traceId: traceIdNumber });
    }
  }, [traceIdNumber, refetch]);
  
  // Process data when it changes
  useEffect(() => {
    if (data?.nodes) {
      // Flatten the hierarchical structure to get all nodes
      const flattenNodes = (nodes: Node[]): Node[] => {
        let result: Node[] = [];
        nodes.forEach(node => {
          result.push(node);
          if (node.children && node.children.length > 0) {
            result = result.concat(flattenNodes(node.children));
          }
        });
        return result;
      };
      
      const allNodes = flattenNodes(data.nodes);
      setAllApiNodes(allNodes);
    }
  }, [data]);
  
  // Handle subscription data
  useEffect(() => {
    if (subscriptionData?.nodeCreated) {
      console.log('New node received:', subscriptionData.nodeCreated);
      
      // Add the new node to our list if it doesn't already exist
      setAllApiNodes(prevNodes => {
        const newNode = subscriptionData.nodeCreated;
        const exists = prevNodes.some(node => node.id === newNode.id);
        
        if (exists) {
          return prevNodes;
        }
        
        // If this is a child node, we need to update its parent's children array
        if (newNode.parentId) {
          return prevNodes.map(node => {
            if (node.id === newNode.parentId) {
              return {
                ...node,
                children: [...(node.children || []), newNode]
              };
            }
            return node;
          }).concat([newNode]);
        }
        
        // Otherwise just add it to the list
        return [...prevNodes, newNode];
      });
    }
  }, [subscriptionData]);
  
  // Update visualization when nodes change
  useEffect(() => {
    console.log('ActionFlow useEffect:', { 
      apiNodesCount: allApiNodes.length,
      filteredNodesCount: allApiNodes.filter(node => !nodeTypeFilter || node.type === nodeTypeFilter).length
    });
    
    let timeoutId: NodeJS.Timeout;
    
    if (allApiNodes.length > 0) {
      // Apply node type filter if set
      let filteredNodes = [...allApiNodes];
      if (nodeTypeFilter) {
        filteredNodes = filteredNodes.filter(node => node.type === nodeTypeFilter);
      }
      
      // Apply search filter if set
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        filteredNodes = filteredNodes.filter(node => 
          node.label.toLowerCase().includes(term) || 
          (node.content && node.content.toLowerCase().includes(term)) ||
          (node.toolName && node.toolName.toLowerCase().includes(term)) ||
          (node.decisionOutcome && node.decisionOutcome.toLowerCase().includes(term))
        );
      }
      
      console.log('Creating flow elements with filtered nodes:', filteredNodes.length);
      
      const { nodes: flowNodes, edges: flowEdges } = createFlowElements(filteredNodes);
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        flowNodes,
        flowEdges,
        layoutDirection
      );
      
      console.log('Setting nodes and edges:', { 
        flowNodesCount: flowNodes.length, 
        flowEdgesCount: flowEdges.length,
        layoutedNodesCount: layoutedNodes.length
      });
      
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
      
      // Fit view after setting nodes
      timeoutId = setTimeout(() => {
        if (reactFlowInstance && layoutedNodes.length > 0) {
          reactFlowInstance.fitView({ padding: 0.4 });
        }
      }, 100);
    } else {
      setNodes([]);
      setEdges([]);
    }
    
    // Cleanup function
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [allApiNodes, layoutDirection, nodeTypeFilter, searchTerm, reactFlowInstance]);
  
  const onLayout = useCallback((direction: 'TB' | 'LR') => {
    setLayoutDirection(direction);
  }, []);
  
  const onNodeClick = useCallback((event: React.MouseEvent, node: FlowNodeType) => {
    setSelectedNodeId(node.id === selectedNodeId ? null : node.id);
  }, [selectedNodeId]);
  
  const resetFilters = useCallback(() => {
    setNodeTypeFilter(null);
    setSearchTerm('');
  }, []);
  
  const fitView = useCallback(() => {
    if (reactFlowInstance) {
      reactFlowInstance.fitView({ padding: 0.4 });
    }
  }, [reactFlowInstance]);
  
  if (!traceId) {
    return (
      <div className="flex items-center justify-center h-full bg-slate-50">
        <div className="text-center p-8">
          <h3 className="text-xl font-semibold text-slate-700 mb-2">No Trace Selected</h3>
          <p className="text-slate-500">Select a trace from the list above to view its action flow.</p>
        </div>
      </div>
    );
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-slate-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading action flow...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-slate-50">
        <div className="text-center p-8 max-w-md">
          <h3 className="text-xl font-semibold text-red-600 mb-2">Error Loading Data</h3>
          <p className="text-slate-600">{error.message}</p>
        </div>
      </div>
    );
  }
  
  if (!data?.nodes || data.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full bg-slate-50">
        <div className="text-center p-8">
          <h3 className="text-xl font-semibold text-slate-700 mb-2">No Nodes Found</h3>
          <p className="text-slate-500">This trace doesn't have any action nodes to display.</p>
        </div>
      </div>
    );
  }
  
  return (
    <div style={{ width: '100%', height: '100%', position: 'absolute' }}>
      <ReactFlow
        key={`flow-${traceIdNumber}`}
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={onNodeClick}
        connectionLineType={ConnectionLineType.SmoothStep}
        defaultEdgeOptions={{ type: 'smoothstep' }}
        fitView
        fitViewOptions={{ padding: 0.4 }}
        style={{ width: '100%', height: '100%' }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#f1f5f9" gap={16} />
        <Controls showInteractive={false} />
        <MiniMap 
          nodeColor={(node) => {
            const nodeData = (node as any).data?.node;
            if (!nodeData) return '#eee';
            
            switch (nodeData.type) {
              case NodeType.LOGGING:
                return '#93c5fd'; // blue-300
              case NodeType.DECISION:
                return '#c4b5fd'; // purple-300
              case NodeType.TOOL_CALL:
                return '#86efac'; // green-300
              case NodeType.TERMINAL:
                return '#fca5a5'; // red-300
              default:
                return '#e5e7eb'; // gray-200
            }
          }}
          maskColor="rgba(241, 245, 249, 0.7)"
        />
        
        <Panel position="top-right" className="bg-white p-3 rounded-lg shadow-md border border-slate-200">
          <div className="flex flex-col gap-3">
            <div className="flex gap-2">
              <button
                onClick={() => onLayout('TB')}
                className={`p-2 rounded ${layoutDirection === 'TB' ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 hover:bg-slate-200'}`}
                title="Vertical Layout"
              >
                <ArrowDownUp size={16} />
              </button>
              <button
                onClick={() => onLayout('LR')}
                className={`p-2 rounded ${layoutDirection === 'LR' ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 hover:bg-slate-200'}`}
                title="Horizontal Layout"
              >
                <ArrowRightLeft size={16} />
              </button>
              <button
                onClick={fitView}
                className="p-2 rounded bg-slate-100 hover:bg-slate-200"
                title="Fit View"
              >
                <Maximize size={16} />
              </button>
            </div>
            
            <div className="border-t border-slate-200 pt-3">
              <div className="text-xs font-medium text-slate-500 mb-2">Filter by Type</div>
              <div className="flex flex-wrap gap-1">
                <button
                  onClick={() => setNodeTypeFilter(null)}
                  className={`px-2 py-1 text-xs rounded ${!nodeTypeFilter ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 hover:bg-slate-200'}`}
                >
                  All
                </button>
                <button
                  onClick={() => setNodeTypeFilter(NodeType.LOGGING)}
                  className={`px-2 py-1 text-xs rounded ${nodeTypeFilter === NodeType.LOGGING ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 hover:bg-slate-200'}`}
                >
                  Logging
                </button>
                <button
                  onClick={() => setNodeTypeFilter(NodeType.DECISION)}
                  className={`px-2 py-1 text-xs rounded ${nodeTypeFilter === NodeType.DECISION ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 hover:bg-slate-200'}`}
                >
                  Decision
                </button>
                <button
                  onClick={() => setNodeTypeFilter(NodeType.TOOL_CALL)}
                  className={`px-2 py-1 text-xs rounded ${nodeTypeFilter === NodeType.TOOL_CALL ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 hover:bg-slate-200'}`}
                >
                  Tool Call
                </button>
              </div>
            </div>
            
            <div className="border-t border-slate-200 pt-3">
              <div className="text-xs font-medium text-slate-500 mb-2">Search</div>
              <div className="relative">
                <Search className="absolute left-2 top-1.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search nodes..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-8 pr-4 py-1 text-sm rounded border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {searchTerm && (
                  <button 
                    onClick={() => setSearchTerm('')}
                    className="absolute right-2 top-1.5"
                  >
                    <X className="h-4 w-4 text-slate-400" />
                  </button>
                )}
              </div>
            </div>
            
            {(nodeTypeFilter || searchTerm) && (
              <button
                onClick={resetFilters}
                className="text-xs text-blue-600 hover:text-blue-800 mt-1"
              >
                Reset all filters
              </button>
            )}
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
};

export default ActionFlow; 