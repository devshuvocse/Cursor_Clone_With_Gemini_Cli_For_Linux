#!/usr/bin/env python3
"""
Configuration and Utilities Module for Cursor AI Clone
Handles configuration management, logging, and utility functions
"""

import os
import json
import logging
import logging.config
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import subprocess
import sys

@dataclass
class GoogleCloudConfig:
    """Google Cloud configuration"""
    project_id: str = ""
    region: str = "us-central1"
    model_name: str = "gemini-pro"
    api_key: str = ""
    credentials_path: str = ""

@dataclass
class EditorConfig:
    """Editor configuration"""
    theme: str = "dark"
    font_family: str = "Consolas"
    font_size: int = 12
    tab_size: int = 4
    auto_save: bool = True
    auto_save_delay: int = 5000  # milliseconds
    show_line_numbers: bool = True
    word_wrap: bool = False
    syntax_highlighting: bool = True

@dataclass
class AIConfig:
    """AI configuration"""
    max_context_length: int = 2048
    completion_delay_ms: int = 500
    enable_streaming: bool = True
    temperature: float = 0.7
    max_tokens: int = 1024
    auto_complete: bool = True
    chat_history_limit: int = 50

@dataclass
class AppConfig:
    """Main application configuration"""
    google_cloud: GoogleCloudConfig
    editor: EditorConfig
    ai: AIConfig
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'google_cloud': asdict(self.google_cloud),
            'editor': asdict(self.editor),
            'ai': asdict(self.ai)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create from dictionary"""
        return cls(
            google_cloud=GoogleCloudConfig(**data.get('google_cloud', {})),
            editor=EditorConfig(**data.get('editor', {})),
            ai=AIConfig(**data.get('ai', {}))
        )

class ConfigManager:
    """Configuration management class"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / '.cursor-ai-clone'
        self.config_file = self.config_dir / 'config.json'
        self.config_dir.mkdir(exist_ok=True)
        
        self._config: Optional[AppConfig] = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                self._config = AppConfig.from_dict(data)
            except (json.JSONDecodeError, Exception) as e:
                logging.warning(f"Failed to load config: {e}. Using defaults.")
                self._config = AppConfig(
                    GoogleCloudConfig(),
                    EditorConfig(),
                    AIConfig()
                )
        else:
            self._config = AppConfig(
                GoogleCloudConfig(),
                EditorConfig(),
                AIConfig()
            )
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config.to_dict(), f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
    
    @property
    def config(self) -> AppConfig:
        """Get current configuration"""
        return self._config
    
    def update_config(self, **kwargs):
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                if isinstance(value, dict):
                    # Update nested config
                    nested_config = getattr(self._config, key)
                    for nested_key, nested_value in value.items():
                        if hasattr(nested_config, nested_key):
                            setattr(nested_config, nested_key, nested_value)
                else:
                    setattr(self._config, key, value)
        self.save_config()

class Logger:
    """Logging utility class"""
    
    def __init__(self, name: str = "cursor-ai-clone", log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / '.cursor-ai-clone' / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.setup_logging(name)
    
    def setup_logging(self, name: str):
        """Setup logging configuration"""
        log_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'simple': {
                    'format': '%(levelname)s: %(message)s'
                }
            },
            'handlers': {
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'detailed',
                    'filename': str(self.log_dir / f'{name}.log'),
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                },
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'simple',
                    'stream': sys.stdout
                }
            },
            'loggers': {
                name: {
                    'level': 'DEBUG',
                    'handlers': ['file', 'console'],
                    'propagate': False
                }
            }
        }
        
        logging.config.dictConfig(log_config)
        self.logger = logging.getLogger(name)
    
    def get_logger(self) -> logging.Logger:
        """Get logger instance"""
        return self.logger

