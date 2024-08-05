import os
import sys
import subprocess
from importlib import reload
import importlib.util

def install_dependencies():
    print("Installing Officely Web Scraper and its dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
    if os.path.exists("requirements.txt"):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("requirements.txt not found. Skipping additional dependencies.")
    print("Installation complete. You can now run the scraper using 'python agentim.py run'.")

def create_config():
    config_path = os.path.join("officely_web_scraper", "config.py")
    if not os.path.exists(config_path):
        print("Creating default config.py...")
        with open(config_path, "w") as f:
            f.write('''config = {
    "domain": "https://www.example.com",
    "include_keywords": None,
    "exclude_keywords": None,
    "max_depth": 1,
    "target_div": None,
    "start_with": None,
}''')
    else:
        print("config.py already exists.")

def load_config():
    config_path = os.path.join("officely_web_scraper", "config.py")
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    return config_module

def run_scraper():
    print(f"Current working directory: {os.getcwd()}")
    print(f"Contents of officely_web_scraper directory: {os.listdir('officely_web_scraper')}")
    if os.path.exists("officely_web_scraper/scan.py"):
        print("Running the web scraper...")
        try:
            config = load_config()
            print(f"Config loaded successfully: {config.config}")
            from officely_web_scraper import scan
            reload(scan)
            print(f"Using domain: {config.config['domain']}")  # Debug output
            scan.run_scraper(config)
        except Exception as e:
            print(f"An error occurred while running the scraper: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("scan.py not found. Please ensure it exists in the officely_web_scraper directory.")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python agentim.py [install|run]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "install":
        install_dependencies()
        create_config()
    elif command == "run":
        run_scraper()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python agentim.py [install|run]")
        sys.exit(1)

if __name__ == "__main__":
    main()
