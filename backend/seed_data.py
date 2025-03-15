from sqlalchemy.orm import Session
from models import Node, NodeType, Trace
from database import engine, SessionLocal, Base

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if we already have data
        if db.query(Trace).count() > 0:
            print("Database already seeded.")
            return
        
        # Create default trace
        default_trace = Trace(
            name="Todo App Creation",
            description="AI agent actions for creating a Todo application"
        )
        db.add(default_trace)
        db.flush()  # Flush to get the ID
        
        # Create a simple 3-step trail
        
        # Step 1: Initial prompt (root node)
        root = Node(
            type=NodeType.LOGGING,
            label="Initial Prompt",
            content="Create a web application that displays a list of todos",
            log_level="INFO",
            trace_id=default_trace.id
        )
        db.add(root)
        db.flush()  # Flush to get the ID
        
        # Step 2: Decision node
        decision = Node(
            type=NodeType.DECISION,
            label="Planning Application Structure",
            content="I need to create both frontend and backend components",
            parent_id=root.id,
            trace_id=default_trace.id,
            decision_outcome="Use React with Next.js"
        )
        db.add(decision)
        db.flush()
        
        # Step 3: Failed implementation attempt (terminal node)
        failed_attempt = Node(
            type=NodeType.TERMINAL,
            label="Implementation Failed",
            content="The chosen approach with server components is not compatible with the requirements",
            parent_id=decision.id,
            trace_id=default_trace.id,
            termination_reason="Incompatible technology choice"
        )
        db.add(failed_attempt)
        db.flush()
        
        # Step 4: New decision after abandoning previous branch
        new_decision = Node(
            type=NodeType.DECISION,
            label="Revised Planning",
            content="Need to use a different frontend approach",
            parent_id=root.id,  # Note: parent is the root node, not the failed branch
            trace_id=default_trace.id,
            decision_outcome="Use React with client components"
        )
        db.add(new_decision)
        db.flush()
        
        # Step 5: Final implementation
        implementation = Node(
            type=NodeType.LOGGING,
            label="Implementation Complete",
            content="Todo application has been successfully implemented",
            parent_id=new_decision.id,
            trace_id=default_trace.id,
            log_level="SUCCESS"
        )
        db.add(implementation)
        
        db.commit()
        print("Database seeded successfully!")
    
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    seed_database() 