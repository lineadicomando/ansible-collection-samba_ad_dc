# SPDX-License-Identifier: GPL-3.0-or-later
"""MCP server exposing the lineadicomando.samba_ad_dc playbooks as tools."""
import asyncio

from mcp.server import Server
from mcp.server.context import ServerRequestContext
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool, CallToolResult, ListToolsResult, PaginatedRequestParams, CallToolRequestParams

from runner import (
    build_backup_command,
    build_samba_command,
    build_samba_win_status_command,
    format_command,
    run_command,
)

app = Server("samba-ad-dc")

_LIMIT_SCHEMA = {
    "type": "string",
    "description": (
        "Ansible host pattern: a single host name or a group. "
        "Passed to the playbook as target_hosts."
    ),
    "default": "all",
}

_INVENTORY_SCHEMA = {
    "type": "string",
    "description": (
        "Inventory name under inventories/, unless ANSIBLE_MCP_INVENTORY "
        "points at an explicit inventory file."
    ),
    "default": "school",
}

_PREVIEW_SCHEMA = {
    "type": "boolean",
    "description": (
        "If true, return the ansible-playbook command without "
        "executing it. Use before destructive actions."
    ),
    "default": False,
}


def _get_tools() -> list[Tool]:
    return [
        Tool(
            name="samba",
            description=(
                "Manage the Samba AD Domain Controller via samba-tool, through the "
                "lineadicomando.samba_ad_dc.samba playbook. "
                "Objects: user, group, computer, ou, home. "
                "Read-only actions (list, show, listmembers, listobjects) never change "
                "state. Mutating user actions are idempotent. "
                "Destructive actions (delete, absent, disable, removemembers) "
                "should be run with preview first to confirm with the user. "
                "args.name is required for every action except list. "
                "Common actions per object: "
                "user [list, show, create, present, delete, absent, enable, disable, "
                "setpassword, setprimarygroup]; "
                "group [list, show, listmembers, add, create, delete, absent, addmembers, "
                "removemembers]; "
                "computer [list, show, create, delete, absent]; "
                "ou [list, listobjects, create, delete, absent]; "
                "home [provision, absent] — creates/removes the physical home directory "
                "(/home/samba/<user> by default), sets homeDrive and homeDirectory LDAP "
                "attributes, and ensures the SMB share exists. "
                "home args: name (required), home_base (default /home/samba), "
                "home_drive (default H:), share_name (default home), "
                "home_group (default Domain Users)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {
                        "type": "string",
                        "enum": ["user", "group", "computer", "ou", "home"],
                        "description": "The kind of AD object to act upon.",
                    },
                    "action": {
                        "type": "string",
                        "description": "The samba-tool verb (e.g. create, delete, list, show, addmembers).",
                    },
                    "args": {
                        "type": "object",
                        "description": (
                            "Action-specific arguments, e.g. "
                            "{\"name\": \"alice\", \"password\": \"...\"} or "
                            "{\"name\": \"staff\", \"members\": [\"alice\", \"bob\"]} or "
                            "{\"name\": \"alice\", \"home_base\": \"/home/samba\"}."
                        ),
                        "default": {},
                    },
                    "l": _LIMIT_SCHEMA,
                    "inventory": _INVENTORY_SCHEMA,
                    "preview": _PREVIEW_SCHEMA,
                },
                "required": ["object", "action"],
            },
        ),
        Tool(
            name="samba_dc_backup",
            description=(
                "Backup and restore the Samba AD Domain Controller, through the "
                "lineadicomando.samba_ad_dc.samba_dc_backup playbook. "
                "Actions: backup (domain + user files), restore (domain, DESTRUCTIVE). "
                "Backup always produces new archives and reports changed. "
                "Restore rebuilds a DC from a backup archive — always run with "
                "preview first and require explicit confirmation (restore_confirm=true)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["backup", "restore"],
                        "description": "Operation to perform.",
                    },
                    "args": {
                        "type": "object",
                        "description": (
                            "Action-specific arguments (keys without the samba_dc_backup_ prefix). "
                            "backup: targetdir (required), domain (bool, default true), "
                            "domain_type (online|offline, default offline), domain_server, "
                            "domain_username, domain_password (required with domain_username), "
                            "files (bool, default true), files_paths (list, default [/home]). "
                            "restore: restore_backup_file (required), restore_targetdir (required), "
                            "restore_newservername (required), restore_confirm=true (required)."
                        ),
                        "default": {},
                    },
                    "l": _LIMIT_SCHEMA,
                    "inventory": _INVENTORY_SCHEMA,
                    "preview": _PREVIEW_SCHEMA,
                },
                "required": ["action"],
            },
        ),
        Tool(
            name="samba_win_status",
            description=(
                "Query the domain or workgroup membership status of Windows hosts, "
                "through the lineadicomando.samba_ad_dc.samba_win_status playbook. "
                "Read-only: never changes state. "
                "Queries Win32_ComputerSystem via CIM and reports whether each host "
                "is joined to an AD domain (and which one) or a workgroup (and which one). "
                "Targets lab_win by default (all Windows hosts in the lab)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "l": _LIMIT_SCHEMA,
                    "inventory": _INVENTORY_SCHEMA,
                    "preview": _PREVIEW_SCHEMA,
                },
                "required": [],
            },
        ),
    ]


def _command_for(name: str, arguments: dict) -> list[str] | None:
    """Translate an MCP tool call into an ansible-playbook command line."""
    limit = arguments.get("l", "all")
    inventory = arguments.get("inventory", "school")
    args = arguments.get("args") or {}

    if name == "samba":
        return build_samba_command(
            arguments["object"], arguments["action"], args or None, limit, inventory
        )
    if name == "samba_dc_backup":
        return build_backup_command(arguments["action"], args or None, limit, inventory)
    if name == "samba_win_status":
        return build_samba_win_status_command(limit, inventory)
    return None


async def handle_list_tools(ctx: ServerRequestContext, params: PaginatedRequestParams) -> ListToolsResult:
    return ListToolsResult(tools=_get_tools())


async def handle_call_tool(ctx: ServerRequestContext, params: CallToolRequestParams) -> CallToolResult:
    name = params.name
    arguments = params.arguments or {}

    cmd = _command_for(name, arguments)
    if cmd is None:
        return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")])

    if arguments.get("preview", False):
        return CallToolResult(content=[
            TextContent(
                type="text",
                text=f"Command to run:\n\n  {format_command(cmd)}\n\nNo command executed.",
            )
        ])

    label = "-".join(
        str(part)
        for part in (name, arguments.get("object"), arguments.get("action"), arguments.get("l", "all"))
        if part
    )
    output = await asyncio.to_thread(run_command, cmd, label)
    return CallToolResult(content=[TextContent(type="text", text=output)])


app.add_request_handler("tools/list", PaginatedRequestParams, handle_list_tools)
app.add_request_handler("tools/call", CallToolRequestParams, handle_call_tool)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def cli():
    asyncio.run(main())


if __name__ == "__main__":
    cli()
