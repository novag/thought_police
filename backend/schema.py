import strawberry
from typing import List, Optional, AsyncGenerator
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session
from models import Node as NodeModel, NodeType as NodeTypeModel, Trace as TraceModel
import asyncio
from strawberry.types import Info

# Create a simple in-memory event system for subscriptions
trace_subscribers = []
node_subscribers = []

@strawberry.enum
class NodeType(Enum):
    LOGGING = "logging"
    DECISION = "decision"
    TOOL_CALL = "tool_call"
    TERMINAL = "terminal"

@strawberry.type
class Trace:
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db_model(cls, trace: TraceModel):
        return cls(
            id=trace.id,
            name=trace.name,
            description=trace.description,
            created_at=trace.created_at,
            updated_at=trace.updated_at
        )

@strawberry.type
class Node:
    id: int
    type: NodeType
    label: str
    content: Optional[str]
    timestamp: datetime
    parent_id: Optional[int]
    trace_id: int
    tool_name: Optional[str]
    decision_outcome: Optional[str]
    log_level: Optional[str]
    termination_reason: Optional[str]
    children: List["Node"]

    @classmethod
    def from_db_model(cls, node: NodeModel, db: Session):
        # Get children manually
        children = db.query(NodeModel).filter(NodeModel.parent_id == node.id).all()
        children_nodes = [cls.from_db_model(child, db) for child in children]
        
        return cls(
            id=node.id,
            type=NodeType[node.type.name],
            label=node.label,
            content=node.content,
            timestamp=node.timestamp,
            parent_id=node.parent_id,
            trace_id=node.trace_id,
            tool_name=node.tool_name,
            decision_outcome=node.decision_outcome,
            log_level=node.log_level,
            termination_reason=node.termination_reason,
            children=children_nodes
        )

# Define generator functions after the class definitions
async def trace_generator() -> AsyncGenerator[Trace, None]:
    queue = asyncio.Queue()
    trace_subscribers.append(queue)
    try:
        while True:
            trace = await queue.get()
            if trace is None:
                break
            yield trace
    finally:
        trace_subscribers.remove(queue)

async def node_generator(trace_id: Optional[int] = None) -> AsyncGenerator[Node, None]:
    queue = asyncio.Queue()
    node_subscribers.append((queue, trace_id))
    try:
        while True:
            node = await queue.get()
            if node is None:
                break
            yield node
    finally:
        node_subscribers.remove((queue, trace_id))

# Publish a new trace to all subscribers
async def publish_trace(trace):
    for queue in trace_subscribers:
        await queue.put(trace)

# Publish a new node to all subscribers
async def publish_node(node):
    for queue, trace_id in node_subscribers:
        # If trace_id is specified, only send to subscribers of that trace
        if trace_id is None or trace_id == node.trace_id:
            await queue.put(node)

@strawberry.type
class Query:
    @strawberry.field
    def traces(self, info) -> List[Trace]:
        db: Session = info.context["db"]
        db_traces = db.query(TraceModel).all()
        return [Trace.from_db_model(trace) for trace in db_traces]
    
    @strawberry.field
    def trace(self, info, id: int) -> Optional[Trace]:
        db: Session = info.context["db"]
        db_trace = db.query(TraceModel).filter(TraceModel.id == id).first()
        if db_trace:
            return Trace.from_db_model(db_trace)
        return None
    
    @strawberry.field
    def nodes(self, info, trace_id: Optional[int] = None) -> List[Node]:
        db: Session = info.context["db"]
        # Get only root nodes (nodes without parents)
        query = db.query(NodeModel).filter(NodeModel.parent_id.is_(None))
        
        # Filter by trace_id if provided
        if trace_id is not None:
            query = query.filter(NodeModel.trace_id == trace_id)
            
        db_nodes = query.all()
        return [Node.from_db_model(node, db) for node in db_nodes]
    
    @strawberry.field
    def node(self, info, id: int) -> Optional[Node]:
        db: Session = info.context["db"]
        db_node = db.query(NodeModel).filter(NodeModel.id == id).first()
        if db_node:
            return Node.from_db_model(db_node, db)
        return None

@strawberry.input
class TraceInput:
    name: str
    description: Optional[str] = None

@strawberry.input
class NodeInput:
    type: NodeType
    label: str
    content: Optional[str] = None
    parent_id: Optional[int] = None
    trace_id: int
    tool_name: Optional[str] = None
    decision_outcome: Optional[str] = None
    log_level: Optional[str] = None
    termination_reason: Optional[str] = None

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_trace(self, info, input: TraceInput) -> Trace:
        db: Session = info.context["db"]
        
        db_trace = TraceModel(
            name=input.name,
            description=input.description
        )
        
        db.add(db_trace)
        db.commit()
        db.refresh(db_trace)
        
        trace = Trace.from_db_model(db_trace)
        
        # Publish the new trace to subscribers
        await publish_trace(trace)
        
        return trace
    
    @strawberry.mutation
    def update_trace(self, info, id: int, input: TraceInput) -> Optional[Trace]:
        db: Session = info.context["db"]
        db_trace = db.query(TraceModel).filter(TraceModel.id == id).first()
        
        if not db_trace:
            return None
        
        db_trace.name = input.name
        db_trace.description = input.description
        
        db.commit()
        db.refresh(db_trace)
        
        return Trace.from_db_model(db_trace)
    
    @strawberry.mutation
    def delete_trace(self, info, id: int) -> bool:
        db: Session = info.context["db"]
        db_trace = db.query(TraceModel).filter(TraceModel.id == id).first()
        
        if not db_trace:
            return False
        
        # Delete all nodes associated with this trace
        db.query(NodeModel).filter(NodeModel.trace_id == id).delete()
        
        # Delete the trace
        db.delete(db_trace)
        db.commit()
        
        return True
    
    @strawberry.mutation
    async def create_node(self, info, input: NodeInput) -> Node:
        db: Session = info.context["db"]
        
        # Create the node
        db_node = NodeModel(
            type=NodeTypeModel[input.type.name],
            label=input.label,
            content=input.content,
            parent_id=input.parent_id,
            trace_id=input.trace_id,
            tool_name=input.tool_name,
            decision_outcome=input.decision_outcome,
            log_level=input.log_level,
            termination_reason=input.termination_reason
        )
        
        db.add(db_node)
        db.commit()
        db.refresh(db_node)
        
        node = Node.from_db_model(db_node, db)
        
        # Publish the new node to subscribers
        await publish_node(node)
        
        return node

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def trace_created(self, info: Info) -> AsyncGenerator[Trace, None]:
        return trace_generator()
        
    @strawberry.subscription
    async def node_created(self, info: Info, trace_id: Optional[int] = None) -> AsyncGenerator[Node, None]:
        return node_generator(trace_id)

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription) 