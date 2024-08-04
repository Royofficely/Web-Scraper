#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Create bin directory if it doesn't exist
mkdir -p ~/bin

# Copy officely-scraper to bin
if cp "$SCRIPT_DIR/officely-scraper" ~/bin/officely-scraper; then
    echo "Copied 'officely-scraper' successfully."
else
    echo "Failed to copy 'officely-scraper'. Check permissions and try again."
    exit 1
fi

# Make it executable
chmod +x ~/bin/officely-scraper

# Function to add path to the appropriate shell profile
add_path_to_profile() {
    local profile_file="$1"
    if [[ -f "$profile_file" ]]; then
        if ! grep -q 'export PATH="$HOME/bin:$PATH"' "$profile_file"; then
            echo 'export PATH="$HOME/bin:$PATH"' >> "$profile_file"
            echo "Updated $profile_file with PATH."
        fi
        source "$profile_file"
    else
        echo "$profile_file not found."
    fi
}

# Determine the shell and update the appropriate profile
if [[ "$SHELL" =~ "zsh" ]]; then
    add_path_to_profile "$HOME/.zshrc"
elif [[ "$SHELL" =~ "bash" ]]; then
    add_path_to_profile "$HOME/.bash_profile"
else
    echo "Unsupported shell. Manually add '$HOME/bin' to your PATH."
fi

echo "Installation complete! You can now use 'officely-scraper' from anywhere."
