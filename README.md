# lineadicomando.samba_ad_dc

[![GitHub tag](https://img.shields.io/github/v/tag/lineadicomando/ansible-collection-samba_ad_dc?label=version)](https://github.com/lineadicomando/ansible-collection-samba_ad_dc/tags)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue)](./LICENSE)
[![CI](https://github.com/lineadicomando/ansible-collection-samba_ad_dc/actions/workflows/ci.yml/badge.svg)](https://github.com/lineadicomando/ansible-collection-samba_ad_dc/actions/workflows/ci.yml)
[![GitHub issues](https://badgen.net/github/open-issues/lineadicomando/ansible-collection-samba_ad_dc)](https://github.com/lineadicomando/ansible-collection-samba_ad_dc/issues)

Ansible collection that provisions a **Samba 4 Active Directory Domain Controller** on Debian Trixie and makes it manageable from a browser — no CLI required for day-to-day operations.

After provisioning, open `https://<dc-fqdn>:9090` to access **[cockpit-samba-ad-dc](https://github.com/lineadicomando/cockpit-samba-ad-dc)**: a Cockpit plugin built specifically for this collection that lets you manage users, groups, DNS records and monitor Kerberos and Samba services directly from the web.

![cockpit-samba-ad-dc screenshot](https://raw.githubusercontent.com/lineadicomando/cockpit-samba-ad-dc/main/docs/screenshot.png)

## What you get

- A fully provisioned Samba 4 AD DC (realm, domain, Kerberos, DNS, NTP)
- A hardened nftables firewall with only the ports required by AD
- Chrony configured as authoritative NTP for domain clients
- **[cockpit-samba-ad-dc](https://github.com/lineadicomando/cockpit-samba-ad-dc)** — browser UI for AD management on port 9090
- Idempotent day-two management of users, groups, computers, OUs, home directories and shared folders (interchangeable with the Cockpit UI, optionally mapped as network drives through a GPO)
- Domain backup and restore
- Roles for joining Windows (and soon Linux) clients to the domain

## Roles

| Role | Target | Purpose |
|------|--------|---------|
| [`samba_dc_build`](roles/samba_dc_build/README.md) | Debian Trixie (13) | Provision a full Samba 4 AD DC with Cockpit web UI |
| [`samba_tool`](roles/samba_tool/README.md) | Debian Trixie (13) | Manage domain objects: users, groups, computers, OUs, home directories, shared folders |
| [`samba_dc_backup`](roles/samba_dc_backup/README.md) | Debian Trixie (13) | Back up the domain and user files; restore a domain |
| [`samba_win_join`](roles/samba_win_join/README.md) | Windows (all) | Join or remove Windows clients from the domain |
| [`samba_win_status`](roles/samba_win_status/README.md) | Windows (all) | Report domain/workgroup membership (read-only) |
| `deb_join` *(coming soon)* | Debian / Ubuntu | Join or remove Linux clients from the domain |

## Modules

| Module | Purpose |
|--------|---------|
| `samba_tool_user` | Idempotent management of domain users (create, delete, enable/disable, password, primary group), with check mode and diff |
| `samba_share` | Idempotent management of shared folders for domain users and groups (access, POSIX ACL, drive mapping through a GPO), with check mode and diff; same model as cockpit-samba-ad-dc |
| `samba_share_info` | List shared folders with their access list and drive mapping |

## MCP service

The collection ships machine-readable catalogs (`meta/mcp.yaml`) and an [MCP server](mcp/README.md) that expose three **MCP tools**, usable by any MCP-compatible client (Claude, Cursor, and similar):

| Tool | Role | What it manages |
|------|------|-----------------|
| `samba` | `samba_tool` | Domain objects: users, groups, computers, OUs, home directories, shared folders |
| `samba_dc_backup` | `samba_dc_backup` | Domain backup (online/offline) and destructive restore |
| `samba_win_status` | `samba_win_status` | Domain/workgroup membership of Windows hosts (read-only) |

### `samba` — AD objects

| Object | Available actions |
|--------|------------------|
| `user` | `list`, `show`, `create`, `present`, `delete`, `absent`, `enable`, `disable`, `setpassword`, `setprimarygroup` |
| `group` | `list`, `show`, `listmembers`, `add`, `create`, `delete`, `absent`, `addmembers`, `removemembers` |
| `computer` | `list`, `show`, `create`, `delete`, `absent` |
| `ou` | `list`, `listobjects`, `create`, `delete`, `absent` |
| `home` | `provision`, `absent` |
| `share` | `list`, `show`, `create`, `present`, `grant`, `revoke`, `delete`, `absent` |

Read-only actions (`list`, `show`, `listmembers`, `listobjects`) never change state. Destructive actions (`delete`, `absent`, `setpassword`, `disable`, `removemembers`, `revoke`) are flagged in the catalog and should be previewed before execution.

### `samba_dc_backup` — Backup & restore

| Object | Action | Note |
|--------|--------|------|
| `backup` | `run` | Archives the domain (online/offline) and/or user files |
| `restore` | `run` | **Destructive** — rebuilds the DC from a backup; requires `restore_confirm: true` |

### `samba_win_status` — Windows membership

| Object | Action | Note |
|--------|--------|------|
| `status` | `query` | Read-only; returns hostname, `part_of_domain`, domain or workgroup |

## Requirements

- ansible-core >= 2.19 (tested against 2.19 and 2.20)
- Collection `community.general >= 7.0.0`
- Collections `microsoft.ad >= 1.0.0` and `ansible.windows >= 2.0.0` (required only for the Windows roles)
- DC target: Debian Trixie (13)
- Windows target: any version supported by `microsoft.ad.membership`

## Installation

```bash
ansible-galaxy collection install lineadicomando.samba_ad_dc
```

## Inventory example

```yaml
# host_vars/dc01.example.com.yaml
samba_dc_build_realm: EXAMPLE.COM
samba_dc_build_domain: EXAMPLE
samba_dc_build_fqdn: dc01.example.com
samba_dc_build_search_domain: example.com
samba_dc_build_nameserver: 192.168.1.1
samba_dc_build_address: 192.168.1.10
samba_dc_build_netmask: 255.255.255.0
samba_dc_build_gateway: 192.168.1.1
samba_dc_build_ifname: enp1s0
samba_dc_build_ntp_server: pool.ntp.org
samba_dc_build_ntp_allow_network: 192.168.1.0/24
# Required, no default — keep it in a vault
samba_dc_build_administrator_passwd: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...
```

## Playbook example

```yaml
- name: Provision Samba AD DC
  hosts: dc
  become: true
  roles:
    - lineadicomando.samba_ad_dc.samba_dc_build

- name: Join Windows clients
  hosts: windows_clients
  roles:
    - lineadicomando.samba_ad_dc.samba_win_join
```

Day-two operations are also available as dispatcher playbooks, callable by FQCN:

```bash
# Create a user
ansible-playbook lineadicomando.samba_ad_dc.samba \
  -e '{"target_hosts":"dc","samba_tool_object":"user","samba_tool_action":"create",
       "samba_tool_args":{"name":"alice","password":"..."}}'

# Back up the domain
ansible-playbook lineadicomando.samba_ad_dc.samba_dc_backup \
  -e '{"target_hosts":"dc","samba_dc_backup_action":"backup",
       "samba_dc_backup_targetdir":"/srv/samba-backup"}'
```

## Development

```bash
ansible-lint                     # profile: production
ansible-test sanity --docker     # from within ansible_collections/lineadicomando/samba_ad_dc
ansible-test units --docker
```

## License

GPL-3.0-or-later

## Author

Alessandro Gagliano — [lineadicomando.it](https://lineadicomando.it)
