"""
MLB Analytics Agent - A baseball expert AI assistant

This agent helps users understand and enjoy baseball through
enthusiastic, knowledgeable conversations.
"""
from .mlb_tools import get_all_tools
from google.adk.agents import Agent
from .agent_instructions import MLB_SCOUT_DESCRIPTION, MLB_SCOUT_INSTRUCTIONS
import os
from toolbox_core import auth_methods  
from google.adk.tools.mcp_tool import (
    MCPToolset,
    StreamableHTTPConnectionParams,
    )
# Get MCP endpoint from environment
MCP_ENDPOINT = os.environ.get('MCP_URL') + '/mcp'

def build_bigquery_toolset() -> MCPToolset:
    # Get MCP endpoint from environment
    MCP_ENDPOINT = os.environ.get('MCP_URL') + '/mcp'
    print(f"MCP_ENDPOINT={os.environ.get('MCP_URL')}")
    """Create MCP toolset connected to our Cloud Run service."""
    # Get Google ID token for service-to-service authentication
    id_token = auth_methods.get_google_id_token(MCP_ENDPOINT)

    return MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=MCP_ENDPOINT,
            headers={"Authorization": id_token()},
            timeout=60,
            sse_read_timeout=300,  # Allow long-running queries
        )
    )
# Create the MLB Analytics agent with enhanced personality
root_agent = Agent(
    name="mlb_scout",
    model="gemini-2.5-flash",
    description=MLB_SCOUT_DESCRIPTION,
    instruction=MLB_SCOUT_INSTRUCTIONS,
    tools=[build_bigquery_toolset(), *get_all_tools()],  # Add this line
)
# For debugging - print confirmation when module loads
if __name__ == "__main__":
    print(f"✅ MLB Analytics agent configured")
    print(f"📝 Name: {root_agent.name}")
    print(f"🧠 Model: {root_agent.model}")
    print(f"📋 Instructions length: {len(root_agent.instruction)} characters")
    print(f"🛠️  Tools: {len(root_agent.tools)} configured")
    print(f"🔗 MCP Endpoint: {MCP_ENDPOINT}")
