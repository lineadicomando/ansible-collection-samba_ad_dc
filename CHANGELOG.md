# Changelog

## Unreleased

### Breaking changes
- The minimum supported ansible-core is now 2.19, declared consistently in
  `meta/runtime.yml`, the README and the CI matrix. 2.15 was claimed but never
  tested, and the matrix only exercised 2.16 and 2.18, both end of life.

### Fixed
- `ansible-test` assumed the modules had to run on every Python version the
  running ansible-core supports as a target, which on ansible-core 2.16 still
  includes Python 2.7 and 3.6. `samba_tool_user` uses
  `from __future__ import annotations`, so `compile`, `import`,
  `future-import-boilerplate` and `metaclass-boilerplate` all failed. A new
  `tests/config.yml` declares `python_requires: ">=3.7"` for modules. The unit
  test job had the same latent failure; it only passed because its unpinned
  `ansible-core>=2.16` resolved to a release that no longer targets Python 2.7.

### Changed
- The unit test job now runs over the same ansible-core matrix as the sanity
  job, and the lint job pins ansible-core and ansible-lint, so neither can
  break or heal without a change to the repository.

## v0.4.0 — 2026-08-17

Review pass over the whole collection: provisioning correctness, idempotency,
credential handling, packaging and tests.

### Breaking changes
- `samba_dc_build_administrator_passwd` and `samba_win_join_administrator_passwd`
  no longer default to `{{ ansible_password }}` and are now required. The SSH /
  WinRM credential and the domain administrator credential are different secrets,
  and `ansible_password` is undefined with key, certificate or Kerberos
  authentication. Supply them from a vault-encrypted variable.
- `samba_dc_build` no longer installs `nmap`, `telnet` or the individual
  `libpcp*` packages (the latter come in as dependencies of `pcp`). The package
  list is now split into `samba_dc_build_base_packages` and
  `samba_dc_build_extra_packages`, both overridable.
- Re-provisioning an existing domain now requires
  `samba_dc_build_force_provision: true`.

### Fixed
- `samba_dc_build`: the domain was provisioned **before** the network was
  configured and without `--host-ip`, so the DC registered a DHCP (or loopback)
  address as its A record in the internal DNS zone. Networking now runs first,
  `/etc/hosts` maps the FQDN to the static address, and the address is passed
  explicitly to `samba-tool domain provision`.
- `samba_dc_build`: the account state markers under `/var/lib/samba` survived a
  re-provisioning, so the administrator password and the `admin` account were
  skipped against a brand-new domain. They are now cleared before provisioning.
- `samba_dc_build`: `/etc/resolv.conf` was removed and rewritten on every run,
  which reported `changed` and notified a reboot every time the role ran. It is
  now only removed when it is a symlink.
- `samba_dc_build`: `libnss-winbind` was installed but `/etc/nsswitch.conf` was
  never updated, so domain accounts were invisible to the OS and home directory
  provisioning failed with "user not found".
- `samba_dc_build`: the Cockpit plugin was re-cloned on every run but never
  rebuilt after the first installation.
- `samba_dc_build`: `source /etc/bashrc_completion.d/*` passed all but the first
  file as positional parameters; it now sources each file.
- `samba_dc_backup`: with a username but no password, `-U user%None` was passed
  literally (`default('')` does not replace `None`). Credentials now travel
  through the `PASSWD` environment variable, are absent from `argv` and from the
  `_samba_dc_backup_argv` fact, and a missing password is refused up front
  instead of hanging on a prompt.
- `samba_dc_backup`: the files archive no longer depends on gathered facts
  (`now()` instead of `ansible_date_time`).
- `samba_tool` (home): the directory group defaulted to a per-user group that
  does not exist in AD; it is now `Domain Users`, overridable via
  `args.home_group`. NSS resolution is checked with an explicit error message.
- `samba_tool` (home): `ldbmodify` always reported `changed`; the attributes are
  now read back first, and the SMB share parameters converge even on a
  pre-existing share.
- `samba_tool` (group): membership deltas are compared case-insensitively, as AD
  treats sAMAccountNames — `Alice` vs `alice` no longer re-applies on every run.
- `samba_win_status`: the summary tasks read the public fact and failed when
  `samba_win_status_set_fact` was `false`; an empty CIM result is now rejected
  with a clear message.
- `samba_tool_user`: `_parse_ldif` now decodes base64 LDIF values
  (`attribute:: <base64>`), and an unexpected `objectSid` format fails with a
  readable message.
- `samba_tool_user`: fixed an invalid `DOCUMENTATION` entry (a `key: value` pair
  parsed as a dict instead of a string) and the missing GPLv3 header, both caught
  by `ansible-test sanity`.

### Added
- `samba_dc_build`: `samba_dc_build_firewall_ssh_sources` and
  `samba_dc_build_firewall_cockpit_sources` restrict management access; the
  ruleset moved to a template and is validated with `nft -c` before being
  installed.
- `samba_dc_build`: `samba_dc_build_cockpit_repo` / `_version` / `_src`, so the
  Cockpit plugin build can be pinned and reproducible.
- `argument_specs.yaml` for `samba_dc_build` and `samba_win_join` — every role
  now has one.
- `README.md` for `samba_dc_backup`, `samba_win_status` and the MCP server.
- Unit tests for the `samba_tool_user` LDIF parsing and account flags, plus
  `ansible-test sanity` and `ansible-test units` jobs in CI.
- `ansible.windows` is declared as a collection dependency (used by
  `samba_win_status`).
- `build_ignore` in `galaxy.yml`: the published tarball no longer embeds
  `.ansible/`, `__pycache__/` or `.pyc` files.

### Changed
- `samba_tool`: `group`, `computer` and `ou` share a single present/absent
  reconciler (`_ensure.yaml`); a missing `args.name` is reported up front instead
  of surfacing as a template error.
- `samba_tool`: new `samba_tool_sam_ldb_path` and `samba_tool_home_share_params`
  variables.
- MCP server: per-run timeout (`ANSIBLE_MCP_TIMEOUT`), explicit inventory
  override (`ANSIBLE_MCP_INVENTORY`), deduplicated tool dispatch.
- `samba_win_join`: task files renamed from `.yml` to `.yaml`, consistent with
  the other roles.

## v0.3.0 — 2026-06-02

### Added
- `samba_win_status` role and MCP tool: read-only domain/workgroup membership
  reporting for Windows hosts via CIM
- Home directory provisioning (`samba_tool_object: home`): physical directory,
  `homeDrive`/`homeDirectory` LDAP attributes and SMB share

### Changed
- Roles renamed: `build_dc` → `samba_dc_build`, `win_join` → `samba_win_join`
- Variables renamed with a consistent role prefix

## v0.2.0 — 2026-05-29

### Added
- `samba_tool` role: object + action + arguments interface for users, groups,
  computers and OUs
- `samba_tool_user` module: idempotent user management with check mode, diff and
  primary group reconciliation
- `samba_dc_backup` role: domain backup (online/offline) and destructive restore
- MCP server and self-describing `meta/mcp.yaml` catalogs

## v0.1.0 — 2026-05-27

### Added
- `build_dc` role: full provisioning of a Samba 4 AD DC on Debian Trixie (13)
- `win_join` role: Windows domain join/leave via `microsoft.ad.membership`
- Cockpit web UI via [cockpit-samba-ad-dc](https://github.com/lineadicomando/cockpit-samba-ad-dc)
- nftables firewall hardened for AD DC
- chrony configured as authoritative NTP for the domain
