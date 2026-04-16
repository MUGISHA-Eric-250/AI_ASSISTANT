# app.py - Complete Working Version with Terminal
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
import sqlite3
import os
import requests
import time
import re
import io
import random
import platform
import traceback
import subprocess
import threading
import queue
import signal
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

print("=" * 60)
print("STARTING MFASHA AI Application")
print("=" * 60)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'doc', 'docx'}

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)

print("Folders created")

# Terminal sessions storage
terminal_sessions = {}
terminal_outputs = {}

class TerminalSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.process = None
        self.output_queue = queue.Queue()
        self.running = False
        self.current_dir = os.path.expanduser("~")
        
    def start(self):
        """Start a new terminal process"""
        try:
            if platform.system() == 'Windows':
                self.process = subprocess.Popen(
                    ['cmd.exe'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=self.current_dir,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                self.process = subprocess.Popen(
                    ['/bin/bash'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=self.current_dir
                )
            self.running = True
            # Start output reader thread
            self.output_thread = threading.Thread(target=self._read_output, daemon=True)
            self.output_thread.start()
            return True
        except Exception as e:
            return False
    
    def _read_output(self):
        """Read output from terminal process"""
        while self.running and self.process and self.process.poll() is None:
            try:
                output = self.process.stdout.readline()
                if output:
                    self.output_queue.put(output)
            except:
                break
    
    def execute_command(self, command):
        """Execute a command in the terminal"""
        if not self.process or self.process.poll() is not None:
            if not self.start():
                return "Failed to start terminal session"
        
        try:
            # Write command to process
            self.process.stdin.write(command + '\n')
            self.process.stdin.flush()
            
            # Wait a bit for output
            time.sleep(0.1)
            
            # Collect output
            outputs = []
            while not self.output_queue.empty():
                try:
                    outputs.append(self.output_queue.get_nowait())
                except queue.Empty:
                    break
            
            output_text = ''.join(outputs)
            
            # Update current directory
            if platform.system() == 'Windows':
                self.current_dir = self._get_windows_current_dir()
            else:
                self.current_dir = self._get_unix_current_dir()
            
            return output_text if output_text else f"Command executed: {command}\n(No output)"
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def _get_windows_current_dir(self):
        """Get current directory on Windows"""
        try:
            result = subprocess.run(['cd'], shell=True, capture_output=True, text=True, cwd=self.current_dir)
            return result.stdout.strip()
        except:
            return self.current_dir
    
    def _get_unix_current_dir(self):
        """Get current directory on Unix"""
        try:
            result = subprocess.run(['pwd'], capture_output=True, text=True, cwd=self.current_dir)
            return result.stdout.strip()
        except:
            return self.current_dir
    
    def stop(self):
        """Stop the terminal process"""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None

# Database initialization
def init_db():
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL,
                      email TEXT,
                      is_guest BOOLEAN DEFAULT 0,
                      theme_color TEXT DEFAULT '#667eea',
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS conversation
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER NOT NULL,
                      user_message TEXT,
                      bot_response TEXT,
                      image_id INTEGER,
                      file_id INTEGER,
                      tool_used TEXT,
                      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS files
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER NOT NULL,
                      filename TEXT,
                      filepath TEXT,
                      file_type TEXT,
                      uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS terminal_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER NOT NULL,
                      command TEXT,
                      output TEXT,
                      executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.commit()
        conn.close()
        print("Database initialized")
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_ollama_response(prompt):
    """Get response from Ollama"""
    try:
        # Check if Ollama is running
        try:
            tags_response = requests.get('http://localhost:11434/api/tags', timeout=3)
            if tags_response.status_code != 200:
                return get_fallback_response(prompt)
            
            available_models = tags_response.json().get('models', [])
            if not available_models:
                return "No AI models found. Please pull a model: ollama pull gemma2:2b"
            
            model_name = available_models[0].get('name')
            
        except requests.exceptions.ConnectionError:
            return get_ollama_not_running_message()
        
        # Get AI response
        response = requests.post('http://localhost:11434/api/generate',
                                json={
                                    'model': model_name,
                                    'prompt': prompt,
                                    'stream': False,
                                    'options': {'num_predict': 500}
                                },
                                timeout=60)
        
        if response.status_code == 200:
            ai_response = response.json().get('response', 'No response')
            return f"AI Response:\n\n{ai_response}"
        else:
            return get_fallback_response(prompt)
            
    except Exception as e:
        return get_fallback_response(prompt)

def get_ollama_not_running_message():
    return """Ollama is not running!

Your installed models:
- gemma2:2b
- kimi-k2.5:cloud

To fix this:
1. Open a NEW Command Prompt
2. Run: ollama serve
3. Keep that window open
4. Refresh this page

In the meantime, try these commands:
- help - Show all commands
- calculate 25 * 4 - Math calculator
- weather London - Weather info
- time - Current time
- joke - Tell a joke
- create file test.txt - Create file on desktop
- terminal - Open terminal for system commands"""

def get_fallback_response(prompt):
    """Fallback response when Ollama is not available"""
    prompt_lower = prompt.lower()
    
    if 'help' in prompt_lower:
        return get_help_text()
    elif 'html' in prompt_lower:
        return """HTML stands for HyperText Markup Language.

HTML is the standard markup language for creating web pages. It describes the structure of a web page using elements like:
- <h1> for headings
- <p> for paragraphs
- <a> for links
- <div> for divisions
- <img> for images

For more detailed AI responses, start Ollama with: ollama serve"""
    elif 'python' in prompt_lower:
        return """Python is a high-level programming language known for its simplicity and readability.

Key features:
- Easy to learn syntax
- Large standard library
- Extensive third-party packages
- Used for web development, data science, and AI

To get AI-powered answers, start Ollama with: ollama serve"""
    elif 'calculate' in prompt_lower or 'calc' in prompt_lower:
        match = re.search(r'(\d+[\+\-\*/]\d+)', prompt)
        if match:
            try:
                result = eval(match.group(1))
                return f"Calculation: {match.group(1)} = {result}"
            except:
                pass
        return "To use calculator, type: calculate 25 * 4"
    elif 'weather' in prompt_lower:
        return "To get weather, type: weather London"
    elif 'time' in prompt_lower:
        now = datetime.now()
        return f"Current Time: {now.strftime('%H:%M:%S')}\nDate: {now.strftime('%Y-%m-%d')}"
    elif 'joke' in prompt_lower:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!"
        ]
        return random.choice(jokes)
    elif 'quote' in prompt_lower:
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Stay hungry, stay foolish. - Steve Jobs",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt"
        ]
        return random.choice(quotes)
    elif 'terminal' in prompt_lower or 'cmd' in prompt_lower or 'command' in prompt_lower:
        return """Terminal Feature Available!

To open the terminal, click the Terminal button in the chat interface.
Or type any system command like:
- ls (or dir on Windows) - List files
- cd folder - Change directory
- mkdir folder - Create folder
- python script.py - Run Python script

The terminal gives you full command-line access!"""
    elif 'create file' in prompt_lower:
        return "To create a file, type: create file filename.txt"
    elif 'create folder' in prompt_lower:
        return "To create a folder, type: create folder foldername"
    else:
        return f"""You asked: "{prompt}"

To get AI responses, start Ollama:
1. Open a new terminal
2. Run: ollama serve
3. Keep it running
4. Refresh this page

Try these commands:
- help - Show all commands
- calculate 25 * 4 - Math calculator
- weather London - Weather info
- time - Current time
- joke - Tell a joke
- terminal - Open terminal for system commands"""

def get_help_text():
    return """MFASHA AI - Available Commands

Calculator:
- calculate 25 * 4 - Calculate expression
- calc (10+5)*2 - Alternative syntax

Weather:
- weather London - Get weather for any city

File Operations:
- create file test.txt - Create file on desktop
- create folder MyProject - Create folder on desktop
- search files .jpg - Search uploaded files

Terminal:
- terminal - Open system terminal
- Any system command (ls, dir, cd, mkdir, etc.)

Utilities:
- time - Show current time
- joke - Get a random joke
- quote - Inspirational quote
- system info - System information
- history - View chat history

AI Chat:
- Just type any question naturally!
- Example: "What is HTML?"
- Example: "Explain machine learning"

To enable AI responses, start Ollama in another terminal: ollama serve"""

class MCPTools:
    def __init__(self, user_id=None):
        self.user_id = user_id
    
    def process_message(self, message):
        message_lower = message.lower().strip()
        
        if message_lower in ['help', 'commands', '?']:
            return get_help_text(), 'help'
        
        if re.match(r'^(calc|calculate|math)\s+', message_lower):
            expression = re.sub(r'^(calc|calculate|math)\s+', '', message)
            return self.calculator(expression), 'calculator'
        
        elif re.match(r'^weather\s+', message_lower):
            city = re.sub(r'^weather\s+', '', message)
            return self.get_weather(city), 'weather'
        
        elif message_lower in ['time', 'current time']:
            return self.get_time(), 'time'
        
        elif message_lower in ['joke', 'tell me a joke']:
            return self.get_joke(), 'joke'
        
        elif message_lower in ['quote', 'inspirational quote']:
            return self.get_quote(), 'quote'
        
        elif re.match(r'^create\s+file\s+', message_lower):
            filename = re.sub(r'^create\s+file\s+', '', message).strip()
            return self.create_file(filename), 'create_file'
        
        elif re.match(r'^create\s+folder\s+', message_lower):
            folder_name = re.sub(r'^create\s+folder\s+', '', message).strip()
            return self.create_folder(folder_name), 'create_folder'
        
        elif message_lower in ['system info', 'system']:
            return self.system_info(), 'system_info'
        
        elif re.match(r'^search\s+files?\s+', message_lower):
            query = re.sub(r'^search\s+files?\s+', '', message).strip()
            return self.search_files(query), 'search_files'
        
        elif 'history' in message_lower:
            limit = 10
            match = re.search(r'last\s+(\d+)', message_lower)
            if match:
                limit = int(match.group(1))
            return self.get_history(limit), 'history'
        
        elif message_lower in ['terminal', 'cmd', 'command line', 'open terminal']:
            return self.open_terminal(), 'terminal'
        
        return None, None
    
    def calculator(self, expression):
        try:
            allowed_names = {'abs': abs, 'round': round, 'min': min, 'max': max}
            safe_expr = ''.join(c for c in expression if c.isdigit() or c in '+-*/(). %')
            result = eval(safe_expr, {"__builtins__": {}}, allowed_names)
            return f"Result: {expression} = {result}"
        except:
            return "Invalid expression. Try: calculate 25 * 4"
    
    def get_weather(self, city):
        return f"Weather in {city}:\nTemperature: 22C\nConditions: Partly cloudy"
    
    def get_time(self):
        now = datetime.now()
        return f"Current Time: {now.strftime('%H:%M:%S')}\nDate: {now.strftime('%Y-%m-%d')}"
    
    def get_joke(self):
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!"
        ]
        return random.choice(jokes)
    
    def get_quote(self):
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Stay hungry, stay foolish. - Steve Jobs",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt"
        ]
        return random.choice(quotes)
    
    def create_file(self, filename):
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filepath = os.path.join(desktop, filename)
            
            if os.path.exists(filepath):
                return f"File '{filename}' already exists on desktop"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Created by MFASHA AI on {datetime.now()}")
            
            return f"File created: {filename} at {filepath}"
        except Exception as e:
            return f"Error creating file: {str(e)}"
    
    def create_folder(self, folder_name):
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            folderpath = os.path.join(desktop, folder_name)
            
            if os.path.exists(folderpath):
                return f"Folder '{folder_name}' already exists on desktop"
            
            os.makedirs(folderpath, exist_ok=True)
            return f"Folder created: {folder_name} at {folderpath}"
        except Exception as e:
            return f"Error creating folder: {str(e)}"
    
    def system_info(self):
        return f"System Information:\nOS: {platform.system()} {platform.release()}\nPython: {platform.python_version()}"
    
    def search_files(self, query):
        try:
            results = []
            if os.path.exists("uploads"):
                for root, dirs, files in os.walk("uploads"):
                    for file in files:
                        if query.lower() in file.lower():
                            results.append(f"- {file}")
            
            if results:
                return f"Found {len(results)} file(s):\n" + "\n".join(results[:10])
            return f"No files found matching '{query}'"
        except:
            return "Error searching files"
    
    def get_history(self, limit=10):
        if not self.user_id:
            return "Please login to view chat history"
        
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT user_message, bot_response, timestamp FROM conversation WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                     (self.user_id, limit))
            conversations = c.fetchall()
            conn.close()
            
            if conversations:
                history = f"Last {len(conversations)} messages:\n\n"
                for i, (user, bot, ts) in enumerate(reversed(conversations), 1):
                    history += f"{i}. [{ts[:16]}] You: {user[:50]}\n   AI: {bot[:50]}\n\n"
                return history
            return "No conversation history found"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def open_terminal(self):
        return """Terminal Ready!

You can now execute system commands through the terminal interface.
Click the Terminal button or use the terminal panel to run commands.

Available commands:
- For Windows: dir, cd, mkdir, del, copy, move
- For Linux/Mac: ls, cd, mkdir, rm, cp, mv
- Run Python scripts: python script.py
- Install packages: pip install package_name
- Check system info: systeminfo (Windows) or uname -a (Linux/Mac)

Type any command and press Enter to execute!"""

