# SPDX-License-Identifier: GPL-3.0-or-later
"""Command builders and runner backing the samba_ad_dc MCP tools.

Configuration comes from the environment:
  ANSIBLE_PROJECT_ROOT  (required) directory the playbooks are run from
  ANSIBLE_MCP_INVENTORY (optional) explicit inventory path; when unset the
                        layout <root>/inventories/<name>/hosts.yaml is used
  ANSIBLE_MCP_TIMEOUT   (optional) per-run timeout in seconds, default 900
  ANSIBLE_MCP_LOG_DIR   (optional) log directory, default <root>/logs
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from runlog import run_logged

# Playbooks shipped by the collection, keyed by MCP tool name.
PLAYBOOKS = {
    "samba": "lineadicomando.samba_ad_dc.samba",
    "samba_dc_backup": "lineadicomando.samba_ad_dc.samba_dc_backup",
    "samba_win_status": "lineadicomando.samba_ad_dc.samba_win_status",
}

DEFAULT_TIMEOUT = 900


def _project_root() -> Path:
    root = os.environ.get("ANSIBLE_PROJECT_ROOT")
    if not root:
        raise RuntimeError("ANSIBLE_PROJECT_ROOT environment variable is not set")
    return Path(root)


def _timeout() -> int:
    try:
        return int(os.environ.get("ANSIBLE_MCP_TIMEOUT", DEFAULT_TIMEOUT))
    except ValueError:
        return DEFAULT_TIMEOUT


def _inventory_path(inventory: str) -> str:
    override = os.environ.get("ANSIBLE_MCP_INVENTORY")
    if override:
        return override
    return str(_project_root() / "inventories" / inventory / "hosts.yaml")


def _build_command(
    tool: str,
    extra: dict,
    limit: str = "all",
    inventory: str = "school",
) -> list[str]:
    cmd = ["ansible-playbook", PLAYBOOKS[tool], "-i", _inventory_path(inventory)]
    # The playbooks take their host pattern from target_hosts rather than from
    # --limit, so that they can also be run against a single host by name.
    if limit and limit != "all":
        extra = dict(extra, target_hosts=limit)
    if extra:
        cmd += ["-e", json.dumps(extra)]
    return cmd


def build_samba_command(
    object_: str,
    action: str,
    args: dict | None = None,
    limit: str = "all",
    inventory: str = "school",
) -> list[str]:
    extra: dict = {"samba_tool_object": object_, "samba_tool_action": action}
    if args:
        extra["samba_tool_args"] = args
    return _build_command("samba", extra, limit, inventory)


def build_backup_command(
    action: str,
    args: dict | None = None,
    limit: str = "all",
    inventory: str = "school",
) -> list[str]:
    extra: dict = {"samba_dc_backup_action": action}
    for key, value in (args or {}).items():
        extra[f"samba_dc_backup_{key}"] = value
    return _build_command("samba_dc_backup", extra, limit, inventory)


def build_samba_win_status_command(
    limit: str = "all",
    inventory: str = "school",
) -> list[str]:
    return _build_command("samba_win_status", {}, limit, inventory)


def run_command(cmd: list[str], label: str = "samba") -> str:
    """Run an ansible-playbook command, streaming its output to a log file.

    Bounded by ANSIBLE_MCP_TIMEOUT: a playbook waiting on a prompt would
    otherwise block the MCP server forever.
    """
    timeout = _timeout()
    result = run_logged(cmd, _project_root(), label, timeout=timeout)
    output = result.output
    if result.timed_out:
        output += f"\n[timed out after {timeout}s and was terminated]"
    elif result.returncode != 0:
        output += f"\n[exit code {result.returncode}]"
    return f"{output}\n[log] {result.log_path}"


def format_command(cmd: list[str]) -> str:
    parts = []
    i = 0
    while i < len(cmd):
        token = cmd[i]
        if token in ("-e", "-i") and i + 1 < len(cmd):
            parts.append(f"{token} '{cmd[i + 1]}'")
            i += 2
        else:
            parts.append(token)
            i += 1
    return " \\\n  ".join(parts)
