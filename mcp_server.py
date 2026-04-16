# mcp_server.py
import asyncio
import json
import os
import sqlite3
import subprocess
import shutil
import platform
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

class ToolResult:
    """Simple Tool Result class"""
    def __init__(self, content):
        self.content = content

class TextContent:
    """Simple Text Content class"""
    def __init__(self, type, text):
        self.type = type
        self.text = text

class MCPChatbotServer:
    """MCP Server for MFASHA AI Chatbot"""
    
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        self.tools = {}
        self.setup_tools()
        
    def setup_tools(self):
        """Setup all MCP tools"""
        
        # Calculator tool
        self.tools["calculator"] = {
            "function": self.calculator,
            "description": "Perform mathematical calculations safely",
            "parameters": ["expression"]
        }
        
        # Weather tool
        self.tools["get_weather"] = {
            "function": self.get_weather,
            "description": "Get weather information for a city",
            "parameters": ["city"]
        }
        
        # Create desktop file
        self.tools["create_desktop_file"] = {
            "function": self.create_desktop_file,
            "description": "Create a file on the desktop",
            "parameters": ["filename", "content"]
        }
        
        # Create desktop folder
        self.tools["create_desktop_folder"] = {
            "function": self.create_desktop_folder,
            "description": "Create a folder on the desktop",
            "parameters": ["folder_name"]
        }
        
        # Search files
        self.tools["search_files"] = {
            "function": self.search_files,
            "description": "Search for files in uploads folder",
            "parameters": ["query"]
        }
        
        # Get conversation history
        self.tools["get_conversation_history"] = {
            "function": self.get_conversation_history,
            "description": "Get recent conversation history for a user",
            "parameters": ["user_id", "limit"]
        }
        
        # Get user info
        self.tools["get_user_info"] = {
            "function": self.get_user_info,
            "description": "Get user information",
            "parameters": ["username"]
        }
        
        # Read file
        self.tools["read_file"] = {
            "function": self.read_file,
            "description": "Read content of a text file",
            "parameters": ["file_path", "max_lines"]
        }
        
        # System info
        self.tools["system_info"] = {
            "function": self.system_info,
            "description": "Get system information",
            "parameters": []
        }
        
        # Web search (simulated)
        self.tools["web_search"] = {
            "function": self.web_search,
            "description": "Simulate web search",
            "parameters": ["query"]
        }
        
        # Get time
        self.tools["get_time"] = {
            "function": self.get_time,
            "description": "Get current date and time",
            "parameters": []
        }
        
        # Get random joke
        self.tools["get_random_joke"] = {
            "function": self.get_random_joke,
            "description": "Get a random joke",
            "parameters": []
        }
        
        # Get quote
        self.tools["get_quote"] = {
            "function": self.get_quote,
            "description": "Get an inspirational quote",
            "parameters": []
        }
        
        # Image analysis
        self.tools["analyze_image"] = {
            "function": self.analyze_image,
            "description": "Analyze image content",
            "parameters": ["image_path"]
        }
        
        # File info
        self.tools["get_file_info"] = {
            "function": self.get_file_info,
            "description": "Get information about a file",
            "parameters": ["file_path"]
        }
        
        # List directory
        self.tools["list_directory"] = {
            "function": self.list_directory,
            "description": "List contents of a directory",
            "parameters": ["directory_path"]
        }
    
    async def calculator(self, expression: str) -> ToolResult:
        """Perform mathematical calculations safely"""
        try:
            # Safe evaluation
            allowed_names = {
                'abs': abs, 'round': round, 'min': min, 'max': max,
                'pow': pow, 'sum': sum, 'len': len, 'int': int, 'float': float
            }
            # Remove dangerous characters and evaluate
            safe_expr = ''.join(c for c in expression if c.isdigit() or c in '+-*/(). %')
            result = eval(safe_expr, {"__builtins__": {}}, allowed_names)
            return ToolResult(
                [TextContent(
                    type="text",
                    text=f"✅ **Calculation Result:**\n`{expression} = {result}`\n\n**JavaScript Calculator Output:**\n```javascript\n{expression} = {result}\n```"
                )]
            )
        except Exception as e:
            return ToolResult(
                [TextContent(
                    type="text",
                    text=f"❌ Error in calculation: {str(e)}\n\n**Example usage:**\n• calculate 25 * 4\n• calc (10 + 5) * 2\n• math sqrt(16) + 10"
                )]
            )
    
    async def get_weather(self, city: str) -> ToolResult:
        """Get weather information for a city"""
        # Simulated weather data (replace with actual API)
        weather_data = {
            "city": city,
            "temperature": "22°C",
            "conditions": "Partly cloudy",
            "humidity": "65%",
            "wind": "12 km/h",
            "feels_like": "24°C",
            "pressure": "1015 hPa"
        }
        return ToolResult(
            [TextContent(
                type="text",
                text=f"🌤️ **Weather in {city}**\n\n"
                     f"• Temperature: {weather_data['temperature']}\n"
                     f"• Feels like: {weather_data['feels_like']}\n"
                     f"• Conditions: {weather_data['conditions']}\n"
                     f"• Humidity: {weather_data['humidity']}\n"
                     f"• Wind: {weather_data['wind']}\n"
                     f"• Pressure: {weather_data['pressure']}\n\n"
                     f"*Note: Real-time weather API integration available.*"
            )]
        )
    
    async def create_desktop_file(self, filename: str, content: str = "") -> ToolResult:
        """Create a file on the desktop"""
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            file_path = os.path.join(desktop_path, filename)
            
            if not content:
                content = f"Created by MFASHA AI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                [TextContent(
                    type="text",
                    text=f"✅ **File Created Successfully!**\n\n"
                         f"📄 **File:** {filename}\n"
                         f"📍 **Location:** {file_path}\n"
                         f"📝 **Size:** {len(content)} characters\n"
                         f"⏰ **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )]
            )
        except Exception as e:
            return ToolResult(
                [TextContent(
                    type="text",
                    text=f"❌ Error creating file: {str(e)}"
                )]
            )
    
    async def create_desktop_folder(self, folder_name: str) -> ToolResult:
        """Create a folder on the desktop"""
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            folder_path = os.path.join(desktop_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            
            return ToolResult(
                [TextContent(
                    type="text",
                    text=f"✅ **Folder Created Successfully!**\n\n"
                         f"📁 **Folder:** {folder_name}\n"
                         f"📍 **Location:** {folder_path}\n"
                         f"⏰ **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )]
            )
        except Exception as e:
            return ToolResult(
                [TextContent(
                    type="text",
                    text=f"❌ Error creating folder: {str(e)}"
                )]
            )
    
    async def search_files(self, query: str) -> ToolResult:
        """Search for files in uploads folder"""
        try:
            results = []
            uploads_dir = "uploads"
            
            if os.path.exists(uploads_dir):
                for root, dirs, files in os.walk(uploads_dir):
                    for file in files:
                        if query.lower() in file.lower():
                            file_path = os.path.join(root, file)
                            file_size = os.path.getsize(file_path)
                            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            results.append({
                                'name': file,
                                'path': file_path,
                                'size': file_size,
                                'modified': file_time
                            })
            
            if results:
                result_text = f"🔍 **Search Results for '{query}'**\n\n"
                result_text += f"Found {len(results)} file(s):\n\n"
                for i, file in enumerate(results[:20], 1):
                    result_text += f"{i}. **{file['name']}**\n"
                    result_text += f"   📁 Size: {file['size'] / 1024:.2f} KB\n"
                    result_text += f"   🕒 Modified: {file['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                if len(results) > 20:
                    result_text += f"... and {len(results) - 20} more files"
                
                return ToolResult([TextContent(type="text", text=result_text)])
            else:
                return ToolResult(
                    [TextContent(
                        type="text",
                        text=f"🔍 No files found matching '{query}'\n\nTry:\n• search files .jpg\n• search files document"
                    )]
                )
        except Exception as e:
            return ToolResult(
                [TextContent(type="text", text=f"❌ Error searching files: {str(e)}")]
            )
    
    async def get_conversation_history(self, user_id: int, limit: int = 10) -> ToolResult:
        """Get recent conversation history for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                SELECT user_message, bot_response, timestamp, tool_used 
                FROM conversation 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id, limit))
            
            conversations = c.fetchall()
            conn.close()
            
            if conversations:
                history_text = f"📝 **Conversation History**\n\n"
                history_text += f"Showing last {len(conversations)} messages:\n\n"
                for i, conv in enumerate(reversed(conversations), 1):
                    history_text += f"**{i}. {conv[2]}**\n"
                    history_text += f"👤 **You:** {conv[0][:100]}\n"
                    if conv[3]:
                        history_text += f"🔧 **Tool:** {conv[3]}\n"
                    history_text += f"🤖 **MFASHA AI:** {conv[1][:100]}\n"
                    history_text += "-" * 40 + "\n\n"
                
                return ToolResult([TextContent(type="text", text=history_text)])
            else:
                return ToolResult(
                    [TextContent(
                        type="text",
                        text="📝 No conversation history found. Start chatting to build your history!"
                    )]
                )
        except Exception as e:
            return ToolResult(
                [TextContent(type="text", text=f"❌ Error fetching history: {str(e)}")]
            )
    
    async def get_user_info(self, username: str) -> ToolResult:
        """Get user information"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                SELECT id, username, email, created_at, theme_color, is_guest 
                FROM users 
                WHERE username = ?
            """, (username,))
            
            user = c.fetchone()
            conn.close()
            
            if user:
                info = f"👤 **User Information**\n\n"
                info += f"• **ID:** {user[0]}\n"
                info += f"• **Username:** {user[1]}\n"
                info += f"• **Email:** {user[2] or 'Not set'}\n"
                info += f"• **Joined:** {user[3]}\n"
                info += f"• **Theme:** {user[4]}\n"
                info += f"• **Type:** {'Guest' if user[5] else 'Registered'}\n"
                
                return ToolResult([TextContent(type="text", text=info)])
            else:
                return ToolResult(
                    [TextContent(type="text", text=f"❌ User '{username}' not found")]
                )
        except Exception as e:
            return ToolResult(
                [TextContent(type="text", text=f"❌ Error: {str(e)}")]
            )
    
    async def read_file(self, file_path: str, max_lines: int = 50) -> ToolResult:
        """Read content of a text file"""
        try:
            if not os.path.exists(file_path):
                return ToolResult(
                    [TextContent(type="text", text=f"❌ File not found: {file_path}")]
                )
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                total_lines = len(lines)
                content_lines = lines[:max_lines]
                content = ''.join(content_lines)
                
            result_text = f"📄 **File Content**\n\n"
            result_text += f"**File:** {os.path.basename(file_path)}\n"
            result_text += f"**Path:** {file_path}\n"
            result_text += f"**Total Lines:** {total_lines}\n"
            result_text += f"**Showing:** First {len(content_lines)} lines\n\n"
            result_text += "```\n"
            result_text += content
            result_text += "```\n\n"
            
            if total_lines > max_lines:
                result_text += f"\n*... and {total_lines - max_lines} more lines (use max_lines parameter to see more)*"
            
            return ToolResult([TextContent(type="text", text=result_text)])
        except Exception as e:
            return ToolResult(
                [TextContent(type="text", text=f"❌ Error reading file: {str(e)}")]
            )
    
    async def system_info(self) -> ToolResult:
        """Get system information"""
        try:
            info = f"💻 **System Information**\n\n"
            info += f"• **OS:** {platform.system()} {platform.release()}\n"
            info += f"• **Python:** {platform.python_version()}\n"
            info += f"• **Machine:** {platform.machine()}\n"
            info += f"• **Processor:** {platform.processor()}\n"
            
            # Get disk usage
            try:
                total, used, free = shutil.disk_usage("/")
                info += f"• **Disk:** {used // (2**30)} GB used / {total // (2**30)} GB total ({free // (2**30)} GB free)\n"
            except:
                pass
            
            # Get CPU info (Windows)
            if platform.system() == "Windows":
                try:
                    import psutil
                    info += f"• **CPU Cores:** {psutil.cpu_count()}\n"
                    info += f"• **Memory:** {psutil.virtual_memory().total // (2**30)} GB total\n"
                except ImportError:
                    info += f"*Install psutil for detailed system info: pip install psutil*\n"
            
            return ToolResult([TextContent(type="text", text=info)])
        except Exception as e:
            return ToolResult(
                [TextContent(type="text", text=f"❌ Error: {str(e)}")]
            )
    
    async def web_search(self, query: str) -> ToolResult:
        """Simulate web search (replace with actual search API)"""
        return ToolResult(
            [TextContent(
                type="text",
                text=f"🔍 **Web Search Results for '{query}'**\n\n"
                     f"1. **Example Result 1**\n"
                     f"   Information about {query} - This is a placeholder result\n\n"
                     f"2. **Example Result 2**\n"
                     f"   More details about {query} - Replace with actual search API\n\n"
                     f"3. **Example Result 3**\n"
                     f"   Additional information related to {query}\n\n"
                     f"*Note: To enable actual web search, integrate with a search API like Google Custom Search or DuckDuckGo*"
            )]
        )
    
    async def get_time(self) -> ToolResult:
        """Get current date and time"""
        now = datetime.now()
        return ToolResult(
            [TextContent(
                type="text",
                text=f"🕐 **Current Date & Time**\n\n"
                     f"• **Date:** {now.strftime('%Y-%m-%d')}\n"
                     f"• **Day:** {now.strftime('%A')}\n"
                     f"• **Time:** {now.strftime('%H:%M:%S')}\n"
                     f"• **Week:** Week {now.strftime('%W')} of {now.strftime('%Y')}\n"
                     f"• **Timestamp:** {int(now.timestamp())}"
            )]
        )
    
    async def get_random_joke(self) -> ToolResult:
        """Get a random joke"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything! 😄",
            "What do you call a fake noodle? An impasta! 🍝",
            "Why did the scarecrow win an award? Because he was outstanding in his field! 🌾",
            "What do you call a bear with no teeth? A gummy bear! 🐻",
            "Why don't eggs tell jokes? They'd crack each other up! 🥚",
            "What do you call a fish wearing a bowtie? Sofishticated! 🐟",
            "Why did the bicycle fall over? Because it was two-tired! 🚲",
            "What do you call a sleeping bull? A bulldozer! 🐂",
            "Why don't skeletons fight? They don't have the guts! 💀"
        ]
        joke = random.choice(jokes)
        return ToolResult(
            [TextContent(type="text", text=f"😂 **Joke Time!**\n\n{joke}")]
        )
    
    async def get_quote(self) -> ToolResult:
        """Get an inspirational quote"""
        quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
            ("Stay hungry, stay foolish.", "Steve Jobs"),
            ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
            ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
            ("The only limit to our realization of tomorrow is our doubts of today.", "Franklin D. Roosevelt"),
            ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
            ("Believe you can and you're halfway there.", "Theodore Roosevelt")
        ]
        quote, author = random.choice(quotes)
        return ToolResult(
            [TextContent(type="text", text=f"💭 **Inspirational Quote**\n\n\"{quote}\"\n\n— {author}")]
        )
    
    async def analyze_image(self, image_path: str) -> ToolResult:
        """Analyze image content"""
        try:
            if not os.path.exists(image_path):
                return ToolResult(
                    [TextContent(type="text", text=f"❌ Image not found: {image_path}")]
                )
            
            from PIL import Image
            img = Image.open(image_path)
            width, height = img.size
            file_size = os.path.getsize(image_path)
            file_ext = os.path.splitext(image_path)[1].lower()
            
            analysis = f"📸 **Image Analysis**\n\n"
            analysis += f"**File Information:**\n"
            analysis += f"• Filename: {os.path.basename(image_path)}\n"
            analysis += f"• Format: {file_ext.upper()}\n"
            analysis += f"• Size: {file_size / 1024:.2f} KB\n"
            analysis += f"• Dimensions: {width} x {height} pixels\n"
            analysis += f"• Mode: {img.mode}\n\n"
            
            # Aspect ratio analysis
            ratio = width / height
            if ratio > 1.5:
                orientation = "Landscape (wide)"
            elif ratio < 0.67:
                orientation = "Portrait (tall)"
            else:
                orientation = "Square or near-square"
            analysis += f"**Image Characteristics:**\n"
            analysis += f"• Orientation: {orientation}\n"
            
            if width > 2000 or height > 2000:
                analysis += f"• Resolution: High resolution\n"
            elif width > 1000 or height > 1000:
                analysis += f"• Resolution: Medium resolution\n"
            else:
                analysis += f"• Resolution: Standard resolution\n"
            
            return ToolResult([TextContent(type="text", text=analysis)])
        except Exception as e:
            return ToolResult(
                [TextContent(type="text", text=f"❌ Error analyzing image: {str(e)}")]
            )
    
    async def get_file_info(self, file_path: str) -> ToolResult:
        """Get information about a file"""
        try:
            if not os.path.exists(file_path):
                return ToolResult(
                    [TextContent(type="text", text=f"❌ File not found: {file_path}")]
                )
            
            stat = os.stat(file_path)
            file_size = stat.st_size
            created = datetime.fromtimestamp(stat.st_ctime)
            modified = datetime.fromtimestamp(stat.st_mtime)
            accessed = datetime.fromtimestamp(stat.st_atime)
            
            info = f"📄 **File Information**\n\n"
            info += f"**Name:** {os.path.basename(file_path)}\n"
            info += f"**Path:** {file_path}\n"
            info += f"**Size:** {file_size / 1024:.2f} KB ({file_size} bytes)\n"
            info += f"**Created:** {created.strftime('%Y-%m-%d %H:%M:%S')}\n"
            info += f"**Modified:** {modified.strftime('%Y-%m-%d %H:%M:%S')}\n"
            info += f"**Accessed:** {accessed.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            return ToolResult([TextContent(type="text", text=info)])
        except Exception as e:
            return ToolResult(
                [TextContent(type="text", text=f"❌ Error: {str(e)}")]
            )
    
    async def list_directory(self, directory_path: str = ".") -> ToolResult:
        """List contents of a directory"""
        try:
            if not os.path.exists(directory_path):
                return ToolResult(
                    [TextContent(type="text", text=f"❌ Directory not found: {directory_path}")]
                )
            
            items = os.listdir(directory_path)
            result_text = f"📁 **Directory Listing: {directory_path}**\n\n"
            result_text += f"Total items: {len(items)}\n\n"
            
            # Separate files and folders
            folders = []
            files = []
            for item in items:
                item_path = os.path.join(directory_path, item)
                if os.path.isdir(item_path):
                    folders.append(item)
                else:
                    files.append(item)
            
            if folders:
                result_text += "**Folders:**\n"
                for folder in sorted(folders)[:20]:
                    result_text += f"📁 {folder}\n"
                if len(folders) > 20:
                    result_text += f"... and {len(folders) - 20} more folders\n"
                result_text += "\n"
            
            if files:
                result_text += "**Files:**\n"
                for file in sorted(files)[:20]:
                    file_path = os.path.join(directory_path, file)
                    file_size = os.path.getsize(file_path)
                    result_text += f"📄 {file} ({file_size / 1024:.1f} KB)\n"
                if len(files) > 20:
                    result_text += f"... and {len(files) - 20} more files\n"
            
            return ToolResult([TextContent(type="text", text=result_text)])
        except Exception as e:
            return ToolResult(
                [TextContent(type="text", text=f"❌ Error: {str(e)}")]
            )
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Handle tool calls from the MCP client"""
        if tool_name in self.tools:
            tool_func = self.tools[tool_name]["function"]
            try:
                return await tool_func(**arguments)
            except Exception as e:
                return ToolResult(
                    [TextContent(
                        type="text",
                        text=f"❌ Error executing {tool_name}: {str(e)}"
                    )]
                )
        else:
            return ToolResult(
                [TextContent(
                    type="text",
                    text=f"❌ Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
                )]
            )
    
    def get_tools_list(self) -> List[Dict[str, Any]]:
        """Return list of available tools for the client"""
        return [
            {"name": name, "description": tool["description"], "parameters": tool["parameters"]}
            for name, tool in self.tools.items()
        ]

# Create global instance
mcp_server = MCPChatbotServer()