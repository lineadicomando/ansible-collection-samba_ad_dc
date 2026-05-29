<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# Role: samba_tool

A wrapper around `samba-tool` to manage the objects of a Samba 4 AD DC (users,
groups, computers, OUs) and to back up/restore the domain. Designed to be driven
both from playbooks and from the `samba` MCP tool.

It runs **on the domain controller** and requires elevated privileges
(`become: true`), because `samba-tool` reads the local `sam.ldb` database.

## Interface

| Variable | Description |
|----------|-------------|
| `samba_tool_object` | `user` \| `group` \| `computer` \| `ou` \| `backup` \| `restore` |
| `samba_tool_action` | samba-tool verb (`create`, `delete`, `list`, `show`, `addmembers`, …). Not required for backup/restore |
| `samba_tool_args` | dictionary of action-specific arguments |
| `samba_tool_bin` | path to the executable (default `samba-tool`) |
| `samba_tool_no_log` | hide the output of tasks containing passwords (default `true`) |

## Idempotency

- **user**: mutating operations are delegated to the
  [`samba_tool_user`](../../plugins/modules/samba_tool_user.py) module, with
  check_mode and diff. The password cannot be read back: with `setpassword`
  (mapped to `update_password: always`) the task always reports `changed`.
- **group/computer/ou**: the current state is read before acting;
  `addmembers`/`removemembers` apply only the membership delta.
- **backup**: inherently non-idempotent (always produces a new archive).
- **restore**: destructive, requires `args.confirm: true`.

## Examples

```yaml
# Create a user
- import_role:
    name: lineadicomando.samba_ad_dc.samba_tool
  vars:
    samba_tool_object: user
    samba_tool_action: create
    samba_tool_args:
      name: alice
      password: "{{ vault_alice_password }}"
      given_name: Alice
      mail: alice@example.com

# Add members to a group (only the missing ones)
- import_role:
    name: lineadicomando.samba_ad_dc.samba_tool
  vars:
    samba_tool_object: group
    samba_tool_action: addmembers
    samba_tool_args:
      name: "Domain Admins"
      members: [alice, bob]

# Offline domain backup
- import_role:
    name: lineadicomando.samba_ad_dc.samba_tool
  vars:
    samba_tool_object: backup
    samba_tool_args:
      type: offline
      targetdir: /srv/samba-backup
```

Or via the FQCN playbook shipped with the collection:

```bash
ansible-playbook lineadicomando.samba_ad_dc.samba -l dc \
  -e '{"samba_tool_object":"user","samba_tool_action":"create",
       "samba_tool_args":{"name":"alice","password":"..."}}'
```

## Known limitations (v0.2.0)

For users, attributes (given name, surname, mail, …) are applied **only at
creation time**. Modifying attributes on existing users, moving users between
OUs and changing account expiry are not yet supported: `samba-tool` offers no
scriptable, idempotent sub-command for these cases (they would require
`ldbmodify`). They are planned as an evolution of the module.
