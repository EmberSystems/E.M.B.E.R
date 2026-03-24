#!/usr/bin/env python3

import sys
import os
import time
import socket
import json
import hashlib
import random
import string
import platform
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.command.parser import CommandParser
from core.command.router import CommandRouter
from core.managers.session_manager import SessionManager
from core.managers.payload_manager import PayloadManager
from core.managers.exploit_manager import ExploitManager
from core.managers.log_manager import LogManager
from core.managers.device_manager import DeviceManager
from core.utils.format_utils import FormatUtils


class EMBERUI:
    VERSION = "2.0.0"
    BUILD = "alpha"

    def __init__(self):
        self.session_manager = SessionManager()
        self.payload_manager = PayloadManager(self.session_manager)
        self.exploit_manager = ExploitManager()
        self.log_manager = LogManager()
        self.device_manager = DeviceManager()

        self.parser = CommandParser()
        self.router = CommandRouter(
            self.session_manager,
            self.payload_manager,
            self.exploit_manager,
            self.log_manager,
            self.device_manager,
        )

        self.log_output: List[str] = []
        self.target_ip = ""
        self.target_port = 9000
        self.logging_port = 9090
        self.logserver_pid = None
        self.current_exploit = None
        self.last_payload = None
        self.debug_mode = False
        self.unsafe_mode = False
        self.logs_paused = False

        self._generate_session_id()

    def _generate_session_id(self):
        while True:
            sid = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
            if sid != self.session_manager.get_session_id():
                self.session_id = sid
                break

    def get_target_info(self) -> Dict[str, Any]:
        return {
            "ip": self.target_ip,
            "port": self.target_port,
            "connected": self.device_manager.is_connected(),
            "firmware": self.device_manager.get_firmware()
            if self.device_manager.is_connected()
            else "Unknown",
        }

    def get_sync_info(self) -> Dict[str, Any]:
        return {
            "luac0re": {
                "repo": "https://github.com/Gezine/luac0re.git",
                "latest": "unknown",
            },
            "y2jb": {"repo": "https://github.com/Gezine/Y2JB.git", "latest": "unknown"},
        }

    def get_about_info(self) -> Dict[str, Any]:
        return {
            "os": platform.system() + " " + platform.release(),
            "logging_port": self.logging_port,
            "target_ip": self.target_ip or "Not set",
            "target_port": self.target_port,
            "author": "foxinwinter",
            "repo": "https://github.com/EmberSystems/E.M.B.E.R",
            "version": self.VERSION,
            "build": self.BUILD,
        }

    def add_log(self, message: str):
        if not self.logs_paused:
            timestamp = FormatUtils.timestamp()
            self.log_output.append(f"[{self.session_id}] {message}")
            if len(self.log_output) > 100:
                self.log_output.pop(0)

    def get_payload_list(self) -> List[str]:
        if not self.current_exploit:
            return []
        return self.payload_manager.get_payloads_for_exploit(self.current_exploit)

    def get_status_info(self) -> Dict[str, Any]:
        return {
            "state": "Connected"
            if self.device_manager.is_connected()
            else "Not Connected",
            "log_server": f"Running ({self.logserver_pid})"
            if self.logserver_pid
            else "Stopped",
            "last_sent_payload": self.last_payload or "None",
            "last_action": self.session_manager.get_last_action() or "None",
        }


