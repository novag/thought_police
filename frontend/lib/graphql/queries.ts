import { gql } from '@apollo/client';

export const GET_TRACES = gql`
  query GetTraces {
    traces {
      id
      name
      description
      createdAt
      updatedAt
    }
  }
`;

export const GET_TRACE = gql`
  query GetTrace($id: Int!) {
    trace(id: $id) {
      id
      name
      description
      createdAt
      updatedAt
    }
  }
`;

export const GET_NODES = gql`
  query GetNodes($traceId: Int!) {
    nodes(traceId: $traceId) {
      id
      type
      label
      content
      timestamp
      parentId
      traceId
      toolName
      decisionOutcome
      logLevel
      children {
        id
        type
        label
        content
        timestamp
        parentId
        traceId
        toolName
        decisionOutcome
        logLevel
        children {
          id
          type
          label
          content
          timestamp
          parentId
          traceId
          toolName
          decisionOutcome
          logLevel
          children {
            id
            type
            label
          }
        }
      }
    }
  }
`;

export const GET_NODE = gql`
  query GetNode($id: Int!) {
    node(id: $id) {
      id
      type
      label
      content
      timestamp
      parentId
      traceId
      toolName
      decisionOutcome
      logLevel
      children {
        id
        type
        label
        content
        timestamp
        parentId
        traceId
        toolName
        decisionOutcome
        logLevel
      }
    }
  }
`;

export const CREATE_TRACE = gql`
  mutation CreateTrace($input: TraceInput!) {
    createTrace(input: $input) {
      id
      name
      description
      createdAt
      updatedAt
    }
  }
`;

export const CREATE_NODE = gql`
  mutation CreateNode($input: NodeInput!) {
    createNode(input: $input) {
      id
      type
      label
      content
      timestamp
      parentId
      traceId
      toolName
      decisionOutcome
      logLevel
    }
  }
`;

export const TRACE_CREATED_SUBSCRIPTION = gql`
  subscription TraceCreated {
    traceCreated {
      id
      name
      description
      createdAt
      updatedAt
    }
  }
`;

export const NODE_CREATED_SUBSCRIPTION = gql`
  subscription NodeCreated($traceId: Int) {
    nodeCreated(traceId: $traceId) {
      id
      type
      label
      content
      timestamp
      parentId
      traceId
      toolName
      decisionOutcome
      logLevel
      children {
        id
        type
        label
        content
        timestamp
        parentId
        traceId
        toolName
        decisionOutcome
        logLevel
      }
    }
  }
`; 