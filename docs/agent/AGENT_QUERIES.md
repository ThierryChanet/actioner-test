# Notion Agent - Example Queries

This document lists example queries the agent can handle, organized by category.

## Navigation Queries

### Basic Navigation
- "Navigate to the Roadmap page"
- "Go to Project Planning"
- "Open the Meeting Notes page"
- "Switch to the Weekly Report"

### Checking Location
- "What page am I on?"
- "Where am I right now?"
- "What's the current page title?"

## Listing & Discovery

### List Pages
- "List all my pages"
- "Show me all available pages"
- "What pages do I have?"
- "What's in my sidebar?"

### Search Pages
- "Find pages about Python"
- "Search for pages with 'meeting' in the title"
- "Show me pages containing 'recipe'"
- "Which pages mention 'project'?"

## Content Extraction

### Single Page Extraction
- "Extract the Roadmap page"
- "Get content from Meeting Notes"
- "What's on the Weekly Report page?"
- "Show me the content of Project Planning"
- "Extract the current page"

### Database Extraction
- "Extract all recipes"
- "Get 10 recipes from my database"
- "Extract all pages from the current database"
- "Extract 20 recipes from database abc123def456" (with database ID)

### Selective Extraction
- "Extract the first 5 pages"
- "Get recipes 10 through 20"
- "Extract just the summary from Roadmap"

## Analysis & Counting

### Counting
- "How many recipes do I have?"
- "Count my pages"
- "How many blocks are in the Roadmap?"
- "What's the total number of pages?"

### Content Analysis
- "Summarize the Roadmap page"
- "What are the main topics in Meeting Notes?"
- "Tell me about the Project Planning page"
- "What's the structure of the Recipe database?"

### Comparison
- "Compare the Q1 and Q2 roadmaps"
- "What's different between Meeting Notes from last week and this week?"

## Combined Operations

### Multi-step Workflows
- "List all pages, then extract the ones about cooking"
- "Find pages with 'report' in the title and extract them"
- "Search for meeting notes and count how many there are"

### Contextual Queries
```
You: "List my pages"
Agent: [Shows pages]

You: "Extract the first one"
Agent: [Extracts the first page from the list]

You: "Now go to the next one"
Agent: [Navigates to next page]
```

## Database-Specific Queries

### With Notion API Token
- "Extract 50 recipes from database abc-123-def"
- "Get all pages from database xyz789"
- "Extract database abc123 with limit 100"

### Without API Token (AX Navigation)
- "Extract recipes from the current view"
- "Get 10 items from this database"
- "Extract all visible rows"

## State & Context

### Check Status
- "What have I extracted so far?"
- "Show me my extraction history"
- "What's my current context?"
- "How many extractions have I done?"

### Session Management
- "Reset and start over"
- "Clear my history"
- "Start fresh"

## Clarification & Help

### When Agent Needs Help
Agent: "I can't find that page. What's the exact name?"
You: "It's called 'Project Roadmap 2024'"

Agent: "Where is your recipe database? Is it open or do you have a database ID?"
You: "It's currently open in Notion"

### Getting Help
- "What can you do?"
- "Help me extract my database"
- "I don't know the database ID, how do I find it?"
- "What's the best way to extract 100 pages?"

## Complex Examples

### Scenario 1: First-time User
```
You: "What can you do?"
Agent: [Explains capabilities]

You: "List my pages"
Agent: [Shows available pages]

You: "Extract the Roadmap"
Agent: [Extracts and summarizes]
```

### Scenario 2: Database Extraction
```
You: "I want to extract all my recipes"
Agent: "I see you have a Recipe database. Should I extract from the 
       current view or do you have a database ID for faster API extraction?"

You: "Use the current view"
Agent: [Extracts using AX navigation]

You: "How many did you get?"
Agent: "I extracted 47 recipes with 1,234 total blocks."
```

### Scenario 3: Exploration
```
You: "Find pages about Python"
Agent: [Searches and finds 3 pages]

You: "Extract all of them"
Agent: [Extracts the 3 pages]

You: "Summarize what you found"
Agent: [Provides summary of content]
```

