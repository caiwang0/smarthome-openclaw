#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import socket
import ssl
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_NAME = "OpenClaw"
DEFAULT_USERNAME = "openclaw"
DEFAULT_LANGUAGE = "en"
DEFAULT_CLIENT_NAME = "SmartHub"
DEFAULT_LIFESPAN_DAYS = 3650
DEFAULT_WAIT_TIMEOUT = 900
DEFAULT_WAIT_INTERVAL = 5


@dataclass
class BootstrapResult:
    created: bool
    name: str
    username: str
    password: str | None
    token: str | None
    base_url: str
    resolved_ip: str | None

    def to_json(self) -> str:
        payload: dict[str, Any] = {
            "created": self.created,
            "name": self.name,
            "username": self.username,
            "base_url": self.base_url,
            "resolved_ip": self.resolved_ip,
        }
        if self.password is not None:
            payload["password"] = self.password
        if self.token is not None:
            payload["token"] = self.token
        return json.dumps(payload)


class BootstrapError(RuntimeError):
    """Raised when Home Assistant onboarding bootstrap fails."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Drive Home Assistant onboarding and create a long-lived token."
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--language", default=DEFAULT_LANGUAGE)
    parser.add_argument("--client-name", default=DEFAULT_CLIENT_NAME)
    parser.add_argument("--lifespan-days", type=int, default=DEFAULT_LIFESPAN_DAYS)
    parser.add_argument("--wait-timeout", type=int, default=DEFAULT_WAIT_TIMEOUT)
    parser.add_argument("--wait-interval", type=int, default=DEFAULT_WAIT_INTERVAL)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def build_client_id(base_url: str) -> str:
    return f"{base_url}/"


def resolve_ip(base_url: str) -> str | None:
    parsed = urllib.parse.urlparse(base_url)
    host = parsed.hostname
    if host is None:
        return None
    try:
        return socket.gethostbyname(host)
    except OSError:
        return None


def http_request(
    method: str,
    url: str,
    *,
    json_data: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any] | list[Any]:
    request_headers = dict(headers or {})
    data: bytes | None = None

    if json_data is not None:
        data = json.dumps(json_data).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    elif form_data is not None:
        data = urllib.parse.urlencode(form_data).encode("utf-8")
        request_headers.setdefault(
            "Content-Type", "application/x-www-form-urlencoded"
        )

    req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        if not body:
            return {}
        return json.loads(body)


def wait_for_onboarding(base_url: str, timeout: int, interval: int) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout
    last_error = "no response"
    onboarding_url = f"{base_url}/api/onboarding"

    while time.monotonic() < deadline:
        try:
            payload = http_request("GET", onboarding_url)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            time.sleep(interval)
            continue

        if isinstance(payload, list):
            return payload
        last_error = f"unexpected onboarding payload: {payload!r}"
        time.sleep(interval)

    raise BootstrapError(
        f"Timed out waiting for Home Assistant onboarding at {base_url}/api/onboarding: {last_error}"
    )


def step_done(status: list[dict[str, Any]], step: str) -> bool:
    for entry in status:
        if entry.get("step") == step:
            return bool(entry.get("done"))
    return False


def create_onboarding_user(
    base_url: str,
    *,
    name: str,
    username: str,
    password: str,
    language: str,
    client_id: str,
) -> str:
    payload = http_request(
        "POST",
        f"{base_url}/api/onboarding/users",
        json_data={
            "name": name,
            "username": username,
            "password": password,
            "client_id": client_id,
            "language": language,
        },
    )
    auth_code = payload.get("auth_code") if isinstance(payload, dict) else None
    if not auth_code:
        raise BootstrapError(f"Home Assistant did not return an auth code: {payload!r}")
    return str(auth_code)


def exchange_auth_code(base_url: str, *, client_id: str, auth_code: str) -> dict[str, Any]:
    payload = http_request(
        "POST",
        f"{base_url}/auth/token",
        form_data={
            "client_id": client_id,
            "grant_type": "authorization_code",
            "code": auth_code,
        },
    )
    if not isinstance(payload, dict) or "access_token" not in payload:
        raise BootstrapError(f"Failed to exchange auth code for tokens: {payload!r}")
    return payload


def auth_json_post(base_url: str, path: str, access_token: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    response = http_request(
        "POST",
        f"{base_url}{path}",
        json_data=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if not isinstance(response, dict):
        raise BootstrapError(f"Unexpected response from {path}: {response!r}")
    return response


def recv_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise BootstrapError("Unexpected end of stream while reading WebSocket frame")
        data.extend(chunk)
    return bytes(data)


class WebSocketClient:
    def __init__(self, ws_url: str, timeout: int = 30) -> None:
        self.ws_url = ws_url
        self.timeout = timeout
        self.sock: socket.socket | ssl.SSLSocket | None = None

    def __enter__(self) -> "WebSocketClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    def connect(self) -> None:
        parsed = urllib.parse.urlparse(self.ws_url)
        host = parsed.hostname
        if host is None:
            raise BootstrapError(f"Invalid WebSocket URL: {self.ws_url}")

        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == "wss" else 80

        raw_sock = socket.create_connection((host, port), timeout=self.timeout)
        raw_sock.settimeout(self.timeout)

        if parsed.scheme == "wss":
            context = ssl.create_default_context()
            self.sock = context.wrap_socket(raw_sock, server_hostname=host)
        else:
            self.sock = raw_sock

        key = base64.b64encode(os.urandom(16)).decode("ascii")
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"

        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        self.sock.sendall(handshake.encode("ascii"))

        response = bytearray()
        while b"\r\n\r\n" not in response:
            response.extend(recv_exact(self.sock, 1))

        header_text = response.decode("utf-8", errors="replace")
        if " 101 " not in header_text:
            raise BootstrapError(f"WebSocket upgrade failed: {header_text!r}")

        accept_expected = base64.b64encode(
            hashlib.sha1(
                (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")
            ).digest()
        ).decode("ascii")
        if f"Sec-WebSocket-Accept: {accept_expected}" not in header_text:
            raise BootstrapError("WebSocket server returned an invalid accept header")

    def close(self) -> None:
        if self.sock is None:
            return
        try:
            self.send_raw_frame(0x8, b"")
        except OSError:
            pass
        self.sock.close()
        self.sock = None

    def send_raw_frame(self, opcode: int, payload: bytes) -> None:
        if self.sock is None:
            raise BootstrapError("WebSocket is not connected")
        header = bytearray()
        header.append(0x80 | opcode)
        payload_len = len(payload)
        if payload_len < 126:
            header.append(0x80 | payload_len)
        elif payload_len < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", payload_len))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", payload_len))

        mask = os.urandom(4)
        header.extend(mask)
        masked = bytes(byte ^ mask[idx % 4] for idx, byte in enumerate(payload))
        self.sock.sendall(header + masked)

    def send_json(self, payload: dict[str, Any]) -> None:
        self.send_raw_frame(0x1, json.dumps(payload).encode("utf-8"))

    def recv_json(self) -> dict[str, Any]:
        if self.sock is None:
            raise BootstrapError("WebSocket is not connected")

        while True:
            first, second = recv_exact(self.sock, 2)
            opcode = first & 0x0F
            payload_len = second & 0x7F
            masked = (second & 0x80) != 0

            if payload_len == 126:
                payload_len = struct.unpack("!H", recv_exact(self.sock, 2))[0]
            elif payload_len == 127:
                payload_len = struct.unpack("!Q", recv_exact(self.sock, 8))[0]

            mask = recv_exact(self.sock, 4) if masked else None
            payload = recv_exact(self.sock, payload_len)
            if mask is not None:
                payload = bytes(
                    byte ^ mask[idx % 4] for idx, byte in enumerate(payload)
                )

            if opcode == 0x8:
                raise BootstrapError("Home Assistant closed the WebSocket connection")
            if opcode == 0x9:
                self.send_raw_frame(0xA, payload)
                continue
            if opcode != 0x1:
                continue

            try:
                message = json.loads(payload.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise BootstrapError(f"Invalid WebSocket JSON payload: {payload!r}") from exc

            if not isinstance(message, dict):
                raise BootstrapError(f"Unexpected WebSocket payload: {message!r}")
            return message


def create_long_lived_token(
    base_url: str, access_token: str, *, client_name: str, lifespan_days: int
) -> str:
    ws_url = urllib.parse.urlunparse(
        urllib.parse.urlparse(base_url)._replace(
            scheme="wss" if base_url.startswith("https://") else "ws",
            path="/api/websocket",
            params="",
            query="",
            fragment="",
        )
    )

    with WebSocketClient(ws_url) as ws:
        first = ws.recv_json()
        if first.get("type") != "auth_required":
            raise BootstrapError(f"Expected auth_required over WebSocket, got {first!r}")

        ws.send_json({"type": "auth", "access_token": access_token})
        auth_reply = ws.recv_json()
        if auth_reply.get("type") != "auth_ok":
            raise BootstrapError(f"Home Assistant WebSocket auth failed: {auth_reply!r}")

        request_id = 1
        ws.send_json(
            {
                "id": request_id,
                "type": "auth/long_lived_access_token",
                "client_name": client_name,
                "lifespan": lifespan_days,
            }
        )

        while True:
            reply = ws.recv_json()
            if reply.get("id") != request_id:
                continue
            if not reply.get("success"):
                raise BootstrapError(
                    f"Home Assistant refused long-lived token creation: {reply!r}"
                )
            result = reply.get("result")
            if not isinstance(result, str) or not result:
                raise BootstrapError(
                    f"Home Assistant returned an invalid long-lived token payload: {reply!r}"
                )
            return result


def bootstrap(args: argparse.Namespace) -> BootstrapResult:
    base_url = normalize_base_url(args.base_url)
    if args.dry_run:
        return BootstrapResult(
            created=True,
            name=args.name,
            username=args.username,
            password="dry-run-password",
            token="dry-run-token",
            base_url=base_url,
            resolved_ip="192.168.2.142",
        )

    client_id = build_client_id(base_url)
    status = wait_for_onboarding(base_url, args.wait_timeout, args.wait_interval)

    if step_done(status, "user") and step_done(status, "core_config") and step_done(
        status, "analytics"
    ) and step_done(status, "integration"):
        raise BootstrapError(
            "Home Assistant onboarding is already complete, so the macOS bootstrap can no longer auto-create the initial user and token. Delete the VM and rerun install.sh for a clean bootstrap, or create a token manually in the UI."
        )

    if step_done(status, "user"):
        raise BootstrapError(
            "Home Assistant onboarding user step is already complete before the installer could create the SmartHub account. Delete the VM and rerun install.sh for a clean bootstrap, or finish setup manually."
        )

    password = secrets.token_urlsafe(18)
    auth_code = create_onboarding_user(
        base_url,
        name=args.name,
        username=args.username,
        password=password,
        language=args.language,
        client_id=client_id,
    )
    tokens = exchange_auth_code(base_url, client_id=client_id, auth_code=auth_code)
    access_token = str(tokens["access_token"])

    status = wait_for_onboarding(base_url, args.wait_timeout, args.wait_interval)

    if not step_done(status, "core_config"):
        auth_json_post(base_url, "/api/onboarding/core_config", access_token)
    if not step_done(status, "analytics"):
        auth_json_post(base_url, "/api/onboarding/analytics", access_token)
    if not step_done(status, "integration"):
        auth_json_post(
            base_url,
            "/api/onboarding/integration",
            access_token,
            {"client_id": client_id, "redirect_uri": client_id},
        )

    token = create_long_lived_token(
        base_url,
        access_token,
        client_name=args.client_name,
        lifespan_days=args.lifespan_days,
    )

    return BootstrapResult(
        created=True,
        name=args.name,
        username=args.username,
        password=password,
        token=token,
        base_url=base_url,
        resolved_ip=resolve_ip(base_url),
    )


def main() -> int:
    args = parse_args()
    try:
        result = bootstrap(args)
    except BootstrapError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected bootstrap failure: {exc}", file=sys.stderr)
        return 1

    print(result.to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