class SystemUtils:
    """System utility functions"""
    
    @staticmethod
    def check_command(command: str) -> bool:
        """Check if command exists in system PATH"""
        try:
            subprocess.run([command, '--version'], 
                         capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Get system information"""
        info = {
            'os': os.name,
            'platform': sys.platform,
            'python_version': sys.version,
            'architecture': os.uname().machine if hasattr(os, 'uname') else 'unknown'
        }
        
        # Check for specific Linux distribution
        if sys.platform.startswith('linux'):
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            info['distribution'] = line.split('=')[1].strip().strip('"')
                            break
            except FileNotFoundError:
                info['distribution'] = 'Linux (unknown distribution)'
        
        return info
    
    @staticmethod
    def check_dependencies() -> Dict[str, bool]:
        """Check system dependencies"""
        dependencies = {
            'python3': SystemUtils.check_command('python3'),
            'pip': SystemUtils.check_command('pip') or SystemUtils.check_command('pip3'),
            'git': SystemUtils.check_command('git'),
            'gcloud': SystemUtils.check_command('gcloud'),
        }
        
        # Check Python modules
        try:
            import tkinter
            dependencies['tkinter'] = True
        except ImportError:
            dependencies['tkinter'] = False
        
        try:
            import requests
            dependencies['requests'] = True
        except ImportError:
            dependencies['requests'] = False
        
        return dependencies
    
    @staticmethod
    def install_missing_deps():
        """Install missing Python dependencies"""
        missing_deps = []
        
        try:
            import requests
        except ImportError:
            missing_deps.append('requests')
        
        try:
            import keyring
        except ImportError:
            missing_deps.append('keyring')
        
        if missing_deps:
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', '--user'
                ] + missing_deps)
                return True
            except subprocess.CalledProcessError:
                return False
        
        return True

class FileManager:
    """File management utilities"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = Logger().get_logger()
    
    def get_recent_files(self, limit: int = 10) -> List[str]:
        """Get list of recently opened files"""
        recent_file = self.config.config_dir / 'recent_files.json'
        
        if recent_file.exists():
            try:
                with open(recent_file, 'r') as f:
                    recent_files = json.load(f)
                return recent_files[:limit]
            except (json.JSONDecodeError, Exception):
                return []
        
        return []
    
    def add_recent_file(self, file_path: str):
        """Add file to recent files list"""
        recent_files = self.get_recent_files()
        
        # Remove if already exists
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning
        recent_files.insert(0, file_path)
        
        # Keep only last 20 files
        recent_files = recent_files[:20]
        
        # Save to file
        recent_file = self.config.config_dir / 'recent_files.json'
        try:
            with open(recent_file, 'w') as f:
                json.dump(recent_files, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save recent files: {e}")
    
    def get_project_files(self, project_path: Path, 
                         extensions: Optional[List[str]] = None) -> List[Path]:
        """Get all files in project matching extensions"""
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', 
                         '.css', '.html', '.json', '.xml', '.yaml', '.yml',
                         '.md', '.txt', '.sh', '.bat']
        
        files = []
        try:
            for ext in extensions:
                files.extend(project_path.rglob(f'*{ext}'))
        except Exception as e:
            self.logger.error(f"Error scanning project files: {e}")
        
        return sorted(files)
    
    def backup_file(self, file_path: Path) -> bool:
        """Create backup of file"""
        try:
            backup_dir = file_path.parent / '.backups'
            backup_dir.mkdir(exist_ok=True)
            
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup file {file_path}: {e}")
            return False

class ThemeManager:
    """Theme and styling management"""
    
    def __init__(self):
        self.themes = {
            'dark': {
                'bg': '#1e1e1e',
                'fg': '#d4d4d4',
                'select_bg': '#264f78',
                'select_fg': '#ffffff',
                'cursor': '#ffffff',
                'syntax': {
                    'keyword': '#569cd6',
                    'string': '#ce9178',
                    'comment': '#6a9955',
                    'number': '#b5cea8',
                    'function': '#dcdcaa'
                }
            },
            'light': {
                'bg': '#ffffff',
                'fg': '#000000',
                'select_bg': '#0078d4',
                'select_fg': '#ffffff',
                'cursor': '#000000',
                'syntax': {
                    'keyword': '#0000ff',
                    'string': '#a31515',
                    'comment': '#008000',
                    'number': '#098658',
                    'function': '#795e26'
                }
            }
        }
    
    def get_theme(self, theme_name: str) -> Dict[str, Any]:
        """Get theme configuration"""
        return self.themes.get(theme_name, self.themes['dark'])
    
    def apply_theme(self, widget, theme_name: str):
        """Apply theme to tkinter widget"""
        theme = self.get_theme(theme_name)
        
        try:
            widget.configure(
                bg=theme['bg'],
                fg=theme['fg'],
                selectbackground=theme['select_bg'],
                selectforeground=theme['select_fg'],
                insertbackground=theme['cursor']
            )
        except Exception:
            # Not all widgets support all options
            pass

class KeybindManager:
    """Keyboard shortcut management"""
    
    def __init__(self):
        self.bindings = {
            'new_file': '<Control-n>',
            'open_file': '<Control-o>',
            'save_file': '<Control-s>',
            'save_as': '<Control-Shift-s>',
            'close_tab': '<Control-w>',
            'undo': '<Control-z>',
            'redo': '<Control-y>',
            'cut': '<Control-x>',
            'copy': '<Control-c>',
            'paste': '<Control-v>',
            'find': '<Control-f>',
            'replace': '<Control-h>',
            'goto_line': '<Control-g>',
            'comment_toggle': '<Control-slash>',
            'ai_completion': '<Control-space>',
            'ai_chat': '<Control-Shift-a>',
            'command_palette': '<Control-Shift-p>',
        }
    
    def get_binding(self, action: str) -> str:
        """Get keybinding for action"""
        return self.bindings.get(action, '')
    
    def set_binding(self, action: str, binding: str):
        """Set keybinding for action"""
        self.bindings[action] = binding
    
    def get_all_bindings(self) -> Dict[str, str]:
        """Get all keybindings"""
        return self.bindings.copy()

# Global instances
config_manager = ConfigManager()
logger = Logger()
theme_manager = ThemeManager()
keybind_manager = KeybindManager()
file_manager = FileManager(config_manager)

def initialize_app():
    """Initialize application components"""
    log = logger.get_logger()
    
    log.info("Initializing Cursor AI Clone...")
    
    # Check system dependencies
    deps = SystemUtils.check_dependencies()
    missing_deps = [dep for dep, available in deps.items() if not available]
    
    if missing_deps:
        log.warning(f"Missing dependencies: {', '.join(missing_deps)}")
        
        # Try to install missing Python packages
        if 'requests' in missing_deps or any('python' in dep for dep in missing_deps):
            log.info("Attempting to install missing Python packages...")
            if SystemUtils.install_missing_deps():
                log.info("Successfully installed missing Python packages")
            else:
                log.error("Failed to install missing Python packages")
    
    # Log system info
    system_info = SystemUtils.get_system_info()
    log.info(f"System: {system_info.get('distribution', system_info.get('platform'))}")
    log.info(f"Python: {system_info['python_version']}")
    
    log.info("Application initialization complete")
    return True

if __name__ == "__main__":
    # Test the configuration system
    initialize_app()
    
    print("Configuration test:")
    print(f"Config directory: {config_manager.config_dir}")
    print(f"Current theme: {config_manager.config.editor.theme}")
    print(f"AI model: {config_manager.config.google_cloud.model_name}")
    
    # Test dependencies
    deps = SystemUtils.check_dependencies()
    print("\nDependency check:")
    for dep, available in deps.items():
        status = "✅" if available else "❌"
        print(f"{status} {dep}")
