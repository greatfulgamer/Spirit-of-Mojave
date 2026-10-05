# The Ollama DNS Blackhole — root cause and fix (2026-09-28)
*Found while pulling models. Not a bandwidth problem, not a size problem, and not the
transient flakiness it first appeared to be.*

## Symptom

`ollama pull` failed on manny-vargas and corporal-betsy with:

```
Error: pull model manifest: Get "https://registry.ollama.ai/v2/library/gemma4/manifests/e4b":
dial tcp 10.0.0.1:443: i/o timeout
```

`10.0.0.1` is not a Cloudflare address. The registry resolves to `104.18.16.170` /
`104.18.17.170`. `10.0.0.1` is the classic captive-portal / blackhole address.

## What made this confusing

The failure was **intermittent**, and every cheap check said the network was fine:

| Check | Result |
|-------|--------|
| `getent hosts registry.ollama.ai` | correct A record |
| `curl -4 https://registry.ollama.ai/v2/` | 404 (expected — endpoint exists) |
| `curl` the exact manifest path | **200** |
| `python3 socket.getaddrinfo(...)` | 104.18.17.170 — correct |
| `ollama pull` | **10.0.0.1 timeout** |

So the host resolved correctly from curl, getent, and Python, and failed only from
ollama. Retrying did not fix it — five consecutive pulls failed on both nodes while
curl to the identical URL returned 200 in the same second.

## Root cause

**ollama is a Go binary, and Go's pure-Go DNS resolver bypasses the system resolver.**
Where curl and glibc-based tools go through `/etc/nsswitch.conf` → systemd-resolved,
Go reads `/etc/resolv.conf` itself. Something on the path Go takes returns `10.0.0.1`
for `registry.ollama.ai` — a wildcard/blackhole response — while the libc path gets the
correct answer.

This is not a hypothetical class of failure. Go's resolver has a documented
`GODEBUG=netdns` switch precisely because its built-in resolver can diverge from the
system one in environments with captive portals, split-horizon DNS, or an
intercepting resolver.

## The fix

One line, forces Go to use the system (libc) resolver:

```ini
# /etc/systemd/system/ollama.service.d/10-dns.conf
[Service]
Environment=GODEBUG=netdns=cgo
```

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment=GODEBUG=netdns=cgo\n' \
  | sudo tee /etc/systemd/system/ollama.service.d/10-dns.conf
sudo systemctl daemon-reload && sudo systemctl restart ollama.service
```

Applied to **manny-vargas** and **corporal-betsy**.

## Result

| Node | Before | After |
|------|--------|-------|
| manny-vargas | 5 consecutive `10.0.0.1` timeouts | `gemma4:e4b` (9.6 GB) pulled |
| corporal-betsy | 5 consecutive `10.0.0.1` timeouts | `lfm2.5:8b` (5.2 GB) pulled |

## Why this was worth chasing

Without it, both nodes cannot pull **any** new model, ever — regardless of bandwidth,
RAM, or disk. The earlier assumption in this repo that it was "transient DNS
blackholing, a retry will fix it" was **wrong**: retrying was the wrong response, and
it cost five failed attempts on two nodes before the real cause was found.

The tell that should have been read sooner: the error named a *specific wrong IP*
rather than a generic timeout. A genuine packet loss does not produce a coherent
routable address for the destination. Something answered.

## Also confirmed: 13.8 GB model on 11 GB free RAM

`gpt-oss:20b` (13.8 GB) **loads and runs on craig-boone with 11 GB available** — no
swap observed, coherent output. This contradicts the assumption, repeated in several
recommendation writeups, that it "won't fit in 24 GB." It does fit, and it runs at
9.8 tok/s while answering correctly.

Corollary for the fleet: the binding constraint on these 19.3 GiB nodes is **not** RAM
for MoE models. Per-token cost tracks *active* parameters, not total size, so a 13.8 GB
MoE with a small active set is cheaper at inference time than a 5.2 GB dense model.

## Verification status

- `gemma4:e4b` (9.6 GB) on manny-vargas — pulled, **not benchmarked**
- `lfm2.5:8b` (5.2 GB) on corporal-betsy — pulled, **not benchmarked**
- `gpt-oss:20b` (13.8 GB) on craig-boone — pulled, **loads and runs at 9.8 tok/s**, correct answer on the control prompt

`GODEBUG=netdns=cgo` was not applied to craig-boone or mr-new-vegas — both pulled
without hitting the blackhole. It is recorded as a fix to apply **when** they do, not
evidence they need it. Claiming it as applied fleet-wide would be wrong.
