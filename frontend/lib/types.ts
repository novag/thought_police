export enum NodeType {
  LOGGING = "LOGGING",
  DECISION = "DECISION",
  TOOL_CALL = "TOOL_CALL",
  TERMINAL = "TERMINAL"
}

export interface Trace {
  id: number;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Node {
  id: number;
  type: NodeType;
  label: string;
  content?: string;
  timestamp: string;
  parentId?: number;
  traceId: number;
  toolName?: string;
  decisionOutcome?: string;
  logLevel?: string;
  termination_reason?: string;
  children: Node[];
}

export interface FlowNode {
  id: string;
  type: string;
  data: {
    node: Node;
  };
  position: {
    x: number;
    y: number;
  };
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  type: string;
} 