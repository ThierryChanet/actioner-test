# Repository Structure

This document describes the organization of the Notion AX Extractor repository.

## 📁 Directory Layout

```
actioner-test/
├── README.md                 # Main documentation
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # MIT License
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup
├── pytest.ini               # Test configuration
├── .gitignore               # Git ignore rules
│
├── docs/                    # 📚 All documentation
│   ├── README.md            # Documentation index
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── IMPLEMENTATION_COMPLETE.md
│   ├── MANIFESTO.md
│   │
│   ├── agent/               # AI Agent docs
│   │   ├── GET_STARTED.md           # 2-min quick start
│   │   ├── AGENT_QUICKSTART.md      # 5-min tutorial
│   │   ├── AGENT_README.md          # Complete guide
│   │   └── AGENT_QUERIES.md         # Example queries
│   │
│   ├── extraction/          # Extraction method docs
│   │   ├── DATABASE_AX_EXTRACTION.md
│   │   ├── DATABASE_EXTRACTION.md
│   │   ├── AX_IMPLEMENTATION_SUMMARY.md
│   │   └── USAGE_EXAMPLES.md
│   │
│   └── guides/              # Setup & configuration
│       ├── PERMISSION_SETUP.md
│       ├── QUICK_START_DATABASE.md
│       ├── QUICK_START_AX_DATABASE.md
│       └── DEBUGGING.md
│
├── src/                     # 💻 Source code
│   ├── __init__.py
│   ├── cli.py               # Classic CLI
│   ├── main.py              # Entry point
│   ├── database_extractor.py
│   ├── orchestrator.py      # Unified extraction orchestrator
│   ├── errors.py
│   │
│   ├── agent/               # AI Agent
│   │   ├── __init__.py
│   │   ├── __main__.py      # Module entry
│   │   ├── cli.py           # Agent CLI
│   │   ├── core.py          # LangChain agent
│   │   ├── tools.py         # Agent tools
│   │   ├── state.py         # State management
│   │   └── callbacks.py     # User interaction
│   │
│   ├── ax/                  # Accessibility API
│   │   ├── client.py
│   │   ├── element.py
│   │   ├── utils.py
│   │   └── bridge.py
│   │
│   ├── notion/              # Notion-specific logic
│   │   ├── detector.py
│   │   ├── navigator.py
│   │   ├── extractor.py
│   │   ├── database_ax_extractor.py
│   │   ├── ocr_navigator.py
│   │   ├── keyboard_navigator.py
│   │   └── mouse_navigator.py
│   │
│   ├── ocr/                 # OCR fallback
│   │   ├── vision.py
│   │   └── fallback.py
│   │
│   ├── output/              # Output handlers
│   │   ├── json_writer.py
│   │   ├── csv_writer.py
│   │   └── logger.py
│   │
│   └── validation/          # API validation
│       ├── notion_api.py
│       ├── comparator.py
│       └── differ.py
│
├── tests/                   # 🧪 Test suite
│   ├── __init__.py
│   ├── test_agent.py        # Agent tests
│   ├── test_comparator.py
│   ├── test_database_extractor.py
│   ├── test_errors.py
│   ├── test_extractor.py
│   └── test_output.py
│
├── examples/                # 📝 Example scripts
│   ├── README.md
│   ├── agent_usage.py       # Agent examples
│   ├── simple_usage.py
│   ├── extract_recipe_database.py
│   └── extract_database_with_ax.py
│
├── output/                  # 📤 Extraction output
│   ├── .gitkeep
│   └── logs/
│       └── .gitkeep
│
└── venv/                    # Python virtual environment (gitignored)
```

## 📚 Documentation Organization