class TerminalUI:
    def __init__(self, ui: EMBERUI):
        self.ui = ui
        self.width = 120

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def render_log_output(self) -> str:
        lines = [FormatUtils.header(" /Log Output")]
        for log in self.ui.log_output[-20:]:
            lines.append(f"  {log}")
        return "\n".join(lines)

    def render_status(self) -> str:
        status = self.ui.get_status_info()
        lines = [
            FormatUtils.header(" /Status"),
            f"  State: {status['state']}",
            f"  Log Server: {status['log_server']}",
            f"  Last Sent Payload: {status['last_sent_payload']}",
            f"  Last Action: {status['last_action']}",
            "",
            FormatUtils.header(" /Quick-Actions"),
            "  --- Logging ---",
            "  [Pause Logs]  [Clear Logs]",
            "  --- Session ---",
            "  [Kill Session]  [Reconnect]",
            "  [Refetch Target Info]  [Enable Debug Mode]",
            "  --- Payload ---",
            "  [Resend Last Payload]  [Refresh Payload List]",
            "  [Enable Unsafe Mode]",
        ]
        return "\n".join(lines)

    def render_sync(self) -> str:
        sync = self.ui.get_sync_info()
        lines = [
            FormatUtils.header(" /Sync"),
            f"  Payloads: Loaded",
            f"  Luac0re: {sync['luac0re']['latest']}",
            f"  Y2JB: {sync['y2jb']['latest']}",
        ]
        return "\n".join(lines)

    def render_about(self) -> str:
        about = self.ui.get_about_info()
        lines = [
            FormatUtils.header(" /About"),
            FormatUtils.header(" --- Host ---"),
            f"  OS: {about['os']}",
            f"  Logging Port: {about['logging_port']}",
            "",
            FormatUtils.header(" --- Target ---"),
            f"  Target IP: {about['target_ip']}",
            f"  Target Port: {about['target_port']}",
            "",
            FormatUtils.header(" --- E.M.B.E.R ---"),
            f"  Version: {about['version']}",
            f"  Build: {about['build']}",
            "",
            FormatUtils.header(" --- Info ---"),
            f"  Developer: {about['author']}",
            f"  Repo: {about['repo']}",
        ]
        return "\n".join(lines)

    def render_payload_explorer(self) -> str:
        payloads = self.ui.get_payload_list()
        lines = [FormatUtils.header(" /Payload Explorer")]

        if not payloads:
            lines.append("  No payloads loaded")
        else:
            for p in payloads:
                lines.append(f"  {p} [send] [edit]")
        return "\n".join(lines)

    def render_command_prompt(self) -> str:
        lines = [
            FormatUtils.header(" /Command Prompt"),
            "  > list exploits",
            "  Exploit: Luac0re",
            "  Exploit: Y2JB",
            "  > select exploit Luac0re",
            "  > start logserver",
        ]
        return "\n".join(lines)

    def render(self):
        log = self.render_log_output()
        status = self.render_status()
        sync = self.render_sync()
        about = self.render_about()
        payload = self.render_payload_explorer()
        command = self.render_command_prompt()

        lines = [
            f"╔{'═' * 78}╗╔{'═' * 26}╗╔{'═' * 25}╗",
            f"║ /Logs{' ' * 71}║║ /Status{' ' * 18}║║ /Sync{' ' * 17}║",
            f"╟{'─' * 78}╢╟{'─' * 26}╢╟{'─' * 25}╢",
        ]

        log_lines = log.split("\n")
        status_lines = status.split("\n")
        sync_lines = sync.split("\n")

        max_lines = max(len(log_lines), len(status_lines), len(sync_lines))

        for i in range(max_lines):
            l = log_lines[i] if i < len(log_lines) else ""
            s = status_lines[i] if i < len(status_lines) else ""
            sy = sync_lines[i] if i < len(sync_lines) else ""
            lines.append(f"║ {l:<76} ║ {s:<24} ║ {sy:<23} ║")

        lines.append(f"╟{'─' * 78}╢╟{'─' * 26}╢╟{'─' * 25}╢")

        about_lines = about.split("\n")
        payload_lines = payload.split("\n")

        max_lines = max(len(about_lines), len(payload_lines))

        for i in range(max_lines):
            a = about_lines[i] if i < len(about_lines) else ""
            p = payload_lines[i] if i < len(payload_lines) else ""
            lines.append(f"║ {a:<76} ║ {p:<23} ║")

        lines.append(f"╚{'═' * 78}╝╚{'═' * 26}╝╚{'═' * 25}╝")

        lines.append("")
        lines.append(
            "╔════════════════════════════════════════════════════════════════════════════════════════╗"
        )
        lines.append(
            "║ /Command Prompt                                                                      ║"
        )
        lines.append(
            "╟────────────────────────────────────────────────────────────────────────────────────────╢"
        )

        command_lines = command.split("\n")
        for cl in command_lines:
            lines.append(f"║ {cl:<96} ║")

        lines.append(
            "╚════════════════════════════════════════════════════════════════════════════════════════╝"
        )

        return "\n".join(lines)


class EMBERApplication:
    def __init__(self):
        self.ui = EMBERUI()
        self.term = TerminalUI(self.ui)
        self.command_history = []
        self.history_index = -1

    def execute_command(self, cmd: str):
        if not cmd.strip():
            return

        self.command_history.append(cmd)
        self.history_index = len(self.command_history)

        self.ui.add_log(f"> {cmd}")

        try:
            parsed = self.ui.parser.parse(cmd)
            result = self.ui.router.route(parsed)
            if result:
                self.ui.add_log(result)
        except Exception as e:
            self.ui.add_log(f"Error: {str(e)}")

    def run(self):
        print(
            f"{FormatUtils.header('E.M.B.E.R v' + self.ui.VERSION)} - Exploit Management, Backup, and Execution Router"
        )
        print(f"Session ID: {self.ui.session_id}")
        print()

        while True:
            try:
                print(self.term.render())
                cmd = input(f"{FormatUtils.prompt('> ')}").strip()
                if cmd.lower() in ["exit", "quit", "shutdown"]:
                    print("Shutting down...")
                    break
                self.execute_command(cmd)
            except KeyboardInterrupt:
                print("\nExiting E.M.B.E.R...")
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    try:
        app = EMBERApplication()
        app.run()
    except KeyboardInterrupt:
        print("\nExiting E.M.B.E.R...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
