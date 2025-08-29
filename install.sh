#!/bin/bash

# YOLOv11e PII Detection Pipeline - Installation Script
# This script helps set up the project on macOS/Linux

set -e  # Exit on any error

echo "🚀 YOLOv11e PII Detection Pipeline - Installation Script"
echo "=========================================================="

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

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    print_status "Detected macOS system"
    IS_MACOS=true
else
    print_status "Detected Linux/Unix system"
    IS_MACOS=false
fi

# Check Python installation
print_status "Checking Python installation..."

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1)
    print_success "Found Python: $PYTHON_VERSION"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python --version 2>&1)
    print_success "Found Python: $PYTHON_VERSION"
else
    print_error "Python not found. Please install Python 3.8+ first."
    if [[ "$IS_MACOS" == true ]]; then
        echo "On macOS, you can install Python using:"
        echo "  brew install python"
        echo "  or download from https://www.python.org/downloads/"
    else
        echo "On Linux, you can install Python using your package manager:"
        echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    fi
    exit 1
fi

# Check pip installation
print_status "Checking pip installation..."

if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
    print_success "Found pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
    print_success "Found pip"
else
    print_warning "pip not found. Attempting to install..."
    
    if [[ "$IS_MACOS" == true ]]; then
        print_status "Installing pip using get-pip.py..."
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        $PYTHON_CMD get-pip.py
        rm get-pip.py
        
        if command -v pip3 &> /dev/null; then
            PIP_CMD="pip3"
        elif command -v pip &> /dev/null; then
            PIP_CMD="pip"
        else
            print_error "Failed to install pip. Please install manually."
            exit 1
        fi
    else
        print_error "Please install pip manually using your package manager."
        exit 1
    fi
fi

# Upgrade pip
print_status "Upgrading pip..."
$PIP_CMD install --upgrade pip

# Install requirements
print_status "Installing Python dependencies..."
$PIP_CMD install -r requirements.txt

# Create sample directories
print_status "Creating sample directories..."
mkdir -p sample_images/identity_docs
mkdir -p sample_images/financial_docs
mkdir -p sample_images/medical_docs
mkdir -p sample_images/digital_screens
mkdir -p sample_videos/meetings
mkdir -p sample_videos/presentations
mkdir -p output_images
mkdir -p output_videos

print_success "Sample directories created"

# Test the installation
print_status "Testing the installation..."
$PYTHON_CMD test_setup.py

if [ $? -eq 0 ]; then
    print_success "Installation completed successfully!"
    echo ""
    echo "🎉 Your PII Detection Pipeline is ready!"
    echo ""
    echo "Next steps:"
    echo "1. Add test images to sample_images/ directory"
    echo "2. Add test videos to sample_videos/ directory"
    echo "3. Run examples: python3 examples/basic_usage.py"
    echo "4. Use CLI: python3 cli.py --help"
    echo ""
    echo "Quick test:"
    echo "  python3 cli.py image sample_images/test.jpg output.jpg"
    echo ""
else
    print_warning "Installation completed with some issues."
    echo "Please check the output above for details."
    echo "You may need to install additional system dependencies."
fi

echo ""
echo "📚 For more information, see README.md"
echo "🐛 For issues, check the troubleshooting section in README.md"
