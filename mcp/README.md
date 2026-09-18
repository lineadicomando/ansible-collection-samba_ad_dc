<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# MCP server

Exposes the collection's dispatcher playbooks as MCP tools, so an MCP-compatible
client (Claude, Cursor, …) can manage the domain controller without shelling out
to `ansible-playbook` by hand.

| Tool | Playbook | What it manages |
|------|----------|-----------------|
| `samba` | `lineadicomando.samba_ad_dc.samba` | users, groups, computers, OUs, home directories, shared folders |
| `samba_dc_backup` | `lineadicomando.samba_ad_dc.samba_dc_backup` | domain backup (online/offline) and destructive restore |
| `samba_win_status` | `lineadicomando.samba_ad_dc.samba_win_status` | domain/workgroup membership of Windows hosts (read-only) |

Every tool accepts `preview: true`, which returns the `ansible-playbook` command
line without running it. Use it before any destructive action.

## Requirements

```bash
pip install -r mcp/requirements.txt
```

The collection itself must be installed (or reachable through
`ANSIBLE_COLLECTIONS_PATH`), because the tools invoke playbooks by FQCN.

## Configuration

| Variable | Required | Meaning |
|----------|----------|---------|
| `ANSIBLE_PROJECT_ROOT` | yes | directory the playbooks are run from |
| `ANSIBLE_MCP_INVENTORY` | no | explicit inventory file; overrides the layout below |
| `ANSIBLE_MCP_TIMEOUT` | no | per-run timeout in seconds (default `900`) |
| `ANSIBLE_MCP_LOG_DIR` | no | per-run log directory (default `$ANSIBLE_PROJECT_ROOT/logs`) |

Each run streams its output to `<log dir>/<timestamp>-<label>.log` while the
playbook is still running, and repoints `<log dir>/latest.log` at it: a
`tail -F logs/latest.log` shows what the tools are doing in real time. The log
path is appended to every tool result. The newest 50 runs are kept.

Without `ANSIBLE_MCP_INVENTORY`, the `inventory` argument of each tool selects
`$ANSIBLE_PROJECT_ROOT/inventories/<inventory>/hosts.yaml`.

## Client configuration

```json
{
  "mcpServers": {
    "samba-ad-dc": {
      "command": "python3",
      "args": ["/path/to/ansible-collection-samba_ad_dc/mcp/server.py"],
      "env": {
        "ANSIBLE_PROJECT_ROOT": "/path/to/your/ansible/project",
        "ANSIBLE_MCP_INVENTORY": "/path/to/your/ansible/project/inventory.yaml"
      }
    }
  }
}
```

`server.py` imports `runner` as a sibling module, so it must be started as a
script from this directory (as above) rather than imported as a package.

## Notes

- The tools run playbooks with `become: true` on the domain controller; the
  connection user needs privilege escalation there.
- `samba_dc_backup` with `action: restore` rebuilds a DC from an archive and
  requires `restore_confirm: true` in `args`.
