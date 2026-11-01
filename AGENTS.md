# Agent instructions

## Keep the repository true today

- Every committed sentence must describe the project as it is now.
- When something changes, rewrite it in place. Don't add "previously",
  "formerly", "deprecated", changelog notes or strikethrough text. Git history is
  the archive.
- Don't commit brainstorming, meeting notes or transcripts.

## Where things live

- `README.md`: what handful is and why it exists.
- `docs/architecture.md`: the current design, including a Mermaid architecture
  diagram, plus a short list of items not decided yet.
- `docs/decisions/`: one file per accepted architecture decision, with its
  reasoning.

For any architecture discussion or decision, use the `architecture-drilldown`
skill. When chords, key names or timings change, use the `update-mappings`
skill so the drawings and docs stay in step.

## Rules

- Dependencies must be permissively licensed (MIT, BSD, Apache-2.0, Zlib or
  similar). No GPL, LGPL or AGPL.
- Don't copy code from other projects. Other keyboards and firmware are
  inspiration only.
- The user wires the hardware; agents write the firmware. When firmware needs
  a wiring change, say exactly which pins and parts.
- Keep the tone positive in user-facing text.
- Show the user the diff and get approval before committing or pushing.
