# win_join

Joins or removes **Windows** clients from a Samba 4 AD domain using the `microsoft.ad.membership` module.

## What it does

- Validates required variables and the value of `win_join_state`
- Performs a domain join (`state: domain`) or removal (`state: workgroup`)
- Hides credentials from logs (`no_log: true`)
- Reboots the client after the operation if `win_join_reboot: true` (default)

## Requirements

- Ansible >= 2.14
- Collection `microsoft.ad` installed on the controller
- WinRM or SSH configured on the Windows targets

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `win_join_state` | `domain` | `domain` to join, `workgroup` to leave |
| `win_join_reboot` | `true` | Reboot the client after the operation |
| `win_join_workgroup` | `WORKGROUP` | Workgroup name to use when `state=workgroup` |
| `samba_ad_dc_realm` | — | AD realm in uppercase (required) |
| `samba_ad_dc_search_domain` | — | DNS search domain (required) |
| `samba_ad_dc_administrator_username` | `admin` | AD administrator username |
| `samba_ad_dc_administrator_passwd` | `{{ ansible_password }}` | AD administrator password |

The `samba_ad_dc_*` variables are shared with `build_dc` and are typically defined in `group_vars/all.yaml`.

## Example

```yaml
- name: Join Windows clients to domain
  hosts: windows_clients
  roles:
    - lineadicomando.samba_ad_dc.win_join
```

To remove a client from the domain:

```yaml
- name: Remove Windows client from domain
  hosts: windows_clients
  roles:
    - role: lineadicomando.samba_ad_dc.win_join
      vars:
        win_join_state: workgroup
```

## Tested platforms

- Windows (all versions supported by `microsoft.ad`)

## License

Apache-2.0
