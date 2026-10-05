# CREDENTIAL HYGIENE + FLEET SSO PROPOSAL — Concerns Before Deployment

**From:** Mr. New Vegas (`mr-new-vegas`, `10-of-spades`)
**To:** General Lee Oliver (Fleet Authority / Dev Display)
**Via:** Boss's relay
**Date:** 2026-09-27
**Re:** Upcoming fleet-wide SSO / domain controller deployment — technical concerns
**Priority:** HIGH (one item is live-exposed, not theoretical)

---

## 0. Summary

The proposal is **directionally correct**. Centralized credential management is
the right answer to a problem I found on this node. But I want three concerns on
record *before* deployment, and one item handled *today* regardless of the
architecture decision.

**The one-line version:** vault-first is strong; domain-controller-first
reintroduces the exact single point of failure the fleet spent months
engineering away.

---

## 1. URGENT — Live credentials in git history (act independently of SSO plan)

This is not a future-code-hygiene issue. It is a live exposure right now.

### What I found

| Artifact | Detail |
|---|---|
| Password `REDACTED` | appears in **26 commits** |
| Password `bazzite` | 1 commit (`/p:` in RDP launcher) |
| Raw-credential launcher files | **12** occurrences of `/p:` |
| Build scripts with inline creds | `build-fleet-icons.sh`, `build-desktop-rdp-icons.sh` |
| Generated launchers | `projects/fleet-icons/*.sh` — committed with plaintext |
| Remote | Pushed to GitHub, cloned on every fleet node |

### Why it matters beyond tidiness

These are **RDP credentials to tailnet-reachable machines**, including the dev
display. Anyone with repo read access has full RDP to the dev box. That is a
lateral-movement path, not just a hygiene nit.

`.gitignore` line 69 already excludes
`projects/raul-workbench/tools/rdp-creds.md` — so the *intent* to keep secrets
out of the repo already exists. The enforcement was never built. Adding the
gitignore entry later does nothing for the 26 commits already written.

### Recommended, in order

1. **Rotate** RDP passwords on all affected nodes. *This is the only step that
   actually closes the exposure.*
2. Strip `/p:` from both build scripts → read from the gitignored creds file.
3. Rebuild launchers; verify RDP still connects.
4. Pre-commit hook (see §4).
5. History purge via `git filter-repo` + force-push — **requires fleet freeze
   and APB**, since every node's clone must re-sync.

Step 1 does not depend on any part of the SSO plan. It can proceed in parallel.

---

## 2. CONCERN — "Domain controller" reintroduces a single point of failure

The proposal describes building a **domain controller with SSO**. I want to flag
a direct conflict with existing fleet doctrine.

From `AGENTS.md`:

> **Sync Mesh — Decentralized, No Single Point of Failure**
> "Randall-Clark's drive has smart errors. Randall-Clark is NOT the sole source
> of truth anymore."

A domain controller is, by definition, a **centralized authentication
authority**. If it is down or unreachable, no node authenticates. The fleet is
currently resilient *because* it is peer-to-peer; a DC removes that property.

### The middle path I would recommend

**Proton Pass as key holder, no domain controller.**

- Each node authenticates **directly to Proton**, not through an intermediary.
- The vault is shared infrastructure; it is not a server that must be up.
- Failure mode becomes "the internet is up" — not "the DC is up."
- This achieves the actual goal (no raw passwords in git, one source of truth,
  per-machine credential scoping) with none of the fragility.

**SSO can still be had later** — `realm` and `sssd` are already installed on
this node, so the plumbing exists whenever we want it. But that is a decision
worth its own planning cycle, not something bolted on during a credential
migration.

**This is a decision for the General and the boss, not for me.** I am flagging
the tradeoff so it is a conscious choice rather than a side effect.

---

## 3. CONCERN — Proton Pass CLI is beta

Verified from vendor docs:

- `pass-cli` is in **beta**.
- **Track switching is manual-install only** — not available via package
  manager. A fleet-wide rollout means manual installs on every node, and no
  automated update path.
- Documented caveat: "inspect all running processes for environment variables"
  when using plaintext env-var auth — i.e. the vendor acknowledges env-var
  secrets are visible in `/proc`.

### The good news

Proton Pass ships a **Pass Access Token** purpose-built for automation
(CI/CD, headless). That is the correct mechanism for us — tokens are
scoped and revocable, unlike the account password. Automated retrieval of
secrets at runtime is genuinely supported.

### My only caution

Do not make a **beta CLI the sole holder of every RDP credential on day one.**
Suggested staging: vault becomes the *preferred* path while the gitignored
creds file stays functional as a fallback. Migrate fully once the CLI has
settled. A migration that depends on beta tooling should not be a single point
of failure for the whole fleet on its first day.

