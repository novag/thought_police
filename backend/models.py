from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Enum
import enum
from datetime import datetime
from database import Base

class NodeType(enum.Enum):
    LOGGING = "logging"
    DECISION = "decision"
    TOOL_CALL = "tool_call"
    TERMINAL = "terminal"  # New node type for abandoned branches

class Trace(Base):
    __tablename__ = "traces"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(NodeType), nullable=False)
    label = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    parent_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    trace_id = Column(Integer, ForeignKey("traces.id"), nullable=False)
    
    # Additional fields specific to node types
    tool_name = Column(String, nullable=True)  # For tool calls
    decision_outcome = Column(String, nullable=True)  # For decisions
    log_level = Column(String, nullable=True)  # For logging 
    termination_reason = Column(String, nullable=True)  # For terminal nodes 