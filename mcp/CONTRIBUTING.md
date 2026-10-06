# Contributing to FluidSim MCP Server

Thank you for your interest in contributing! This document outlines how to get started.

## Development Setup

1. **Clone the repository:**

```bash
git clone https://github.com/BayazidHabibSiddikee/Fluidsim-Linux.git
cd FluidSim-Linux
```

2. **Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -e mcp/ -r mcp/requirements.txt
```

4. **Run tests:**

```bash
cd mcp
python test_basic.py
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Keep functions small (<50 lines)
- Add docstrings to all public methods
- Use descriptive variable names

## Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests** for new functionality
5. **Ensure all tests pass**
6. **Update documentation**
7. **Submit a pull request**

## Adding New Tools

1. Add the tool definition in `server.py`
2. Create handler function in the appropriate module
3. Add documentation in `docs/API_REFERENCE.md`
4. Add tests in `mcp/tests/`
5. Update `README.md` if the tool is user-facing

## Reporting Issues

- Use the GitHub issue tracker
- Include Python version and OS
- Provide reproduction steps
- Include error messages and logs
