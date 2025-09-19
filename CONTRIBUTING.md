# Contributing to PC Maintenance Dashboard

Thank you for your interest in contributing to PC Maintenance Dashboard! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.7 or higher
- Git
- Basic knowledge of PyQt5 and Python

### Setting Up Development Environment

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/pc-maintenance-dashboard.git
   cd pc-maintenance-dashboard
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]  # Install development dependencies
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## 🔧 Development Guidelines

### Code Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines
- Use meaningful variable and function names
- Add docstrings for all functions and classes
- Keep functions small and focused
- Use type hints where appropriate

### Code Formatting
We use `black` for code formatting:
```bash
black .
```

### Linting
We use `flake8` for linting:
```bash
flake8 .
```

### Project Structure
```
pc-maintenance-dashboard/
├── main.py                 # Application entry point
├── main_window_simple.py   # Main GUI implementation
├── performance_benchmark.py # Benchmark system
├── system_utils.py         # System monitoring utilities
├── browser_cleaner.py      # Browser cleanup functionality
├── duplicate_finder.py     # Duplicate file detection
├── themes.py              # UI theme management
├── version.py             # Version information
├── requirements.txt       # Dependencies
├── setup.py              # Package setup
├── tests/                # Test files
└── docs/                 # Documentation
```

## 🐛 Bug Reports

When filing a bug report, please include:

1. **Environment Information**
   - Operating System and version
   - Python version
   - PyQt5 version
   - Application version

2. **Steps to Reproduce**
   - Clear, numbered steps
   - Expected behavior
   - Actual behavior

3. **Additional Information**
   - Screenshots (if applicable)
   - Error messages or logs
   - Any relevant system information

## ✨ Feature Requests

Before submitting a feature request:

1. Check if the feature already exists
2. Search existing issues for similar requests
3. Consider if the feature fits the project's scope

When submitting a feature request:
- Provide a clear description of the feature
- Explain the use case and benefits
- Include mockups or examples if applicable

## 🔄 Pull Request Process

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   python -m pytest tests/
   python main.py  # Manual testing
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add: Brief description of changes"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Guidelines
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when applicable

Examples:
- `Add: Performance benchmark export functionality`
- `Fix: Memory leak in system monitoring thread`
- `Update: README with new installation instructions`
- `Refactor: Cleanup worker thread implementation`

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=.

# Run specific test file
python -m pytest tests/test_benchmark.py
```

### Writing Tests
- Place tests in the `tests/` directory
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

## 📚 Documentation

### Code Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include parameter types and return values
- Provide usage examples for complex functions

### README Updates
When adding new features:
- Update the features list
- Add usage examples
- Update screenshots if UI changes

## 🏷️ Release Process

1. Update version in `version.py`
2. Update `CHANGELOG.md` with new features and fixes
3. Create a new release on GitHub
4. Build and upload executables

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help newcomers get started
- Provide constructive feedback
- Follow the code of conduct

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/pc-maintenance-dashboard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/pc-maintenance-dashboard/discussions)
- **Email**: your.email@example.com

## 🎯 Areas for Contribution

We welcome contributions in these areas:

### High Priority
- Performance optimizations
- Bug fixes and stability improvements
- Cross-platform compatibility
- Accessibility improvements

### Medium Priority
- New system monitoring features
- Additional cleanup tools
- UI/UX enhancements
- Documentation improvements

### Low Priority
- New themes and customization options
- Plugin system development
- Internationalization (i18n)
- Mobile companion app

Thank you for contributing to PC Maintenance Dashboard! 🚀
