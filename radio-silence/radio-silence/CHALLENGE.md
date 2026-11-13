# Challenge listing - Radio Silence

| Field | Value |
|---|---|
| **Name** | Radio Silence |
| **Category** | Misc |
| **Difficulty** | Medium |
| **Suggested points** | 300 (use 250-400 depending on your scale) |
| **Author** | (your name) |
| **Flag** | `IBOH26{d07af141-882f-43bc-8ccf-04cc651eb15c}` (case-sensitive, static) |
| **Service** | `ctf-lookup.cofastic.com:5052` (UDP and TCP) |

**Why Medium:** players must know DNSSEC/NSEC zone walking, notice that the flag is
not in any TXT record, understand the NSEC type bitmap, and finish with a NATO decode.
Four small steps, each easy once seen, but together they take real thought.

## Description (paste into the platform)

> **CLASSIFIED - EYES ONLY**
>
> Outpost Zulu went dark 72 hours ago. No voice, no data, no beacon. Our listening post is still intercepting traffic from the relay network, but every station broadcasts only static and enemy disinformation.
>
> Command believes the message is not in what the stations say, but in which channels each one keeps open. Once recovered, it will be read out in standard radio phonetics. Transcribe it.
>
> The recovered message is the flag's contents only, in lowercase, without the `IBOH26{}` wrapper.
>
> Service: `ctf-lookup.cofastic.com:5052` (UDP/TCP, retry on timeouts)
> Zone: `signals.cofastic.com`
>
> Flag format: `IBOH26{...}`

## Hints (release in order)

1. "Don't read the transmissions. Study the network itself."
2. "Eight channels per station, one byte per station. Ignore the carrier tones (RRSIG, NSEC)."
3. "The decoded bytes aren't the flag. They're a radio operator reading it out."

Optional extra hint if nobody solves it: "The zone will tell you who comes next. Keep asking."

## Alternative titles

Dead Drop, Comms Blackout, Signal Intercept.
