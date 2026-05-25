"""Isolate test logs from project logs/monitor.log (must run before src imports)."""

import os
import tempfile

_test_dir = tempfile.mkdtemp(prefix='em_pytest_')
os.environ['LOG_FILE_PATH'] = os.path.join(_test_dir, 'monitor.log')
os.environ['ERROR_LOG_FILE_PATH'] = os.path.join(_test_dir, 'error.log')
