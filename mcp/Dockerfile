# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY mcp/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the MCP server code
COPY mcp/src /app/src

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create a non-root user
RUN useradd -m -u 1000 mcpuser

# Switch to non-root user
USER mcpuser

# Set the entrypoint
ENTRYPOINT ["python3", "-m", "mcp_server.server"]

# Default command (stdio mode)
CMD ["--stdio"]

# Health check (basic: server responds to a simple command)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('localhost', 0))" || exit 1
