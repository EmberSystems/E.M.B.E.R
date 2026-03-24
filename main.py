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
import tty
import termios
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
        self.command_history: List[str] = []
        self.target_ip = ""
        self.target_port = 9000
        self.logging_port = 9090
        self.logserver_pid = None
        self.current_exploit = None
        self.last_payload = None
        self.debug_mode = False
        self.unsafe_mode = False
        self.logs_paused = False
        self.exploit_class = ""

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
            "target_ip": self.target_ip or "target-ip",
            "target_port": self.target_port,
            "author": "foxinwinter",
            "repo": "https://github.com/EmberSystems/E.M.B.E.R",
            "version": self.VERSION,
            "build": self.BUILD,
            "exploit_class": self.exploit_class or "class (Webkit, Kernel, Etc.)",
            "current_exploit": self.current_exploit or "Current Selected Exploit",
            "session_uptime": self.session_manager.get_uptime(),
            "connection_time": self.session_manager.get_connection_time(),
        }

    def add_log(self, message: str):
        if not self.logs_paused:
            self.log_output.append(f"[{self.session_id}]: {message}")
            if len(self.log_output) > 50:
                self.log_output.pop(0)

    def add_command(self, command: str):
        self.command_history.append(command)
        if len(self.command_history) > 12:
            self.command_history.pop(0)

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


LOG_WIDTH = 96
STATUS_WIDTH = 26
SYNC_WIDTH = 24
ABOUT_WIDTH = 78
PAYLOAD_WIDTH = 41
CMD_WIDTH = 96

LOG_HEIGHT = 27
STATUS_HEIGHT = 18
SYNC_HEIGHT = 2
ABOUT_HEIGHT = 22
PAYLOAD_HEIGHT = 20
CMD_HEIGHT = 14

CMD_START_ROW = 31


class ANSI:
    CLEAR = "\033[2J"
    HOME = "\033[H"
    SAVE = "\033[s"
    RESTORE = "\033[u"

    @staticmethod
    def move(row: int, col: int) -> str:
        return f"\033[{row};{col}H"

    @staticmethod
    def clear_line() -> str:
        return "\033[K"


class TerminalUI:
    def __init__(self, ui: EMBERUI):
        self.ui = ui
        self.ansi = ANSI()

    def render_log_output(self) -> List[str]:
        lines = self.ui.log_output.copy()
        while len(lines) < 27:
            lines.append("")
        return lines[:27]

    def render_status(self) -> List[str]:
        status = self.ui.get_status_info()
        return [
            f"State: {status['state']}",
            f"Log Server: {status['log_server']}",
            f"Last Sent Payload: {status['last_sent_payload']}",
            f"Last Action: {status['last_action']}",
            "",
            "/Quick-Actions",
            "--- Logging ---",
            "[Pause Logs]",
            "[Clear Logs]",
            "--- Session Mangement ---",
            "[Kill Session",
            "[Reconnect]",
            "[Refetch Target Info]",
            "[Enable Debug Mode]",
            "--- Payload Mangement ---",
            "[Resend Last Payload]",
            "[Refresh Payload List]",
            "[Enable Unsafe Mode]",
        ]

    def render_sync(self) -> List[str]:
        return [
            f"Payloads: Payload Satus (more info in 2)",
            f"Latest Release: check if latest release",
        ]

    def render_about(self) -> List[str]:
        about = self.ui.get_about_info()
        return [
            "--- Host ---",
            f"OS: {about['os']}",
            f"Logging Port: {about['logging_port']}",
            "",
            "--- Target --",
            f"Target IP: {about['target_ip']}",
            f"Target Port: {about['target_port']}",
            f"Author: {about['author']}",
            f"Exploit Class: {about['exploit_class']}",
            f"Current Selected Exploit: {about['current_exploit']}",
            "",
            "--- Session ---",
            f"Session ID: {self.ui.session_id}",
            f"Session Uptime: {about['session_uptime']}",
            f"Connection Time: {about['connection_time']}",
            "",
            "--- E.M.B.E.R ---",
            f"Version: {about['version']}",
            f"Build: {about['build']}",
            "",
            "--- Info ---",
            f"Developer: {about['author']}",
            f"Repo: {about['repo']}",
        ]

    def render_payload_explorer(self) -> List[str]:
        payloads = self.ui.get_payload_list()
        lines = []
        for p in payloads:
            lines.append(f"{p} [send] [edit]")
        while len(lines) < 20:
            lines.append("")
        return lines[:20]

    def render_command_prompt(self) -> List[str]:
        lines = []
        for cmd in self.ui.command_history:
            lines.append(f">{cmd}")
        lines.append(">")
        while len(lines) < 14:
            lines.append("")
        return lines[:14]

    def pad(self, text: str, width: int) -> str:
        if len(text) < width:
            return text + " " * (width - len(text))
        return text[:width]

    def render(self) -> str:
        lines = (
            open(os.path.join(os.path.dirname(__file__), "appearance.txt"))
            .read()
            .split("\n")[:44]
        )

        def pad_to(text: str, length: int) -> str:
            if len(text) < length:
                return text + " " * (length - len(text))
            return text

        replacements = {
            "[Session ID]": self.ui.session_id,
            " State: Connected or Not Connected                ": pad_to(
                f"│ State: {self.ui.get_status_info()['state']}", 51
            ),
            " Log Server: State (PID #)                        ": pad_to(
                f"│ Log Server: {self.ui.get_status_info()['log_server']}", 51
            ),
            " Last Sent Payload:                               ": pad_to(
                f"│ Last Sent Payload: {self.ui.get_status_info()['last_sent_payload']}",
                51,
            ),
            " Last Action: (last ran command)                 ": pad_to(
                f"│ Last Action: {self.ui.get_status_info()['last_action']}", 51
            ),
            "││ --- Host ---": "││ --- Host ---",
            " OS: Detected OS                     ": pad_to(
                f"│ OS: {self.ui.get_about_info()['os']}", 27
            ),
            " Logging Port: Port #               ": pad_to(
                f"│ Logging Port: {self.ui.get_about_info()['logging_port']}", 27
            ),
            "││ --- Target --": "││ --- Target --",
            " Target IP: target-ip               ": pad_to(
                f"│ Target IP: {self.ui.get_about_info()['target_ip']}", 27
            ),
            " Target Port: target-port           ": pad_to(
                f"│ Target Port: {self.ui.get_about_info()['target_port']}", 27
            ),
            " Author: author of exploit          ": pad_to(
                f"│ Author: {self.ui.get_about_info()['author']}", 27
            ),
            " Exploit Class: class (Webkit, Kernel, Etc.)      ": pad_to(
                f"│ Exploit Class: {self.ui.get_about_info()['exploit_class']}", 43
            ),
            " Current Selected Exploit:         ": pad_to(
                f"│ Current Selected Exploit: {self.ui.get_about_info()['current_exploit']}",
                27,
            ),
            "││ --- Session ---": "││ --- Session ---",
            " Session ID: randomly generated 3 letter string   ": pad_to(
                f"│ Session ID: {self.ui.session_id}", 41
            ),
            " Session Uptime: uptime             ": pad_to(
                f"│ Session Uptime: {self.ui.get_about_info()['session_uptime']}", 27
            ),
            " Connection Time: connection-time  ": pad_to(
                f"│ Connection Time: {self.ui.get_about_info()['connection_time']}", 27
            ),
            "││ --- E.M.B.E.R ---": "││ --- E.M.B.E.R ---",
            " Version: ver #                     ": pad_to(
                f"│ Version: {self.ui.get_about_info()['version']}", 27
            ),
            " Build: (build type)                ": pad_to(
                f"│ Build: {self.ui.get_about_info()['build']}", 27
            ),
            "││ --- Info ---": "││ --- Info ---",
            " Developer: foxinwinter             ": pad_to(
                f"│ Developer: {self.ui.get_about_info()['author']}", 27
            ),
            " Repo: https://github.com/EmberSystems/E.M.B.E.R  ": pad_to(
                f"│ Repo: {self.ui.get_about_info()['repo']}", 54
            ),
            " Support: Discord Server Link, or Website": "Support: Discord Server Link, or Website",
        }

        result = []
        for line in lines:
            new_line = line
            for old, new in replacements.items():
                new_line = new_line.replace(old, new)
            result.append(new_line)

        return "\n".join(result)

    def render_without_bottom(self) -> str:
        return self.render()