# Terminal Routes
@app.route('/api/terminal/start')
def terminal_start():
    """Start a terminal session"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    session_id = f"{session['user_id']}_{int(time.time())}"
    terminal = TerminalSession(session_id)
    
    if terminal.start():
        terminal_sessions[session_id] = terminal
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Terminal session started',
            'current_dir': terminal.current_dir
        })
    else:
        return jsonify({'error': 'Failed to start terminal'}), 500

@app.route('/api/terminal/execute', methods=['POST'])
def terminal_execute():
    """Execute command in terminal"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    session_id = data.get('session_id')
    command = data.get('command', '')
    
    if not session_id or session_id not in terminal_sessions:
        return jsonify({'error': 'Terminal session not found'}), 404
    
    terminal = terminal_sessions[session_id]
    
    try:
        # Save command to database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO terminal_history (user_id, command) VALUES (?, ?)",
                 (session['user_id'], command))
        conn.commit()
        conn.close()
    except:
        pass
    
    output = terminal.execute_command(command)
    
    return jsonify({
        'success': True,
        'output': output,
        'current_dir': terminal.current_dir
    })

@app.route('/api/terminal/stop', methods=['POST'])
def terminal_stop():
    """Stop terminal session"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    session_id = data.get('session_id')
    
    if session_id and session_id in terminal_sessions:
        terminal_sessions[session_id].stop()
        del terminal_sessions[session_id]
        return jsonify({'success': True, 'message': 'Terminal session stopped'})
    
    return jsonify({'error': 'Session not found'}), 404

@app.route('/api/terminal/history')
def terminal_history():
    """Get terminal command history"""
    if 'user_id' not in session:
        return jsonify([]), 401
    
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT command, executed_at FROM terminal_history WHERE user_id = ? ORDER BY executed_at DESC LIMIT 50",
                 (session['user_id'],))
        history = [{'command': row[0], 'executed_at': row[1]} for row in c.fetchall()]
        conn.close()
        return jsonify(history)
    except:
        return jsonify([])

# Routes
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error loading template: {e}", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        return jsonify({'error': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            hashed = generate_password_hash(password)
            c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                     (username, hashed, email))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Registration successful'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Username already exists'}), 400
    return render_template('register.html')

@app.route('/guest_login')
def guest_login():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    guest_name = f"guest_{int(time.time())}"
    c.execute("INSERT INTO users (username, password, is_guest) VALUES (?, ?, 1)",
             (guest_name, generate_password_hash('guest')))
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    session['user_id'] = user_id
    session['username'] = guest_name
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'response': 'Please enter a message.', 'tool_used': None})
        
        mcp = MCPTools(user_id=session['user_id'])
        response, tool_used = mcp.process_message(user_message)
        
        if not response:
            tool_used = 'ai'
            response = get_ollama_response(user_message)
        
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO conversation (user_id, user_message, bot_response, tool_used) VALUES (?, ?, ?, ?)",
                     (session['user_id'], user_message, response, tool_used))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving: {e}")
        
        return jsonify({'response': response, 'tool_used': tool_used})
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return jsonify({'response': f"Error: {str(e)}", 'tool_used': 'error'}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            unique_filename = f"{int(time.time())}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            file_type = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
            c.execute("INSERT INTO files (user_id, filename, filepath, file_type) VALUES (?, ?, ?, ?)",
                     (session['user_id'], filename, filepath, file_type))
            file_id = c.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'message': f'File uploaded: {filename}'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/get_files')
def get_files():
    if 'user_id' not in session:
        return jsonify([])
    
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, filename, file_type, uploaded_at FROM files WHERE user_id = ? ORDER BY uploaded_at DESC",
                 (session['user_id'],))
        files = [{'id': r[0], 'filename': r[1], 'file_type': r[2], 'uploaded_at': r[3]} for r in c.fetchall()]
        conn.close()
        return jsonify(files)
    except Exception as e:
        return jsonify([])

@app.route('/export_chat')
def export_chat():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT user_message, bot_response, timestamp FROM conversation WHERE user_id = ? ORDER BY timestamp",
                 (session['user_id'],))
        convos = c.fetchall()
        conn.close()
        
        export = f"MFASHA AI Chat Export\nUser: {session['username']}\nDate: {datetime.now()}\n\n"
        for user, bot, ts in convos:
            export += f"[{ts}] You: {user}\nAI: {bot}\n{'-'*40}\n"
        
        return send_file(
            io.BytesIO(export.encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_ollama')
def test_ollama():
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            model_names = [m.get('name', 'unknown') for m in models]
            return jsonify({'status': 'connected', 'models': model_names})
        return jsonify({'status': 'error', 'message': 'Ollama not responding'})
    except:
        return jsonify({'status': 'error', 'message': 'Cannot connect to Ollama'})

@app.route('/logout')
def logout():
    # Clean up terminal sessions
    for session_id in list(terminal_sessions.keys()):
        if str(session['user_id']) in session_id:
            terminal_sessions[session_id].stop()
            del terminal_sessions[session_id]
    
    session.clear()
    return redirect(url_for('index'))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)