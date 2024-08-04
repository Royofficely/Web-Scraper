from setuptools import setup, find_packages

# Reading the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Reading requirements from requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="officely-web-scraper",
    version="0.1.0",
    author="Roy Nativ",
    author_email="roy@example.com",
    description="A powerful, recursive URL-smart web scraping tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/roynativ/officely-web-scraper",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "officely-scraper=officely_web_scraper.scan:main",
        ],
    },
)
