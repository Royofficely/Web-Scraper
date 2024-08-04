#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Create bin directory if it doesn't exist
mkdir -p ~/bin

# Copy officely-scraper to bin
cp "$SCRIPT_DIR/officely-scraper" ~/bin/officely-scraper

# Make it executable
chmod +x ~/bin/officely-scraper

# Add ~/bin to PATH if it's not already there
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bash_profile
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
    export PATH="$HOME/bin:$PATH"
fi

echo "Installation complete! You can now use 'officely-scraper' from anywhere."
echo "Please restart your terminal or run 'source ~/.bash_profile' (or 'source ~/.zshrc' if you're using Zsh) to update your PATH."