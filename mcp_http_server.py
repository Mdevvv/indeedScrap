"""
HTTP wrapper for the MCP job automation server
Exposes the stdio-based MCP server via HTTP endpoints for n8n
Implements JSON-RPC protocol for proper MCP client compatibility
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import the MCP server functions
from server import (
    handle_list_tools,
    handle_call_tool,
)

# Configure logging
log_dir = Path(__file__).parent
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'mcp_http_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="MCP Job Automation HTTP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global request ID counter
_request_id_counter = 0


def generate_request_id() -> int:
    """Generate a unique request ID"""
    global _request_id_counter
    _request_id_counter += 1
    return _request_id_counter


async def convert_tools_to_dict(tools_response: Any) -> List[Dict]:
    """Convert Tool objects to dictionary format"""
    tools_list = []
    if isinstance(tools_response, list):
        for tool in tools_response:
            tool_dict = {
                "name": tool.name if hasattr(tool, 'name') else tool.get("name", ""),
                "description": tool.description if hasattr(tool, 'description') else tool.get("description", ""),
                "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else tool.get("inputSchema", {})
            }
            tools_list.append(tool_dict)
    return tools_list


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Main MCP endpoint implementing JSON-RPC 2.0 protocol
    Handles both initialization and tool calls
    """
    try:
        body = await request.json()
        logger.debug(f"Raw request body: {body}")
        
        # Handle JSON-RPC calls
        if isinstance(body, dict):
            method = body.get("method")
            params = body.get("params", {})
            req_id = body.get("id")
            
            logger.info(f"JSON-RPC Method: {method}, ID: {req_id}, Params: {params}")
            
            # Handle initialization
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "MCP Job Automation Server",
                            "version": "1.0.0"
                        }
                    }
                }
                logger.info(f"Sending initialization response")
                return JSONResponse(content=response)
            
            # Handle list tools
            elif method == "tools/list":
                try:
                    tools_response = await handle_list_tools()
                    tools_list = await convert_tools_to_dict(tools_response)
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "tools": tools_list
                        }
                    }
                    logger.info(f"Returning {len(tools_list)} tools")
                    return JSONResponse(content=response)
                except Exception as e:
                    logger.error(f"Error listing tools: {e}", exc_info=True)
                    return JSONResponse(
                        status_code=500,
                        content={
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "error": {
                                "code": -32603,
                                "message": f"Internal error: {str(e)}"
                            }
                        }
                    )
            
            # Handle tool call
            elif method == "tools/call":
                try:
                    tool_name = params.get("name")
                    tool_input = params.get("arguments", {})
                    
                    logger.info(f"Calling tool: {tool_name} with input: {tool_input}")
                    result = await handle_call_tool(tool_name, tool_input)
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": str(result)
                                }
                            ]
                        }
                    }
                    return JSONResponse(content=response)
                except Exception as e:
                    logger.error(f"Error calling tool: {e}", exc_info=True)
                    return JSONResponse(
                        status_code=500,
                        content={
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "error": {
                                "code": -32603,
                                "message": f"Tool call failed: {str(e)}"
                            }
                        }
                    )
            
            # Handle notifications (methods without an id)
            elif method and method.startswith("notifications/"):
                logger.info(f"Notification received: {method}")
                # Notifications don't expect a response
                return JSONResponse(status_code=200, content={})
            
            # Unknown method
            else:
                logger.warning(f"Unknown method: {method}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                )
        
        # Invalid request
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error or invalid request"
                }
            }
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal server error: {str(e)}"
                }
            }
        )


@app.get("/mcp")
async def mcp_get_info():
    """GET endpoint for basic server info"""
    try:
        tools_response = await handle_list_tools()
        tools_list = await convert_tools_to_dict(tools_response)
        
        return JSONResponse(content={
            "serverName": "MCP Job Automation Server",
            "version": "1.0.0",
            "toolCount": len(tools_list),
            "tools": tools_list
        })
    except Exception as e:
        logger.error(f"Error in MCP GET: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting MCP HTTP Server")
    logger.info("=" * 60)
    logger.info("Server URL: http://127.0.0.1:8001")
    logger.info("MCP endpoint: http://127.0.0.1:8001/mcp")
    logger.info("Tools endpoint: http://127.0.0.1:8001/mcp/tools")
    logger.info("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
