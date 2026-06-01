"""
PURETEGO CRM - Structured Logging Configuration
Provides JSON formatting, request context tracking, and data washing.
"""

import json
import logging
import uuid
import re
from datetime import datetime
from flask import has_request_context, request, session, g

# Sensitive keys to wash (redact)
SENSITIVE_KEYS = {
    'password', 'password_hash', 'password_confirm', 'confirm_password',
    'token', 'access_token', 'refresh_token', 'client_secret', 'secret',
    'secret_key', 'api_key', 'key', 'serpapi_key', 'serper_api_key',
    'hasdata_api_key', 'mail_password', 'authorization', 'cookie'
}

# Regex to scrub sensitive values in string messages
SENSITIVE_PATTERN = re.compile(
    r'(' + '|'.join(SENSITIVE_KEYS) + r')(\s*(?:[:=]|\bval\b)?\s*)(["\']?)[a-zA-Z0-9_\-\.\:\/\=\+@]{4,}(["\']?)',
    re.IGNORECASE
)

def wash_data(data):
    """
    Recursively redacts sensitive values in dicts, lists, and strings.
    """
    if isinstance(data, dict):
        return {k: wash_data(v) if str(k).lower() not in SENSITIVE_KEYS else "[REDACTED]" for k, v in data.items()}
    elif isinstance(data, list):
        return [wash_data(item) for item in data]
    elif isinstance(data, str):
        # Attempt to clean serialized JSON within strings first
        if (data.startswith('{') and data.endswith('}')) or (data.startswith('[') and data.endswith(']')):
            try:
                parsed = json.loads(data)
                if isinstance(parsed, (dict, list)):
                    return json.dumps(wash_data(parsed))
            except (ValueError, TypeError):
                pass
        # Apply regex to general text strings
        return SENSITIVE_PATTERN.sub(r'\1\2\3[REDACTED]\4', data)
    return data

class RequestContextFilter(logging.Filter):
    """
    Logging filter to inject request context (request_id, user_id, action) into the log record.
    """
    def filter(self, record):
        record.request_id = "-"
        record.user_id = "-"
        record.company_id = "-"
        record.path = "-"
        record.method = "-"
        record.remote_ip = "-"
        record.action = "-"

        if has_request_context():
            # Inject Request ID
            if hasattr(g, 'request_id'):
                record.request_id = g.request_id
            
            # Inject User Context
            if 'user_id' in session:
                record.user_id = session['user_id']
            if 'company_id' in session:
                record.company_id = session['company_id']
                
            # Inject HTTP Metadata
            record.path = request.path
            record.method = request.method
            record.remote_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if record.remote_ip and ',' in record.remote_ip:
                record.remote_ip = record.remote_ip.split(',')[0].strip()
                
            # Inject Custom Action from Route Context if specified
            if hasattr(g, 'log_action'):
                record.action = g.log_action

        return True

class JSONFormatter(logging.Formatter):
    """
    Formatter to output logs in valid JSON format, with automatic field sanitization.
    """
    def format(self, record):
        log_payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname.lower() if record.levelname != "WARNING" else "warn",
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, 'request_id', '-'),
            "user_id": getattr(record, 'user_id', '-'),
            "company_id": getattr(record, 'company_id', '-'),
            "action": getattr(record, 'action', '-'),
            "http": {
                "method": getattr(record, 'method', '-'),
                "url": getattr(record, 'path', '-'),
                "client_ip": getattr(record, 'remote_ip', '-')
            }
        }
        
        # Map critical -> fatal to match professional levels requested
        if log_payload["level"] == "critical":
            log_payload["level"] = "fatal"

        # Capture exception tracebacks if present
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        # Merge extra fields passed in logging (e.g. logger.info("msg", extra={"key": "val"}))
        standard_attrs = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'msg', 'name', 'pathname', 'process', 'processName',
            'relativeCreated', 'stack_info', 'thread', 'threadName',
            'request_id', 'user_id', 'company_id', 'action', 'method', 'path', 'remote_ip'
        }
        
        extra_fields = {k: v for k, v in record.__dict__.items() if k not in standard_attrs}
        if extra_fields:
            log_payload["metadata"] = extra_fields

        # Apply data washing
        sanitized_payload = wash_data(log_payload)

        return json.dumps(sanitized_payload)

def setup_observability(app):
    """
    Configures structured logging and middleware context tracking.
    """
    # 1. Register request hooks to generate/capture Request ID
    @app.before_request
    def start_request():
        g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        g.log_action = request.endpoint or "anonymous_endpoint"
        
    @app.after_request
    def append_response_headers(response):
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        return response

    # 2. Setup standard logging stream handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO if not app.debug else logging.DEBUG)
    
    # Attach filter and formatter
    handler.addFilter(RequestContextFilter())
    handler.setFormatter(JSONFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO if not app.debug else logging.DEBUG)
    
    # Restrict noise from standard libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
