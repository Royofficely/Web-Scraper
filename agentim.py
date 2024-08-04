#!/usr/bin/env python3
import os
import sys
import subprocess

def install_dependencies():
    print("Installing Officely Web Scraper and its dependencies...")
    
    # Install the package itself
    subprocess.check_call([sys.executable, "-m", "pip", "install", "."])
    
    # Install other dependencies if requirements.txt exists
    if os.path.exists("requirements.txt"):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("requirements.txt not found. Skipping additional dependencies.")

def create_config():
    if not os.path.exists("config.py"):
        print("Creating default config.py...")
        with open("config.py", "w") as f:
            f.write('''config = {
    "domain": "https://help.officely.ai",
    "include_keywords": None,
    "exclude_keywords": None,
    "max_depth": 1,
    "target_div": None,
    "start_with": None,
}''')
    else:
        print("config.py already exists.")

def run_scraper():
    if os.path.exists("scan.py"):
        print("Running the web scraper...")
        subprocess.call([sys.executable, "scan.py"])
    else:
        print("scan.py not found. Please ensure it exists in the current directory.")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: officely-scraper web scraper [install|run]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "install":
        install_dependencies()
        create_config()
        print("Installation complete. You can now run the scraper using 'officely-scraper web scraper run'.")
    elif command == "run":
        run_scraper()
    else:
        print(f"Unknown command: {command}")
        print("Usage: officely-scraper web scraper [install|run]")
        sys.exit(1)

if __name__ == "__main__":
    main()