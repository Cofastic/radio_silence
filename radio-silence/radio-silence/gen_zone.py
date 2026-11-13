#!/usr/bin/env python3
"""Radio Silence zone generator (deterministic).

The flag GUID is read from flag_guid.txt, so re-running this on a fresh server
always rebuilds the SAME flag and the SAME zone. Delete flag_guid.txt to make
a brand new flag (then update your CTF platform!).
"""
import os, random, uuid

ZONE = "signals.cofastic.com"
GUID_FILE = "flag_guid.txt"

if os.path.exists(GUID_FILE):
    GUID = open(GUID_FILE).read().strip().lower()
else:
    GUID = str(uuid.uuid4())
    open(GUID_FILE, "w").write(GUID + "\n")
FLAG = f"IBOH26{{{GUID}}}"

rng = random.Random(GUID)          # deterministic decoys
def rand_uuid():
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))

NATO = {
 "0":"Zero","1":"One","2":"Two","3":"Three","4":"Four","5":"Five","6":"Six",
 "7":"Seven","8":"Eight","9":"Niner",
 "a":"Alfa","b":"Bravo","c":"Charlie","d":"Delta","e":"Echo","f":"Foxtrot",
 "-":"Dash",
}
TRANSCRIPT = " ".join(NATO[c] for c in GUID)

TYPES = ["A","AAAA","MX","TXT","HINFO","SRV","LOC","CAA"]  # MSB -> LSB
SAMPLE = {
 "A":    'A 10.13.37.1',
 "AAAA": 'AAAA fd00::1',
 "MX":   f'MX 10 mail.{ZONE}.',
 "TXT":  'TXT "static static static"',
 "HINFO":'HINFO "RADIO" "NOISE"',
 "SRV":  f'SRV 0 0 1 relay.{ZONE}.',
 "LOC":  'LOC 52 22 23.000 N 4 53 32.000 E -2.00m 0.00m 10000m 10m',
 "CAA":  'CAA 0 issue "none.invalid"',
}

lines = ["$TTL 60",
 f"@ IN SOA ns1.{ZONE}. admin.{ZONE}. (1 3600 600 86400 60)",
 f"@ IN NS ns1.{ZONE}.",
 "ns1 IN A 127.0.0.1",
 '@ IN TXT "LISTENING POST ECHO-7 ONLINE. MONITOR ALL RELAY CHANNELS."']

# the real signal: one station per character of the phonetic transcript
for i, ch in enumerate(TRANSCRIPT):
    for t, bit in zip(TYPES, f"{ord(ch):08b}"):
        if bit == "1":
            lines.append(f"relay-{i:03d} IN {SAMPLE[t]}")

# enemy decoys
calls = ["alpha","bravo","charlie","delta","echo","foxtrot","golf","hotel","india",
         "juliet","kilo","lima","mike","november","oscar","papa","quebec","romeo",
         "sierra","tango","uniform","victor","whiskey","xray","yankee","zulu"]
taunts = ["TRANSMISSION INTERCEPTED. NOTHING TO SEE HERE, OPERATOR.",
          "THIS CHANNEL IS COMPROMISED.",
          "NEGATIVE. TARGET NOT AT THIS LOCATION.",
          "ENEMY DISINFORMATION. DO NOT TRUST."]
decoys = set()
while len(decoys) < 120:
    decoys.add(f"{rng.choice(calls)}-{rng.randint(1,999):03d}")
for h in sorted(decoys):
    if rng.random() < 0.5:
        lines.append(f'{h} IN TXT "IBOH26{{{rand_uuid()}}}"')
    else:
        lines.append(f'{h} IN TXT "{rng.choice(taunts)}"')

for h in ["outpost-zulu","command-hq","extraction-point","listening-post"]:
    lines.append(f'{h} IN TXT "NO SIGNAL"')

os.makedirs("zones", exist_ok=True)
open("zones/db.signals", "w").write("\n".join(lines) + "\n")
open("zones/db.check", "w").write(
 "$TTL 60\n"
 "@ IN SOA ns1 admin (1 3600 600 86400 60)\n"
 "@ IN NS ns1\n"
 "ns1 IN A 127.0.0.1\n"
 '@ IN TXT "radio_check_Over_And_Out"\n')

open("flag.txt", "w").write(FLAG + "\n")
print("FLAG:", FLAG)
print("Stations:", len(TRANSCRIPT))
