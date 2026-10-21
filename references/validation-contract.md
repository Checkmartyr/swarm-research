# Structured validation contract (schema 1)

Read when creating artifacts or validating draft/final delivery. Semantic rules remain in [research-protocol.md](research-protocol.md); storage ownership in [obsidian-workflow.md](obsidian-workflow.md). Python 3.10+ and PyYAML are required. Missing dependencies return an unverified result; the script never installs packages, calls services or edits notes.

## Invocation and result

```text
python scripts/validate_research.py --plan <actual-plan.md> --vault-root <vault> --export-dir <export> --phase draft|final
```

Use the actual committed vault plan for final validation. Draft accepts a pending local plan and validates available records without demanding finished review/exports. Capture stdout to a local `validation.json` receipt after the command completes. Output separates `structure`, `content`, `persistence` (project/dashboard/exports), computed counts, errors, warnings and unverified checks. Exit 0 means no detected structural/delivery errors and no outstanding recorded verification gaps, not that the program established source truth. Exit 1 means errors; exit 2 means missing evidence/unsupported format/access/dependency. Errors take precedence over unverified. Content results say `recorded-review-passed`, `limited`, or `unverified`; a reviewer attestation is not a machine proof.

Old notes without these blocks remain unchanged and return unverified-format. An audit can identify legacy defects separately; do not manufacture version-1 data or backfill missing review testimony to obtain a pass.

## Canonical records

Place exactly one fenced block with info string `json swarm-research-state` in the plan. Place fenced `json swarm-research-sources` and `json swarm-research-claims` arrays in the ledger or its parts. Canonical blocks, evidence anchors and report citations belong inside `# Swarm Research`; lookalike content in `# Personal Notes` is user content and cannot satisfy validation. Preserve IDs and explicit `<a id="s001"></a>` / `<a id="c001"></a>` anchors beside the records (batch arrays can follow an index of anchored headings). These are the maintained records; optional tables/prose summarize them. Avoid duplicating their facts in another independently maintained JSON file. [workspace-layout.md](workspace-layout.md) defines local `state.json` for observed I/O/recovery and generated `sources.json` caches with input hashes. They do not replace these canonical blocks, and the current validator does not validate those local operational/cache schemas.

Plan state fields:

| Field | Value |
|---|---|
| `schema_version`, `run_id`, `revision`, `research_status` | `1`, stable UUID, positive checkpoint integer, storage workflow research state |
| `brief` | `{status, branches}`; every branch has `{id, topic, depends_on, status, resolution, basis, scenario_check}`. Core topics: decision, audience, terms, scope, time, geography, constraints, assumptions, deliverables, acceptance. `basis` cites context/doc/user answer; scenario check records the challenge and outcome. |
| `budget` | `{assignment_limit, round_limit, review_limit, recheck_limit}`; nonnegative integers, defaults follow selected tier. |
| `events` | Ordered `{id, kind, task_id, attempt, round, at}`. Kinds: `research_dispatch`, `review_dispatch`, `recheck_dispatch`; unique event ID, ISO timestamp. Research round 0 is initial; positive IDs form follow-up batches. Review/recheck use round 0 and separate counters. |
| `tasks` | `{id, kind, depends_on, question, scope, method, output_location, acceptance, status}`; acceptance array entries `{text, status, evidence}`. Status `met/limited/unmet`; evidence is an artifact reference. Task states/kinds follow output-contracts. |
| `requirements` | `{id, text, obligation, status, tasks, artifacts, review_disposition, limitation}`. Obligation `required/target/conditional`, status `met/limited/unmet`, disposition `passed/limited/pending`. A limited/conditional requirement explains limitation/condition. Required unmet/limited items prevent complete. |
| `artifacts` | `{report, ledger, parts, review, dashboard}`. Project filenames are relative to the plan directory; `parts` array may be empty. `review` is the independent review note. `dashboard` is vault-relative. |
| `reviews` | Array of `{kind, reviewer, independent, status, report_sha256, scope_claims, scope_requirements, claim_digests, requirement_digests, findings}`. Reviewer identity is nonempty; kinds `review/recheck`, status `passed/limited/failed`. Digest maps bind each scoped ID to the exact reviewed record/passages. Findings: `{id, severity, status, resolution_artifacts}`; severity `critical/high/medium/low`, status `open/resolved/accepted-limit`. Resolution references are mandatory for resolved/accepted-limit findings. |
| `manifest` | Map of every non-plan project filename to `{managed_sha256, owned_metadata_sha256}`. Include report, ledger, every part and review note. Never the plan's own hash. |

An artifact reference is `{path, anchor}` relative to the plan's project directory, with an explicit HTML anchor in managed content. Keep these within declared project artifacts (or the plan itself). A requirement's section runs from its anchor to the next standalone HTML anchor or the end of managed content; place explicit boundaries around each deliverable. Task scratch `output_location` is descriptive and may be outside the project; acceptance evidence points to merged artifacts. Use acceptance evidence and review disposition, not a bare task-finished flag. Require at least one requirement and accountable task mapping; complete outcomes cannot conceal pending/partial tasks. A cancelled out-of-scope task needs `failure_or_gap` explaining its removal.

Usage and remaining budget are calculated from events, not stored counters. An attempt is a real dispatch even when unsuccessful; retry attempt numbers increment per task. Completed research/review/recheck tasks need corresponding dispatch events; coordinator synthesis needs none. Positive research round IDs are consecutive from 1. Requirement/task IDs must resolve; dependency graph is acyclic; prerequisite tasks must be accepted before downstream completion.

