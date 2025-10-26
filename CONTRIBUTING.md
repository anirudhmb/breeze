# Contributing to Breeze Trading Client

Thank you for your interest in contributing! This project is currently in initial development (v1.0).

## Development Status

**Current Version:** 1.0 (In Development)

Contributions will be welcome after the v1.0 release. For now, please:
- Report bugs via GitHub Issues
- Suggest features via GitHub Issues
- Share feedback on the design

## Future Contribution Guidelines

After v1.0 release, we'll accept:
- Bug fixes
- Feature enhancements
- Documentation improvements
- Example scripts
- Test coverage improvements

## Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd breeze

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linter
flake8 breeze_client/
black breeze_client/
mypy breeze_client/
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public methods
- Keep functions focused and small
- Write tests for new features

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write/update tests
5. Ensure all tests pass
6. Update documentation
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Testing

All PRs must:
- Pass all existing tests
- Include tests for new functionality
- Maintain >80% code coverage
- Pass linting (flake8, black, mypy)

## Documentation

All PRs must:
- Update relevant documentation
- Include docstrings for new methods
- Add examples for new features
- Update CHANGELOG.md

## Questions?

Feel free to open an issue for discussion before starting work on a major feature.

---

Thank you for helping make Breeze Trading Client better! 🚀

