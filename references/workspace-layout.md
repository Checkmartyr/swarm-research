# Workspace roles and artifact lifecycle

Read before creating local run files, assigning scratch paths, saving a checkpoint, or resuming. This reference owns local layout and file responsibilities. [obsidian-workflow.md](obsidian-workflow.md) owns vault access, locking, preservation and write ordering; [validation-contract.md](validation-contract.md) owns canonical records and validation.

## Roots and identity

Use `work/<run-folder>/` for execution and recovery, and `outputs/<run-folder>/` for the delivered snapshot. The default run-folder is `YYYY-MM-DD-<topic>` with the same collision suffix in both roots. The UUID `run_id` stays inside records and is independent of directory names. Discover and reuse recorded paths on resume. Honor an explicit `works/` root or an existing user-selected root; record it in the location map and use that one root consistently rather than creating both `work/` and `works/`.

The committed Obsidian plan/ledger are authoritative after verified readback. Before the first save, the locally prepared plan/ledger are explicitly pending. Newer unpublished research belongs in drafts and a durable pending transaction until reconciled with the committed snapshot. Local operational records and caches describe those files; they do not independently decide research status, budget, source truth or review acceptance.

Illustrative layout; create optional folders only when they contain actual work:

```text
work/<run-folder>/
  run.json
  resume.md
  state.json
  sources.json                         # generated once a canonical registry exists
  scratch/<task-id>/                    # task notes; existing scratch/T1.md is valid
  drafts/                              # editable coordinator integration
  pending/<transaction-id>/
    base/                              # exact previously read snapshots
    intended/                          # frozen proposed snapshot
    manifest.json
    receipt.json                       # actual observations, when available
  checkpoints/revision-<N>/
    base/
    intended/
    manifest.json
    receipt.json
  history/<dated-reason>/               # preserved material outside verified checkpoints

outputs/<run-folder>/
  <topic>-research-plan.md
  <topic>-evidence.md
  <topic>-report.md
  <referenced-parts-and-review>.md
  dashboard.md
  workspace.json                       # copy of the location map
  validation.json                      # actual final readback result
  pending/<transaction-id>/            # optional, explicitly unpublished preview
```

## Responsibility and lifetime

| Location | Owner and contents | When it changes / completion rule |
|---|---|---|
| `work/` (or explicitly selected `works/`) | Coordinator's execution root; one readable folder per investigation | Resolve locations before starting/resuming. Preserve run identity across renames. |
| `outputs/` | Coordinator's reader-facing delivery root | Regenerate from one confirmed checkpoint, convert links, then compare against that checkpoint. Keep earlier verified delivery available while a new save is pending. |
| `scratch/` | Assigned researcher owns only its task file/subfolder: raw findings, search logs, provisional source IDs, access failures and partial results | Coordinator inspects acceptance criteria before merging. Scratch is evidence of work performed, not an accepted ledger or final report. Preserve useful failed attempts and distinguish retry notes. |
| `drafts/` | Coordinator's mutable assembled plan, ledger, claims, report and review repairs | Receives accepted scratch material and fact-check changes. Freeze an exact intended snapshot before writing destinations. Editing drafts alone does not update committed notes or delivery. |
| `pending/<transaction-id>/` | Coordinator's active save/recovery transaction: base, intended, manifest and observed receipt | Persist before the first destination mutation. Keep while a write is uncertain, conflicting, incomplete, or derived delivery remains stale. Never silently replace an unresolved transaction. |
| `base/` | Exact bytes/text and metadata read before this transaction, plus explicit absent-file entries in the manifest | Immutable comparison input for conflict detection and three-way reconciliation. Absence of a file is different from an empty file. |
| `intended/` | Exact frozen next snapshot for one transaction, including the plan, project notes and proposed dashboard | Immutable after dispatching writes. It is a child of a pending transaction or archived checkpoint, not a separate authoritative root. If the target changes, create a new transaction with its own base. |
| `checkpoints/revision-<N>/` | Immutable archived verified transaction with its base/intended snapshots, manifest and actual readback receipt | Archive after project and required derived outputs verify. Verify archived hashes before clearing only that matching pending transaction; later changes use a new revision. If delivery closes with an accepted unsaved/stale limit, retain pending material and disclose it. |
| `history/<dated-reason>/` | Preserved superseded drafts, legacy base-only files, cancelled attempts or migration notes | Label original provenance and reason. History is not an active pending write and not a verified checkpoint. Preserve genuine existing checkpoints under `checkpoints/`; do not relabel unknown old files as verified. |
| `run.json` | Stable location map: schema version, run ID, topic, work/export roots, vault plan/dashboard and local subpaths | Update only on destination changes. Copy to output `workspace.json`; both maps must match. Store locations, not task/budget state. |
| `resume.md` | Human entrypoint linking plan, ledger, report, scratch and latest receipt/active transaction | Refresh when paths or the next resume action change. Read it with actual plan and pending manifests; prose is not a status authority. |
| `state.json` | Coordinator's local operational/recovery state, described below | Write observations after actual I/O and bind them to snapshot hashes. Research status/budget summaries, if displayed, are generated from the referenced plan. |
| `sources.json` | Generated cache of canonical source records, described below | Regenerate after accepted source changes; retain stable source IDs. A cache is never edited independently to change the ledger. |
| `validation.json` | Actual JSON stdout/receipt from validating the committed snapshot | Generate after readback, retaining errors, unknowns and separate persistence dimensions. A new draft or source count cannot manufacture a passing receipt. |

