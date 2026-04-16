# mcp_client.py
import asyncio
import re
from typing import Dict, Any, Optional
from mcp_server import mcp_server

class MCPChatbotClient:
    """MCP Client for integrating with the chatbot"""
    
    def __init__(self, user_id: int = None):
        self.user_id = user_id
        self.tools = mcp_server.get_tools_list()
        
    def process_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Process user message and determine if it should use MCP tools"""
        message_lower = message.lower().strip()
        
        # Calculator
        if re.match(r'^(calc|calculate|math|compute)\s+', message_lower):
            expression = re.sub(r'^(calc|calculate|math|compute)\s+', '', message)
            return {
                "tool": "calculator",
                "arguments": {"expression": expression}
            }
        
        # Weather
        elif re.match(r'^weather\s+', message_lower):
            city = re.sub(r'^weather\s+', '', message)
            return {
                "tool": "get_weather",
                "arguments": {"city": city}
            }
        
        # Create file on desktop
        elif re.match(r'^create\s+file\s+', message_lower):
            # Extract filename and optional content
            if ' with content ' in message_lower:
                parts = message.split(' with content ', 1)
                filename = parts[0].replace('create file ', '').strip()
                content = parts[1].strip()
            else:
                filename = re.sub(r'^create\s+file\s+', '', message).strip()
                content = ""
            return {
                "tool": "create_desktop_file",
                "arguments": {"filename": filename, "content": content}
            }
        
        # Create folder on desktop
        elif re.match(r'^create\s+folder\s+', message_lower):
            folder_name = re.sub(r'^create\s+folder\s+', '', message).strip()
            return {
                "tool": "create_desktop_folder",
                "arguments": {"folder_name": folder_name}
            }
        
        # Search files
        elif re.match(r'^search\s+files?\s+', message_lower):
            query = re.sub(r'^search\s+files?\s+', '', message).strip()
            return {
                "tool": "search_files",
                "arguments": {"query": query}
            }
        
        # Get conversation history
        elif 'history' in message_lower or 'previous messages' in message_lower or 'chat history' in message_lower:
            limit = 10
            # Extract limit if specified
            match = re.search(r'last\s+(\d+)', message_lower)
            if match:
                limit = int(match.group(1))
            return {
                "tool": "get_conversation_history",
                "arguments": {"user_id": self.user_id, "limit": limit}
            }
        
        # Get user info
        elif re.match(r'^user\s+info\s+', message_lower) or re.match(r'^who\s+is\s+', message_lower):
            username = re.sub(r'^(user\s+info|who\s+is)\s+', '', message).strip()
            return {
                "tool": "get_user_info",
                "arguments": {"username": username}
            }
        
        # Read file
        elif re.match(r'^read\s+file\s+', message_lower):
            parts = message.split()
            if 'lines' in message_lower:
                # Extract lines limit
                match = re.search(r'(\d+)\s+lines', message_lower)
                if match:
                    max_lines = int(match.group(1))
                    file_path = re.sub(r'^read\s+file\s+', '', message)
                    file_path = re.sub(r'\s+\d+\s+lines', '', file_path).strip()
                else:
                    file_path = re.sub(r'^read\s+file\s+', '', message).strip()
                    max_lines = 50
            else:
                file_path = re.sub(r'^read\s+file\s+', '', message).strip()
                max_lines = 50
            
            return {
                "tool": "read_file",
                "arguments": {"file_path": file_path, "max_lines": max_lines}
            }
        
        # System info
        elif message_lower in ['system info', 'system information', 'system']:
            return {
                "tool": "system_info",
                "arguments": {}
            }
        
        # Web search
        elif re.match(r'^search\s+web\s+', message_lower) or re.match(r'^google\s+', message_lower):
            query = re.sub(r'^(search\s+web|google)\s+', '', message).strip()
            return {
                "tool": "web_search",
                "arguments": {"query": query}
            }
        
        # Time
        elif message_lower in ['time', 'current time', 'what time is it']:
            return {
                "tool": "get_time",
                "arguments": {}
            }
        
        # Joke
        elif message_lower in ['joke', 'tell me a joke', 'make me laugh']:
            return {
                "tool": "get_random_joke",
                "arguments": {}
            }
        
        # Quote
        elif message_lower in ['quote', 'inspirational quote', 'motivational quote']:
            return {
                "tool": "get_quote",
                "arguments": {}
            }
        
        # Analyze image
        elif re.match(r'^analyze\s+image\s+', message_lower):
            image_path = re.sub(r'^analyze\s+image\s+', '', message).strip()
            return {
                "tool": "analyze_image",
                "arguments": {"image_path": image_path}
            }
        
        # File info
        elif re.match(r'^file\s+info\s+', message_lower):
            file_path = re.sub(r'^file\s+info\s+', '', message).strip()
            return {
                "tool": "get_file_info",
                "arguments": {"file_path": file_path}
            }
        
        # List directory
        elif re.match(r'^list\s+dir\s+', message_lower) or message_lower == 'list dir':
            if 'list dir' in message_lower and len(message.split()) > 2:
                directory = re.sub(r'^list\s+dir\s+', '', message).strip()
            else:
                directory = "."
            return {
                "tool": "list_directory",
                "arguments": {"directory_path": directory}
            }
        
        return None
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the result"""
        try:
            result = await mcp_server.handle_tool_call(tool_name, arguments)
            # Extract text from result
            for content in result.content:
                if hasattr(content, 'text'):
                    return content.text
            return "No response from tool"
        except Exception as e:
            return f"❌ Error executing tool: {str(e)}"
    
    def get_tools_description(self) -> str:
        """Get description of all available tools for UI"""
        description = "🔧 **MCP Tools Available:**\n\n"
        for tool in self.tools:
            description += f"• **{tool['name']}**: {tool['description']}\n"
            if tool['parameters']:
                description += f"  *Parameters: {', '.join(tool['parameters'])}*\n"
            description += "\n"
        
        description += "💡 **Usage Examples:**\n"
        description += "• `calculate 25 * 4` - Calculate expression\n"
        description += "• `weather London` - Get weather\n"
        description += "• `create file test.txt` - Create file on desktop\n"
        description += "• `create file notes.txt with content Hello World` - Create file with content\n"
        description += "• `create folder MyProject` - Create folder on desktop\n"
        description += "• `search files .jpg` - Search for files\n"
        description += "• `history` - Show chat history\n"
        description += "• `system info` - Get system information\n"
        description += "• `time` - Current time\n"
        description += "• `joke` - Tell a joke\n"
        description += "• `quote` - Inspirational quote\n"
        description += "• `read file C:/path/to/file.txt` - Read file content\n"
        description += "• `list dir` - List current directory\n"
        
        return description