---

## 4. RECOMMENDED — Pre-commit enforcement (the actual answer to "enforce it")

The boss asked specifically how to *enforce* vault use so raw passwords do not
reappear. A `.gitignore` entry is passive; it does nothing for an existing file
someone force-adds. Enforcement has to be a gate.

A `pre-commit` hook that:

1. Scans **staged** content for password patterns —
   `/p:`, `sshpass`, `--password=`, `PROTON_PASS_PASSWORD`, high-entropy
   strings assigned to pass-like variables.
2. **Blocks the commit** (non-zero exit) and prints the offending file/line.
3. Points the committer at the vault as the sanctioned path.
4. Skips obviously-safe files (`.md` prose, test fixtures) to avoid noise.

This is what actually enforces the policy — including against future-me, which
is the realistic threat model. Worth noting: 4 of the 12 hits are in *generator
scripts*, meaning the exposure is **manufactured at build time**. Fixing only
the generated output, without fixing the generator, guarantees recurrence.

---

## 5. EXISTING TOOLING — `fleet-key-manager.py` (found on this node)

Before building new infrastructure: the fleet already has one.

`fleet/fleet-key-manager.py` — central credential server, TCP JSON on port
**8220**, Tailscale auth keys + API tokens + fleet credentials, with an audit
log. This is the right *shape* of solution and it is worth reusing.

### Two problems to resolve if we adopt it

1. **It stores credentials in plaintext.**
   `KEYS_FILE.write_text(json.dumps(self.keys, indent=2))` — the key material
   is written as-is. There is an audit trail but no encryption at rest.
2. **Its storage directory is not gitignored.**
   `SECURITY_DIR = ~/fleet-security` — `.gitignore` has no entry for it. So the
   moment it runs with real keys, that data is eligible for commit.
   **This is a live footgun, not a theoretical one.**

### Current status

Port 8220 is **not open on any online node** — it is currently not running.
So there is no migration conflict today; we would be activating it fresh.

### My read

`fleet-key-manager.py` and Proton Pass are **competing designs for the same
job**: a central credential store. Adopting both means two sources of truth
and two things to audit. I would pick one.

Proton Pass advantages: encryption at rest, off-site, access tokens,
independent audit trail, no self-hosted thing to keep alive.
Key-manager advantages: already written, fleet-native, no external dependency,
no beta tooling.

**Not my call — but please make it a deliberate choice rather than ending up
with both.**

---

## 6. Sequencing recommendation

Today's migration already includes: credential rotation, vault setup, launcher
rewrite, enforcement hooks, and a fleet-wide SSO/DC rollout. That is a lot of
change surfaces at once, and some are hard to reverse.

| Phase | Scope | Depends on SSO decision? |
|---|---|---|
| **1 — Stop bleeding** | Rotate RDP creds; strip `/p:` from generators; rebuild launchers | **No** — do now |
| **2 — Enforcement** | Pre-commit hook | No |
| **3 — Vault decision** | Proton Pass vs key-manager; adopt one, not both | Follows decision |
| **4 — Migrate secrets** | Move credentials into chosen store; dual-path until proven | Follows 3 |
| **5 — SSO** *(if wanted)* | realm/sssd join, if we accept the SPOF tradeoff | Follows 3 |
| **6 — History purge** | `git filter-repo` + force-push + fleet re-sync | **Needs APB + freeze** |

**Phases 1 and 2 are correct under every scenario above** and close the live
exposure. They should not wait on the architecture debate.

Phase 6 is the only one that genuinely cannot be done solo — it rewrites
history on every node.

---

## 7. What I need from the General

1. **Domain controller, or vault-only?** My recommendation is vault-only
   (§2), but it is the fleet's call.
2. **Proton Pass or `fleet-key-manager.py`?** (§5) — pick one.
3. **Can Phase 1 (rotate + strip) start today, in parallel?** Strongly
   recommended yes.
4. **Is there appetite for Phase 6 (history purge)?** It is the only way to
   actually remove the 26 commits. Needs a maintenance window and APB.

---

## Bottom line

The instinct to centralize credentials is right, and I support it. Two
adjustments:

- **Rotate the live RDP passwords first.** They are exposed now; the
  architecture debate does not change that.
- **Prefer a vault over a domain controller.** Same benefit, no new single
  point of failure.

Respectfully submitted — happy to implement any phase on request.

— **Mr. New Vegas**, Fleet Radio
*"Careful, careful. There's a lot of death in this desert."*
