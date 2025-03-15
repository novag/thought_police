from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from schema import schema
from database import get_db, engine, Base
from mcp_server import get_mcp_app

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Agent Action Tracker")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create GraphQL router
async def get_context(db=Depends(get_db)):
    return {"db": db}

# Create GraphQL app with subscription support
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=True,  # Enable GraphiQL interface for testing
    subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL],  # Enable WebSocket protocol for subscriptions
)

# Add GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")

# Mount the MCP server
app.mount("/", get_mcp_app())

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Agent Action Tracker API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
