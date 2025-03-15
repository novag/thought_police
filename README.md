# AI Agent Action Tracker

This application tracks all actions performed by the Cursor AI agent and visualizes them as a tree graph in the frontend.

## Project Structure

- **Backend**: FastAPI + Strawberry GraphQL + SQLAlchemy + SQLite
- **Frontend**: React + Next.js + Apollo GraphQL + XYFlow/React

## Features

- Visualizes AI agent actions as a tree graph
- Supports different node types:
  - Logging step
  - Decision
  - Tool call
- Interactive graph with zoom, pan, and layout options
- GraphQL API for data retrieval

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+
- Yarn

### Running the Backend

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -e .
   ```

4. Run the backend server:
   ```
   uvicorn main:app --reload
   ```

The backend will be available at http://localhost:8000. The GraphQL playground will be at http://localhost:8000/graphql.

### Running the Frontend

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   yarn install
   ```

3. Run the development server:
   ```
   yarn dev
   ```

The frontend will be available at http://localhost:3000.

## Development

### Backend

The backend uses:
- FastAPI for the REST API
- Strawberry for GraphQL
- SQLAlchemy for ORM
- SQLite for the database

### Frontend

The frontend uses:
- Next.js for the React framework
- Apollo Client for GraphQL
- XYFlow/React for the flow visualization

## Future Enhancements

- Real-time updates using WebSockets
- More detailed node information
- Filtering and searching capabilities
- Integration with the actual Cursor AI agent 