#!/usr/bin/env python3
# core/command/router.py
# Receives parsed command (from parser.py) and decides what handler to call


def route_command(parsed: dict, app_state: dict) -> None:
    command = parsed.get("command")
    args = parsed.get("args", [])

    handlers = {
        "send": "handle_send",
        "start": "handle_start",
        "stop": "handle_stop",
        "clear": "handle_clear",
        "kill": "handle_kill",
        "reconnect": "handle_reconnect",
        "refetch": "handle_refetch",
        "list": "handle_list",
        "select": "handle_select",
        "help": "handle_help",
        "exit": "handle_exit",
        "quit": "handle_quit",
        "debug": "handle_debug",
        "resend": "handle_resend",
        "refresh": "handle_refresh",
        "unsafe": "handle_unsafe",
        "config": "handle_config",
    }

    if command in handlers:
        handler_name = handlers[command]
        return handler_name, args

    return None, args


class CommandRouter:
    def __init__(
        self,
        session_manager,
        payload_manager,
        exploit_manager,
        log_manager,
        device_manager,
    ):
        self.session_manager = session_manager
        self.payload_manager = payload_manager
        self.exploit_manager = exploit_manager
        self.log_manager = log_manager
        self.device_manager = device_manager

    def route(self, parsed: dict) -> str:
        command = parsed.get("command")
        args = parsed.get("args", [])

        handlers = {
            "send": self._handle_send,
            "start": self._handle_start,
            "stop": self._handle_stop,
            "clear": self._handle_clear,
            "kill": self._handle_kill,
            "reconnect": self._handle_reconnect,
            "refetch": self._handle_refetch,
            "list": self._handle_list,
            "select": self._handle_select,
            "help": self._handle_help,
            "exit": self._handle_exit,
            "quit": self._handle_quit,
            "debug": self._handle_debug,
            "resend": self._handle_resend,
            "refresh": self._handle_refresh,
            "unsafe": self._handle_unsafe,
            "config": self._handle_config,
        }

        if command in handlers:
            return handlers[command](args)
        return f"Unknown command: {command}"

    def _handle_send(self, args):
        if not args:
            return "Usage: send <payload>"
        return f"Sending payload: {args[0]}"

    def _handle_start(self, args):
        if not args:
            return "Usage: start <service>"
        return f"Starting: {args[0]}"

    def _handle_stop(self, args):
        if not args:
            return "Usage: stop <service>"
        return f"Stopping: {args[0]}"

    def _handle_clear(self, args):
        return "Logs cleared"

    def _handle_kill(self, args):
        return self.session_manager.kill_session()

    def _handle_reconnect(self, args):
        return "Reconnecting..."

    def _handle_refetch(self, args):
        return "Refetching target info..."

    def _handle_list(self, args):
        if args and args[0] == "exploits":
            exploits = self.exploit_manager.list_exploits()
            return "Available exploits: " + ", ".join(exploits)
        return "Usage: list exploits"

    def _handle_select(self, args):
        if not args:
            return "Usage: select <exploit|payload>"
        return f"Selected: {args[0]}"

    def _handle_help(self, args):
        return "Available commands: send, start, stop, clear, kill, reconnect, refetch, list, select, help, exit, quit"

    def _handle_exit(self, args):
        return "shutdown"

    def _handle_quit(self, args):
        return "shutdown"

    def _handle_debug(self, args):
        return "Debug mode toggled"

    def _handle_resend(self, args):
        return "Resending last payload..."

    def _handle_refresh(self, args):
        self.payload_manager.refresh_payload_list()
        return "Payload list refreshed"

    def _handle_unsafe(self, args):
        return "Unsafe mode toggled"

    def _handle_config(self, args):
        return "Config updated"
