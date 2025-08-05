# Cursor AI Clone for Linux 🚀

A complete AI-powered code editor that replicates Cursor AI functionality using Google's free Gemini CLI. Built specifically for Ubuntu Linux with full integration of intelligent code completion, chat-based programming assistance, and seamless development workflows.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)

## ✨ Features

### 🤖 AI-Powered Development
- **Intelligent Code Completion**: Real-time code suggestions using Google Gemini
- **AI Chat Assistant**: Context-aware programming help and debugging
- **Code Analysis**: Automated code review, security scanning, and optimization suggestions
- **Documentation Generation**: Auto-generate docstrings, comments, and README sections
- **Unit Test Creation**: AI-generated test suites for your code
- **Multi-language Support**: Python, JavaScript, Java, C++, HTML, CSS, and more

### 📝 Advanced Editor Features
- **Multi-tab Editing**: Handle multiple files with unsaved changes tracking
- **Syntax Highlighting**: Support for 20+ programming languages
- **File Explorer**: Hierarchical project view with intuitive navigation
- **Search & Replace**: Powerful find/replace with regex support
- **Git Integration**: Built-in version control operations
- **Integrated Terminal**: Execute commands without leaving the editor
- **Customizable Themes**: Dark and light modes with syntax coloring

### 🔧 Developer Experience
- **Smart Keybindings**: VS Code-style keyboard shortcuts
- **Auto-save**: Configurable automatic file saving
- **Recent Files**: Quick access to recently opened files
- **Project Workspace**: Full project management with context awareness
- **Error Handling**: Comprehensive error reporting and recovery
- **Performance Optimized**: Fast startup and responsive UI

## 🚀 Quick Start

### One-Command Installation

```bash
# Download and run the setup script
curl -sSL https://raw.githubusercontent.com/your-repo/cursor-ai-clone/main/setup.sh | bash
```

### Manual Installation

1. **Clone and Setup**
   ```bash
   git clone https://github.com/your-repo/cursor-ai-clone.git
   cd cursor-ai-clone
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure Google Cloud**
   ```bash
   ./setup_gcloud.sh
   ```

3. **Verify Installation**
   ```bash
   ./verify_install.sh
   ```

4. **Launch the Application**
   ```bash
   ./run.sh
   ```

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ (or compatible Linux distribution)
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space
- **Internet**: Required for AI features

### Required Dependencies (Auto-installed)
- Python 3 with tkinter
- Google Cloud CLI
- Git
- Essential Python packages (requests, keyring, etc.)

## 🔑 Google Cloud Setup

### 1. Create Google Cloud Project
```bash
# Install Google Cloud CLI (done automatically by setup script)
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login

# Create or select project
gcloud projects create your-cursor-clone-project
gcloud config set project your-cursor-clone-project
```

### 2. Enable Required APIs
```bash
# Enable AI Platform API
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

### 3. Setup Authentication
```bash
# Application default credentials
gcloud auth application-default login

# Or use service account (for production)
gcloud iam service-accounts create cursor-ai-service
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:cursor-ai-service@your-project-id.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

## 💻 Usage Guide

### Basic Operations

#### Starting the Application
```bash
# Normal mode
./run.sh

# Development mode (with debug output)
./dev.sh
```

#### File Operations
- **New File**: `Ctrl+N`
- **Open File**: `Ctrl+O`
- **Save File**: `Ctrl+S`
- **Save As**: `Ctrl+Shift+S`

#### AI Features
- **Code Completion**: `Ctrl+Space`
- **AI Chat**: Click the chat panel or `Ctrl+Shift+A`
- **Code Analysis**: Right-click → "Analyze Code"

### Advanced Features

#### 1. AI Code Completion
```python
# Type your code and press Ctrl+Space
def calculate_fibonacci(n):
    # AI will suggest completion
```

#### 2. AI Chat Assistant
- Ask programming questions
- Get explanations of complex code
- Request debugging help
- Seek architecture advice

#### 3. Code Analysis
- **Security Scan**: Find vulnerabilities
- **Performance Review**: Optimization suggestions  
- **Style Check**: Best practices compliance
- **Bug Detection**: Logical error identification

#### 4. Documentation Generation
- Auto-generate docstrings
- Create README sections
- Generate API documentation
- Add inline comments

## ⚙️ Configuration

### Main Configuration File: `config/config.json`

```json
{
  "google_cloud": {
    "project_id": "your-project-id",
    "region": "us-central1",
    "model_name": "gemini-pro"
  },
  "editor": {
    "theme": "dark",
    "font_family": "Consolas",
    "font_size": 12,
    "tab_size": 4,
    "auto_save": true,
    "auto_save_delay": 5000
  },
  "ai": {
    "max_context_length": 2048,
    "completion_delay_ms": 500,
    "enable_streaming": true,
    "temperature": 0.7,
    "max_tokens": 1024
  }
}
```

### Environment Variables (Optional)
Create `config/.env`:
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GEMINI_MODEL=gemini-pro
DEBUG=false
LOG_LEVEL=INFO
```

