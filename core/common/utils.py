import os
import re
import hashlib

ESCAPE_SEQUENCE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def log_info(msg):
    print(f"[INFO] {msg}")


def log_error(msg):
    print(f"[ERROR] {msg}")


def log_warn(msg):
    print(f"[WARN] {msg}")


def log_ok(msg):
    print(f"[ OK ] {msg}")


def read_file(path):
    with open(path, "r") as f:
        return f.read()


def read_file_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_file(path, data):
    with open(path, "w") as f:
        f.write(data)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def sanitize_log(message):
    return ESCAPE_SEQUENCE_RE.sub("", message)


COLOR_CODES = {
    # Standard
    "black": "\033[38;2;0;0;0m",
    "red": "\033[38;2;220;20;20m",
    "green": "\033[38;2;20;200;60m",
    "yellow": "\033[38;2;255;215;0m",
    "blue": "\033[38;2;96;96;255m",
    "magenta": "\033[38;2;255;100;200m",
    "cyan": "\033[38;2;0;255;255m",
    "white": "\033[38;2;255;255;255m",
    "gray": "\033[38;2;128;128;128m",
    "orange": "\033[38;2;255;165;0m",
    "purple": "\033[38;2;180;80;255m",
    "pink": "\033[38;2;255;150;200m",
    "reset": "\033[0m",
    "bold": "\033[1m",
    # Custom
    "web": "\033[38;2;208;208;255m",
    "preq": "\033[38;2;208;255;208m",
    "stepnum": "\033[38;2;208;255;255m",
    "code": "\033[38;2;176;255;176m",
    "warn": "\033[38;2;255;80;80m",
}


def apply_colors(text):
    import re

    for color_name, code in COLOR_CODES.items():
        if color_name == "reset":
            continue
        pattern = rf"\[{color_name}\]([\s\S]*?)\[/{color_name}\]"
        replacement = rf"{code}\1{COLOR_CODES['reset']}"
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def sha256_file(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()
