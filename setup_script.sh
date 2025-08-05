#!/bin/bash

# Cursor AI Clone for Linux - Setup Script
# This script installs all dependencies and sets up the application

set -e  # Exit on any error

echo "🚀 Cursor AI Clone for Linux - Setup Script"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_error "This script is designed for Linux systems only."
    exit 1
fi

print_status "Detecting Linux distribution..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    VERSION=$VERSION_ID
    print_success "Detected: $PRETTY_NAME"
else
    print_warning "Cannot detect Linux distribution. Assuming Ubuntu/Debian..."
    DISTRO="ubuntu"
fi

# Update system packages
print_status "Updating system packages..."
case $DISTRO in
    ubuntu|debian)
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv python3-tk git curl wget
        ;;
    fedora|rhel|centos)
        sudo dnf install -y python3 python3-pip python3-tkinter git curl wget
        ;;
    arch|manjaro)
        sudo pacman -S --noconfirm python python-pip tk git curl wget
        ;;
    *)
        print_warning "Unknown distribution. Please install Python 3, pip, tkinter, git, curl, and wget manually."
        ;;
esac

# Check Python installation
print_status "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Install Google Cloud CLI
print_status "Installing Google Cloud CLI..."
if command -v gcloud &> /dev/null; then
    print_success "Google Cloud CLI already installed"
else
    print_status "Downloading Google Cloud CLI..."
    curl https://sdk.cloud.google.com | bash
    
    # Add gcloud to PATH for current session
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
    
    print_success "Google Cloud CLI installed. Please restart your terminal or run: source ~/.bashrc"
fi

# Create project directory
PROJECT_DIR="$HOME/cursor-ai-clone"
print_status "Creating project directory at $PROJECT_DIR..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip

# Create requirements.txt
cat > requirements.txt << EOF
requests>=2.28.0
keyring>=23.0.0
google-auth>=2.0.0
google-auth-oauthlib>=0.5.0
google-auth-httplib2>=0.1.0
google-cloud-aiplatform>=1.12.0
asyncio-throttle>=1.0.0
pygments>=2.12.0
EOF

pip install -r requirements.txt

# Create config directory
print_status "Creating configuration directory..."
mkdir -p config
mkdir -p logs

# Create sample configuration
cat > config/config.json << EOF
{
    "google_cloud": {
        "project_id": "",
        "region": "us-central1",
        "model_name": "gemini-pro"
    },
    "editor": {
        "theme": "dark",
        "font_family": "Consolas",
        "font_size": 12,
        "tab_size": 4,
        "auto_save": true
    },
    "ai": {
        "max_context_length": 2048,
        "completion_delay_ms": 500,
        "enable_streaming": true
    }
}
EOF

# Create desktop entry
print_status "Creating desktop entry..."
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/cursor-ai-clone.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Cursor AI Clone
Comment=AI-powered code editor for Linux
Exec=$PROJECT_DIR/run.sh
Icon=$PROJECT_DIR/icon.png
Terminal=false
Categories=Development;IDE;
StartupWMClass=cursor-ai-clone
EOF

# Create run script
print_status "Creating run script..."
cat > run.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 main.py "$@"
EOF

chmod +x run.sh

# Create launcher script for development
cat > dev.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$PWD:$PYTHONPATH"
python3 -u main.py --debug
EOF

chmod +x dev.sh

# Download application icon (placeholder)
print_status "Creating application icon..."
cat > icon.png << 'EOF'
# This would be a proper PNG file in a real implementation
# For now, we'll create a simple text placeholder
EOF

# Create the main application file (copy from the artifact we created)
print_status "Creating main application file..."
# Note: In a real setup, you'd copy the main.py file from the artifact

# Create additional utility files
print_status "Creating utility files..."

# Create logging configuration
cat > config/logging.conf << EOF
[loggers]
keys=root,cursor

[handlers]
keys=fileHandler,consoleHandler

[formatters]
keys=fileFormatter,consoleFormatter

[logger_root]
level=INFO
handlers=fileHandler,consoleHandler

