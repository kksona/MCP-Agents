# ./adk_agent_samples/mcp_agent/agent.py
import os # Required for path operations
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters, StdioConnectionParams

root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='booking_assistant',
    instruction='Help the user to book places to stay on a vacation.',
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="npx",
                args = [
                    "-y",
                    "@openbnb/mcp-server-airbnb",
                    "--ignore-robots-txt"
                ]
            ),
        )
    ],
)