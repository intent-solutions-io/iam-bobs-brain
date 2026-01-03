# Contributing to Bob's Brain Templates

Thank you for your interest in improving these multi-agent pattern templates!

## How to Contribute

### Reporting Issues

1. Check existing issues first
2. Create a new issue with:
   - Template name
   - Description of the problem
   - Steps to reproduce
   - Expected vs actual behavior

### Improving Templates

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Submit a pull request

## Template Standards

### Directory Structure

Each template must have:
```
template_name/
├── README.md           # Required: Pattern documentation
├── workflow.py         # Required: Reusable workflow factory
├── example.py          # Required: Runnable example
└── requirements.txt    # Optional: Additional dependencies
```

### README.md Requirements

- Pattern overview with ASCII diagram
- "When to Use" section
- Implementation code example
- "Key Requirements" section
- References to Google ADK docs

### workflow.py Requirements

- Clear docstrings with Args/Returns
- Factory functions (not classes)
- `__all__` export list
- Example workflow at the bottom

### example.py Requirements

- Runnable without ADK installed (for demo)
- Shows pattern structure
- Prints execution instructions

## Code Style

- Follow PEP 8
- Use type hints
- Keep functions focused
- Prefer composition over inheritance

## Testing

Before submitting:
```bash
# Check syntax
python -m py_compile templates/*/workflow.py

# Run examples
python templates/sequential_workflow/example.py
python templates/parallel_workflow/example.py
python templates/quality_gates/example.py
python templates/foreman_worker/example.py
python templates/human_approval/example.py
```

## Documentation

When updating templates:
1. Update the template's README.md
2. Update PATTERNS.md if pattern behavior changes
3. Update the main templates/README.md

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 license.