### Root Directory (Essentials Only)
- `README.md` - Main project documentation
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE` - License file
- `REPOSITORY_STRUCTURE.md` - This file

### docs/ (All Documentation)

**Main documentation:**
- `README.md` - Documentation index and navigation
- `IMPLEMENTATION_SUMMARY.md` - Original implementation notes
- `IMPLEMENTATION_COMPLETE.md` - Agent implementation details
- `MANIFESTO.md` - Project philosophy

**docs/agent/** (AI Agent):
- Natural language interface documentation
- Quick starts and tutorials
- Example queries and usage patterns

**docs/extraction/** (Extraction Methods):
- AX navigation documentation
- API-based extraction guides
- Technical implementation details
- Classic CLI usage examples

**docs/guides/** (Setup & Troubleshooting):
- Permission setup instructions
- Quick start guides
- Debugging and troubleshooting
- Configuration guides

## 🎯 Finding What You Need

### I Want To...

| Goal | Location |
|------|----------|
| Start using the agent | [docs/agent/GET_STARTED.md](docs/agent/GET_STARTED.md) |
| See example queries | [docs/agent/AGENT_QUERIES.md](docs/agent/AGENT_QUERIES.md) |
| Use classic CLI | [docs/extraction/USAGE_EXAMPLES.md](docs/extraction/USAGE_EXAMPLES.md) |
| Extract databases (no API) | [docs/extraction/DATABASE_AX_EXTRACTION.md](docs/extraction/DATABASE_AX_EXTRACTION.md) |
| Extract databases (with API) | [docs/extraction/DATABASE_EXTRACTION.md](docs/extraction/DATABASE_EXTRACTION.md) |
| Set up permissions | [docs/guides/PERMISSION_SETUP.md](docs/guides/PERMISSION_SETUP.md) |
| Debug issues | [docs/guides/DEBUGGING.md](docs/guides/DEBUGGING.md) |
| Understand architecture | [docs/IMPLEMENTATION_COMPLETE.md](docs/IMPLEMENTATION_COMPLETE.md) |
| See code examples | [examples/](examples/) |
| Contribute | [CONTRIBUTING.md](CONTRIBUTING.md) |

## 💻 Code Organization

### Core Modules

**src/orchestrator.py**
- Unified interface for all extraction methods
- Automatic method selection (API → AX → OCR → Keyboard → Mouse)
- Error handling and fallbacks

**src/agent/**
- LangChain-based AI agent
- Natural language query processing
- Tool definitions and state management

**src/notion/**
- Notion-specific extraction logic
- Navigation implementations
- Database extractors

**src/ax/**
- macOS Accessibility API wrapper
- Element abstraction
- Utility functions

**src/ocr/**
- OCR fallback for inaccessible elements
- macOS Vision API
- Tesseract fallback

**src/validation/**
- Notion API client
- Content comparison
- Validation reports

**src/output/**
- JSON/CSV writers
- Logging infrastructure

## 🧪 Testing

Run tests:
```bash
# All tests
pytest

# Agent tests specifically
python tests/test_agent.py

# With coverage
pytest --cov=src
```

## 📦 Output

All extraction output goes to `output/`:
- `*.json` - JSON extraction results
- `*.csv` - CSV extraction results
- `logs/*.log` - Detailed extraction logs

Note: Output files are gitignored but directory structure is preserved with `.gitkeep` files.

## 🔧 Entry Points

### CLI Commands

```bash
# Classic CLI
python -m src.cli [command]

# AI Agent
python -m src.agent [query]

# Package commands (after pip install -e .)
notion-extract [command]
notion-agent [query]
```

### Programmatic

```python
# Classic extraction
from src.database_extractor import extract_database_pages

# Agent
from src.agent import create_agent

# Orchestrator
from src.orchestrator import NotionOrchestrator
```

## 🌲 Development

### Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Installing in Dev Mode
```bash
pip install -e .
```

### Adding Dependencies
1. Add to `requirements.txt`
2. Update `setup.py` if it's a core dependency
3. Run `pip install -r requirements.txt`

## 📋 File Naming Conventions

- **UPPERCASE.md** - Documentation files
- **lowercase.py** - Source code files
- **test_*.py** - Test files
- **example_*.py** - Example scripts

## 🗂️ Git Management

### Ignored
- `venv/` - Virtual environment
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python
- `output/*.json` - Extraction output
- `output/*.csv` - CSV output
- `output/logs/*.log` - Log files
- `.DS_Store` - macOS metadata
- `.vscode/`, `.idea/` - IDE settings

### Tracked
- All source code
- All documentation
- Examples
- Tests
- Configuration files
- `output/.gitkeep` - Directory structure

## 🔄 Recent Refactoring

The repository was recently reorganized to improve maintainability:

### Before
- 15+ markdown files in root directory
- Confusing documentation structure
- Test files mixed with examples

### After
- Clean root with only essentials
- Organized docs/ directory with clear structure
- Proper separation of concerns
- Easy navigation with docs/README.md

## 📈 Version History

- **v0.2.0** - Added LangChain AI agent, reorganized documentation
- **v0.1.0** - Initial release with AX-based extraction

## 🤝 Contributing

When adding new features:

1. **Code** → Add to appropriate `src/` subdirectory
2. **Tests** → Add to `tests/`
3. **Docs** → Add to `docs/` (agent/, extraction/, or guides/)
4. **Examples** → Add to `examples/`

Follow the existing structure and naming conventions.

## 📞 Support

- **Quick Start**: [docs/agent/GET_STARTED.md](docs/agent/GET_STARTED.md)
- **Documentation Index**: [docs/README.md](docs/README.md)
- **Troubleshooting**: [docs/guides/DEBUGGING.md](docs/guides/DEBUGGING.md)
- **Issues**: Open an issue on GitHub

---

**Navigation**: [← Back to Main README](README.md) | [📚 Browse Documentation](docs/)

