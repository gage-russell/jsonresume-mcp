"""
Middleware for ResumeJSON-MCP server.

Provides logging and monitoring for tool calls and other server operations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Sequence
from resumejson_mcp.constants import (
    SEPARATOR_LENGTH,
    STRING_TRUNCATE_PREVIEW,
    STRING_TRUNCATE_LINE,
    MS_PER_SECOND,
)
from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
from fastmcp.tools import Tool, ToolResult
import mcp.types as mt

# Configure logging
logger = logging.getLogger("resumejson_mcp")


class LoggingMiddleware(Middleware):
    """Middleware that logs all tool calls for debugging and monitoring.
    
    Logs include:
    - Tool name and arguments
    - Execution time
    - Success/failure status
    - Result summary
    
    Logs are written to ~/.hire-me/logs/tool_calls.log
    """
    
    def __init__(self, log_dir: Path | None = None, verbose: bool = False):
        """Initialize the logging middleware.
        
        Args:
            log_dir: Directory for log files. Defaults to ~/.hire-me/logs
            verbose: If True, log full arguments and results. If False, summarize.
        """
        self.log_dir = log_dir or Path.home() / ".hire-me" / "logs"
        self.verbose = verbose
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up the file logger."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir / "tool_calls.log"
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            logger.addHandler(file_handler)
            logger.setLevel(logging.INFO)
    
    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Log tool calls with timing and result info."""
        params = context.params
        tool_name = params.name
        arguments = params.arguments or {}
        
        # Start timing
        start_time = datetime.now()
        
        # Log the call
        args_summary = self._summarize_args(arguments)
        logger.info(f"CALL | {tool_name} | args: {args_summary}")
        
        try:
            # Execute the tool
            result = await call_next(context)
            
            # Calculate duration
            duration_ms = (datetime.now() - start_time).total_seconds() * MS_PER_SECOND
            
            # Log success
            result_summary = self._summarize_result(result)
            logger.info(f"OK   | {tool_name} | {duration_ms:.0f}ms | {result_summary}")
            
            return result
            
        except Exception as e:
            # Calculate duration
            duration_ms = (datetime.now() - start_time).total_seconds() * MS_PER_SECOND
            
            # Log failure
            logger.error(f"FAIL | {tool_name} | {duration_ms:.0f}ms | {type(e).__name__}: {str(e)[:100]}")
            
            raise
    
    def _summarize_args(self, arguments: dict) -> str:
        """Create a summary of tool arguments."""
        if not arguments:
            return "(no args)"
        
        if self.verbose:
            return json.dumps(arguments, default=str)
        
        # Summarize each argument
        parts = []
        for key, value in list(arguments.items())[:3]:
            if isinstance(value, str) and len(value) > STRING_TRUNCATE_PREVIEW:
                parts.append(f"{key}={value[:STRING_TRUNCATE_PREVIEW]}...")
            elif isinstance(value, (list, dict)):
                parts.append(f"{key}=<{type(value).__name__}:{len(value)}>")
            else:
                parts.append(f"{key}={value}")
        
        if len(arguments) > 3:
            parts.append(f"(+{len(arguments) - 3} more)")
        
        return ", ".join(parts)
    
    def _summarize_result(self, result: ToolResult) -> str:
        """Create a summary of tool result."""
        if not result.content:
            return "(empty)"
        
        # Get first text content
        for item in result.content:
            if hasattr(item, "text"):
                text = item.text
                if self.verbose:
                    return text[:500]
                # Return first line or truncate
                first_line = text.split("\n")[0]
                if len(first_line) > 80:
                    return first_line[:80] + "..."
                return first_line
        
        return f"({len(result.content)} content items)"
    
    async def on_initialize(
        self,
        context: MiddlewareContext[mt.InitializeRequest],
        call_next: CallNext[mt.InitializeRequest, mt.InitializeResult | None],
    ) -> mt.InitializeResult | None:
        """Log server initialization."""
        logger.info("INIT | Server initializing")
        
        result = await call_next(context)
        
        logger.info("INIT | Server initialized successfully")
        
        return result
    
    async def on_list_tools(
        self,
        context: MiddlewareContext[mt.ListToolsRequest],
        call_next: CallNext[mt.ListToolsRequest, Sequence[Tool]],
    ) -> Sequence[Tool]:
        """Log tool listing requests."""
        result = await call_next(context)
        
        logger.info(f"LIST | Tools requested | {len(result)} tools available")
        
        return result


class MetricsMiddleware(Middleware):
    """Middleware that tracks tool usage metrics.
    
    Maintains counts of:
    - Tool calls per tool name
    - Success/failure rates
    - Average execution times
    
    Metrics are persisted to disk for analysis.
    """
    
    def __init__(self, metrics_dir: Path | None = None):
        """Initialize the metrics middleware.
        
        Args:
            metrics_dir: Directory for metrics files. Defaults to ~/.hire-me/metrics
        """
        self.metrics_dir = metrics_dir or Path.home() / ".hire-me" / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.metrics_dir / "tool_metrics.json"
        self._load_metrics()
    
    def _load_metrics(self) -> None:
        """Load existing metrics from disk."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file) as f:
                    self.metrics = json.load(f)
            except Exception:
                self.metrics = {}
        else:
            self.metrics = {}
    
    def _save_metrics(self) -> None:
        """Save metrics to disk."""
        try:
            with open(self.metrics_file, "w") as f:
                json.dump(self.metrics, f, indent=2)
        except Exception:
            pass  # Don't fail on metrics save
    
    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Track tool call metrics."""
        tool_name = context.params.name
        start_time = datetime.now()
        
        # Initialize tool metrics if needed
        if tool_name not in self.metrics:
            self.metrics[tool_name] = {
                "calls": 0,
                "successes": 0,
                "failures": 0,
                "total_time_ms": 0,
            }
        
        self.metrics[tool_name]["calls"] += 1
        
        try:
            result = await call_next(context)
            
            # Record success
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics[tool_name]["successes"] += 1
            self.metrics[tool_name]["total_time_ms"] += duration_ms
            
            self._save_metrics()
            return result
            
        except Exception as e:
            # Record failure
            self.metrics[tool_name]["failures"] += 1
            self._save_metrics()
            raise
    
    def get_summary(self) -> str:
        """Get a formatted summary of metrics."""
        if not self.metrics:
            return "No metrics recorded yet."
        
        lines = ["📊 TOOL METRICS SUMMARY", "=" * SEPARATOR_LENGTH]
        
        # Sort by call count
        sorted_tools = sorted(
            self.metrics.items(),
            key=lambda x: x[1]["calls"],
            reverse=True
        )
        
        for tool_name, data in sorted_tools[:20]:
            calls = data["calls"]
            avg_time = data["total_time_ms"] / calls if calls > 0 else 0
            success_rate = (data["successes"] / calls * 100) if calls > 0 else 0
            
            lines.extend([
                f"\n{tool_name}",
                f"  Calls: {calls} | Success: {success_rate:.0f}% | Avg: {avg_time:.0f}ms"
            ])
        
        return "\n".join(lines)
