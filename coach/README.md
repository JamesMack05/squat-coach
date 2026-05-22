# coach/ — folder methodology

Bot's system prompt + behaviour spec. Claude reads this folder at runtime to construct its coaching behaviour.

## File-class strict separation (DC-26 — HARD RULE)

| File | Class | Holds | Does NOT hold |
|---|---|---|---|
| `identity.md` | **configuration** | Coach name, persona attributes — who the coach IS | Behaviour clauses, drill content, user state |
| `rules.md` | **behaviour** | Canonical RP-NN clauses, voice-mode gates, register-switch mechanism (DC-20 Constitutional spine) | Drill prose, persona attributes, user state, example interactions |
| `examples.md` | **examples** | Narrated coaching interactions citing RP-NN clauses by name (DC-27) | Restated rule text, drill content, persona |
| `reference/` | **content** | Drill library (DC-28 tabular), hypertrophy operationalisation, narrated-rep examples | Behaviour clauses, persona, user state |
| `profile-template.md` | **state-template** | Per-user state slot template; stamped at onboarding (DC-07) to create live `profile.md` | Behaviour, content, persona |

**Cross-contamination is a hard fail.** Drill prose in `rules.md` collapses EX-07 (multi-domain swap) into a behaviour rewrite — real retrofit cost. Each file does one job.

## Discipline citations

- **DC-04** — folder shape + 6 entries
- **DC-20** — Constitutional spine (rules.md canonical for behaviour; other files reference rules by name, never restate)
- **DC-21** — parameterisation discipline (identity, drill library, reference content built as pluggable parameters consumed by system-prompt template, not hard-coded prose)
- **DC-22** — read-before-write conflict check on `profile.md` writes
- **DC-26** — file-class strict separation (THIS FILE)
- **DC-27** — RP-NN naming convention (clauses in rules.md)
- **DC-28** — drill library as tagged lookup table (in reference/)

## How Claude consumes this folder

`bot/prompt.py` builds the system prompt as a list of cached blocks per the DC-21 parameterisation pattern: `identity.md` (configuration) + `rules.md` (Constitutional spine, DC-20) + all four files in `reference/` (content) + `examples.md` (few-shot priming). A single `cache_control` breakpoint sits on the last system block, so the whole user-invariant prefix hits the prompt cache across every user + every turn.

Per-user state (`profile.md`) and per-turn data (pose pipeline markdown, user message) live in the user message — NOT the system prompt — so the cache stays warm. `bot/prompt.py` reads `profile.md` fresh at the start of every turn via `bot/profiles.py`.
