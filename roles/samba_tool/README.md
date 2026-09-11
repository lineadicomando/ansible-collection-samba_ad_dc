<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# Role: samba_tool

A wrapper around `samba-tool` to manage the objects of a Samba 4 AD DC (users,
groups, computers, OUs) and to provision user home directories. Designed to be
driven both from playbooks and from the `samba` MCP tool.

Domain backup and restore live in the separate
[`samba_dc_backup`](../samba_dc_backup/README.md) role.

It runs **on the domain controller** and requires elevated privileges
(`become: true`), because `samba-tool` reads the local `sam.ldb` database.

## Interface

| Variable | Description |
|----------|-------------|
| `samba_tool_object` | `user` \| `group` \| `computer` \| `ou` \| `home` |
| `samba_tool_action` | samba-tool verb (`create`, `delete`, `list`, `show`, `addmembers`, …) |
| `samba_tool_args` | dictionary of action-specific arguments. `name` is required for every action except `list` |
| `samba_tool_bin` | path to the executable (default `samba-tool`) |
| `samba_tool_sam_ldb_path` | directory database used by `ldbmodify` (default `/var/lib/samba/private/sam.ldb`) |
| `samba_tool_home_share_params` | parameters enforced on the home SMB share |
| `samba_tool_no_log` | hide the output of tasks containing passwords (default `true`) |

## Actions

| Object | Actions |
|--------|---------|
| `user` | `list`, `show`, `create`, `present`, `delete`, `absent`, `enable`, `disable`, `setpassword`, `setprimarygroup` |
| `group` | `list`, `show`, `listmembers`, `add`, `create`, `delete`, `absent`, `addmembers`, `removemembers` |
| `computer` | `list`, `show`, `create`, `delete`, `absent` |
| `ou` | `list`, `listobjects`, `create`, `delete`, `absent` |
| `home` | `provision`, `absent` |

## Idempotency

- **user**: mutating operations are delegated to the
  [`samba_tool_user`](../../plugins/modules/samba_tool_user.py) module, with
  check_mode and diff. The password cannot be read back: with `setpassword`
  (mapped to `update_password: always`) the task always reports `changed`.
- **group/computer/ou**: the current state is read before acting;
  `addmembers`/`removemembers` apply only the membership delta, compared
  case-insensitively as AD does.
- **home**: the LDAP attributes are read back and only rewritten when they
  differ; the SMB share parameters converge to
  `samba_tool_home_share_params`.

## Home directories

`object: home`, `action: provision` replicates what cockpit-samba-ad-dc does:
it creates `<home_base>/<name>`, sets the `homeDrive` and `homeDirectory`
attributes through `ldbmodify`, and ensures the SMB share exists.

| Argument | Default | Description |
|----------|---------|-------------|
| `name` | — | sAMAccountName (required) |
| `home_base` | `/home/samba` | base path for home directories |
| `home_drive` | `H:` | Windows drive letter mapping |
| `share_name` | `home` | SMB share name |
| `home_group` | `Domain Users` | group owning the directory |

The directory is owned by the domain account, so domain accounts must be
resolvable through NSS. The `samba_dc_build` role configures this by adding
`winbind` to the `passwd`/`group` lines of `/etc/nsswitch.conf`; the role fails
with an explicit message when the lookup does not work.

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

# Provision a home directory
- import_role:
    name: lineadicomando.samba_ad_dc.samba_tool
  vars:
    samba_tool_object: home
    samba_tool_action: provision
    samba_tool_args:
      name: alice
```

Or via the FQCN playbook shipped with the collection:

```bash
ansible-playbook lineadicomando.samba_ad_dc.samba \
  -e '{"target_hosts":"dc","samba_tool_object":"user","samba_tool_action":"create",
       "samba_tool_args":{"name":"alice","password":"..."}}'
```

## Known limitations

For users, attributes (given name, surname, mail, …) are applied **only at
creation time**. Modifying attributes on existing users, moving users between
OUs and changing account expiry are not yet supported: `samba-tool` offers no
scriptable, idempotent sub-command for these cases (they would require
`ldbmodify`). They are planned as an evolution of the module.

Passwords are passed to `samba-tool` on the command line, because it cannot read
them from stdin: they are visible in the process list of the DC for the duration
of the call.
