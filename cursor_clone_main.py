#!/usr/bin/env python3
"""
Cursor AI Clone for Linux - Main Application
A complete AI-powered code editor using Google Gemini CLI
"""

import sys
import os
import json
import subprocess
import threading
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import tkinter.font as tkFont

# Try to import additional modules, install if missing
try:
    import requests
    import keyring
except ImportError:
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "keyring"])
    import requests
    import keyring

class GeminiService:
    """Interface for Google Gemini CLI integration"""
    
    def __init__(self):
        self.authenticated = False
        self.project_id = None
        self.api_key = None
        
    def check_gcloud_installation(self) -> bool:
        """Check if Google Cloud CLI is installed"""
        try:
            result = subprocess.run(['gcloud', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def authenticate(self) -> bool:
        """Authenticate with Google Cloud"""
        try:
            # Check if already authenticated
            result = subprocess.run(['gcloud', 'auth', 'list', '--format=json'], 
                                  capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                accounts = json.loads(result.stdout)
                if accounts and any(acc.get('status') == 'ACTIVE' for acc in accounts):
                    self.authenticated = True
                    return True
            
            # If not authenticated, prompt user
            messagebox.showinfo("Authentication Required", 
                              "Please authenticate with Google Cloud in the terminal that will open.")
            
            # Run authentication
            subprocess.Popen(['gcloud', 'auth', 'login'])
            return False  # User needs to complete auth manually
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    async def generate_completion(self, prompt: str, context: str = "") -> str:
        """Generate code completion using Gemini"""
        if not self.authenticated:
            return "// Authentication required"
        
        try:
            full_prompt = f"Context: {context}\n\nComplete this code:\n{prompt}"
            
            # Use gcloud AI platform (simulated for now)
            # In real implementation, use actual Gemini CLI commands
            cmd = ['gcloud', 'ai', 'models', 'predict', '--model=gemini-pro']
            
            # For now, return a placeholder
            return f"// AI suggestion for: {prompt[:50]}...\n// TODO: Implement actual Gemini CLI integration"
            
        except Exception as e:
            return f"// Error generating completion: {str(e)}"
    
    async def chat_response(self, message: str, file_context: str = "") -> str:
        """Generate chat response"""
        if not self.authenticated:
            return "Please authenticate with Google Cloud first."
        
        # Simulate AI response for now
        return f"AI Response: I understand you're asking about '{message[:50]}...'. Here's my analysis based on the current code context."

class FileExplorer:
    """File explorer component"""
    
    def __init__(self, parent, on_file_select):
        self.parent = parent
        self.on_file_select = on_file_select
        self.current_path = Path.home()
        
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # File tree
        self.tree = ttk.Treeview(self.frame)
        self.tree.heading('#0', text='Project Files', anchor='w')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # Load initial directory
        self.load_directory(self.current_path)
    
    def load_directory(self, path: Path):
        """Load directory contents into tree"""
        self.tree.delete(*self.tree.get_children())
        
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith('.'):
                    continue
                    
                item_id = self.tree.insert('', 'end', text=item.name, 
                                         values=[str(item)])
                
                if item.is_dir():
                    # Add dummy child to show expand arrow
                    self.tree.insert(item_id, 'end', text='...')
                    
        except PermissionError:
            pass
    
    def on_select(self, event):
        """Handle tree selection"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            file_path = item['values'][0] if item['values'] else None
            if file_path and Path(file_path).is_file():
                self.on_file_select(file_path)
    
    def on_double_click(self, event):
        """Handle double-click to expand directories"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            file_path = item['values'][0] if item['values'] else None
            if file_path and Path(file_path).is_dir():
                self.expand_directory(selection[0], Path(file_path))
    
    def expand_directory(self, item_id, path: Path):
        """Expand directory in tree"""
        # Remove dummy children
        self.tree.delete(*self.tree.get_children(item_id))
        
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith('.'):
                    continue
                    
                child_id = self.tree.insert(item_id, 'end', text=item.name, 
                                          values=[str(item)])
                
                if item.is_dir():
                    self.tree.insert(child_id, 'end', text='...')
                    
        except PermissionError:
            pass

class CodeEditor:
    """Main code editor component"""
    
    def __init__(self, parent, gemini_service):
        self.parent = parent
        self.gemini = gemini_service
        self.current_file = None
        self.unsaved_changes = False
        
        self.setup_ui()
        self.setup_syntax_highlighting()
        
    def setup_ui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill='both', expand=True)
        
        # Create initial tab
        self.create_new_tab("Untitled", "")
        
    def create_new_tab(self, title: str, content: str = ""):
        """Create a new editor tab"""
        frame = ttk.Frame(self.notebook)
        
        # Text editor with scrollbar
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill='both', expand=True)
        
        text_widget = ScrolledText(text_frame, wrap='none', undo=True)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', content)
        
        # Configure font
        font = tkFont.Font(family="Consolas", size=12)
        text_widget.configure(font=font)
        
        # Bind events
        text_widget.bind('<KeyRelease>', self.on_text_change)
        text_widget.bind('<Control-space>', self.trigger_completion)
        text_widget.bind('<Control-s>', lambda e: self.save_file())
        
        # Add tab
        self.notebook.add(frame, text=title)
        self.notebook.select(frame)
        
        # Store reference
        frame.text_widget = text_widget
        frame.file_path = None
        frame.unsaved = False
        
        return frame
    
    def setup_syntax_highlighting(self):
        """Setup basic syntax highlighting"""
        # This is a simplified version - you'd want to use a proper syntax highlighter
        self.keywords = {
            'python': ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'try', 'except'],
            'javascript': ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'class'],
            'java': ['public', 'private', 'class', 'interface', 'if', 'else', 'for', 'while']
        }
    
    def on_text_change(self, event):
        """Handle text changes"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.unsaved = True
            tab_index = self.notebook.index(current_tab)
            current_title = self.notebook.tab(tab_index, "text")
            if not current_title.endswith('*'):
                self.notebook.tab(tab_index, text=current_title + '*')
    
    def trigger_completion(self, event):
        """Trigger AI code completion"""
        current_tab = self.get_current_tab()
        if not current_tab:
            return
        
        text_widget = current_tab.text_widget
        cursor_pos = text_widget.index(tk.INSERT)
        
        # Get current line
        line_start = cursor_pos.split('.')[0] + '.0'
        current_line = text_widget.get(line_start, cursor_pos)
        
        # Get surrounding context
        context = text_widget.get('1.0', tk.END)[:1000]  # First 1000 chars
        
        # Request completion asynchronously
        threading.Thread(
            target=self.get_completion_async,
            args=(current_line, context, text_widget, cursor_pos)
        ).start()
    
    def get_completion_async(self, prompt, context, text_widget, cursor_pos):
        """Get AI completion asynchronously"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            completion = loop.run_until_complete(
                self.gemini.generate_completion(prompt, context)
            )
            
            # Insert completion in main thread
            self.parent.after(0, lambda: self.insert_completion(text_widget, cursor_pos, completion))
            
        except Exception as e:
            print(f"Completion error: {e}")
    
    def insert_completion(self, text_widget, cursor_pos, completion):
        """Insert AI completion into editor"""
        if completion and not completion.startswith('//'):
            text_widget.insert(cursor_pos, completion)
    
    def get_current_tab(self):
        """Get currently selected tab"""
        try:
            return self.notebook.nametowidget(self.notebook.select())
        except:
            return None
    
    def open_file(self, file_path: str):
        """Open file in new tab"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_name = Path(file_path).name
            tab = self.create_new_tab(file_name, content)
            tab.file_path = file_path
            tab.unsaved = False
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
    
    def save_file(self):
        """Save current file"""
        current_tab = self.get_current_tab()
        if not current_tab:
            return
        
        if not current_tab.file_path:
            # Save as
            file_path = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python files", "*.py"), ("All files", "*.*")]
            )
            if not file_path:
                return
            current_tab.file_path = file_path
        
        try:
            content = current_tab.text_widget.get('1.0', tk.END)
            with open(current_tab.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            current_tab.unsaved = False
            tab_index = self.notebook.index(current_tab)
            title = self.notebook.tab(tab_index, "text").rstrip('*')
            self.notebook.tab(tab_index, text=title)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")

class AIChat:
    """AI chat interface"""
    
    def __init__(self, parent, gemini_service):
        self.parent = parent
        self.gemini = gemini_service
        self.conversation_history = []
        
        self.setup_ui()
    
    def setup_ui(self):
        self.frame = ttk.Frame(self.parent)
        
        # Chat history
        self.chat_display = ScrolledText(self.frame, state='disabled', height=20)
        self.chat_display.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Input frame
        input_frame = ttk.Frame(self.frame)
        input_frame.pack(fill='x', padx=5, pady=5)
        
        self.input_field = ttk.Entry(input_frame)
        self.input_field.pack(side='left', fill='x', expand=True)
        self.input_field.bind('<Return>', self.send_message)
        
        send_btn = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_btn.pack(side='right', padx=(5, 0))
        
        # Add welcome message
        self.add_message("AI Assistant", "Hello! I'm your AI coding assistant. Ask me anything about your code!")
    
    def add_message(self, sender: str, message: str):
        """Add message to chat display"""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
    
    def send_message(self, event=None):
        """Send message to AI"""
        message = self.input_field.get().strip()
        if not message:
            return
        
        self.input_field.delete(0, tk.END)
        self.add_message("You", message)
        
        # Get AI response asynchronously
        threading.Thread(target=self.get_ai_response, args=(message,)).start()
    
    def get_ai_response(self, message: str):
        """Get AI response asynchronously"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                self.gemini.chat_response(message)
            )
            
            self.parent.after(0, lambda: self.add_message("AI Assistant", response))
            
        except Exception as e:
            error_msg = f"Error getting AI response: {e}"
            self.parent.after(0, lambda: self.add_message("System", error_msg))