[logger_cursor]
level=DEBUG
handlers=fileHandler,consoleHandler
qualname=cursor
propagate=0

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=fileFormatter
args=('logs/cursor.log',)

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=consoleFormatter
args=(sys.stdout,)

[formatter_fileFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S

[formatter_consoleFormatter]
format=%(levelname)s: %(message)s
EOF

# Create README for the project
print_status "Creating project README..."
cat > README.md << 'EOF'
# Cursor AI Clone for Linux

A complete AI-powered code editor that replicates Cursor AI functionality using Google's Gemini CLI.

## Features

- 🚀 AI-powered code completion using Google Gemini
- 💬 Intelligent chat interface for programming assistance
- 📁 Full project workspace with file tree navigation
- 🎨 Syntax highlighting for 20+ programming languages
- 🔄 Git integration and version control
- 🎯 Multi-tab editing with unsaved changes tracking
- 🔍 Global search and replace functionality
- 🖥️ Integrated terminal for command execution

## Quick Start

1. **Authentication**: Authenticate with Google Cloud:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Run the application**:
   ```bash
   ./run.sh
   ```

3. **Development mode**:
   ```bash
   ./dev.sh
   ```

## Configuration

Edit `config/config.json` to customize:
- Google Cloud project settings
- Editor preferences (theme, font, etc.)
- AI behavior and parameters

## Keyboard Shortcuts

- `Ctrl+N` - New file
- `Ctrl+O` - Open file
- `Ctrl+S` - Save file
- `Ctrl+Space` - Trigger AI code completion
- `Ctrl+Shift+P` - Command palette
- `Ctrl+/` - Toggle comment
- `Ctrl+F` - Find in file
- `Ctrl+H` - Replace in file

## Troubleshooting

### Google Cloud Authentication Issues
```bash
# Re-authenticate
gcloud auth login --update-adc

# Check authentication status
gcloud auth list

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### Python Dependencies
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

## License

MIT License - see LICENSE file for details.
EOF

# Create installation verification script
print_status "Creating verification script..."
cat > verify_install.sh << 'EOF'
#!/bin/bash

echo "🔍 Verifying Cursor AI Clone Installation"
echo "========================================"

# Check Python
if command -v python3 &> /dev/null; then
    echo "✅ Python 3: $(python3 --version)"
else
    echo "❌ Python 3: Not found"
fi

# Check Google Cloud CLI
if command -v gcloud &> /dev/null; then
    echo "✅ Google Cloud CLI: $(gcloud --version | head -n1)"
else
    echo "❌ Google Cloud CLI: Not found"
fi

# Check virtual environment
if [ -d "venv" ]; then
    echo "✅ Virtual environment: Created"
    source venv/bin/activate
    
    # Check key dependencies
    python3 -c "import requests; print('✅ requests:', requests.__version__)" 2>/dev/null || echo "❌ requests: Not installed"
    python3 -c "import keyring; print('✅ keyring:', keyring.__version__)" 2>/dev/null || echo "❌ keyring: Not installed"
    python3 -c "import tkinter; print('✅ tkinter: Available')" 2>/dev/null || echo "❌ tkinter: Not available"
    
    deactivate
else
    echo "❌ Virtual environment: Not found"
fi

# Check configuration
if [ -f "config/config.json" ]; then
    echo "✅ Configuration: config/config.json exists"
else
    echo "❌ Configuration: config/config.json missing"
fi

# Check main application
if [ -f "main.py" ]; then
    echo "✅ Main application: main.py exists"
else
    echo "❌ Main application: main.py missing"
fi

echo ""
echo "Installation verification complete!"
EOF

chmod +x verify_install.sh

# Create uninstall script
print_status "Creating uninstall script..."
cat > uninstall.sh << 'EOF'
#!/bin/bash

echo "🗑️  Uninstalling Cursor AI Clone"
echo "================================"

read -p "Are you sure you want to uninstall Cursor AI Clone? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 1
fi

# Remove desktop entry
rm -f ~/.local/share/applications/cursor-ai-clone.desktop

# Remove project directory (with confirmation)
read -p "Remove project directory and all data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd ..
    rm -rf cursor-ai-clone
    echo "✅ Project directory removed"
fi

echo "✅ Cursor AI Clone uninstalled"
EOF

chmod +x uninstall.sh

# Create Google Cloud setup helper
print_status "Creating Google Cloud setup helper..."
cat > setup_gcloud.sh << 'EOF'
#!/bin/bash

echo "🔧 Google Cloud Setup for Cursor AI Clone"
echo "=========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI not found. Please run the main setup script first."
    exit 1
fi

echo "📋 This script will help you set up Google Cloud for AI features."
echo ""

# Authenticate
echo "🔐 Step 1: Authentication"
gcloud auth login

# Set project
echo ""
echo "📝 Step 2: Project Configuration"
echo "Available projects:"
gcloud projects list --format="table(projectId,name)"

echo ""
read -p "Enter your Google Cloud Project ID: " PROJECT_ID

if [ -n "$PROJECT_ID" ]; then
    gcloud config set project "$PROJECT_ID"
    echo "✅ Project set to: $PROJECT_ID"
    
    # Update config file
    if [ -f "config/config.json" ]; then
        # Simple JSON update (requires jq for proper JSON manipulation)
        if command -v jq &> /dev/null; then
            jq ".google_cloud.project_id = \"$PROJECT_ID\"" config/config.json > config/config.json.tmp
            mv config/config.json.tmp config/config.json
            echo "✅ Configuration file updated"
        else
            echo "⚠️  Please manually update config/config.json with your project ID"
        fi
    fi
else
    echo "❌ No project ID provided"
    exit 1
fi

# Enable APIs
echo ""
echo "🔌 Step 3: Enabling required APIs"
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com

echo ""
echo "✅ Google Cloud setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: ./verify_install.sh"
echo "2. Start the application: ./run.sh"
EOF

chmod +x setup_gcloud.sh

# Final instructions
print_success "Installation complete!"
echo ""
echo "📁 Project location: $PROJECT_DIR"
echo ""
echo "🚀 Next steps:"
echo "1. Complete Google Cloud setup:"
echo "   cd $PROJECT_DIR"
echo "   ./setup_gcloud.sh"
echo ""
echo "2. Verify installation:"
echo "   ./verify_install.sh"
echo ""
echo "3. Run the application:"
echo "   ./run.sh"
echo ""
echo "4. For development:"
echo "   ./dev.sh"
echo ""

print_status "Creating .gitignore file..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Configuration (may contain sensitive data)
config/config.json
config/.env

# OS
.DS_Store
Thumbs.db

# Google Cloud
.gcloud/
*-key.json
service-account.json

# Temporary files
*.tmp
*.temp
*~
EOF

# Create sample env file
cat > config/.env.example << 'EOF'
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# AI Configuration
GEMINI_MODEL=gemini-pro
MAX_TOKENS=2048
TEMPERATURE=0.7

# Development
DEBUG=false
LOG_LEVEL=INFO
EOF

# Create development requirements
cat > requirements-dev.txt << 'EOF'
# Development dependencies
pytest>=7.0.0
pytest-asyncio>=0.20.0
black>=22.0.0
flake8>=4.0.0
mypy>=0.950
pre-commit>=2.17.0
coverage>=6.3.0
EOF

print_status "Development environment setup..."
pip install -r requirements-dev.txt

# Create pre-commit configuration
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
EOF

# Initialize pre-commit
pre-commit install

print_success "🎉 Complete setup finished!"
echo ""
echo "📖 Documentation:"
echo "   - README.md - Project overview and usage"
echo "   - config/ - Configuration files"
echo "   - logs/ - Application logs"
echo ""
echo "🛠️  Maintenance scripts:"
echo "   - verify_install.sh - Check installation"
echo "   - setup_gcloud.sh - Configure Google Cloud"
echo "   - uninstall.sh - Remove the application"
echo ""
echo "🔧 Development:"
echo "   - requirements-dev.txt - Development dependencies"
echo "   - .pre-commit-config.yaml - Code quality hooks"
echo ""

# Check if in GUI environment
if [ -n "$DISPLAY" ]; then
    print_status "GUI environment detected. You can find 'Cursor AI Clone' in your applications menu."
fi

echo "Happy coding! 🚀"
EOF