### Scenario 4: Contextual Workflow
```
You: "List all my pages"
Agent: [Shows 20 pages]

You: "How many are there?"
Agent: "You have 20 pages in your sidebar."

You: "Extract the ones with 'meeting' in the name"
Agent: [Searches, finds 3 meeting pages, extracts them]

You: "What did you find?"
Agent: [Summarizes the 3 meeting pages]
```

## Natural Language Variations

The agent understands many ways to express the same intent:

### "Extract Page X"
- "Extract the Roadmap page"
- "Get content from Roadmap"
- "Show me the Roadmap"
- "What's on Roadmap?"
- "Read the Roadmap page"
- "Pull the Roadmap content"

### "List Pages"
- "List all pages"
- "Show me my pages"
- "What pages do I have?"
- "List available pages"
- "Show me everything"

### "Extract Database"
- "Extract all recipes"
- "Get all recipe pages"
- "Extract my recipe database"
- "Pull all recipes"
- "Extract recipes from the database"

## Tips for Better Results

### Be Specific
❌ "Get that page"
✅ "Extract the Project Roadmap page"

### Use Context
```
You: "List my pages"
Agent: [Shows pages including "Roadmap Q1" and "Roadmap Q2"]

You: "Extract the first one"  ← Agent understands "first one" from context
```

### Break Down Complex Tasks
❌ "Extract all pages and analyze them and create a report"
✅ First: "Extract all pages"
✅ Then: "Analyze the extracted content"
✅ Then: "Create a summary"

### Let the Agent Ask
If the agent needs clarification, it will ask:
```
Agent: "I need more information. Are you referring to:
        1. The Recipe database (47 pages)
        2. The current page
        Please specify which one."
```

## Advanced Queries

### With Filters
- "Extract recipes that mention 'chicken'"
- "Get pages created this week"
- "Find pages longer than 100 blocks"

### With Output Preferences
- "Extract recipes and save as CSV"
- "Get the Roadmap and output to custom_output/"
- "Extract with verbose logging"

### With Method Preferences
- "Extract using OCR navigation"
- "Use the API to extract database xyz"
- "Navigate using keyboard to extract this"

## Troubleshooting Queries

### When Extraction Fails
- "Why did that fail?"
- "Try again with OCR"
- "Use a different method"
- "List pages first so I can see what's available"

### When Page Not Found
Agent: "I can't find a page called 'Roadmap'"
You: "List all pages" ← See what's actually available
You: "It's called 'Project Roadmap 2024'"

### When Database Extraction Is Slow
- "Stop extraction"
- "How many have you extracted so far?"
- "Skip to the next step"

## Interactive Mode Commands

In interactive mode, these special commands work:

- `exit` or `quit` - Exit the agent
- `reset` - Clear conversation history
- `status` - Show current agent state

## Testing Queries

Good queries for testing the agent:

1. **Basic Test**: "What is your current context?"
2. **Navigation Test**: "List all my pages"
3. **Extraction Test**: "Extract the current page"
4. **Search Test**: "Find pages with 'test' in the name"
5. **State Test**: "How many extractions have I done?"

## Real-World Examples

### Recipe Organization
```
"Extract all recipes"
"How many recipes do I have?"
"Which recipes mention chicken?"
"Summarize my recipe collection"
```

### Project Management
```
"Extract all roadmap pages"
"Compare Q1 and Q2 roadmaps"
"List all meeting notes"
"Extract meeting notes from this month"
```

### Documentation
```
"Extract all documentation pages"
"Find pages about API documentation"
"Get the installation guide"
"Extract the troubleshooting section"
```

### Research
```
"Extract all research notes"
"Find pages about machine learning"
"Get citations from the Research page"
"Summarize my research on neural networks"
```

## Query Categories by User Type

### Beginner User
- "What can you do?"
- "List my pages"
- "Extract the Roadmap"
- "Help me extract my database"

### Power User
- "Extract 100 pages from database abc123 using API"
- "Navigate to ProjectX and extract with OCR fallback"
- "Batch extract all pages matching 'report'"
- "Extract with custom output directory ./results"

### Developer
- "Show me the raw extraction result"
- "Extract with verbose logging"
- "Test all navigation methods"
- "Validate extraction against API"

---

**Note**: All these queries work in both one-shot mode and interactive mode. The agent uses context from previous queries when in interactive mode.

