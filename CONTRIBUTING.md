# Contributing to Notion AX Extractor

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/actioner-test.git
   cd actioner-test
   ```
3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8
   ```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests:
   ```bash
   pytest
   ```

4. Format code:
   ```bash
   black src/
   ```

5. Lint code:
   ```bash
   flake8 src/
   ```

6. Commit changes:
   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

7. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

8. Create a Pull Request

## Code Style

- Follow PEP 8 style guidelines
- Use Black for code formatting
- Maximum line length: 88 characters (Black default)
- Use type hints where appropriate
- Write docstrings for all public functions and classes

### Example Function

```python
def extract_page(
    self,
    use_ocr: bool = True,
    scroll_delay: float = 0.3,
    max_scrolls: int = 100
) -> ExtractionResult:
    """Extract content from the current page.
    
    Args:
        use_ocr: Whether to use OCR for inaccessible elements
        scroll_delay: Delay between scroll actions (seconds)
        max_scrolls: Maximum number of scroll iterations
        
    Returns:
        ExtractionResult with all extracted blocks
    """
    # Implementation
```

## Testing

### Writing Tests

- Place tests in the `tests/` directory
- Test files should start with `test_`
- Test classes should start with `Test`
- Test functions should start with `test_`

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_extractor.py

# Run specific test
pytest tests/test_extractor.py::TestBlock::test_block_creation
```

### Test Example

```python
import pytest
from src.notion.extractor import Block

class TestBlock:
    def test_block_creation(self):
        """Test block creation with default values."""
        block = Block(content="Test content")
        assert block.content == "Test content"
        assert block.block_type == "text"
```

## Adding Features

### Before You Start

- Check existing issues to avoid duplicates
- Open an issue to discuss major changes
- Ensure the feature aligns with project goals

### Implementation Checklist

- [ ] Write tests first (TDD)
- [ ] Implement the feature
- [ ] Add docstrings
- [ ] Update README if needed
- [ ] Add usage examples
- [ ] Run all tests
- [ ] Format and lint code

## Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Detailed steps to reproduce
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:
   - macOS version
   - Python version
   - Notion app version
6. **Logs**: Relevant log output (use `--verbose`)

### Bug Report Template

```markdown
**Description**
Brief description of the bug

**Steps to Reproduce**
1. Step one
2. Step two
3. Step three

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- macOS: 13.0
- Python: 3.10.5
- Notion: 2.0.30

**Logs**
```
Paste relevant logs here
```
```

## Feature Requests

When requesting features, please include:

1. **Use Case**: Why is this feature needed?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other solutions you've considered
4. **Additional Context**: Any other relevant information

## Pull Request Guidelines

### Before Submitting

- Ensure all tests pass
- Add tests for new functionality
- Update documentation
- Follow code style guidelines
- Keep commits atomic and well-described

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added
- [ ] Manually tested

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

## Project Structure

```
actioner-test/
├── src/
│   ├── ax/              # Accessibility layer
│   ├── notion/          # Notion-specific logic
│   ├── ocr/             # OCR fallback
│   ├── validation/      # API validation
│   ├── output/          # Export handlers
│   ├── cli.py           # CLI interface
│   ├── errors.py        # Error handling
│   └── main.py          # Entry point
├── tests/               # Test suite
├── requirements.txt     # Dependencies
└── README.md           # Documentation
```

## Areas for Contribution

We especially welcome contributions in these areas:

1. **Testing**: More comprehensive test coverage
2. **Documentation**: Improved examples and guides
3. **Performance**: Optimization of extraction speed
4. **Features**: New extraction capabilities
5. **Bug Fixes**: Resolving open issues
6. **Compatibility**: Support for different Notion versions

## Questions?

- Open an issue for questions
- Tag with `question` label
- Provide context and what you've tried

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in the README. Thank you for helping improve this project!

