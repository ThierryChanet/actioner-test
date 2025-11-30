from setuptools import setup, find_packages

setup(
    name="notion-ax-extractor",
    version="0.2.0",
    description="macOS tool for extracting Notion content via Accessibility APIs with AI Agent",
    author="Thierry",
    packages=find_packages(),
    install_requires=[
        "pyobjc-core>=9.0",
        "pyobjc-framework-Cocoa>=9.0",
        "pyobjc-framework-Quartz>=9.0",
        "pyobjc-framework-Vision>=9.0",
        "notion-client>=2.0.0",
        "pytesseract>=0.3.10",
        "Pillow>=10.0.0",
        "click>=8.1.0",
        "python-dateutil>=2.8.2",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "langchain-anthropic>=0.1.0",
        "langchain-community>=0.0.20",
        "openai>=1.12.0",
        "anthropic>=0.18.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "notion-extract=src.cli:main",
            "notion-agent=src.agent.cli:main",
        ],
    },
)

