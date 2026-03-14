# log_server.py
# Copyright (c) 2025 Gezine
# Licensed under the MIT License. See Extra/Licenses/LICENSE-Y2JB

#!/usr/bin/env python3
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

ESCAPE_SEQUENCE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def sanitize_log(message):
    return ESCAPE_SEQUENCE_RE.sub("", message)


class LogHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default HTTP logging

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        log_msg = self.rfile.read(length).decode("utf-8")
        sanitized = sanitize_log(log_msg)
        print(sanitized, flush=True)

        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


print("Logger listening on port 8080...")
HTTPServer(("0.0.0.0", 8080), LogHandler).serve_forever()
