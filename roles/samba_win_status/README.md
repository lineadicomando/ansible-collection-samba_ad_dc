<!-- SPDX-License-Identifier: GPL-3.0-or-later -->
# Role: samba_win_status

Read-only role that reports whether a **Windows** host is joined to an Active
Directory domain or to a workgroup. It queries `Win32_ComputerSystem` via CIM
and never changes state.

## Interface

| Variable | Default | Description |
|----------|---------|-------------|
| `samba_win_status_set_fact` | `true` | publish the result as the `samba_win_status` fact |
| `samba_win_status_verbose` | `true` | print a human-readable membership summary |

## Result

The `samba_win_status` fact holds:

| Key | Description |
|-----|-------------|
| `hostname` | NetBIOS computer name |
| `part_of_domain` | `true` when the host is a domain member |
| `domain` | domain FQDN, or `null` when not joined |
| `workgroup` | workgroup name, or `null` when joined to a domain |

The summary is printed regardless of `samba_win_status_set_fact`: reporting reads
an internal variable, not the public fact.

## Requirements

- Collection `ansible.windows` on the controller
- WinRM or SSH configured on the Windows targets

## Examples

```yaml
- name: Report membership
  hosts: windows_clients
  roles:
    - lineadicomando.samba_ad_dc.samba_win_status

- name: Act on the result
  hosts: windows_clients
  tasks:
    - import_role:
        name: lineadicomando.samba_ad_dc.samba_win_status
      vars:
        samba_win_status_verbose: false

    - name: Join hosts that are not domain members yet
      import_role:
        name: lineadicomando.samba_ad_dc.samba_win_join
      when: not samba_win_status.part_of_domain
```

Or via the FQCN playbook shipped with the collection:

```bash
ansible-playbook lineadicomando.samba_ad_dc.samba_win_status -e '{"target_hosts":"lab_win"}'
```

## License

GPL-3.0-or-later
