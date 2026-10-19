# Research protocol

Read this before assigning research or review. Artifact schemas live in [output-contracts.md](output-contracts.md).

## Budgets and scheduling

An **assignment** is one dispatched research brief, including a retry or a substantial new brief sent to an existing worker. Sequential fallback counts the same units. Clarifying an existing brief does not consume another assignment unless it adds substantive research scope. Debit the assignment when dispatched, even if it later fails. Workers do not spawn additional agents or expand their briefs; the coordinator owns scheduling and accounting.

A **follow-up round** is a coordinator-authorized batch of targeted research after initial synthesis or review. Initial dependency stages are not follow-up rounds. All assignments across all stages, retries, and follow-ups share the selected tier's total. Focused permits an initial pass only; an initial task retry can use an unspent assignment, but new questions after synthesis require an expanded user budget.

For Standard, aim to reserve two assignments for its follow-up round; for Deep, aim to reserve four across its two rounds. Initial task count can be lower when fewer tasks answer the question. These are planning defaults, not minimum workloads. Never manufacture tasks to use the allowance.

Review and optional recheck are separate from the research assignment count. Reserve capacity for one reviewer distinct from the research workers whose work is being assessed. A reviewer may inspect cited sources within review scope; a new research question returns to the coordinator and consumes a research assignment. Recheck can use the same reviewer. If review fails, the optional recheck allocation can fund one replacement attempt; further review attempts require an expanded budget. If both attempts fail, deliver with an explicit unverified status.

Honor explicit user caps on elapsed time, assignments, concurrency, or total agent use. Concurrency is the minimum of available worker slots and any user concurrency cap; do not count the coordinator as an available worker slot. A total-agent/assignment cap includes review when the user says it does. If only a time budget is supplied, use Standard's assignment/round ceilings under that deadline and state this operational default. If only a custom assignment cap is supplied, use Standard's round ceiling and the separate review allowance unless the cap explicitly includes all work. Clarify incompatible limits before dispatch, such as requiring independent review while forbidding any reviewer.

Start an elapsed-time budget when research execution begins and record the deadline with its timezone. Check remaining time before dispatch and between results. Reserve a practical portion of the time for synthesis and review; close early if needed to meet the deadline. At the deadline, stop dispatching, request workers to stop, collect already available partial findings, and consolidate. Cleanup/report assembly may finish after the deadline, but disclose that overrun and perform no new research. Never claim token usage precision unless the host exposes it.

Use host-supported interruption/cancellation when available. Until a worker acknowledges stopping, retain its actual running state and note that interruption is pending; mark it partial or cancelled once confirmed. Base the deadline-limited report on evidence available by the cutoff. Log late returns separately as unincorporated results rather than silently extending the research window; using them in a renewed investigation requires a renewed budget.

On resumption, follow [obsidian-workflow.md](obsidian-workflow.md) to read authoritative vault notes and reconcile pending checkpoints before scheduling work. Local exports may be stale. Verify which tasks actually completed, and preserve consumed budget unless the user renews it. Preserve existing run/task/claim/source IDs. If accounting is missing or inconsistent, reconstruct it from available records or ask before assuming a fresh budget.

Only the coordinator saves vault notes, dashboard entries, and exports. Researchers return separate scratch notes. Checkpoint at dispatch/completion, after each wave, and during review, completion, or interruption. Vault connection checks and saving do not consume research assignments, but do consume elapsed time; avoid repeated polling when an access condition has not changed. Save failures affect persistence status, not the truth of research task outcomes, and must remain visible until verified recovery.

## Mode-specific evidence

### General

Use sources suited to the actual question: original studies and datasets for scientific claims, official statistics and filings for economic or organizational facts, first-party records for stated policies. Secondary sources can provide context or surface competing interpretations; label their role and trace consequential claims to underlying evidence where accessible. Distinguish what a first-party source asserts from what independently establishes the assertion.

For consequential disputed claims, seek independent corroboration within the budget. Two articles repeating the same study, press release, or dataset are one evidence lineage. If corroboration is unavailable or conflicting, keep the claim qualified and record the uncertainty. Match current claims to current sources and historical claims to their historical period.

### Technical

For codebase questions, inspect applicable repository instructions, relevant entrypoints, dependencies, lockfiles, tests, and version information. Record the revision or inspected working state, including relevant uncommitted changes when observable. Avoid treating current upstream docs as proof of behavior in an older installed version.

Consult Context7 when available for relevant external libraries/frameworks/APIs. If unavailable or insufficient, use official version-matched docs, specifications, release notes, or upstream source through available search tools. Record version/access gaps. Local code can establish implementation behavior; documented guarantees and runtime observations are distinct evidence categories.

Read-only checks can validate claims when permitted. Do not implement fixes or mutate the target system as part of research. Necessary access or extra permission must come through the host's normal mechanisms; unavailable access becomes a documented limitation.

## Worker handoff

Provide each researcher:

- The research brief, selected mode, task ID, and specific question.
- Scope boundaries, prerequisite findings, and acceptance criteria.
- Source strategy, freshness/version requirements, and applicable user constraints.
- Its assignment deadline, the separate scratch output location, and available tools.
- Instructions to work within this assignment without subdelegation or edits to shared artifacts.

Require a return containing answered questions, findings with precise source locators, supporting and conflicting evidence, evidence versus inference, source inspection status, remaining gaps, and acceptance-criteria status. Use task-prefixed provisional IDs in worker notes; the coordinator assigns stable ledger IDs during merge. A tool failure or inaccessible source is a limitation, not evidence for a negative claim.

If filesystem output is unavailable but research is otherwise permitted, return structured notes in the agent response. The coordinator can consolidate inline. Source excerpts should be limited to what is needed to verify claims and comply with applicable quotation limits.

## Merge and failure handling

Deduplicate sources by underlying evidence lineage, retaining distinct versions when relevant. Confirm important claims against their cited source passages; worker confidence is not verification. Record sources actually inspected separately from discovery-only links. Search snippets alone do not establish that the underlying source was inspected.

Mark a task complete only when its acceptance criteria are met. On failure, record the cause and usable partial results. Retry or narrow the task only when allowance remains, counting a new research attempt as another assignment. For blocked dependencies, either complete the prerequisite, explicitly revise the dependent task to a viable independent question, or leave it blocked. Do not silently treat partial evidence as a satisfied prerequisite.

If a delegation tool is absent or unavailable, run tasks sequentially with the same accounting and outputs, and label self-review as lacking independence. If delegation fails mid-run, account for the failed dispatch and any sequential retry. If evidence access is unavailable altogether, report the access gap and a partial plan rather than inventing findings.

## Independent review handoff

Give the reviewer the original research brief, task acceptance criteria, draft report, ledger, inspected source locations, and remaining budget. Ask for specific actionable findings without prescribing the conclusion:

1. Trace consequential report claims to source passages. Flag unsupported extrapolation, stale versions/dates, discovery-only citations, and mismatches between evidence and stated confidence.
2. Identify omitted perspectives or unanswered questions that materially affect the conclusion.
3. Examine contradictory evidence and whether apparent corroboration comes from independent sources.
4. Return each finding with affected claim/task IDs, the supporting reason, and a proposed correction or targeted research question.

The coordinator resolves findings by correcting the report, adding bounded research, or explicitly documenting unresolved limits. Recheck only repaired findings and any consequential claims changed by the repair. The review loop ends when its allowance is used, even if gaps remain.
