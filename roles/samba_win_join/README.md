# samba_win_join

Joins or removes **Windows** clients from a Samba 4 AD domain using the `microsoft.ad.membership` module.

## What it does

- Validates required variables and the value of `samba_win_join_state`
- Performs a domain join (`state: domain`) or removal (`state: workgroup`)
- Hides credentials from logs (`no_log: true`)
- Reboots the client after the operation if `samba_win_join_reboot: true` (default)

## Requirements

- Ansible >= 2.15
- Collection `microsoft.ad` installed on the controller
- WinRM or SSH configured on the Windows targets

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `samba_win_join_state` | `domain` | `domain` to join, `workgroup` to leave |
| `samba_win_join_reboot` | `true` | Reboot the client after the operation |
| `samba_win_join_workgroup` | `WORKGROUP` | Workgroup name to use when `state=workgroup` |
| `samba_win_join_realm` | — | AD realm in uppercase (required) |
| `samba_win_join_search_domain` | — | DNS search domain (required) |
| `samba_win_join_administrator_username` | `admin` | AD administrator username |
| `samba_win_join_administrator_passwd` | `{{ ansible_password }}` | AD administrator password |

The `samba_win_join_realm`, `samba_win_join_search_domain`, `samba_win_join_administrator_username` and `samba_win_join_administrator_passwd` variables hold the same values used by `samba_build_dc` and are typically defined in `group_vars/all.yaml`.

## Example

```yaml
- name: Join Windows clients to domain
  hosts: windows_clients
  roles:
    - lineadicomando.samba_ad_dc.samba_win_join
```

To remove a client from the domain:

```yaml
- name: Remove Windows client from domain
  hosts: windows_clients
  roles:
    - role: lineadicomando.samba_ad_dc.samba_win_join
      vars:
        samba_win_join_state: workgroup
```

## Tested platforms

- Windows (all versions supported by `microsoft.ad`)

## License

GPL-3.0-or-later
