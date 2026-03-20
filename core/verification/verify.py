#!/usr/bin/env python3
import os
import sys
import argparse
import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VERIFICATION_DIR = SCRIPT_DIR
PROJECT_ROOT = os.path.dirname(os.path.dirname(VERIFICATION_DIR))


def generate_keys():
    private_dir = os.path.join(VERIFICATION_DIR, "keys")
    os.makedirs(private_dir, exist_ok=True)

    private_key_path = os.path.join(private_dir, "private_key.pem")
    public_key_path = os.path.join(private_dir, "public_key.pem")

    print("Generating RSA keypair...")

    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=4096, backend=default_backend()
    )

    public_key = private_key.public_key()

    with open(private_key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    print(f"Private key saved to: {private_key_path}")
    print("IMPORTANT: Keep this key secret and offline!")

    with open(public_key_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    print(f"Public key saved to: {public_key_path}")
    print("\nDone!")


def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_exploits():
    exploits_dir = os.path.join(PROJECT_ROOT, "core", "exploits")
    exploits = []
    if os.path.exists(exploits_dir):
        for item in os.listdir(exploits_dir):
            exploit_path = os.path.join(exploits_dir, item)
            if os.path.isdir(exploit_path):
                exploit_file = os.path.join(exploit_path, "exploit.py")
                if os.path.isfile(exploit_file):
                    exploits.append(item.upper())
    return exploits


def get_tools(exploit):
    tools_base = os.path.join(PROJECT_ROOT, "core", "tools")
    tools_dir = None

    if os.path.exists(tools_base):
        for item in os.listdir(tools_base):
            if item.lower() == exploit.lower():
                tools_dir = os.path.join(tools_base, item)
                break

    tools = []
    if tools_dir:
        for item in os.listdir(tools_dir):
            if item.endswith(".py"):
                tools.append(item[:-3])
    return tools


def get_payload_extensions():
    ext_path = os.path.join(PROJECT_ROOT, "core", "exploits", "extensions.json")
    if os.path.exists(ext_path):
        with open(ext_path, "r") as f:
            return json.load(f)
    return {}


def get_payload_manifest():
    manifest_path = os.path.join(PROJECT_ROOT, "core", "payloads", "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            return json.load(f)
    return {}


def get_exploit_manifest():
    manifest_path = os.path.join(PROJECT_ROOT, "core", "exploits", "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            return json.load(f).get("exploits", [])
    return []


def get_exploit_payload_manifest(exploit):
    manifest_path = os.path.join(
        PROJECT_ROOT, "core", "exploits", exploit, "payloads", "manifest.json"
    )
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            return json.load(f).get("payloads", [])
    return []


def get_common_files():
    common_dir = os.path.join(PROJECT_ROOT, "core", "common")
    files = []
    if os.path.exists(common_dir):
        for item in os.listdir(common_dir):
            if item.endswith(".py"):
                files.append(item[:-3])
    return files


def get_payload_display_name(filename, exploit_payloads):
    for payload in exploit_payloads:
        if payload.get("file") == filename:
            return payload.get("name", filename)
    return os.path.splitext(filename)[0].replace("_", " ").title()


def get_payloads():
    payloads = []
    extensions = get_payload_extensions()
    exploit_manifest = get_exploit_manifest()
    payload_manifest = get_payload_manifest()

    js_dir = os.path.join(PROJECT_ROOT, "core", "payloads", "js")
    if os.path.exists(js_dir):
        allowed = payload_manifest.get("Y2JB", [])
        for item in os.listdir(js_dir):
            if item.endswith(".js") and item in allowed:
                payloads.append(("JS", item, "PS5 Heuristic"))

    lua_dir = os.path.join(PROJECT_ROOT, "core", "payloads", "lua")
    if os.path.exists(lua_dir):
        allowed = payload_manifest.get("Luac0re", [])
        for item in os.listdir(lua_dir):
            if item.endswith(".lua") and item in allowed:
                payloads.append(
                    (
                        "LUAC0RE",
                        item,
                        item.replace(".lua", "").replace("_", " ").title(),
                    )
                )

    exploits_dir = os.path.join(PROJECT_ROOT, "core", "exploits")
    if os.path.exists(exploits_dir):
        for exploit in os.listdir(exploits_dir):
            if exploit.startswith("."):
                continue
            exploit_upper = exploit.upper()
            if exploit_manifest and exploit_upper not in [
                e.upper() for e in exploit_manifest
            ]:
                continue
            exploit_path = os.path.join(exploits_dir, exploit)
            if not os.path.isdir(exploit_path):
                continue
            exploit_payloads_dir = os.path.join(exploit_path, "payloads")
            exploit_payload_manifest = get_exploit_payload_manifest(exploit)
            if os.path.isdir(exploit_payloads_dir):
                allowed_exts = (
                    extensions.get(exploit)
                    or extensions.get(exploit.lower())
                    or extensions.get(exploit.upper())
                    or [
                        e
                        for k, v in extensions.items()
                        if k.lower() == exploit.lower()
                        for e in v
                    ]
                )
                if allowed_exts:
                    for item in os.listdir(exploit_payloads_dir):
                        if any(item.endswith(ext) for ext in allowed_exts):
                            display_name = get_payload_display_name(
                                item, exploit_payload_manifest
                            )
                            payloads.append((exploit, item, display_name))

    return payloads


def auto():
    keys_dir = os.path.join(VERIFICATION_DIR, "keys")
    private_key_path = os.path.join(keys_dir, "private_key.pem")
    public_key_path = os.path.join(keys_dir, "public_key.pem")

    if not os.path.exists(private_key_path):
        print("No keys found. Generating new keypair...")
        generate_keys()

    print("\n--- Computing hashes ---")

    exploits = get_exploits()
    tools_dict = {}
    for exploit in exploits:
        tools_dict[exploit] = get_tools(exploit)
    payloads = get_payloads()

    hashes_output = [
        "# Trusted SHA256 hashes for Core, Exploits, Tools, and Payloads",
        "# Format: NAME:hash",
        "# Sections: Core, Exploits, Tools, Payloads",
        "",
        "# Core",
    ]

    common_files = get_common_files()
    for common_file in common_files:
        file_path = os.path.join(PROJECT_ROOT, "core", "common", f"{common_file}.py")
        if os.path.exists(file_path):
            hash_val = compute_sha256(file_path)
            hashes_output.append(f"CORE_{common_file.upper()}:{hash_val}")
            print(f"  CORE_{common_file}: {hash_val}")

    hashes_output.extend(["", "# Exploits"])

    for exploit in exploits:
        exploit_file = os.path.join(
            PROJECT_ROOT, "core", "exploits", exploit.lower(), "exploit.py"
        )
        if os.path.isfile(exploit_file):
            hash_val = compute_sha256(exploit_file)
            hashes_output.append(f"{exploit}:{hash_val}")
            print(f"  Exploit {exploit}: {hash_val}")

    hashes_output.extend(["", "# Tools"])

    for exploit in exploits:
        tools_base = os.path.join(PROJECT_ROOT, "core", "tools")
        tools_dir = None
        if os.path.exists(tools_base):
            for item in os.listdir(tools_base):
                if item.lower() == exploit.lower():
                    tools_dir = os.path.join(tools_base, item)
                    break

        if not tools_dir:
            continue

        for tool in tools_dict.get(exploit, []):
            tool_path = os.path.join(tools_dir, f"{tool}.py")
            if os.path.exists(tool_path):
                hash_val = compute_sha256(tool_path)
                hashes_output.append(f"TOOL_{exploit}_{tool.upper()}:{hash_val}")
                print(f"  TOOL_{exploit}_{tool}: {hash_val}")

    hashes_output.extend(["", "# Payloads"])

    for exploit, payload, display_name in payloads:
        if exploit == "JS":
            payload_path = os.path.join(PROJECT_ROOT, "core", "payloads", "js", payload)
        elif exploit.lower() == "luac0re":
            payload_path = os.path.join(
                PROJECT_ROOT, "core", "exploits", "luac0re", "payloads", payload
            )
        else:
            payload_path = os.path.join(
                PROJECT_ROOT, "core", "exploits", exploit.lower(), "payloads", payload
            )

        if os.path.exists(payload_path):
            hash_val = compute_sha256(payload_path)
            hash_name = display_name.upper().replace(" ", "_")
            hashes_output.append(f"PAYLOAD_{exploit.upper()}_{hash_name}:{hash_val}")
            print(f"  {display_name}: {hash_val}")

    hashes_file = os.path.join(VERIFICATION_DIR, "hashes", "hashes.txt")
    os.makedirs(os.path.dirname(hashes_file), exist_ok=True)

    with open(hashes_file, "w") as f:
        f.write("\n".join(hashes_output) + "\n")

    print(f"\nHashes written to: {hashes_file}")

    print("\n--- Signing hashes ---")
    sign_hashes()
    print("\nAll done!")


def sign_hashes():
    keys_dir = os.path.join(VERIFICATION_DIR, "keys")
    private_key_path = os.path.join(keys_dir, "private_key.pem")
    hashes_file = os.path.join(VERIFICATION_DIR, "hashes", "hashes.txt")
    signature_file = os.path.join(VERIFICATION_DIR, "hashes", "hashes.sig")

    if not os.path.exists(private_key_path):
        print("Error: private_key.pem not found!")
        print("Run with: python3 core/verification/verify.py generate-keys")
        sys.exit(1)

    if not os.path.exists(hashes_file):
        print("Error: hashes.txt not found!")
        sys.exit(1)

    print("Loading private key...")
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )

    print("Reading hashes.txt...")
    with open(hashes_file, "rb") as f:
        data = f.read()

    print("Signing hashes...")
    signature = private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())  # type: ignore

    with open(signature_file, "wb") as f:
        f.write(signature)

    print(f"Signature saved to: {signature_file}")
    print("Done!")


def main():
    parser = argparse.ArgumentParser(description="Hash Verification Management Tool")
    parser.add_argument(
        "command",
        nargs="?",
        default="auto",
        choices=["generate-keys", "sign", "auto"],
        help="Command to run (default: auto)",
    )
    args = parser.parse_args()

    if args.command == "generate-keys":
        generate_keys()
    elif args.command == "sign":
        sign_hashes()
    elif args.command == "auto":
        auto()


if __name__ == "__main__":
    main()