class EMBERApplication:
    def __init__(self):
        self.ui = EMBERUI()
        self.term = TerminalUI(self.ui)
        self.ansi = ANSI()
        self.history_index = -1
        self.cmd_start_row = CMD_START_ROW

    def execute_command(self, cmd: str):
        if not cmd.strip():
            return

        self.ui.add_command(cmd)

        self.ui.add_log(f"> {cmd}")

        try:
            parsed = self.ui.parser.parse(cmd)
            result = self.ui.router.route(parsed)
            if result:
                self.ui.add_log(result)
                if result == "shutdown":
                    return "shutdown"
        except Exception as e:
            self.ui.add_log(f"Error: {str(e)}")
        return None

    def run(self):
        sys.stdout.write(ANSI.CLEAR + ANSI.HOME)
        sys.stdout.flush()

        print(
            f"{FormatUtils.header('E.M.B.E.R v' + self.ui.VERSION)} - Exploit Management, Backup, and Execution Router"
        )
        print(f"Session ID: {self.ui.session_id}")
        print()

        print(self.term.render_without_bottom())
        sys.stdout.flush()

        while True:
            try:
                self.draw_input_line()
                cmd = self.read_input_line()

                if cmd.lower() in ["exit", "quit", "shutdown"]:
                    print("Shutting down...")
                    break
                result = self.execute_command(cmd)
                if result == "shutdown":
                    break
            except KeyboardInterrupt:
                print("\nExiting E.M.B.E.R...")
                break
            except Exception as e:
                print(f"Error: {e}")

    def draw_input_line(self):
        sys.stdout.write(self.ansi.move(self.cmd_start_row, 3))
        sys.stdout.write(">")
        sys.stdout.write(self.ansi.move(self.cmd_start_row, 4))
        sys.stdout.flush()

    def read_input_line(self) -> str:
        cmd = ""
        old_settings = termios.tcgetattr(sys.stdin)

        try:
            tty.setcbreak(sys.stdin.fileno())
            while True:
                ch = sys.stdin.read(1)
                if not ch:
                    break
                if ch == "\n" or ch == "\r":
                    print()
                    break
                elif ch == "\x7f":
                    if cmd:
                        cmd = cmd[:-1]
                        sys.stdout.write(
                            self.ansi.move(self.cmd_start_row, 4 + len(cmd))
                        )
                        sys.stdout.write(" ")
                        sys.stdout.write(
                            self.ansi.move(self.cmd_start_row, 4 + len(cmd))
                        )
                elif ch == "\x03":
                    raise KeyboardInterrupt()
                elif ch == "\x1b":
                    continue
                else:
                    cmd += ch
                    sys.stdout.write(ch)
                sys.stdout.flush()
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        return cmd.strip()


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
