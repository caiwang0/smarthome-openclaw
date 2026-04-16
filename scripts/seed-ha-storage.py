#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import secrets
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from hmac import new as hmac_new
from pathlib import Path

import bcrypt


REQUIRED_STORAGE_FILES = (
    "auth",
    "auth_provider.homeassistant",
    "onboarding",
    "core.config",
)
DEFAULT_USERNAME = "openclaw"
DEFAULT_NAME = "OpenClaw"
DEFAULT_LOCATION_NAME = "Home"
DEFAULT_COUNTRY = "US"
DEFAULT_CURRENCY = "USD"
DEFAULT_LANGUAGE = "en"
DEFAULT_RADIUS = 100
LONG_LIVED_EXPIRATION_SECONDS = 315360000
ACCESS_TOKEN_EXPIRATION_SECONDS = 1800.0


@dataclass
class SeedResult:
    created: bool
    username: str
    name: str
    storage_files: tuple[str, ...]
    password: str | None = None
    token: str | None = None

    def to_json(self) -> str:
        payload = {
            "created": self.created,
            "username": self.username,
            "name": self.name,
            "storage_files": list(self.storage_files),
        }
        if self.password is not None:
            payload["password"] = self.password
        if self.token is not None:
            payload["token"] = self.token
        return json.dumps(payload)


class PartialStorageError(RuntimeError):
    def __init__(self, storage_files: list[str]) -> None:
        super().__init__("refusing to seed partial Home Assistant auth state")
        self.storage_files = storage_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed Home Assistant private storage for no-browser installs."
    )
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--time-zone", default="UTC")
    parser.add_argument("--ha-version", default="2026.3.4")
    parser.add_argument("--username", default=DEFAULT_USERNAME)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--location-name", default=DEFAULT_LOCATION_NAME)
    parser.add_argument("--country", default=DEFAULT_COUNTRY)
    parser.add_argument("--currency", default=DEFAULT_CURRENCY)
    parser.add_argument("--language", default=DEFAULT_LANGUAGE)
    return parser.parse_args()


def encode_b64url(raw: bytes) -> bytes:
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def json_bytes(payload: object) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()


def encode_jwt(refresh_token_id: str, jwt_key: str, issued_at: int, expires_at: int) -> str:
    header = encode_b64url(json_bytes({"alg": "HS256", "typ": "JWT"}))
    payload = encode_b64url(
        json_bytes({"exp": expires_at, "iat": issued_at, "iss": refresh_token_id})
    )
    signing_input = b".".join((header, payload))
    signature = encode_b64url(
        hmac_new(jwt_key.encode(), signing_input, digestmod=sha256).digest()
    )
    return b".".join((header, payload, signature)).decode()


def bcrypt_hash(password: str) -> str:
    return base64.b64encode(
        bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    ).decode()


def iso_now(now: datetime) -> str:
    return now.isoformat()


def required_paths(storage_dir: Path) -> list[Path]:
    return [storage_dir / name for name in REQUIRED_STORAGE_FILES]


