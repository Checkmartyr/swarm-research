# Swarm Research

A Codex skill for planning and carrying out bounded, evidence-led research. It helps clarify what the user needs, coordinate research tasks, compare independent sources, fact-check important claims, and verify the final deliverables.

## What it does

- Clarifies the decision, audience, scope, constraints, and acceptance criteria before assigning research.
- Supports General and Technical research modes with Focused, Standard, and Deep effort budgets. The exact limits and rules live in [SKILL.md](SKILL.md).
- Builds a source plan, records source lineage and access limits, and looks for evidence that could contradict emerging conclusions.
- Creates fact-check cards for important claims with supporting and opposing evidence.
- Uses independent review and follows consequential corrections through dependent recommendations and report sections.
- Organizes active work, drafts, evidence, checkpoints, and final exports according to [the workspace layout](references/workspace-layout.md).
- Provides a read-only validator for plan, evidence, review, and saved-output records.

## Install

Copy the complete repository directory into your Codex skills directory:

- Windows: `%USERPROFILE%\\.codex\\skills\\swarm-research`
- Other platforms: `~/.codex/skills/swarm-research` (or `$CODEX_HOME/skills/swarm-research`)

Keep `SKILL.md`, `agents/`, `references/`, and `scripts/` together. The skill can then be invoked explicitly with `$swarm-research`; Codex may also select it automatically for a matching research request.

## Research workflow

The skill follows this sequence:

1. Read the user's request and relevant documents, then clarify open decisions with a document-grounded “grill” before dispatch.
2. Define requirements, acceptance checks, research tasks, source plans, and the effort budget.
3. Research within the authorized scope and record claims separately from direct observations and inferences.
4. Fact-check important conclusions, including conflicting and disconfirming evidence.
5. Synthesize the report, obtain an independent review, and revise affected recommendations when needed.
6. Validate the saved artifacts and read them back to confirm that the exported results match the final revision.

Resume work by checking the existing brief and state first. Preserve settled decisions unless the user changes them.

## Workspace and deliverables

The workspace separates mutable working material from user-facing deliverables:

- `work/<research-id>/` contains active task state, notes, source and claim records, scratch work, drafts, pending items, and checkpoints.
- `outputs/<research-id>/` contains reviewed deliverables and their supporting evidence records.
- `history/` holds superseded snapshots; `state.json` supports operational recovery; `sources.json` is a derived source index. Follow the detailed lifecycle and ownership rules in [references/workspace-layout.md](references/workspace-layout.md).
- If an Obsidian vault is part of the task, the verified vault copy is authoritative and exports are read back after saving. Record partial save failures instead of reporting them as complete.

The validator checks recorded structure and consistency. It cannot establish that a source is truthful or that a conclusion is substantively correct; human/source review remains necessary.

## Validate a research run

Requirements: Python 3.10+ and PyYAML.

```sh
python scripts/validate_research.py --plan <path> --vault-root <path> --export-dir <path> --phase draft
python scripts/validate_research.py --plan <path> --vault-root <path> --export-dir <path> --phase final
```

The validator emits JSON to stdout. Exit code `0` means the requested structural checks passed, `1` means it found errors, and `2` means the records are insufficient to validate. A passing result is not a fact-check verdict.

Run the test suite with:

```sh
python -m unittest discover -s scripts -p "test_*.py"
```

## Documentation

- [Skill instructions](SKILL.md)
- [Clarification and research brief](references/clarification.md)
- [Research protocol](references/research-protocol.md)
- [Output contracts](references/output-contracts.md)
- [Workspace layout](references/workspace-layout.md)
- [Validation contract](references/validation-contract.md)

