import io
import sys
import os
import json
import logging
from flask import Flask, g, session

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.utils.logging_config import setup_observability, wash_data, JSONFormatter, RequestContextFilter

def run_observability_tests():
    print("--- Running Observability & Structured Logging Tests ---")
    
    # 1. Test wash_data (Data Washing)
    print("Testing: Data Washing (wash_data)")
    
    dirty_dict = {
        "username": "admin",
        "password": "secret_password_123",
        "nested": {
            "token": "api-token-value-XYZ",
            "api_key": "some-api-key"
        },
        "safe_list": [
            {"password_hash": "hash_123_456"},
            {"client_secret": "client_secret_789"}
        ]
    }
    
    clean_dict = wash_data(dirty_dict)
    assert clean_dict["password"] == "[REDACTED]"
    assert clean_dict["nested"]["token"] == "[REDACTED]"
    assert clean_dict["nested"]["api_key"] == "[REDACTED]"
    assert clean_dict["safe_list"][0]["password_hash"] == "[REDACTED]"
    assert clean_dict["safe_list"][1]["client_secret"] == "[REDACTED]"
    assert clean_dict["username"] == "admin"
    
    dirty_str = "Error during auth with password 'pass123' and token 'abc-xyz'."
    clean_str = wash_data(dirty_str)
    assert "[REDACTED]" in clean_str
    assert "pass123" not in clean_str
    assert "abc-xyz" not in clean_str
    
    dirty_json_str = json.dumps({"password": "xyz", "safe": 123})
    clean_json_str = wash_data(dirty_json_str)
    clean_parsed = json.loads(clean_json_str)
    assert clean_parsed["password"] == "[REDACTED]"
    assert clean_parsed["safe"] == 123

    print("Data Washing tests passed.")

    # 2. Test JSON Formatter & RequestContextFilter
    print("Testing: JSON Formatter and Filter")
    
    app = Flask("test_observability_app")
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key-123'
    
    # Build a custom log stream to capture output
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    handler.addFilter(RequestContextFilter())
    handler.setFormatter(JSONFormatter())
    
    test_logger = logging.getLogger("test_context_logger")
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.DEBUG)
    test_logger.propagate = False  # Avoid printing to main stderr
    
    # Logging outside request context
    test_logger.info("Message outside request context", extra={"extra_field": "hello"})
    
    log_stream.seek(0)
    lines = log_stream.getvalue().strip().split('\n')
    assert len(lines) == 1
    log_data = json.loads(lines[0])
    
    assert log_data["message"] == "Message outside request context"
    assert log_data["level"] == "info"
    assert log_data["request_id"] == "-"
    assert log_data["user_id"] == "-"
    assert log_data["metadata"]["extra_field"] == "hello"
    
    # Logging inside request context
    log_stream.truncate(0)
    log_stream.seek(0)
    
    with app.test_request_context(path="/test-route", method="POST", headers={"X-Request-ID": "test-req-id"}):
        # Emulate Flask hooks
        g.request_id = "test-req-id"
        g.log_action = "test_endpoint"
        session["user_id"] = 42
        session["company_id"] = 99
        
        test_logger.warning("Message inside request context with password 'unsafe_password'")
        
        # Test fatal log mapping
        test_logger.critical("Fatal system error!")

    log_stream.seek(0)
    lines = log_stream.getvalue().strip().split('\n')
    assert len(lines) == 2
    
    # Verify warning log (with context & sanitization)
    warn_log = json.loads(lines[0])
    assert warn_log["level"] == "warn"  # Mapped from warning
    assert warn_log["request_id"] == "test-req-id"
    assert warn_log["user_id"] == 42
    assert warn_log["company_id"] == 99
    assert warn_log["action"] == "test_endpoint"
    assert warn_log["http"]["method"] == "POST"
    assert warn_log["http"]["url"] == "/test-route"
    assert "unsafe_password" not in warn_log["message"]
    assert "[REDACTED]" in warn_log["message"]
    
    # Verify critical log (mapped to fatal)
    fatal_log = json.loads(lines[1])
    assert fatal_log["level"] == "fatal"  # Mapped from critical
    assert fatal_log["message"] == "Fatal system error!"
    assert fatal_log["request_id"] == "test-req-id"
    
    print("JSON Formatter and Filter tests passed.")
    
    # 3. Test setup_observability works on app
    print("Testing: setup_observability integration")
    setup_observability(app)
    
    # Verify that before/after request handlers are registered
    assert len(app.before_request_funcs.get(None, [])) >= 1
    assert len(app.after_request_funcs.get(None, [])) >= 1
    print("setup_observability integration tests passed.")
    
    print("--- All Observability & Logging tests passed successfully! ---")

if __name__ == '__main__':
    run_observability_tests()