Source records:

```json
{"id":"S001","title":"Original study","publisher":"Publisher","url":"https://example.org/study","published_at":null,"accessed_at":"2026-10-22T10:00:00+07:00","version":null,"kind":"primary","lineage":"original-study-1","inspection":"inspected","access_scope":"full","locator":"Table 2","limitations":"Bounded sample","group":{"region":"TH","role":"buyer"}}
```

`kind`: `primary/secondary/repository/marketplace/search-excerpt`. Inspection: `inspected/discovery-only/inaccessible`. Scope: `full/partial/abstract/search-excerpt/none`. Date/version unknowns are explicit nulls. `group` is optional metadata for computed counts, not evidence of a purchase. Identical lineage labels are one underlying evidence origin; reviewers validate their accuracy. An inaccessible target has scope `none`; an inspected excerpt has scope `search-excerpt` and kind `search-excerpt`. Each URL/path is a locator, not permission to read private content or execute anything.

Claim records:

```json
{"id":"C001","statement":"A bounded finding","material":true,"type":"source-reported","nature":"descriptive","scope":"Study sample and date","assessment":"supported","qualified":false,"numeric":false,"evidence":[{"source_id":"S001","relation":"support","locator":"Table 2 row 1","paraphrase":"What the table establishes"}],"fact_check":{"method":"Reopened original table","verified_by":"coordinator","counter_search":{"query":"Competing results","outcome":"No independent replication found within this search","source_ids":[]},"independence_note":"One original experiment","single_source_reason":"Statement describes this primary source's bounded result","conflict_resolution":"No conflicting result located; not proof of absence","numeric_check":"Not applicable","conclusion_impact":"Limit generalization"}}
```

Types: `source-reported/direct-observation/inference/proposal`; nature: `descriptive/comparative/causal/trend`. Assessments: `supported/partially-supported/disputed/unresolved`. Evidence relation: `support/contradiction/context`. Supported/partially-supported material findings need supporting evidence; disputed/unresolved propositions may have only counter/context evidence or a documented unsuccessful search. Proposals need explicit design reasoning rather than a fictitious source. All material claims need completed fact-check fields; numeric ones need a meaningful arithmetic check. Limited/disputed/unresolved claims require `qualified: true` and matching report caveats assessed by reviewer.

A fully supported comparative/causal/trend claim needs two inspected independent support lineages. A descriptive single-source supported claim needs an authoritative primary/repository source and `single_source_reason`; otherwise qualify its assessment. Sole search excerpts cannot establish a fully supported material finding. Explicit contradiction with a supported verdict requires a recorded reconciliation, which the reviewer judges substantively.

Each material claim appears as a link to its ledger anchor in the report. For facts/inferences, put a direct URL supporting the assessment in the same paragraph/table row. For unresolved/disputed claims this can be context or contradiction rather than support for the asserted proposition. An unresolved search with no evidence stays explicitly unresolved and records the search limit instead of inventing a supporting source. Proposal claims use a Claim ID and label their assumptions; they need not invent external citations. Every source/claim record has its own anchor, including when split across parts.

## Digests, readback and limits

Use `sha256-utf8-lf-v1`: UTF-8 text with CRLF/CR converted to LF and no trimming. The managed body is the exact text after the unique `# Swarm Research` heading text (including its trailing newline) and before the sibling `# Personal Notes` heading. A report's reviewed digest hashes that body. Put final review status in the plan, not an added report paragraph that would change the digest.

Use the validator's `claim_digest(claim, report, sources)` and `requirement_digest(requirement, docs)` helpers when recording review; `sources` is the current ID-to-record mapping. The first hashes compact key-sorted JSON of `{record: claim, passages: [exact managed report paragraphs linking that claim], sources: {referenced ID: full source record}}`, including evidence and counter-search sources. The second hashes `{record: requirement, sections: [exact anchor-bounded managed artifact sections in reference order]}`. Review coverage counts only scoped IDs whose digest still matches current content. Unchanged previously reviewed items retain coverage; changed items/source revisions need recheck coverage at their current digest. An empty recheck cannot launder an old review onto new content. The last reviewed whole-report digest must also match. Human review still checks uncited material statements and whether declared scopes/qualifications are truthful.

Owned metadata digest is SHA-256 of compact recursively key-sorted JSON for `title,created,updated,type,tags,sources,swarm_owner,run_id,checkpoint_revision,research_status`, literal Unicode and preserved array order. ISO timestamps must be quoted strings in YAML. Exclude unknown/user-owned keys. The validator requires metadata/revision agreement, valid known links/anchors, the full companion manifest, and readable final vault files. It does not rewrite or validate arbitrary Markdown syntax beyond these contracts.

Exports are the same confirmed notes with wikilinks converted to Markdown: same-run targets are relative, outside-run targets use verified absolute vault files, claim/source heading IDs use their explicit lowercase anchors. Include `dashboard.md` snapshot with its current run row/revision; other runs can point to their existing vault files. Validation reads actual files and compares converted snapshots, never a file against itself.

Project readback, dashboard freshness and export freshness are separate results. Transient `save_state`/previous error text belongs in a pending record or validation receipt, not the canonical plan state. A receipt records observations after the reads and cannot promise future synchronization. Final complete requires all mandatory deliverables, accepted tasks, recorded material-claim/requirement review coverage and no unresolved critical/high finding. If delegation is unavailable, retain the disclosed self-review but final content stays unverified rather than inventing independence.
