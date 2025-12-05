# Documentation

This directory contains all documentation for the Notion AX Extractor project.

## 📚 Documentation Structure

### Agent Documentation (`agent/`)
The LangChain-based AI agent for natural language extraction:

- **[GET_STARTED.md](agent/GET_STARTED.md)** - Quick 2-minute setup guide
- **[AGENT_QUICKSTART.md](agent/AGENT_QUICKSTART.md)** - 5-minute quick start
- **[AGENT_README.md](agent/AGENT_README.md)** - Complete agent documentation
- **[AGENT_QUERIES.md](agent/AGENT_QUERIES.md)** - 100+ example queries

👉 **Start here if you want to use natural language**: [agent/GET_STARTED.md](agent/GET_STARTED.md)

### Extraction Methods (`extraction/`)
Documentation for specific extraction methods:

- **[DATABASE_AX_EXTRACTION.md](extraction/DATABASE_AX_EXTRACTION.md)** - Extract databases using AX navigation (no API token needed)
- **[DATABASE_EXTRACTION.md](extraction/DATABASE_EXTRACTION.md)** - Extract databases using Notion API (fast)
- **[AX_IMPLEMENTATION_SUMMARY.md](extraction/AX_IMPLEMENTATION_SUMMARY.md)** - Technical details of AX implementation
- **[USAGE_EXAMPLES.md](extraction/USAGE_EXAMPLES.md)** - Classic CLI usage examples

### Setup & Configuration (`guides/`)
Setup guides and troubleshooting:

- **[PERMISSION_SETUP.md](guides/PERMISSION_SETUP.md)** - macOS Accessibility permissions
- **[QUICK_START_DATABASE.md](guides/QUICK_START_DATABASE.md)** - Quick start for database extraction (API)
- **[QUICK_START_AX_DATABASE.md](guides/QUICK_START_AX_DATABASE.md)** - Quick start for database extraction (AX)
- **[DEBUGGING.md](guides/DEBUGGING.md)** - Debugging and troubleshooting
- **[TROUBLESHOOT_AX_DATABASE.md](guides/TROUBLESHOOT_AX_DATABASE.md)** - AX database extraction troubleshooting
- **[VERBOSITY_LEVELS.md](guides/VERBOSITY_LEVELS.md)** - Verbosity level configuration

### Implementation Notes (`implementation/`)
Technical implementation summaries:

- **[COMPUTER_USE_IMPLEMENTATION.md](implementation/COMPUTER_USE_IMPLEMENTATION.md)** - Computer Use integration details (Anthropic)
- **[VISION_INTEGRATION_SUMMARY.md](implementation/VISION_INTEGRATION_SUMMARY.md)** - Vision integration summary
- **[AX_VISION_IMPLEMENTATION_SUMMARY.md](implementation/AX_VISION_IMPLEMENTATION_SUMMARY.md)** - AX + Vision implementation
- **[AX_NAVIGATION_FIX_SUMMARY.md](implementation/AX_NAVIGATION_FIX_SUMMARY.md)** - AX navigation fixes

### Project Documentation
High-level project documentation:

- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Original implementation summary
- **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** - Agent implementation details
- **[MANIFESTO.md](MANIFESTO.md)** - Project philosophy and goals

## 🚀 Quick Navigation

### I Want To...

**Use natural language to extract content**  
→ Go to [agent/GET_STARTED.md](agent/GET_STARTED.md)

**Use the classic CLI commands**  
→ Go to [extraction/USAGE_EXAMPLES.md](extraction/USAGE_EXAMPLES.md)

**Extract from a database without API token**  
→ Go to [extraction/DATABASE_AX_EXTRACTION.md](extraction/DATABASE_AX_EXTRACTION.md)

**Extract from a database with API token (fast)**  
→ Go to [extraction/DATABASE_EXTRACTION.md](extraction/DATABASE_EXTRACTION.md)

**Set up permissions**  
→ Go to [guides/PERMISSION_SETUP.md](guides/PERMISSION_SETUP.md)

**Debug issues**  
→ Go to [guides/DEBUGGING.md](guides/DEBUGGING.md)

**Understand the architecture**  
→ Go to [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)

## 📖 Reading Order

### For New Users

1. [agent/GET_STARTED.md](agent/GET_STARTED.md) - 2-minute setup
2. [agent/AGENT_QUICKSTART.md](agent/AGENT_QUICKSTART.md) - Basic usage
3. [agent/AGENT_QUERIES.md](agent/AGENT_QUERIES.md) - Example queries

### For Classic CLI Users

1. [guides/PERMISSION_SETUP.md](guides/PERMISSION_SETUP.md) - Setup permissions
2. [extraction/USAGE_EXAMPLES.md](extraction/USAGE_EXAMPLES.md) - CLI examples
3. [extraction/DATABASE_EXTRACTION.md](extraction/DATABASE_EXTRACTION.md) - Database extraction

### For Developers

1. [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) - Architecture overview
2. [extraction/AX_IMPLEMENTATION_SUMMARY.md](extraction/AX_IMPLEMENTATION_SUMMARY.md) - AX details
3. [MANIFESTO.md](MANIFESTO.md) - Project goals

## 🔗 External Resources

- **Main README**: [../README.md](../README.md)
- **Contributing Guide**: [../CONTRIBUTING.md](../CONTRIBUTING.md)
- **License**: [../LICENSE](../LICENSE)
- **Examples**: [../examples/](../examples/)

## 📝 Documentation Guidelines

When contributing documentation:

1. **Agent docs** → `agent/` - Natural language interface documentation
2. **Extraction methods** → `extraction/` - Specific extraction techniques
3. **Setup/config** → `guides/` - Installation and configuration
4. **Implementation notes** → `implementation/` - Technical summaries and migration guides
5. **Project docs** → `docs/` root - High-level architecture and design

Keep documentation:
- Clear and concise
- With working examples
- Up to date with code changes
- Well-organized with headers

## 🆘 Need Help?

- Check [guides/DEBUGGING.md](guides/DEBUGGING.md)
- Run `python -m src.agent check` to verify setup
- See [agent/AGENT_README.md](agent/AGENT_README.md) for troubleshooting

---

**Navigation**: [← Back to Main README](../README.md)

