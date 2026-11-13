#!/usr/bin/env python3
"""Radio Silence - full solver: walk NSEC -> read type bitmaps -> NATO -> flag."""
import sys, socket
import dns.resolver, dns.exception, dns.rdatatype as rt

SERVER = sys.argv[1] if len(sys.argv) > 1 else "ctf-lookup.cofastic.com"
PORT   = int(sys.argv[2]) if len(sys.argv) > 2 else 5052
ZONE   = "signals.cofastic.com"

ORDER = ["A","AAAA","MX","TXT","HINFO","SRV","LOC","CAA"]   # MSB -> LSB
NATO = {"Zero":"0","One":"1","Two":"2","Three":"3","Four":"4","Five":"5","Six":"6",
        "Seven":"7","Eight":"8","Niner":"9","Alfa":"a","Bravo":"b","Charlie":"c",
        "Delta":"d","Echo":"e","Foxtrot":"f","Dash":"-"}

r = dns.resolver.Resolver(configure=False)
r.nameservers = [socket.gethostbyname(SERVER)]
r.port = PORT
r.timeout, r.lifetime = 3, 10

def query_nsec(name):
    for attempt in range(3):                      # retry, last try over TCP
        try:
            return r.resolve(name, "NSEC", tcp=(attempt == 2))[0]
        except dns.exception.DNSException:
            pass
    raise SystemExit(f"giving up at {name}")

def types_of(nsec):
    out = set()
    for window, bitmap in nsec.windows:
        for i, b in enumerate(bitmap):
            for j in range(8):
                if b & (0x80 >> j):
                    out.add(rt.to_text(window * 256 + i * 8 + j))
    return out

# 1) walk the NSEC chain: apex -> ... -> apex
chain, name = {}, ZONE
while name not in chain:
    rec = query_nsec(name)
    chain[name] = rec
    name = rec.next.to_text(omit_final_dot=True)
print(f"[+] walked {len(chain)} names")

# 2) the sequential relay-NNN stations are the signal
relays = sorted(n for n in chain if n.startswith("relay-"))
print(f"[+] found {len(relays)} relay stations")

# 3) channel bitmap -> byte -> character
transcript = ""
for n in relays:
    t = types_of(chain[n])
    transcript += chr(int("".join("1" if x in t else "0" for x in ORDER), 2))
print("[+] transcript:", transcript)

# 4) NATO phonetics -> GUID -> flag
guid = "".join(NATO[w] for w in transcript.split())
print(f"[+] FLAG: IBOH26{{{guid}}}")
