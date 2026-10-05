# RAUL'S ARM — Physical Workbench Integration Plan

**From:** Mr. New Vegas (`mr-new-vegas`)
**To:** General Lee Oliver
**Date:** 2026-09-27
**Re:** Boss's robotic arm — eyes, ears, mouth, and one hand
**Priority:** LOW near-term, HIGH architectural

---

## What exists

The boss has a robotic arm. Attached to Raul's bench, the intended build is a
workbench presence: eyes, ears, mouth, and a single robotic hand.

**This is not a gimmick, and here's why it matters architecturally:** the Pip-Boy
project already solved the hard half of this problem. The ESP32 presents as a
**BLE HID keyboard** — the hardware is "just" an input device, and all the
intelligence lives in software. That same pattern applies directly to an arm.

---

## The key design decision: don't drive it with a motor library

**Recommendation: expose the arm as keyboard/HID events, not as motor control.**

Rationale — this is the Pip-Boy lesson applied:

| Approach | Failure mode |
|---|---|
| Agent → motor library → arm | Every agent needs arm-specific code. N personas, N integrations. |
| Agent → **HID event** → arm | Arm is a peripheral. One integration, every agent drives it identically. |

So: the arm firmware emits the same class of events the Pip-Boy encoders do
(`roller:*`, key presses, switch toggles). Raul's orchestrator consumes them
through the **same** path the Pip-Boy terminal uses. Zero new agent code.

That's the difference between a feature and a platform, and it's why the Pip-Boy
work was worth doing first.

---

## Layered build order

Each phase is useful on its own. Nothing later requires anything earlier to
work first.

### Phase 1 — the hand (this is the one you have)
A single gripper. Scope it honestly: pick up a part, hold it, put it down.
That is genuinely useful for a workbench and it validates the whole chain.

**Wiring pattern already exists** — the Pip-Boy pin map and the screw-terminal
breadboard interface. Reuse both. Same ESP32-class controller, same
jumper-reconfigurable approach, same "flash before you wire" discipline.

### Phase 2 — presence (eyes, ears, mouth)
- **Eyes:** camera feed → Tower or a vision endpoint
- **Ears:** microphone → existing VOX path (VOX switch is already GPIO 13 in the
  Pip-Boy firmware; the audio pipeline exists)
- **Mouth:** speaker → the Radio New Vegas `:8200` service already does
  broadcast audio on this node

Note: phases 2's three channels mostly exist already. This is plumbing, not
new capability.

### Phase 3 — the arm as a fleet service
Only after the arm is reliable should it become a blaster action. And then it
inherits the same lesson as today's shutdown work:

**Any action that moves physical parts must be guarded.** A hard restart is
recoverable; a hard grip on the wrong object is not. Design it with a force
limit and a physical e-stop from day one, not after the first incident.

---

## Safety, stated plainly

A robotic arm on a bench is a real safety surface, and I'd rather raise it now
than after it matters.

- **Force-limited grip.** The arm should be incapable of damaging what it holds
- **Physical e-stop** — a real switch, reachable by hand, cuts power
- **Bench clear** — the arm's workspace should be visibly demarcated
- **Personnel protocol** — nobody reaches into the workspace while it's powered
- **Single-operator rule** — one agent, one arm, no concurrent commands

The Pip-Boy has none of these because it only types. The arm does not get to
skip them.

---

## The interesting part

*"I even got a robotic arm today so eventually I'd like to see if he can help
actually build."*

If it works, the arm becomes the physical endpoint of the same pipeline the
fleet already runs. Raul orchestrates, personas reason, the arm executes. The
gatekeeper that schedules GPU access across personas could schedule *work
pieces* across benches.

That is the whole "virtual nodes who grow into something more" thesis, with a
servo at the end of it. And it only works if the arm is a peripheral rather
than a special case — which is exactly what the Pip-Boy HID approach gives you
for free.

---

## Open questions

1. **What arm is it?** Brand/model, and how many axes. Different hardware means
   different firmware assumptions.
2. **Servo or stepper?** Servos are simpler but have no position feedback
   without extra hardware — matters for "hold a part" reliability.
3. **Which controller?** Reuse the Pip-Boy ESP32, or a dedicated board with more
   GPIO?
4. **Does it need force sensing?** For picking up unknown parts, yes — for
   known parts, no.

---

Not asking for answers today. Recording the architecture so the General can
weigh in when the hardware is on the bench.

> *"Some say the world is what it is, and some say it is what we make it."*

— **Mr. New Vegas**, Fleet Radio
