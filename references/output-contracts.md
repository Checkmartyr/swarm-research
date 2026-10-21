# Research output contracts

Use these formats when creating the plan, merging evidence, and writing the report. Adapt presentation to the audience while preserving the fields needed for provenance and resumption.

Use [validation-contract.md](validation-contract.md) for versioned machine-readable records and the read-only validator. These records live in the same plan/ledger as their human-readable interpretation; derive summaries from them, not a separately edited state file. Use [clarification.md](clarification.md) before deciding the brief is settled.

## Locations and ownership

Honor explicit user destination overrides. Read [workspace-layout.md](workspace-layout.md) for local folder/file responsibilities and [obsidian-workflow.md](obsidian-workflow.md) for vault ownership and saving. Use the same readable run-folder under the selected work root and `outputs/`; keep the UUID as internal identity. Resume recorded locations for an existing investigation. The coordinator owns shared drafts, canonical records, operational state, generated caches and exports; researchers write only their assigned scratch locations.

Files are `<topic>-research-plan.md`, `<topic>-evidence.md`, and `<topic>-report.md`. Obsidian copies use vault-relative wikilinks; local exports use relative Markdown links between companions, plus direct source URLs or supported local-file links. Export split child notes and verify their links too. In no-write environments, present equivalent content inline if permitted and disclose unsaved state; in host Plan Mode return only the research plan in the host's required format without creating vault notes.

## Research plan

Record:

- **Brief:** question, intended audience/use, selected mode, scope exclusions, relevant timeframe, required sources, and overall acceptance criteria.
- **Clarification:** settled decision-tree branches with their document basis, resolution and scenario check; unresolved consequential branches block dependent research.
- **Requirements:** stable IDs, obligation (`required`, `target`, `conditional`), affected tasks, artifact/section evidence, acceptance status, review disposition and limitation/condition where applicable. Every requested deliverable, language and count is represented.
- **Budget:** selected effort/custom limits; assignment ceiling and used/remaining counts; follow-up rounds used/remaining; review and recheck state; concurrency cap; execution start and deadline when applicable.
- **Method:** source strategy, access/tool limitations, and independent or sequential execution.
- **Dependency graph:** task IDs and edges; execution waves are illustrative, while satisfied dependencies control readiness.
- **Tasks:** use the record below for each task, including synthesis and review tasks. Distinguish research assignments from coordinator/review work for budget accounting.
- **Handoff:** failures, unresolved questions, output locations, next eligible tasks, and the latest update timestamp.
- **Persistence:** stable run ID, verified vault binding, vault-relative folder and dashboard paths, active backend, checkpoint revision and managed-content manifest, local export location, and any pending-save/conflict information. Follow the Obsidian workflow for commit ordering; research status and persistence status are distinct.

```yaml
id: T1
kind: research
depends_on: []
research_question: "The bounded question this task will answer"
scope: "Included and excluded subjects"
method: "Sources, evidence collection, and checks"
output_location: "Scratch note or shared artifact location"
acceptance_criteria:
  - "An observable condition for completion"
status: pending
attempts: 0
failure_or_gap: null
completed_output: null
```

Task kinds: `research`, `synthesis`, `review`, `recheck`. Statuses: `pending`, `running`, `complete`, `partial`, `failed`, `blocked`, `cancelled`. A retry increments attempts and consumes another research assignment. Coordinator synthesis does not consume a research assignment. Review accounting follows the research protocol.

Update the plan at dispatch/completion and reconcile after each wave. Mark the overall outcome as complete, partial, or blocked based on acceptance criteria, not merely whether agents finished.

## Evidence ledger

Use stable source IDs (`S001`) and claim IDs (`C001`). Preserve them when revising or resuming. Keep the source registry and claim records together until the vault's note-length rule requires linked parts; the root ledger then indexes those parts and retains claim-link stubs. Worker notes can retain provisional task-prefixed IDs.

### Source registry

For each source record:

- ID, title, author/publisher, URL or local path, and source type.
- Publication/update date when available, access date, and relevant version/revision.
- Inspection status: `inspected`, `discovery-only`, or `inaccessible`; access scope: `full`, `partial`, `abstract`, `search-excerpt`, or `none`. An inspected excerpt cannot be counted as an inspected underlying full page.
- Underlying evidence lineage and limitations affecting interpretation.

Unknown dates remain explicitly unknown. Access date is not publication date. A discovery-only or inaccessible source can identify a gap but cannot establish a claim.

Give each source a stable heading such as `### S001` and portable anchor `<a id="s001"></a>`. Claim evidence links to these source records. Preserve a root heading/anchor stub pointing to the child if a source record moves during splitting, just as for claim records.

### Claim record

For each material claim record:

- **ID and statement:** a specific, bounded claim, with timeframe/population/version where relevant.
- **Type:** source-reported finding, direct observation, or inference. For an inference, state the reasoning and its limits.
- **Evidence:** source IDs with precise page/section/line/table/passage locators; indicate support, contradiction, or contextual relevance. Include a brief paraphrase or permitted short excerpt to make the link auditable.
- **Fact-check:** coordinator identity, verification method, disconfirmation search and outcome, independence/single-source rationale, conflict resolution, numerical check where applicable, and consequence for conclusions.
- **Assessment:** `supported`, `partially-supported`, `disputed`, or `unresolved`; qualitative confidence with a reason tied to evidence quality, independence, applicability, and consistency. A limited/disputed/unresolved claim remains visibly qualified in the report.
- **Provenance:** originating task IDs, verification/reviewer findings, and remaining gaps.

Separate a source's assertion from the researcher's conclusion. Record contrary evidence beside supporting evidence. Do not assign numerical confidence without an appropriate method.

## Research report

Write a reader-facing report with:

1. The research question and the answer or best-supported findings, stated early.
2. Findings and synthesis organized around the user's question; consequential factual claims carry a direct source citation and a link to their claim record in the ledger.
3. Competing explanations or disagreements and how they affect the conclusion.
4. Methods and coverage: mode, timeframe, source approach, work completed, and review status.
5. Limitations, unanswered questions, incomplete tasks, and any useful next investigation.

Use stable claim headings such as `### C001` in the root ledger, with an additional `<a id="c001"></a>` for portable Markdown exports. Obsidian reports link to the vault-relative ledger path and heading, for example `[[Research/swarm-research/<run-folder>/<topic>-evidence#C001|C001]]`; exports use `[C001](<topic>-evidence.md#c001)`. If a claim moves to a child note, keep its root heading/anchor and point it to the child. Direct source links should point to the supporting page or artifact, not a search-results page. Clearly mark inference and recommendations rather than presenting them as sourced facts.

State when a deadline, assignment cap, missing access, or failed review limited the result. Do not claim exhaustive coverage from a bounded search. Finish with links to the plan and evidence ledger. The chat delivery links all three local exports, identifies the vault location, and briefly describes material limitations, including pending vault saves or stale dashboard/exports.

Completion requires the actual requirement matrix and fact-check/review dispositions, not just terminated agents. Incomplete mandatory deliverables keep the outcome partial. Access-limited targets may close with disclosed limits when the brief explicitly allows that. Preserve source/claim anchors through splitting and validate the actual vault/export snapshot after the last edit.
