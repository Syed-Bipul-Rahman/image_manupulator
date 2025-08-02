#!/bin/bash

echo "🔧 Installing tkinter for Enhanced Image Manipulator"
echo "=============================================="

# Check if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 Detected macOS system"
    
    # Check if Homebrew is installed
    if command -v brew &> /dev/null; then
        echo "🍺 Homebrew found, installing python-tk..."
        brew install python-tk
        
        # Also try installing tkinter through conda if available
        if command -v conda &> /dev/null; then
            echo "🐍 Conda found, also installing tk..."
            conda install tk -y
        fi
        
    else
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "   Then run: brew install python-tk"
    fi
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Detected Linux system"
    
    # Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        echo "📦 Installing python3-tk with apt-get..."
        sudo apt-get update
        sudo apt-get install python3-tk
    
    # Red Hat/CentOS/Fedora
    elif command -v yum &> /dev/null; then
        echo "📦 Installing tkinter with yum..."
        sudo yum install tkinter
    
    # Arch Linux
    elif command -v pacman &> /dev/null; then
        echo "📦 Installing tk with pacman..."
        sudo pacman -S tk
    
    else
        echo "❌ Package manager not found. Please install tkinter manually for your Linux distribution."
    fi
    
else
    echo "❓ Unknown operating system. Please install tkinter manually."
fi

echo ""
echo "✅ Installation attempt completed!"
echo "💡 If tkinter still doesn't work, try using the web-based version instead:"
echo "   pip install streamlit"
echo "   streamlit run web_image_manipulator.py"