## `state.json`: operations and recovery

Use a versioned object containing:

- `schema_version`, `run_id`, `recorded_at` and the active storage backend.
- `committed`: plan path, revision and plan-file SHA-256 from actual readback, or null before a verified initial save.
- `pending_transaction`: transaction ID, manifest path and target revision, or null when there is no unresolved save. Resolve this pointer and verify the run ID before recovery.
- `save_state`: `pending`, `saved` or `conflict`; `saved` refers to the project checkpoint only. Record errors with the affected operation/path and timestamp.
- `last_validation`: receipt path, observation time and the project/dashboard/exports results it actually recorded, or null before validation. Stale receipts remain labelled as observations of their referenced revision.

For local file bindings, record `file_hash_scheme: sha256-bytes-v1` and hash exact file bytes. These file hashes detect cache/input changes and differ from the canonical managed-section hashes defined by the validation contract.

Do not independently author task arrays, assignment counters, reviews or `research_status` here. Read canonical plan records and calculate any display summary from their events/tasks. Bind a generated summary to the plan revision/hash and refresh it when the binding differs. A saved project with failed export therefore has `save_state: saved` and a stale/unverified export observation, plus its unresolved transaction pointer; it is not fully synchronized.

Before any verified save, retain exact intended/base documents and manifests; `state.json` alone cannot reconstruct missing evidence. If an older run used this filename as its only state authority, preserve its original bytes in history, inspect the associated notes/scripts, and migrate only facts established by those artifacts. Missing review testimony, budget events or source access remain unknown. Never replace an unsupported legacy run with invented schema-1 records.

## `sources.json`: generated registry cache

Use a versioned object containing `schema_version`, `run_id`, `generated_at`, `file_hash_scheme: sha256-bytes-v1`, `registry_inputs` and `sources`. Each registry input identifies the canonical ledger/part path and its exact-file-byte SHA-256. A prepared local registry may be used before commitment only when `registry_stage: pending` and its transaction/target revision are explicit; otherwise record `registry_stage: committed` and the committed revision. Each source uses the canonical source schema in [validation-contract.md](validation-contract.md), without a parallel set of fields or reassigned IDs.

Generate `sources` from the canonical ledger and its declared parts. Preserve provenance, access scope, dates, lineage and limitations. Keep provisional worker discoveries and downloaded excerpts in assigned scratch files until accepted. Fact-check assessments and counterevidence reasoning remain in canonical claim records; a source cache does not establish a claim.

On resume compare all recorded input hashes with the actual registry files. A missing or stale cache can be rebuilt after reconciling pending evidence; a newer unmerged candidate is retained in its transaction. Never overwrite newer draft/ledger findings from an older cache. Do not put credentials or unrelated private content in these records.

## Handoffs and closure

1. Resolve `run.json` and `resume.md`, then inspect the committed plan, `state.json`, pending manifests and latest actual receipt. Reconcile unfinished saves before dispatching dependent work.
2. Researchers produce scratch notes. The coordinator accepts or qualifies them, integrates drafts and completes claim checks. Update canonical plan events/tasks rather than a second editable state mirror.
3. Freeze `drafts/` into a new pending transaction's `intended/`; retain exact bases and binding/hashes. Follow the storage protocol to write notes, commit the plan last and read back.
4. Generate registry cache from the accepted snapshot; refresh the dashboard and outputs; validate actual files. Record observed operation outcomes in `state.json` and the receipt even when the project save succeeded but delivery failed.
5. Archive a fully verified transaction to `checkpoints/`, verify its contents, then clear that transaction's pending pointer. Place only genuinely superseded/unverified legacy material in history. Link final exports and explain any remaining pending or content limitation.

For relocation, verify source/target containment, preserve scratch/history bytes and the stable run ID, update current plan/task pointers in a new checkpoint, and refresh location maps/exports. Historical snapshots keep their original paths. Review digests remain valid only if their covered report/claim/requirement content is unchanged.

These local operational/cache schemas support recovery. The current read-only research validator checks canonical plan/ledger/review and vault/export snapshots; it does not automatically validate `state.json`, `sources.json`, or the local directory lifecycle. Check their bindings, paths and observed receipts explicitly before claiming recovery or synchronization succeeded.