## 🎯 Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| New File | `Ctrl+N` |
| Open File | `Ctrl+O` |
| Save File | `Ctrl+S` |
| Save As | `Ctrl+Shift+S` |
| Close Tab | `Ctrl+W` |
| Find | `Ctrl+F` |
| Replace | `Ctrl+H` |
| Go to Line | `Ctrl+G` |
| Toggle Comment | `Ctrl+/` |
| AI Completion | `Ctrl+Space` |
| AI Chat | `Ctrl+Shift+A` |
| Command Palette | `Ctrl+Shift+P` |
| Undo | `Ctrl+Z` |
| Redo | `Ctrl+Y` |

## 🔧 Troubleshooting

### Common Issues

#### 1. Authentication Problems
```bash
# Re-authenticate with Google Cloud
gcloud auth login --update-adc

# Check authentication status
gcloud auth list

# Verify project setting
gcloud config get-value project
```

#### 2. Missing Dependencies
```bash
# Reinstall Python packages
source venv/bin/activate
pip install -r requirements.txt --force-reinstall

# Check system dependencies
./verify_install.sh
```

#### 3. AI Features Not Working
```bash
# Check Google Cloud CLI
gcloud --version

# Test AI API access
gcloud ai models list --region=us-central1

# Check project permissions
gcloud projects get-iam-policy your-project-id
```

#### 4. Performance Issues
- **Large Files**: Split into smaller modules
- **Memory Usage**: Restart application periodically
- **Slow Completions**: Reduce context length in config

### Error Messages

| Error | Solution |
|-------|----------|
| "Google Cloud CLI not found" | Run setup script or install manually |
| "Authentication required" | Run `gcloud auth login` |
| "API Error: Permission denied" | Enable required APIs and check IAM |
| "Rate limit exceeded" | Wait or upgrade to paid tier |

## 🏗️ Architecture

### Project Structure
```
cursor-ai-clone/
├── main.py                 # Main application entry point
├── config_utils.py         # Configuration management
├── gemini_integration.py   # AI service integration
├── setup.sh               # Installation script
├── run.sh                 # Application launcher
├── config/
│   ├── config.json        # Main configuration
│   └── logging.conf       # Logging setup
├── logs/                  # Application logs
├── venv/                  # Python virtual environment
└── README.md             # This file
```

### Core Components

1. **Main Application** (`main.py`)
   - GUI framework (Tkinter)
   - File management
   - Editor functionality
   - Event handling

2. **AI Integration** (`gemini_integration.py`)
   - Google Gemini CLI interface
   - Request/response handling
   - Context management
   - Rate limiting

3. **Configuration** (`config_utils.py`)
   - Settings management
   - Theme handling
   - Logging setup
   - System utilities

## 🚧 Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/your-repo/cursor-ai-clone.git
cd cursor-ai-clone

# Setup development environment
./setup.sh

# Install development dependencies
source venv/bin/activate
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run in development mode
./dev.sh
```

### Development Scripts

```bash
# Run tests
python -m pytest tests/

# Code formatting
black .

# Linting
flake8 .

# Type checking
mypy .
```

### Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📊 Performance & Limits

### Google Cloud Free Tier Limits
- **Gemini API**: 60 requests per minute
- **Storage**: 15GB total across all services
- **Compute**: Limited free quota

### Application Performance
- **Startup Time**: < 3 seconds
- **Memory Usage**: 200-500MB typical
- **Response Time**: 1-3 seconds for AI features
- **File Size Limit**: 10MB per file recommended

## 🔒 Security & Privacy

### Data Handling
- **Local Storage**: All code stays on your machine
- **AI Processing**: Code snippets sent to Google Gemini (encrypted)
- **No Data Retention**: Google doesn't store your code permanently
- **Authentication**: Secure OAuth 2.0 flow

### Best Practices
- Use service accounts for production
- Enable audit logging
- Regularly rotate credentials
- Review API permissions

## 🛣️ Roadmap

### Phase