def write_json_0600(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as tmp:
        json.dump(payload, tmp, indent=2)
        tmp.write("\n")
        temp_path = Path(tmp.name)
    temp_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    temp_path.replace(path)


def build_auth_payload(
    username: str,
    name: str,
    password_hash: str,
    ha_version: str,
    created_at: str,
    refresh_token_id: str,
    jwt_key: str,
    system_refresh_id: str,
    credential_id: str,
    admin_user_id: str,
    system_user_id: str,
) -> dict:
    return {
        "version": 1,
        "minor_version": 1,
        "key": "auth",
        "data": {
            "users": [
                {
                    "id": system_user_id,
                    "group_ids": ["system-read-only"],
                    "is_owner": False,
                    "is_active": True,
                    "name": "Home Assistant Content",
                    "system_generated": True,
                    "local_only": False,
                },
                {
                    "id": admin_user_id,
                    "group_ids": ["system-admin"],
                    "is_owner": True,
                    "is_active": True,
                    "name": name,
                    "system_generated": False,
                    "local_only": False,
                },
            ],
            "groups": [
                {"id": "system-admin", "name": "Administrators"},
                {"id": "system-users", "name": "Users"},
                {"id": "system-read-only", "name": "Read Only"},
            ],
            "credentials": [
                {
                    "id": credential_id,
                    "user_id": admin_user_id,
                    "auth_provider_type": "homeassistant",
                    "auth_provider_id": None,
                    "data": {"username": username},
                }
            ],
            "refresh_tokens": [
                {
                    "id": system_refresh_id,
                    "user_id": system_user_id,
                    "client_id": None,
                    "client_name": None,
                    "client_icon": None,
                    "token_type": "system",
                    "created_at": created_at,
                    "access_token_expiration": ACCESS_TOKEN_EXPIRATION_SECONDS,
                    "token": secrets.token_hex(64),
                    "jwt_key": secrets.token_hex(64),
                    "last_used_at": None,
                    "last_used_ip": None,
                    "expire_at": None,
                    "credential_id": None,
                    "version": ha_version,
                },
                {
                    "id": refresh_token_id,
                    "user_id": admin_user_id,
                    "client_id": None,
                    "client_name": username,
                    "client_icon": None,
                    "token_type": "long_lived_access_token",
                    "created_at": created_at,
                    "access_token_expiration": float(LONG_LIVED_EXPIRATION_SECONDS),
                    "token": secrets.token_hex(64),
                    "jwt_key": jwt_key,
                    "last_used_at": None,
                    "last_used_ip": None,
                    "expire_at": None,
                    "credential_id": None,
                    "version": ha_version,
                },
            ],
        },
    }


def build_auth_provider_payload(username: str, password_hash: str) -> dict:
    return {
        "version": 1,
        "minor_version": 1,
        "key": "auth_provider.homeassistant",
        "data": {
            "users": [
                {
                    "username": username,
                    "password": password_hash,
                }
            ]
        },
    }


def build_onboarding_payload() -> dict:
    return {
        "version": 4,
        "minor_version": 1,
        "key": "onboarding",
        "data": {
            "done": [
                "user",
                "core_config",
                "analytics",
                "integration",
            ]
        },
    }


def build_core_config_payload(
    time_zone: str,
    location_name: str,
    country: str,
    currency: str,
    language: str,
) -> dict:
    return {
        "version": 1,
        "minor_version": 4,
        "key": "core.config",
        "data": {
            "latitude": 0.0,
            "longitude": 0.0,
            "elevation": 0,
            "unit_system_v2": "metric",
            "location_name": location_name,
            "time_zone": time_zone,
            "external_url": None,
            "internal_url": None,
            "currency": currency,
            "country": country,
            "language": language,
            "radius": DEFAULT_RADIUS,
        },
    }


def seed_storage(args: argparse.Namespace) -> SeedResult:
    config_dir = Path(args.config_dir)
    storage_dir = config_dir / ".storage"
    paths = required_paths(storage_dir)

    if all(path.exists() for path in paths):
        return SeedResult(
            created=False,
            username=args.username,
            name=args.name,
            storage_files=REQUIRED_STORAGE_FILES,
        )

    if any(path.exists() for path in paths):
        raise PartialStorageError([path.name for path in paths if path.exists()])

    issued_at_dt = datetime.now(UTC)
    issued_at = int(issued_at_dt.timestamp())
    expires_at = issued_at + LONG_LIVED_EXPIRATION_SECONDS
    created_at = iso_now(issued_at_dt)

    password = secrets.token_urlsafe(18)
    password_hash = bcrypt_hash(password)

    system_user_id = secrets.token_hex(16)
    admin_user_id = secrets.token_hex(16)
    credential_id = secrets.token_hex(16)
    system_refresh_id = secrets.token_hex(16)
    refresh_token_id = secrets.token_hex(16)
    jwt_key = secrets.token_hex(64)
    long_lived_token = encode_jwt(refresh_token_id, jwt_key, issued_at, expires_at)

    payloads = {
        "auth": build_auth_payload(
            username=args.username,
            name=args.name,
            password_hash=password_hash,
            ha_version=args.ha_version,
            created_at=created_at,
            refresh_token_id=refresh_token_id,
            jwt_key=jwt_key,
            system_refresh_id=system_refresh_id,
            credential_id=credential_id,
            admin_user_id=admin_user_id,
            system_user_id=system_user_id,
        ),
        "auth_provider.homeassistant": build_auth_provider_payload(
            username=args.username,
            password_hash=password_hash,
        ),
        "onboarding": build_onboarding_payload(),
        "core.config": build_core_config_payload(
            time_zone=args.time_zone,
            location_name=args.location_name,
            country=args.country,
            currency=args.currency,
            language=args.language,
        ),
    }

    for name, payload in payloads.items():
        write_json_0600(storage_dir / name, payload)

    return SeedResult(
        created=True,
        username=args.username,
        name=args.name,
        password=password,
        token=long_lived_token,
        storage_files=REQUIRED_STORAGE_FILES,
    )


def main() -> int:
    args = parse_args()
    try:
        result = seed_storage(args)
    except PartialStorageError as exc:
        print(
            json.dumps(
                {
                    "status": "partial",
                    "message": str(exc),
                    "storage_files": exc.storage_files,
                }
            ),
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1

    print(result.to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
