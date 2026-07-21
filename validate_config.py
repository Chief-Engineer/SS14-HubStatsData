#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


def validate_hub(raw: Any, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"hubs[{index}]"

    if not isinstance(raw, dict):
        errors.append(f"{prefix}: expected mapping, got {type(raw).__name__}")
        return errors

    for field in ("id", "name", "url"):
        if field not in raw:
            errors.append(f"{prefix}: missing required field '{field}'")

    if "id" in raw and not isinstance(raw["id"], int):
        errors.append(f"{prefix}.id: expected int, got {type(raw['id']).__name__}")

    if "name" in raw and not isinstance(raw["name"], str):
        errors.append(
            f"{prefix}.name: expected string, got {type(raw['name']).__name__}"
        )

    if "url" in raw and not isinstance(raw["url"], str):
        errors.append(f"{prefix}.url: expected string, got {type(raw['url']).__name__}")

    if (
        "color" in raw
        and raw["color"] is not None
        and not isinstance(raw["color"], str)
    ):
        errors.append(
            f"{prefix}.color: expected string or null, got {type(raw['color']).__name__}"
        )

    return errors


def validate_server(raw: Any, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"servers[{index}]"

    if not isinstance(raw, dict):
        errors.append(f"{prefix}: expected mapping, got {type(raw).__name__}")
        return errors

    for field in ("name", "addresses"):
        if field not in raw:
            errors.append(f"{prefix}: missing required field '{field}'")

    if "name" in raw and not isinstance(raw["name"], str):
        errors.append(
            f"{prefix}.name: expected string, got {type(raw['name']).__name__}"
        )

    if "name" in raw and isinstance(raw["name"], str) and raw["name"] == "":
        errors.append(f"{prefix}.name: must not be empty")

    if "addresses" in raw:
        if not isinstance(raw["addresses"], list):
            errors.append(
                f"{prefix}.addresses: expected list, got {type(raw['addresses']).__name__}"
            )
        else:
            for i, addr in enumerate(raw["addresses"]):
                if not isinstance(addr, str):
                    errors.append(
                        f"{prefix}.addresses[{i}]: expected string, got {type(addr).__name__}"
                    )
                elif not addr.startswith(("ss14://", "ss14s://")):
                    errors.append(
                        f"{prefix}.addresses[{i}]: must start with 'ss14://' or 'ss14s://'"
                    )

    if "connect" in raw and not isinstance(raw["connect"], bool):
        errors.append(
            f"{prefix}.connect: expected bool, got {type(raw['connect']).__name__}"
        )

    return errors


def validate_config(raw: Any) -> list[str]:
    errors: list[str] = []

    if not isinstance(raw, dict):
        errors.append(f"expected top-level mapping, got {type(raw).__name__}")
        return errors

    if "hubs" not in raw:
        errors.append("missing required field 'hubs'")
    elif not isinstance(raw["hubs"], list):
        errors.append(f"hubs: expected list, got {type(raw['hubs']).__name__}")
    else:
        for i, hub in enumerate(raw["hubs"]):
            errors.extend(validate_hub(hub, i))

    if "servers" not in raw:
        errors.append("missing required field 'servers'")
    elif not isinstance(raw["servers"], list):
        errors.append(f"servers: expected list, got {type(raw['servers']).__name__}")
    else:
        for i, server in enumerate(raw["servers"]):
            errors.extend(validate_server(server, i))

    if "default_server_name" in raw and not isinstance(raw["default_server_name"], str):
        errors.append(
            f"default_server_name: expected string, got {type(raw['default_server_name']).__name__}"
        )

    if "footer" in raw and not isinstance(raw["footer"], str):
        errors.append(f"footer: expected string, got {type(raw['footer']).__name__}")

    return errors


def check_duplicates(raw: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    hubs = raw.get("hubs", [])
    if isinstance(hubs, list):
        hub_ids: dict[int, int] = {}
        for i, hub in enumerate(hubs):
            if not isinstance(hub, dict) or "id" not in hub:
                continue
            hid = hub["id"]
            if not isinstance(hid, int):
                continue
            if hid in hub_ids:
                errors.append(
                    f"duplicate hub id {hid} (hubs[{hub_ids[hid]}] and hubs[{i}])"
                )
            else:
                hub_ids[hid] = i

    servers = raw.get("servers", [])
    if isinstance(servers, list):
        addrs: dict[str, int] = {}
        names: dict[str, int] = {}
        for i, server in enumerate(servers):
            if not isinstance(server, dict):
                continue

            name = server.get("name")
            if isinstance(name, str) and name:
                if name in names:
                    errors.append(
                        f"duplicate server name '{name}' (servers[{names[name]}] and servers[{i}])"
                    )
                else:
                    names[name] = i

            addresses = server.get("addresses", [])
            if isinstance(addresses, list):
                for addr in addresses:
                    if not isinstance(addr, str):
                        continue
                    if addr in addrs:
                        errors.append(
                            f"duplicate server address '{addr}' (servers[{addrs[addr]}] and servers[{i}])"
                        )
                    else:
                        addrs[addr] = i

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate config.yaml for SS14-HubStats"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config YAML (default: config.yaml)",
    )
    args = parser.parse_args()

    path = Path(args.config)
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 1

    with open(path) as f:
        try:
            raw = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"ERROR: invalid YAML: {e}", file=sys.stderr)
            return 1

    if raw is None:
        print("ERROR: config file is empty", file=sys.stderr)
        return 1

    errors = validate_config(raw)
    errors.extend(check_duplicates(raw))

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        print(f"Validation failed with {len(errors)} error(s)", file=sys.stderr)
        return 1

    hubs = raw.get("hubs", [])
    servers = raw.get("servers", [])
    print(f"Config OK: {len(hubs)} hubs, {len(servers)} servers", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
