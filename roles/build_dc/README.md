# build_dc

Full provisioning of a **Samba 4 Active Directory Domain Controller** on Debian Trixie (13).

## What it does

1. **Validation** — ensures all required variables are defined before proceeding
2. **System** — sets the FQDN, updates packages, installs base tools and Cockpit
3. **Samba AD** — installs and provisions the domain (`samba-tool domain provision`), disables nmbd/smbd/winbind, enables only `samba-ad-dc`
4. **Kerberos** — configures `/etc/krb5.conf`
5. **Network** — assigns a static IP with DNS pointing to the DC itself
6. **Firewall** — configures nftables, opening only the ports required by AD (DNS, Kerberos, LDAP, RPC, SMB) plus SSH and Cockpit (9090)
7. **Services** — enables `samba-ad-dc` and `cockpit`, configures chrony as authoritative NTP for the domain
8. **Admin user** — creates/configures the AD administrator account
9. **Cockpit plugin** — installs [cockpit-samba-ad-dc](https://github.com/lineadicomando/cockpit-samba-ad-dc) for browser-based domain management

## Requirements

- Debian Trixie (13)
- Ansible >= 2.15
- Root / sudo access on the target

## Variables

All variables are mandatory and must be defined in `host_vars/<hostname>.yaml`. The role fails explicitly if any variable is missing or null.

| Variable | Description |
|----------|-------------|
| `build_dc_realm` | Kerberos realm in uppercase (e.g. `EXAMPLE.COM`) |
| `build_dc_domain` | NetBIOS domain name (e.g. `EXAMPLE`) |
| `build_dc_fqdn` | DC fully qualified domain name (e.g. `dc01.example.com`) |
| `build_dc_search_domain` | DNS search domain (e.g. `example.com`) |
| `build_dc_nameserver` | Upstream nameserver IP (used before provisioning) |
| `build_dc_address` | Static IP address of the DC |
| `build_dc_netmask` | Netmask (e.g. `255.255.255.0`) |
| `build_dc_gateway` | Default gateway |
| `build_dc_ifname` | Network interface name (e.g. `enp1s0`) |
| `build_dc_ntp_server` | Upstream NTP server (e.g. `pool.ntp.org`) |
| `build_dc_ntp_allow_network` | Network allowed to use the DC as NTP source (e.g. `192.168.1.0/24`) |
| `build_dc_administrator_username` | AD admin username (default: `admin`) |
| `build_dc_administrator_passwd` | AD admin password (default: `{{ ansible_password }}`) |

## Example

```yaml
- name: Provision DC
  hosts: dc
  become: true
  roles:
    - lineadicomando.samba_ad_dc.build_dc
```

```yaml
# host_vars/dc01.example.com.yaml
build_dc_realm: EXAMPLE.COM
build_dc_domain: EXAMPLE
build_dc_fqdn: dc01.example.com
build_dc_search_domain: example.com
build_dc_nameserver: 192.168.1.1
build_dc_address: 192.168.1.10
build_dc_netmask: 255.255.255.0
build_dc_gateway: 192.168.1.1
build_dc_ifname: enp1s0
build_dc_ntp_server: pool.ntp.org
build_dc_ntp_allow_network: 192.168.1.0/24
```

## Cockpit

After provisioning, the management panel is available at `https://<dc-fqdn>:9090`. The [cockpit-samba-ad-dc](https://github.com/lineadicomando/cockpit-samba-ad-dc) plugin provides a graphical interface for managing AD users, groups, and services without using the CLI.

## Tested platforms

- Debian Trixie (13)

## License

Apache-2.0
