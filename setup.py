from setuptools import setup, find_packages

setup(
    name="notion-ax-extractor",
    version="0.1.0",
    description="macOS tool for extracting Notion content via Accessibility APIs",
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
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "notion-extract=src.cli:main",
        ],
    },
)

