# Contributing to AI-Powered Kubernetes SRE Agent

Thank you for your interest in contributing! This project is open to contributions from the community.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/synerax-cloud/iamsre-agent/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, K8s version, etc.)
   - Relevant logs

### Suggesting Features

1. Check existing [Issues](https://github.com/synerax-cloud/iamsre-agent/issues) for similar requests
2. Create a new issue with:
   - Clear use case description
   - Proposed solution (if any)
   - Alternative solutions considered

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass
6. Update documentation
7. Commit with clear messages
8. Push to your fork
9. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/iamsre-agent.git
cd iamsre-agent

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies for all services
cd backend && pip install -r requirements.txt && cd ..
cd ai-engine && pip install -r requirements.txt && cd ..
cd collector && pip install -r requirements.txt && cd ..
cd executor && pip install -r requirements.txt && cd ..

# Start local development environment
docker-compose up -d
```

## Code Style

- **Python**: Follow PEP 8, use `black` for formatting, `pylint` for linting
- **Terraform**: Use `terraform fmt`
- **YAML**: 2-space indentation
- **Commit Messages**: Use conventional commits format
  - `feat: add new feature`
  - `fix: resolve bug`
  - `docs: update documentation`
  - `refactor: restructure code`
  - `test: add tests`

## Testing

```bash
# Run tests for a specific service
cd backend
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for system design changes
- Add inline comments for complex logic
- Update API documentation in docstrings

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
