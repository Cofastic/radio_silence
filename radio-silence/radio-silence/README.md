# Radio Silence - deployment guide (IBOH26, Misc)

Everything needed to rebuild the challenge server from nothing in about 15 minutes.
The flag is pinned in `flag_guid.txt`, so every redeploy produces the **same flag
and same zone**. Keep this folder backed up (git repo or zip) - it is the whole challenge.

Current values (change here if you change them in the files):

| Item | Value |
|---|---|
| Zone | `signals.cofastic.com` |
| Verify zone | `comms-check.cofastic.com` |
| Server hostname | `ctf-lookup.cofastic.com` |
| Port | `5052` (UDP **and** TCP) |
| Hetzner type | CAX11 (ARM), Ubuntu, Falkenstein |
| Folder on server | `/opt/radio-silence` |

## 0. Cost plan (competition: 14 Nov 2026)

- Hetzner bills hourly until the server is **deleted** (powering off does not stop it).
- Keep it deleted until **12-13 Nov**; deploy, test, leave running through the event.
- Free to keep between runs: SSH key, firewall, this package.
- A CAX11 at about 6.99/mo costs only a couple of dollars for the whole event window.
- **Delete the `ctf-lookup` DNS record while no server exists.** A record pointing
  at an IP you no longer own can end up pointing at a stranger's machine.

## 1. Prepare (once, anywhere)

```sh
tar czf radio-silence.tar.gz radio-silence/     # already provided as a tarball
```

## 2. Create the server (Hetzner Cloud)

1. **Servers -> Add server**: Location Falkenstein (or any), Image Ubuntu, Type **CAX11** (or CPX/CX equivalent), IPv4 on.
2. **SSH key**: select your existing key (`~/.ssh/secret.pub` was added as `kali-ctf`). Never skip this.
3. **Firewall**: attach the existing firewall, or create one with inbound rules:

   | Proto | Port | Source |
   |---|---|---|
   | TCP | 22 | **your current public IP /32** (`curl -4 ifconfig.me` on Kali) or Any |
   | UDP | 5052 | Any IPv4 + IPv6 |
   | TCP | 5052 | Any IPv4 + IPv6 (click `Add "5052"` in the port box to confirm it) |

   Do not use a private address like 192.168.x.x as the SSH source.
4. Name it `radio-silence`, create, and note the **new public IPv4** (it will differ from last time).

## 3. Point DNS at it (Squarespace)

Domains -> cofastic.com -> DNS Settings -> **Add Record**: Type `A`, Name `ctf-lookup`, TTL 30 mins (or lowest), Data = new IPv4.
Do not touch any other records (Firebase CNAMEs/TXT, `_acme-challenge`, `@`).

## 4. Deploy

On Kali:

```sh
scp -i ~/.ssh/secret radio-silence.tar.gz root@<NEW-IP>:/opt/
ssh -i ~/.ssh/secret root@<NEW-IP>
```

On the server:

```sh
cd /opt && tar xzf radio-silence.tar.gz && cd radio-silence
./deploy.sh
```

If SSH warns about a changed host key (a new server reuses your DNS/IP history), run
`ssh-keygen -R <NEW-IP>` on Kali and reconnect.

Expected self-test output: `"radio_check_Over_And_Out"`, key data, a line like
`relay-001.signals.cofastic.com. AAAA SRV RRSIG NSEC`, and `AXFR correctly refused`.
The warnings `has no address records` in the BIND log are harmless.

## 5. Verify from OUTSIDE (Kali, not the server)

```sh
dig @ctf-lookup.cofastic.com -p 5052 comms-check.cofastic.com TXT +short
dig @ctf-lookup.cofastic.com -p 5052 +tcp signals.cofastic.com DNSKEY +short
dig @ctf-lookup.cofastic.com -p 5052 signals.cofastic.com AXFR +tcp     # must say: Transfer failed
python3 solve.py ctf-lookup.cofastic.com 5052                            # must print the pinned flag
```

If the hostname is not found yet, wait a few minutes or test with `solve.py <NEW-IP> 5052`.
The solver output must equal `IBOH26{d07af141-882f-43bc-8ccf-04cc651eb15c}`.

## 6. During the event

- `docker compose logs -f` in `/opt/radio-silence` for the first hour.
- Timeouts for teams on shared networks: raise `responses-per-second` in `named.conf` (now 300), then `docker compose restart`. Zone data and flag are unaffected.
- Do not run `gen_zone.py` again on a live server unless you want it regenerated (it will produce the same zone because the flag is pinned).
- Never delete `flag_guid.txt` unless you intend to change the flag everywhere.

## 7. Teardown

1. Hetzner: **Servers -> radio-silence -> Delete** (confirm billing stops).
2. Squarespace: delete the `ctf-lookup` A record.
3. Optionally delete the firewall and SSH key if you will not reuse them.

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `dig` times out from outside, works on server | Firewall not attached, UDP/TCP 5052 rule missing, or port not confirmed |
| Works over TCP but not UDP | UDP 5052 rule missing |
| No DNSKEY / no NSEC | Signing failed: check `docker compose logs`, make sure `zones/` and `cache/` are writable (`chmod -R 777 zones cache`) |
| Hashed names in NSEC3 records | `nsec3param` was added to the policy - remove it |
| Container restarts | `docker compose logs --tail 50`; usually a typo in `named.conf` |
| Platform mismatch error on x86 vs ARM | `ubuntu/bind9` is multi-arch; ensure Docker is current |
| Flag differs from the CTF platform | `flag_guid.txt` was changed/removed; restore the pinned GUID and redeploy |

## Files

- `named.conf`: BIND config (plain NSEC, no recursion, AXFR denied)
- `docker-compose.yml`: container on host port 5052
- `gen_zone.py`: deterministic zone and flag generator (reads `flag_guid.txt`)
- `flag_guid.txt`: the secret GUID inside the flag
- `deploy.sh`: installs Docker, builds zone, starts server, self-tests
- `solve.py`: reference solver (also useful for post-deploy verification)
- `CHALLENGE.md`: platform listing text; `WRITEUP.md`: full solution (**keep private until the event ends**)
