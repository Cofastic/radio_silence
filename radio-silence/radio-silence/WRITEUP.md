# Writeup - Radio Silence (Misc, Medium)

**Flag:** `IBOH26{d07af141-882f-43bc-8ccf-04cc651eb15c}`

## TL;DR

The service is a DNSSEC-signed DNS zone using **NSEC**. Walking the NSEC chain lists every
name. The flag is not stored in any record's content; it is encoded in **which record types
exist** at the sequential `relay-NNN` names (one byte per name). The decoded bytes are a
**NATO phonetic transcript** of the flag's GUID.

## 1\. Recon

```sh
dig @ctf-lookup.cofastic.com -p 5052 comms-check.cofastic.com TXT +short
# "radio\\\\\\\_check\\\\\\\_Over\\\\\\\_And\\\\\\\_Out"
dig @ctf-lookup.cofastic.com -p 5052 signals.cofastic.com DNSKEY +short
```

DNSKEY data means the zone is DNSSEC-signed. Signed zones carry NSEC (or NSEC3) records.

```sh
dig @ctf-lookup.cofastic.com -p 5052 signals.cofastic.com NSEC +short
# alpha-182.signals.cofastic.com. NS SOA TXT RRSIG NSEC DNSKEY TYPE65534
```

The next-name field is readable, so it is plain **NSEC** (NSEC3 would show hashes). Zone
transfers are refused (`AXFR` fails), so walking is the way in.

## 2\. Walk the zone

Each NSEC record says "the next name is X" and lists the types present at this name. Follow
`next` until it loops back to the apex: **334 names**.

* 120 callsign decoys (`alpha-182`, `tango-045`, ...) with TXT records: half are fake
`IBOH26{...}` flags, half are taunts.
* 4 dead ends (`outpost-zulu`, `command-hq`, `extraction-point`, `listening-post`): `NO SIGNAL`.
* **208 sequential stations `relay-000` ... `relay-207`**. These are the real signal.

## 3\. The trap

Querying TXT everywhere and grepping `IBOH26{` yields only decoy flags (this is exactly how
the zone-walk challenges this one is inspired by are solved). None validate.

## 4\. Read the channels

```sh
dig @ctf-lookup.cofastic.com -p 5052 relay-000.signals.cofastic.com NSEC +short
# relay-001.signals.cofastic.com. AAAA SRV RRSIG NSEC
```

The type list differs per station. `RRSIG` and `NSEC` are always present (carrier tones), so
ignore them. The remaining eight types are the bits, most significant first:

|Bit|7|6|5|4|3|2|1|0|
|-|-|-|-|-|-|-|-|-|
|Type|A|AAAA|MX|TXT|HINFO|SRV|LOC|CAA|

Present = 1, absent = 0. For `relay-000`: AAAA + SRV = `01000100` = 68 = `D`.
Decoding all 208 stations the same way gives:

```
Delta Zero Seven Alfa Foxtrot One Four One Dash Eight Eight Two Foxtrot Dash Four Three
Bravo Charlie Dash Eight Charlie Charlie Foxtrot Dash Zero Four Charlie Charlie Six Five
One Echo Bravo One Five Charlie
```

(The hint that the transcript is a radio read-out tells the player the bytes are letters,
not the flag itself.)

## 5\. NATO to GUID

Map each word to its character (`Niner`=9, `Dash`=-, lowercase hex letters):

Delta=d, Zero=0, Seven=7, Alfa=a, Foxtrot=f, One=1, Four=4, One=1, Dash=- ... gives `d07af141-882f-43bc-8ccf-04cc651eb15c`

Wrap it: `IBOH26{d07af141-882f-43bc-8ccf-04cc651eb15c}`

## Solver

```python
#!/usr/bin/env python3
import sys, socket
import dns.resolver, dns.exception, dns.rdatatype as rt

SERVER = sys.argv\\\\\\\[1] if len(sys.argv) > 1 else "ctf-lookup.cofastic.com"
PORT   = int(sys.argv\\\\\\\[2]) if len(sys.argv) > 2 else 5052
ZONE   = "signals.cofastic.com"

ORDER = \\\\\\\["A","AAAA","MX","TXT","HINFO","SRV","LOC","CAA"]   # MSB -> LSB
NATO = {"Zero":"0","One":"1","Two":"2","Three":"3","Four":"4","Five":"5","Six":"6",
        "Seven":"7","Eight":"8","Niner":"9","Alfa":"a","Bravo":"b","Charlie":"c",
        "Delta":"d","Echo":"e","Foxtrot":"f","Dash":"-"}

r = dns.resolver.Resolver(configure=False)
r.nameservers = \\\\\\\[socket.gethostbyname(SERVER)]
r.port = PORT
r.timeout, r.lifetime = 3, 10

def query\\\\\\\_nsec(name):
    for attempt in range(3):                      # retry, last try over TCP
        try:
            return r.resolve(name, "NSEC", tcp=(attempt == 2))\\\\\\\[0]
        except dns.exception.DNSException:
            pass
    raise SystemExit(f"giving up at {name}")

def types\\\\\\\_of(nsec):
    out = set()
    for window, bitmap in nsec.windows:
        for i, b in enumerate(bitmap):
            for j in range(8):
                if b \\\\\\\& (0x80 >> j):
                    out.add(rt.to\\\\\\\_text(window \\\\\\\* 256 + i \\\\\\\* 8 + j))
    return out

# 1) walk the NSEC chain: apex -> ... -> apex
chain, name = {}, ZONE
while name not in chain:
    rec = query\\\\\\\_nsec(name)
    chain\\\\\\\[name] = rec
    name = rec.next.to\\\\\\\_text(omit\\\\\\\_final\\\\\\\_dot=True)
print(f"\\\\\\\[+] walked {len(chain)} names")

# 2) the sequential relay-NNN stations are the signal
relays = sorted(n for n in chain if n.startswith("relay-"))
print(f"\\\\\\\[+] found {len(relays)} relay stations")

# 3) channel bitmap -> byte -> character
transcript = ""
for n in relays:
    t = types\\\\\\\_of(chain\\\\\\\[n])
    transcript += chr(int("".join("1" if x in t else "0" for x in ORDER), 2))
print("\\\\\\\[+] transcript:", transcript)

# 4) NATO phonetics -> GUID -> flag
guid = "".join(NATO\\\\\\\[w] for w in transcript.split())
print(f"\\\\\\\[+] FLAG: IBOH26{{{guid}}}")
```

Run: `pip install dnspython \\\\\\\&\\\\\\\& python3 solve.py ctf-lookup.cofastic.com 5052`

Expected output ends with:
`\\\\\\\[+] FLAG: IBOH26{d07af141-882f-43bc-8ccf-04cc651eb15c}`

## Key takeaways

* DNSSEC **NSEC** leaks the entire zone; **NSEC3** was designed to prevent this.
* NSEC also leaks the **types** at each name, which can carry hidden data.
* Do not assume the flag is in record *content*; metadata can be the message.

## Notes for the organizer (not for publishing)

* Intended path: walk -> spot `relay-` sequence -> decode bitmaps -> NATO.
* Easy shortcut check: AXFR is refused in `named.conf` (`allow-transfer { none; }`).
* Fake decoy flags are random UUIDs and never match the real one.
* Station count is 208 only for this GUID's transcript length; the pinned GUID keeps it stable.

