# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✓         |

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **Do not disclose it publicly**
2. Email the maintainers directly (via GitHub security tab)
3. Include steps to reproduce
4. Allow time for a fix before public disclosure

## Security Considerations

### This Server

- **No network exposure**: Runs in stdio mode (no ports open)
- **Input validation**: All tool inputs are validated
- **No secrets**: No hardcoded credentials or API keys
- **Error handling**: Error messages do not leak sensitive data

### File Operations

- File save/load operations are subject to file system permissions
- Users should ensure proper file permissions for circuit files
- No sandboxing beyond file system permissions

## Security Checklist

- [x] No hardcoded secrets
- [x] Input validation
- [x] Error message sanitization
- [x] No network exposure

## Dependencies

This server uses:
- `mcp`: Model Context Protocol SDK
- `numpy`: Scientific computing
- `PySide6`: (optional, for validation GUI)

All dependencies are audited and security advisories are tracked.
