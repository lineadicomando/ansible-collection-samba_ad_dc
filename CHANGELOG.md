# Changelog

## v0.1.0 — 2026-05-27

### Added
- `build_dc` role: full provisioning of a Samba 4 AD DC on Debian Trixie (13)
- `win_join` role: Windows domain join/leave via `microsoft.ad.membership`
- Cockpit web UI via [cockpit-samba-ad-dc](https://github.com/lineadicomando/cockpit-samba-ad-dc)
- nftables firewall hardened for AD DC
- chrony configured as authoritative NTP for the domain
