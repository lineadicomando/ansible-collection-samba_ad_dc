# lineadicomando.samba_ad_dc

Ansible collection that provisions a **Samba 4 Active Directory Domain Controller** on Debian Trixie and makes it manageable from a browser — no CLI required for day-to-day operations.

After provisioning, open `https://<dc-fqdn>:9090` to access **[cockpit-samba-ad-dc](https://github.com/lineadicomando/cockpit-samba-ad-dc)**: a Cockpit plugin built specifically for this collection that lets you manage users, groups, DNS records and monitor Kerberos and Samba services directly from the web.

![cockpit-samba-ad-dc screenshot](https://raw.githubusercontent.com/lineadicomando/cockpit-samba-ad-dc/main/docs/screenshot.png)

## What you get

- A fully provisioned Samba 4 AD DC (realm, domain, Kerberos, DNS, NTP)
- A hardened nftables firewall with only the ports required by AD
- Chrony configured as authoritative NTP for domain clients
- **[cockpit-samba-ad-dc](https://github.com/lineadicomando/cockpit-samba-ad-dc)** — browser UI for AD management on port 9090
- Roles for joining Windows (and soon Linux) clients to the domain

## Roles

| Role | Target | Purpose |
|------|--------|---------|
| [`build_dc`](roles/build_dc/README.md) | Debian Trixie (13) | Provision a full Samba 4 AD DC with Cockpit web UI |
| [`win_join`](roles/win_join/README.md) | Windows (all) | Join or remove Windows clients from the domain |
| `deb_join` *(coming soon)* | Debian / Ubuntu | Join or remove Linux clients from the domain |

## Requirements

- Ansible >= 2.15
- Collection `community.general >= 7.0.0`
- Collection `microsoft.ad >= 1.0.0` (required only for `win_join`)
- DC target: Debian Trixie (13)
- Windows target: any version supported by `microsoft.ad.membership`

## Installation

```bash
ansible-galaxy collection install lineadicomando.samba_ad_dc
```

## Inventory example

```yaml
# host_vars/dc01.example.com.yaml
samba_ad_dc_realm: EXAMPLE.COM
samba_ad_dc_domain: EXAMPLE
samba_ad_dc_fqdn: dc01.example.com
samba_ad_dc_search_domain: example.com
samba_ad_dc_nameserver: 192.168.1.1
samba_ad_dc_address: 192.168.1.10
samba_ad_dc_netmask: 255.255.255.0
samba_ad_dc_gateway: 192.168.1.1
samba_ad_dc_ifname: enp1s0
samba_ad_dc_ntp_server: pool.ntp.org
samba_ad_dc_ntp_allow_network: 192.168.1.0/24
```

## Playbook example

```yaml
- name: Provision Samba AD DC
  hosts: dc
  become: true
  roles:
    - lineadicomando.samba_ad_dc.build_dc

- name: Join Windows clients
  hosts: windows_clients
  roles:
    - lineadicomando.samba_ad_dc.win_join
```

## License

Apache-2.0

## Author

Alessandro Gagliano <alessandro.gagliano@lineadicomando.it>
