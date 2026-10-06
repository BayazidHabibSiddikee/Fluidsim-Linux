# Deployment Guide

## Overview

This guide covers installing and running the FluidSim MCP server in production.

## 1. pip Package Installation

```bash
# Install the package
pip install -e /path/to/FluidSim-Linux/mcp/

# Verify installation
mcp-fluidsim --help
```

## 2. Docker Deployment

### Build the image

```bash
cd mcp
docker build -t fluidsim-mcp .
```

### Run the container

```bash
# Run in a container
docker run -i --rm fluidsim-mcp
```

### Docker Compose

```yaml
# docker-compose.yml
version: "3.8"
services:
  fluidsim-mcp:
    build: .
    image: fluidsim-mcp:latest
    restart: unless-stopped
    # Optional volume mount for saving circuits
    volumes:
      - ./circuits:/app/circuits
    # Optional environment variables
    environment:
      - PYTHONUNBUFFERED=1
```

```bash
docker-compose up -d
```

## 3. systemd Service

### Install the service

```bash
sudo cp mcp/systemd/mcp-fluidsim.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mcp-fluidsim
sudo systemctl start mcp-fluidsim
```

### Configure

```bash
sudo systemctl edit mcp-fluidsim
```

Add environment variables:

```ini
[Service]
Environment=PYTHONUNBUFFERED=1
```

### Manage the service

```bash
# Check status
sudo systemctl status mcp-fluidsim

# View logs
journalctl -u mcp-fluidsim -f

# Restart
sudo systemctl restart mcp-fluidsim

# Stop
sudo systemctl stop mcp-fluidsim
```

## 4. Client Configuration

### Claude Desktop / MCP-compatible clients

```json
{
  "mcpServers": {
    "fluidsim": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/FluidSim-Linux/mcp"
    }
  }
}
```

### For Docker-based setup

```json
{
  "mcpServers": {
    "fluidsim": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "fluidsim-mcp"]
    }
  }
}
```

## 5. Monitoring and Logging

### systemd logs

```bash
journalctl -u mcp-fluidsim -f
```

### Docker logs

```bash
docker logs -f fluidsim-mcp
```

### Application logging

The MCP server prints status messages to stdout/stderr. Configure your logging system to capture these.

## 6. Security Notes

1. **No network exposure**: The server runs in stdio mode, so no ports are exposed
2. **File permissions**: Ensure the user running the server has appropriate permissions for circuit files
3. **Input validation**: All tool inputs are validated before processing
4. **Error messages**: No sensitive information is leaked in error messages

## 7. Updating

### pip

```bash
pip install -U fluidsim-mcp
```

### Docker

```bash
docker pull fluidsim-mcp:latest
docker run -i --rm fluidsim-mcp
```

### systemd

```bash
sudo systemctl stop mcp-fluidsim
sudo systemctl disable mcp-fluidsim
# Update the code
sudo systemctl enable mcp-fluidsim
sudo systemctl start mcp-fluidsim
```
