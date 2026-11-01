---
name: architecture-drilldown
description: Use when discussing, deciding or changing handful's architecture (microcontroller, firmware stack, chord detection and timing, key mappings, configuration, OS targets, switches, wiring, enclosure, wireless, dependency licensing). Records the outcome in docs/architecture.md and docs/decisions/ without leaving outdated text behind.
---

# Architecture drilldown

The repository records only the current architecture. Git history keeps
everything that has been replaced.

## Start

1. Read `docs/architecture.md` and every file in `docs/decisions/`. Together
   they are the current state.
2. Pick topics from the "Not decided yet" list in `docs/architecture.md`. If the
   file doesn't exist yet, ask the user which topics to cover.
3. Don't read git history unless the user asks why an older decision changed,
   except for the metadata query needed to allocate a new decision number.

## Discuss

- Keep exploration, options and back-and-forth in the conversation. Don't
  commit them.
- Present real options with tradeoffs, and let the user make the decision.
- Ask one focused question at a time, with the options as choices and the
  recommended one first.

## Record a decision

When the user makes a decision, do all of the following in the same change:

1. Add `docs/decisions/NNNN-short-title.md`, numbering it after the highest
   number ever used. Check `git log --all --diff-filter=A --name-only --
   docs/decisions` so numbers from deleted files are never reused. Use the
   template below.
2. Update `docs/architecture.md` so it describes the design with the decision
   in place. Remove the topic from "Not decided yet".
3. Update the architecture diagram if the decision changes components, links
   or power paths (see "Architecture diagram").
4. Create `docs/architecture.md` if it's missing. Use these sections: Overview,
   Diagram, Components, Interfaces, Power, "Not decided yet". Include only
   sections that have content.

If a file in `docs/decisions/` exists, the decision is accepted. There is no
status field.

## Replace a decision

1. Delete the old decision file in the same change that adds the new one.
2. In the new file, add `Replaces: ADR-NNNN (removed; see git history)` under
   the title.
3. Rewrite the affected parts of `docs/architecture.md`.

Never keep a replaced decision in the tree, and never mark one as deprecated.

## Architecture diagram

- Keep the diagram as a fenced ` ```mermaid ` block inside the "Diagram"
  section of `docs/architecture.md`, so GitHub and local Markdown previews
  render it from text. Don't commit exported images.
- It shows the current design only: buttons, microcontroller, firmware layers,
  host computer and power, with labelled links (for example `GPIO`, `USB HID`,
  `BLE HID`, `5 V`).
- Use `flowchart` (and `sequenceDiagram` for protocols, `stateDiagram-v2` for
  chord detection). Avoid experimental
  Mermaid types such as `C4Context` or `architecture-beta`, which GitHub may not
  render.
- Show undecided parts with a dashed link or a node labelled "TBD". Remove the
  label once the part is decided.
- Validate the syntax before finishing:
  `npx -y @mermaid-js/mermaid-cli -i docs/architecture.md -o /tmp/arch.md`.

## Decision template

```markdown
# NNNN: Short decision title

## Context

The problem and the forces at play, stated as facts.

## Options considered

- Option A: one-line tradeoff.
- Option B: one-line tradeoff.

## Decision

We will ... (full sentences, active voice).

## Consequences

Positive, negative and neutral effects, including what this makes harder.
```

Keep each decision under a page.

## Before finishing

- Search the changed files for "previously", "formerly", "deprecated", "old",
  "TBD later" and "superseded". Rewrite any hit so it describes the present.
- Check that `docs/architecture.md`, including the diagram, doesn't contradict
  any decision file.
- Open each changed doc in the editor side panel, then show the user the diff.
  Commit only after approval, with a message that says why the decision was
  made.
