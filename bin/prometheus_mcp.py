# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "prometheus-mcp-server>=1.5.3",
# ]
# ///
"""Prometheus MCP server launcher.

Run with: uv run bin/prometheus_mcp.py
"""

from prometheus_mcp_server.main import run_server

run_server()
