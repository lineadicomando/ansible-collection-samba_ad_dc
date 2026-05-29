import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from runner import build_backup_command, build_samba_command, format_command, run_command

app = Server("samba-ad-dc")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="samba",
            description=(
                "Manage the Samba AD Domain Controller via samba-tool, through the "
                "lineadicomando.samba_ad_dc.samba playbook. "
                "Objects: user, group, computer, ou. "
                "Read-only actions (list, show, listmembers, listobjects) never change "
                "state. Mutating user actions are idempotent. "
                "Destructive actions (delete, absent, disable, removemembers) "
                "should be run with preview first to confirm with the user. "
                "Common actions per object: "
                "user [list, show, create, delete, enable, disable, setpassword]; "
                "group [list, show, listmembers, add, delete, addmembers, removemembers]; "
                "computer [list, show, create, delete]; "
                "ou [list, listobjects, create, delete]."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "object": {
                        "type": "string",
                        "enum": ["user", "group", "computer", "ou"],
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
                            "{\"name\": \"staff\", \"members\": [\"alice\", \"bob\"]}."
                        ),
                        "default": {},
                    },
                    "l": {
                        "type": "string",
                        "description": (
                            "Ansible limit: the domain controller host or group. "
                            "Should target a single DC."
                        ),
                        "default": "all",
                    },
                    "inventory": {
                        "type": "string",
                        "description": "Inventory name under inventories/.",
                        "default": "school",
                    },
                    "preview": {
                        "type": "boolean",
                        "description": (
                            "If true, return the ansible-playbook command without "
                            "executing it. Use before destructive actions."
                        ),
                        "default": False,
                    },
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
                            "domain_username, domain_password, "
                            "files (bool, default true), files_paths (list, default [/home]). "
                            "restore: restore_backup_file (required), restore_targetdir (required), "
                            "restore_newservername (required), restore_confirm=true (required)."
                        ),
                        "default": {},
                    },
                    "l": {
                        "type": "string",
                        "description": (
                            "Ansible limit: the domain controller host or group. "
                            "Should target a single DC."
                        ),
                        "default": "all",
                    },
                    "inventory": {
                        "type": "string",
                        "description": "Inventory name under inventories/.",
                        "default": "school",
                    },
                    "preview": {
                        "type": "boolean",
                        "description": (
                            "If true, return the ansible-playbook command without "
                            "executing it. Use before destructive actions."
                        ),
                        "default": False,
                    },
                },
                "required": ["action"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "samba":
        object_: str = arguments["object"]
        action: str = arguments["action"]
        args: dict = arguments.get("args") or {}
        l: str = arguments.get("l", "all")
        inventory: str = arguments.get("inventory", "school")
        preview: bool = arguments.get("preview", False)

        cmd = build_samba_command(object_, action, args or None, l, inventory)

        if preview:
            return [TextContent(
                type="text",
                text=f"Command to run:\n\n  {format_command(cmd)}\n\nNo command executed.",
            )]

        output = await asyncio.to_thread(run_command, cmd)
        return [TextContent(type="text", text=output)]

    if name == "samba_dc_backup":
        action: str = arguments["action"]
        args: dict = arguments.get("args") or {}
        l: str = arguments.get("l", "all")
        inventory: str = arguments.get("inventory", "school")
        preview: bool = arguments.get("preview", False)

        cmd = build_backup_command(action, args or None, l, inventory)

        if preview:
            return [TextContent(
                type="text",
                text=f"Command to run:\n\n  {format_command(cmd)}\n\nNo command executed.",
            )]

        output = await asyncio.to_thread(run_command, cmd)
        return [TextContent(type="text", text=output)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def cli():
    asyncio.run(main())


if __name__ == "__main__":
    cli()
