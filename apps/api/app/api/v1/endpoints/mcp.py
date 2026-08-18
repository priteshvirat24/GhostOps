from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.agents.mcp.server import GhostOpsMCPServer
from app.agents.mcp.contracts import (
    MCPToolDefinition,
    MCPToolRequest,
    MCPToolResponse,
)

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])

@router.get("/tools", response_model=List[MCPToolDefinition])
def list_mcp_tools():
    """Returns catalog of all registered MCP tools with JSON schemas and risk levels (§9.2, §19.3)."""
    return GhostOpsMCPServer.list_tools()

@router.post("/execute", response_model=MCPToolResponse)
def execute_mcp_tool(request: MCPToolRequest, db: Session = Depends(get_db)):
    """
    Executes an MCP tool call with strict allowlists, prompt-injection defense,
    and CockroachDB idempotency guarantees.
    """
    response = GhostOpsMCPServer.execute_tool(request, db)
    return response
