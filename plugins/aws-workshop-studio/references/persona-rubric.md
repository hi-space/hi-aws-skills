# Persona evaluation rubric

So the generated workshop does not ship in a state that "only makes sense to the person who made it," level × role personas actually read it and finalize the improvements. Run it as a generate → adversarial-review → synthesis workflow (personas in parallel → sort by severity → apply loop).

## Matrix — activate only the cells that fit the audience

Run only the cells corresponding to the audience specified in `brief.yaml`. Running them all is wasteful.

| Level \ Role | Developer | Architect | Decision-maker/PM | Ops/SRE | Security | Data/ML |
|---|---|---|---|---|---|---|
| L100 intro | ✔ | | ✔ | | | |
| L200 | ✔ | ✔ | | ✔ | | ✔ |
| L300 | ✔ | ✔ | | ✔ | ✔ | ✔ |
| L400+ | | ✔ | | | ✔ | |

- **Level** judges prerequisite knowledge, explanation density, and hands-on difficulty. Does L100 hold your hand, does L400 go all the way to pitfalls and trade-offs.
- **Role** judges concerns. Does it cover what this role wants to know, and does it avoid dwelling at length on what they don't care about.

## What each persona produces (fixed schema)

```yaml
persona: "L200 / Ops·SRE"
findings:
  - severity: blocker | major | minor
    axis: stuck | needs-mismatch | use-case-unfit | difficulty-jump | terminology | insight-gap
    where: "scenario-a/scene3.md line 12 / features/a-04"
    problem: "an abbreviation this level doesn't know appears without explanation"
    fix: "concrete fix — change what, how (no abstract 'needs improvement')"
```

**Evaluation axes:**
- **stuck** — a term pops up without explanation, prior knowledge assumed, a jump in the hands-on steps.
- **needs mismatch** — doesn't cover what this role wants to know / too much of what they don't care about.
- **use-case unfit** — can't be mapped onto our (the customer's) situation.
- **difficulty jump** — difficulty spikes between adjacent scenes.
- **insight gap (INV-9)** — the page says what to do but not why this architecture or service was chosen, what it contributes, or what changes once adopted. Test: can this persona answer "so why should we adopt this?" from the site alone? The Architect and Decision-maker/PM personas **must** check the overview's architecture sections and every scene's "Why these services here" table; a generic answer ("improves security") or an unlabeled/invented figure is a `major`.

## Honesty rules

- **A "all good" review is treated as void.** Each persona seriously attempts at least 2 defects. If it can't find any, it says so explicitly.
- Be cold about severity. blocker = this persona can't finish the hands-on. major = finishes, but with misunderstanding or drop-off. minor = polish.

## Synthesis & apply loop

1. Gather findings from all personas → dedupe the same where/problem.
2. Sort by severity (blocker → major → minor).
3. **Apply all blocker & major**; minor is the SA's call.
4. If blockers remain after rebuild, repeat once more (max 2 rounds).
5. State any remaining unapplied items as "known limitations" in the handoff report.