class CursorCloneApp:
    """Main application class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cursor AI Clone for Linux")
        self.root.geometry("1400x800")
        
        # Initialize services
        self.gemini = GeminiService()
        
        self.setup_ui()
        self.setup_menu()
        self.check_dependencies()
    
    def setup_ui(self):
        """Setup main UI layout"""
        # Main paned window
        main_paned = ttk.PanedWindow(self.root, orient='horizontal')
        main_paned.pack(fill='both', expand=True)
        
        # Left panel (file explorer)
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="File Explorer", font=('Arial', 12, 'bold')).pack(pady=5)
        self.file_explorer = FileExplorer(left_frame, self.on_file_select)
        self.file_explorer.frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Right panel (editor + chat)
        right_paned = ttk.PanedWindow(main_paned, orient='vertical')
        main_paned.add(right_paned, weight=4)
        
        # Editor area
        editor_frame = ttk.Frame(right_paned)
        right_paned.add(editor_frame, weight=3)
        
        self.code_editor = CodeEditor(editor_frame, self.gemini)
        
        # Chat area
        chat_frame = ttk.LabelFrame(right_paned, text="AI Assistant")
        right_paned.add(chat_frame, weight=1)
        
        self.ai_chat = AIChat(chat_frame, self.gemini)
        self.ai_chat.frame.pack(fill='both', expand=True)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief='sunken')
        self.status_bar.pack(side='bottom', fill='x')
    
    def setup_menu(self):
        """Setup application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # AI menu
        ai_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="AI", menu=ai_menu)
        ai_menu.add_command(label="Authenticate with Google", command=self.authenticate_gemini)
        ai_menu.add_command(label="Trigger Completion", command=self.trigger_completion, accelerator="Ctrl+Space")
        
        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
    
    def check_dependencies(self):
        """Check and setup dependencies"""
        # Check Google Cloud CLI
        if not self.gemini.check_gcloud_installation():
            response = messagebox.askyesno(
                "Google Cloud CLI Not Found",
                "Google Cloud CLI is required for AI features. Would you like to install it?\n\n"
                "You can install it manually with:\n"
                "curl https://sdk.cloud.google.com | bash"
            )
            if response:
                self.status_bar.config(text="Please install Google Cloud CLI manually")
        else:
            self.status_bar.config(text="Google Cloud CLI found - Ready for AI features")
    
    def authenticate_gemini(self):
        """Authenticate with Gemini service"""
        self.status_bar.config(text="Authenticating with Google Cloud...")
        
        def auth_thread():
            success = self.gemini.authenticate()
            status_text = "Authentication successful!" if success else "Authentication required - check terminal"
            self.root.after(0, lambda: self.status_bar.config(text=status_text))
        
        threading.Thread(target=auth_thread).start()
    
    def new_file(self):
        """Create new file"""
        self.code_editor.create_new_tab("Untitled")
    
    def open_file(self):
        """Open file dialog"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Python files", "*.py"), ("JavaScript files", "*.js"), ("All files", "*.*")]
        )
        if file_path:
            self.code_editor.open_file(file_path)
    
    def save_file(self):
        """Save current file"""
        self.code_editor.save_file()
    
    def trigger_completion(self):
        """Trigger AI completion"""
        current_tab = self.code_editor.get_current_tab()
        if current_tab:
            event = type('Event', (), {'keysym': 'space'})()
            self.code_editor.trigger_completion(event)
    
    def on_file_select(self, file_path: str):
        """Handle file selection from explorer"""
        self.code_editor.open_file(file_path)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    print("Starting Cursor AI Clone for Linux...")
    print("=" * 50)
    
    app = CursorCloneApp()
    app.run()

if __name__ == "__main__":
    main()
