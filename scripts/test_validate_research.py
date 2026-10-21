"""Observable contract/regression checks. All fixtures live in a temporary vault."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

import yaml

import validate_research as validator


TOPICS = ["decision", "audience", "terms", "scope", "time", "geography",
          "constraints", "assumptions", "deliverables", "acceptance"]


class ResearchFixture:
    def __init__(self, root):
        self.vault = Path(root) / "vault"
        self.run = self.vault / "Research" / "swarm-research" / "2026-10-22-demo"
        self.exports = Path(root) / "exports"
        self.run.mkdir(parents=True)
        self.exports.mkdir()
        self.plan = self.run / "demo-research-plan.md"
        self.run_id = "3ca296d1-1256-4d11-acb4-198d660e00b7"
        self.report = 'A bounded observed result [original](https://example.org/study). [C001](demo-evidence.md#c001)\n\n<a id="delivery"></a>\nA reproducible result within the agreed sample.\n'
        self.source = {
            "id": "S001", "title": "Original study", "publisher": "Publisher",
            "url": "https://example.org/study", "published_at": None,
            "accessed_at": "2026-10-22T10:00:00+07:00", "version": None,
            "kind": "primary", "lineage": "original-study-1",
            "inspection": "inspected", "access_scope": "full",
            "locator": "Table 2", "limitations": "Bounded sample",
            "group": {"region": "TH", "role": "buyer"},
        }
        self.sources = [self.source]
        self.claim = {
            "id": "C001", "statement": "A bounded observed finding", "material": True,
            "type": "source-reported", "nature": "descriptive", "scope": "Study sample, 2026",
            "assessment": "supported", "qualified": False, "numeric": False,
            "evidence": [{"source_id": "S001", "relation": "support", "locator": "Table 2 row 1",
                          "paraphrase": "The table establishes the bounded result"}],
            "fact_check": {
                "method": "Reopened the original table", "verified_by": "coordinator",
                "counter_search": {"query": "Competing results", "outcome": "No independent replication found in this bounded search", "source_ids": []},
                "independence_note": "One original experiment",
                "single_source_reason": "Describes the bounded result of this original study",
                "conflict_resolution": "No contradicting result found; absence is not proof",
                "numeric_check": "Not applicable", "conclusion_impact": "Limit generalization",
            },
        }
        self.claims = [self.claim]
        self.state = {
            "schema_version": 1, "run_id": self.run_id, "revision": 1,
            "research_status": "complete",
            "brief": {"status": "settled", "branches": [
                {"id": f"B{i:02}", "topic": topic, "depends_on": [], "status": "settled",
                 "resolution": f"The user resolved {topic}", "basis": "User request and supplied scenario",
                 "scenario_check": "Boundary example discussed; accepted interpretation recorded"}
                for i, topic in enumerate(TOPICS, 1)]},
            "budget": {"assignment_limit": 10, "round_limit": 2, "review_limit": 1, "recheck_limit": 1},
            "events": [
                {"id": "E001", "kind": "research_dispatch", "task_id": "T1", "attempt": 1,
                 "round": 0, "at": "2026-10-22T10:00:00+07:00"},
                {"id": "E002", "kind": "review_dispatch", "task_id": "REV", "attempt": 1,
                 "round": 0, "at": "2026-10-22T11:00:00+07:00"},
            ],
            "tasks": [self.task("T1", "research", []), self.task("SYN", "synthesis", ["T1"]),
                      self.task("REV", "review", ["SYN"])],
            "requirements": [{"id": "R001", "text": "Deliver a cited bounded answer", "obligation": "required",
                              "status": "met", "tasks": ["T1", "SYN"],
                              "artifacts": [self.ref("demo-report.md", "delivery")],
                              "review_disposition": "passed", "limitation": ""}],
            "artifacts": {"report": "demo-report.md", "ledger": "demo-evidence.md", "parts": [],
                          "review": "demo-review.md", "dashboard": "Research/swarm-research/dashboard.md"},
            "reviews": [{"kind": "review", "reviewer": "independent-reviewer", "independent": True,
                         "status": "passed", "report_sha256": "", "scope_claims": ["C001"],
                         "scope_requirements": ["R001"], "findings": []}],
            "manifest": {},
        }

    @staticmethod
    def ref(path="demo-report.md", anchor="delivery"):
        return {"path": path, "anchor": anchor}

    def task(self, tid, kind, deps):
        evidence = self.ref("demo-review.md", "review-verdict") if kind == "review" else self.ref()
        return {"id": tid, "kind": kind, "depends_on": deps, "question": "Answer the bounded question",
                "scope": "Only the supplied sample", "method": "Read and cross-check source passages",
                "output_location": f"scratch/{tid}.md", "status": "complete",
                "acceptance": [{"text": "Source and answer inspected", "status": "met", "evidence": evidence}]}

    def meta(self, name, kind="report"):
        return {"title": name, "created": "2026-10-22T10:00:00+07:00", "updated": "2026-10-22T11:00:00+07:00",
                "type": f"research-{kind}", "tags": ["research", "test"], "sources": [],
                "swarm_owner": "swarm-research", "run_id": self.run_id, "checkpoint_revision": 1,
                "research_status": self.state["research_status"]}

    def note(self, name, body, kind="report"):
        links = "\n\n[plan](demo-research-plan.md) · [ledger](demo-evidence.md) · [report](demo-report.md)\n"
        return "---\n" + yaml.safe_dump(self.meta(name, kind), allow_unicode=True, sort_keys=False) + "---\n\n# Swarm Research\n\n" + body + links + "\n# Personal Notes\n\n"

    def write(self, bind_review=True):
        ledger = "\n".join(f'<a id="{s["id"].lower()}"></a>' for s in self.sources)
        ledger += "\n" + "\n".join(f'<a id="{c["id"].lower()}"></a>' for c in self.claims)
        ledger += "\n```json swarm-research-sources\n" + json.dumps(self.sources) + "\n```\n"
        ledger += "\n```json swarm-research-claims\n" + json.dumps(self.claims) + "\n```\n"
        notes = {
            "demo-report.md": self.note("Demo report", self.report),
            "demo-evidence.md": self.note("Demo evidence", ledger, "evidence"),
            "demo-review.md": self.note("Demo review", '<a id="review-verdict"></a>\nIndependent source and requirements review passed.\n', "part"),
        }
        if bind_review:
            by_claim = {claim["id"]: claim for claim in self.claims}
            by_source = {source["id"]: source for source in self.sources}
            by_requirement = {req["id"]: req for req in self.state["requirements"]}
            for record in self.state["reviews"]:
                record["report_sha256"] = validator.managed_digest(notes["demo-report.md"])
                record["claim_digests"] = {
                    cid: validator.claim_digest(by_claim[cid], notes["demo-report.md"], by_source)
                    for cid in record["scope_claims"] if cid in by_claim}
                record["requirement_digests"] = {
                    rid: validator.requirement_digest(by_requirement[rid], notes)
                    for rid in record["scope_requirements"] if rid in by_requirement}
        self.state["manifest"] = {
            name: {"managed_sha256": validator.managed_digest(content),
                   "owned_metadata_sha256": validator.metadata_digest(yaml.safe_load(content.split("---", 2)[1]))}
            for name, content in notes.items()
        }
        plan_body = "<a id=\"brief\"></a>\n```json swarm-research-state\n" + json.dumps(self.state) + "\n```\n"
        notes[self.plan.name] = self.note("Demo plan", plan_body, "plan")
        for name, content in notes.items():
            (self.run / name).write_text(content, encoding="utf-8")
            (self.exports / name).write_text(validator.export_text(content, self.run, self.vault), encoding="utf-8")
        completed = sum(task["status"] == "complete" for task in self.state["tasks"])
        task_count = len(self.state["tasks"])
        assignments = sum(event["kind"] == "research_dispatch" for event in self.state["events"])
        assignment_limit = self.state["budget"]["assignment_limit"]
        dashboard = ("---\ntitle: Dashboard\nswarm_owner: swarm-research\n---\n\n# Swarm Research\n\n"
                     "| Run | Notes | Status | Tasks | Assignments | Updated | Blocker | Revision |\n"
                     "|---|---|---|---|---|---|---|---|\n"
                     f"| {self.run_id} | [[Research/swarm-research/2026-10-22-demo/demo-research-plan|plan]] / "
                     f"[[Research/swarm-research/2026-10-22-demo/demo-report|report]] | {self.state['research_status']} | {completed}/{task_count} | {assignments}/{assignment_limit} | 2026-10-22 | — | 1 |\n\n# Personal Notes\n")
        (self.vault / self.state["artifacts"]["dashboard"]).write_text(dashboard, encoding="utf-8")
        (self.exports / "dashboard.md").write_text(validator.export_text(dashboard, self.run, self.vault), encoding="utf-8")

    def check(self, phase="final"):
        return validator.validate(self.plan, self.vault, self.exports, phase)

    def add_recheck(self, claims, requirements):
        task = self.task("RECHECK", "recheck", ["REV"])
        task["acceptance"][0]["evidence"] = self.ref("demo-review.md", "review-verdict")
        self.state["tasks"].append(task)
        self.state["events"].append({"id": "E003", "kind": "recheck_dispatch", "task_id": "RECHECK", "attempt": 1, "round": 0, "at": "2026-10-22T11:30:00+07:00"})
        record = {"kind": "recheck", "reviewer": "independent-reviewer", "independent": True,
                  "status": "passed", "report_sha256": "", "scope_claims": claims,
                  "scope_requirements": requirements, "findings": [],
                  "claim_digests": {}, "requirement_digests": {}}
        self.state["reviews"].append(record)
        return record

    def bind_only(self, record):
        self.write(bind_review=False)
        docs = {path.name: path.read_text(encoding="utf-8") for path in self.run.glob("*.md")}
        record["report_sha256"] = validator.managed_digest(docs["demo-report.md"])
        by_source = {source["id"]: source for source in self.sources}
        record["claim_digests"] = {claim["id"]: validator.claim_digest(claim, docs["demo-report.md"], by_source)
                                   for claim in self.claims if claim["id"] in record["scope_claims"]}
        record["requirement_digests"] = {req["id"]: validator.requirement_digest(req, docs)
                                         for req in self.state["requirements"] if req["id"] in record["scope_requirements"]}
        self.write(bind_review=False)

    def mutate_note(self, name, transform):
        path = self.run / name
        text = transform(path.read_text(encoding="utf-8"))
        path.write_text(text, encoding="utf-8")
        self.state["manifest"][name] = {
            "managed_sha256": validator.managed_digest(text),
            "owned_metadata_sha256": validator.metadata_digest(yaml.safe_load(text.split("---", 2)[1]))}
        plan = self.plan.read_text(encoding="utf-8")
        start = plan.index("```json swarm-research-state\n") + len("```json swarm-research-state\n")
        end = plan.index("\n```", start)
        plan = plan[:start] + json.dumps(self.state) + plan[end:]
        self.plan.write_text(plan, encoding="utf-8")
        for filename, content in ((name, text), (self.plan.name, plan)):
            (self.exports / filename).write_text(validator.export_text(content, self.run, self.vault), encoding="utf-8")


class ValidatorContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="swarm-test-", dir=Path.cwd())
        self.addCleanup(self.temp.cleanup)
        self.f = ResearchFixture(self.temp.name)

    def invalid(self, result):
        self.assertTrue(result["errors"], result)

    def test_complete_bounded_single_primary_case_passes(self):
        self.f.write()
        r = self.f.check()
        self.assertEqual([], r["errors"], r)
        self.assertEqual([], r["unverified"], r)
        self.assertEqual("recorded-review-passed", r["content"])

    def test_open_clarification_prevents_complete(self):
        self.f.state["brief"]["branches"][0]["status"] = "open"
        self.f.state["brief"]["status"] = "open"
        self.f.write()
        self.invalid(self.f.check())

    def test_scenario_challenge_is_required(self):
        self.f.state["brief"]["branches"][0]["scenario_check"] = ""
        self.f.write()
        self.invalid(self.f.check())

    def test_brief_dependency_must_reference_an_existing_branch(self):
        self.f.state["brief"]["branches"][0]["depends_on"] = ["B999"]
        self.f.write()
        self.invalid(self.f.check())

    def test_complete_snapshot_requires_nonempty_requirements(self):
        self.f.state["requirements"] = []
        self.f.write()
        self.invalid(self.f.check())

    def test_unknown_research_status_is_rejected(self):
        self.f.state["research_status"] = "potato"
        self.f.write()
        self.invalid(self.f.check())

    def test_missing_english_deliverable_cannot_be_complete(self):
        req = deepcopy(self.f.state["requirements"][0])
        req.update(id="R002", text="English description", status="unmet", artifacts=[], review_disposition="pending")
        self.f.state["requirements"].append(req)
        self.f.write()
        self.invalid(self.f.check())

    def test_met_deliverable_needs_existing_artifact_anchor(self):
        self.f.write()
        self.f.state["requirements"][0]["artifacts"] = [self.f.ref(anchor="absent")]
        self.f.write(bind_review=False)
        self.invalid(self.f.check())

    def test_personal_notes_are_not_canonical_source_or_claim_records(self):
        self.f.write()
        def move_records(text):
            pattern = r"(?ms)^```json swarm-research-(?:sources|claims)\n.*?^```[ \t]*\n"
            blocks = "\n".join(re.findall(pattern, text))
            return re.sub(pattern, "", text).replace("# Personal Notes\n", "# Personal Notes\n\n" + blocks)
        self.f.mutate_note("demo-evidence.md", move_records)
        r = self.f.check()
        self.assertTrue(r["errors"] or r["unverified"], r)
        self.assertEqual(0, r["counts"]["sources"])
        self.assertEqual(0, r["counts"]["claims"])

    def test_personal_notes_citation_cannot_support_managed_report(self):
        paragraph, rest = self.f.report.split("\n\n", 1)
        self.f.report = rest
        self.f.write()
        self.f.mutate_note("demo-report.md", lambda text: text.replace("# Personal Notes\n", "# Personal Notes\n\n" + paragraph + "\n"))
        r = self.f.check()
        self.assertTrue(any(e["code"] == "REPORT_CLAIM_LINK" for e in r["errors"]), r)

    def test_report_must_link_claim_id(self):
        self.f.report = self.f.report.replace("[C001](demo-evidence.md#c001)", "")
        self.f.write()
        self.invalid(self.f.check())

    def test_report_must_directly_cite_support(self):
        self.f.report = self.f.report.replace("[original](https://example.org/study)", "original study")
        self.f.write()
        self.invalid(self.f.check())

    def test_claim_evidence_needs_locator(self):
        self.f.claim["evidence"][0]["locator"] = ""
        self.f.write()
        self.invalid(self.f.check())

    def test_duplicate_source_ids_are_rejected(self):
        self.f.sources.append(deepcopy(self.f.source))
        self.f.write()
        self.invalid(self.f.check())

    def test_syndicated_sources_are_not_two_independent_lineages(self):
        source = deepcopy(self.f.source)
        source.update(id="S002", title="Story about original", kind="secondary", url="https://example.net/story")
        self.f.sources.append(source)
        self.f.claim.update(nature="comparative")
        self.f.claim["evidence"].append({"source_id": "S002", "relation": "support", "locator": "Paragraph 3", "paraphrase": "Repeats the first study"})
        self.f.write()
        self.invalid(self.f.check())

    def test_independent_comparative_support_passes(self):
        source = deepcopy(self.f.source)
        source.update(id="S002", title="Independent replication", lineage="independent-study-2", url="https://example.net/replication")
        self.f.sources.append(source)
        self.f.claim.update(nature="comparative")
        self.f.claim["evidence"].append({"source_id": "S002", "relation": "support", "locator": "Table 3", "paraphrase": "Independent comparison agrees within the stated scope"})
        self.f.write()
        self.assertEqual([], self.f.check()["errors"])

    def test_only_search_excerpt_cannot_fully_support_material_fact(self):
        self.f.source.update(kind="search-excerpt", access_scope="search-excerpt")
        self.f.write()
        self.invalid(self.f.check())

    def test_search_excerpt_kind_cannot_claim_full_page_access(self):
        self.f.source.update(kind="search-excerpt", access_scope="full")
        self.f.write()
        self.invalid(self.f.check())

    def test_inaccessible_source_is_not_support(self):
        self.f.source.update(inspection="inaccessible", access_scope="none")
        self.f.write()
        self.invalid(self.f.check())

    def test_source_access_date_must_be_a_valid_date(self):
        self.f.source["accessed_at"] = "not-a-date"
        self.f.write()
        self.invalid(self.f.check())

    def test_numeric_claim_requires_recorded_arithmetic_check(self):
        self.f.claim["numeric"] = True
        self.f.claim["fact_check"]["numeric_check"] = ""
        self.f.write()
        self.invalid(self.f.check())

    def test_material_claim_needs_counterevidence_search(self):
        self.f.claim["fact_check"]["counter_search"]["outcome"] = ""
        self.f.write()
        self.invalid(self.f.check())

    def test_partial_fact_requires_visible_qualification(self):
        self.f.claim["assessment"] = "partially-supported"
        self.f.write()
        self.invalid(self.f.check())

    def test_qualified_unresolved_claim_can_cite_context_without_inventing_support(self):
        self.f.claim.update(statement="Whether the intervention increases hiring is unresolved",
                            type="inference", nature="causal", assessment="unresolved", qualified=True)
        self.f.claim["evidence"][0].update(relation="context", paraphrase="This study does not measure hiring outcomes")
        self.f.claim["fact_check"].update(method="Checked the study outcomes and searched for hiring data",
                                         independence_note="One context source; no applicable hiring data found",
                                         conclusion_impact="Do not claim a hiring increase from these data")
        self.f.report = self.f.report.replace("A bounded observed result", "Whether hiring increases is unresolved; available data do not establish it")
        self.f.write()
        r = self.f.check()
        self.assertEqual([], r["errors"], r)
        self.assertEqual([], r["unverified"], r)
        self.assertEqual("limited", r["content"])

    def test_supported_contradicted_claim_needs_reconciliation(self):
        self.f.claim["evidence"].append({"source_id": "S001", "relation": "contradiction", "locator": "Limitations", "paraphrase": "Potentially contradicts extrapolation"})
        self.f.claim["fact_check"]["conflict_resolution"] = ""
        self.f.write()
        self.invalid(self.f.check())

    def test_budget_is_derived_from_real_dispatch_events(self):
        self.f.state["events"].append({"id": "E003", "kind": "research_dispatch", "task_id": "T1", "attempt": 2, "round": 1, "at": "2026-10-22T10:30:00+07:00"})
        self.f.state["events"].sort(key=lambda e: e["at"])
        self.f.write()
        r = self.f.check()
        self.assertEqual(2, r["counts"]["assignments"]["used"])
        self.assertEqual(1, r["counts"]["rounds"]["used"])
        self.assertEqual(1, r["counts"]["reviews"]["used"])
        self.assertEqual(0, r["counts"]["rechecks"]["used"])

    def test_review_and_recheck_do_not_spend_research_rounds(self):
        task = self.f.task("RECHECK", "recheck", ["REV"])
        task["acceptance"][0]["evidence"] = self.f.ref("demo-review.md", "review-verdict")
        self.f.state["tasks"].append(task)
        self.f.state["events"].append({"id": "E003", "kind": "recheck_dispatch", "task_id": "RECHECK", "attempt": 1, "round": 0, "at": "2026-10-22T11:30:00+07:00"})
        review = deepcopy(self.f.state["reviews"][0]); review["kind"] = "recheck"
        self.f.state["reviews"].append(review)
        self.f.write()
        r = self.f.check()
        self.assertEqual(1, r["counts"]["assignments"]["used"])
        self.assertEqual(0, r["counts"]["rounds"]["used"])
        self.assertEqual(1, r["counts"]["rechecks"]["used"])

    def test_budget_overrun_is_rejected(self):
        self.f.state["budget"]["assignment_limit"] = 0
        self.f.write()
        self.invalid(self.f.check())

    def test_completed_task_requires_dispatch(self):
        self.f.state["events"] = self.f.state["events"][1:]
        self.f.write()
        self.invalid(self.f.check())

    def test_cycle_is_rejected(self):
        self.f.state["tasks"][0]["depends_on"] = ["REV"]
        self.f.write()
        self.invalid(self.f.check())

    def test_incomplete_prerequisite_is_not_accepted(self):
        self.f.state["tasks"][0]["status"] = "partial"
        self.f.state["tasks"][0]["acceptance"][0]["status"] = "unmet"
        self.f.write()
        self.invalid(self.f.check())

    def test_complete_snapshot_cannot_leave_review_task_pending(self):
        self.f.state["tasks"][-1]["status"] = "pending"
        self.f.write()
        self.invalid(self.f.check())

    def test_requirement_needs_task_mapping(self):
        self.f.state["requirements"][0]["tasks"] = []
        self.f.write()
        self.invalid(self.f.check())

    def test_unsupported_task_state_cannot_pass(self):
        self.f.state["tasks"][-1]["status"] = "potato"
        self.f.write()
        self.invalid(self.f.check())

    def test_changed_report_invalidates_exact_review_digest(self):
        self.f.write()
        self.f.report += "\nA newly added consequential recommendation.\n"
        self.f.write(bind_review=False)
        self.invalid(self.f.check())

    def test_empty_recheck_does_not_revalidate_changed_claim(self):
        self.f.write()
        self.f.claim["statement"] = "A different material conclusion"
        self.f.report = self.f.report.replace("A bounded observed result", "A materially different result")
        recheck = self.f.add_recheck([], [])
        self.f.bind_only(recheck)
        r = self.f.check()
        self.assertTrue(r["errors"] or r["unverified"], r)

    def test_source_revision_drift_invalidates_prior_claim_review(self):
        self.f.write()
        self.f.source["version"] = "revision-2"
        self.f.write(bind_review=False)
        r = self.f.check()
        self.assertTrue(any(item["code"] == "REVIEW_COVERAGE" for item in r["unverified"]), r)

    def test_scoped_recheck_can_revalidate_source_revision_drift(self):
        self.f.write()
        self.f.source["version"] = "revision-2"
        recheck = self.f.add_recheck(["C001"], [])
        self.f.bind_only(recheck)
        r = self.f.check()
        self.assertEqual([], r["errors"], r)
        self.assertEqual([], r["unverified"], r)

    def test_narrow_recheck_preserves_unchanged_prior_claim_coverage(self):
        second = deepcopy(self.f.claim)
        second.update(id="C002", statement="A second bounded finding")
        self.f.claims.append(second)
        second_passage = "Second bounded result [original](https://example.org/study). [C002](demo-evidence.md#c002)\n\n"
        self.f.report = second_passage + self.f.report
        self.f.state["reviews"][0]["scope_claims"] = ["C001", "C002"]
        self.f.write()
        second["statement"] = "A corrected second finding"
        self.f.report = self.f.report.replace("Second bounded result", "Corrected second result")
        recheck = self.f.add_recheck(["C002"], ["R001"])
        self.f.bind_only(recheck)
        r = self.f.check()
        self.assertEqual([], r["errors"], r)
        self.assertEqual([], r["unverified"], r)

    def test_stale_export_keeps_project_result_separate(self):
        self.f.write()
        (self.f.exports / "demo-report.md").write_text("Old report", encoding="utf-8")
        r = self.f.check()
        self.invalid(r)
        self.assertEqual("verified", r["persistence"]["project"])
        self.assertNotEqual("fresh", r["persistence"]["exports"])

    def test_missing_export_keeps_project_result_separate(self):
        self.f.write()
        (self.f.exports / "demo-report.md").unlink()
        r = self.f.check()
        self.invalid(r)
        self.assertEqual("verified", r["persistence"]["project"])

    def test_stale_dashboard_keeps_project_result_separate(self):
        self.f.write()
        path = self.f.vault / self.f.state["artifacts"]["dashboard"]
        text = path.read_text(encoding="utf-8").replace(" | — | 1 |", " | — | 0 |")
        path.write_text(text, encoding="utf-8")
        r = self.f.check()
        self.invalid(r)
        self.assertEqual("verified", r["persistence"]["project"])
        self.assertEqual("stale", r["persistence"]["dashboard"])

    def test_dashboard_revision_is_checked_in_its_own_column(self):
        self.f.write()
        path = self.f.vault / self.f.state["artifacts"]["dashboard"]
        text = path.read_text(encoding="utf-8").replace(" | — | 1 |", " | 1 | 0 |")
        path.write_text(text, encoding="utf-8")
        (self.f.exports / "dashboard.md").write_text(validator.export_text(text, self.f.run, self.f.vault), encoding="utf-8")
        r = self.f.check()
        self.assertTrue(any(e["code"] == "DASHBOARD_STALE" for e in r["errors"]), r)

    def test_dashboard_task_and_assignment_counts_must_match_records(self):
        for current, stale in ((" | 3/3 | 1/10 |", " | 2/3 | 1/10 |"),
                               (" | 3/3 | 1/10 |", " | 3/3 | 0/10 |")):
            with self.subTest(stale=stale):
                self.f.write()
                path = self.f.vault / self.f.state["artifacts"]["dashboard"]
                text = path.read_text(encoding="utf-8").replace(current, stale)
                path.write_text(text, encoding="utf-8")
                (self.f.exports / "dashboard.md").write_text(validator.export_text(text, self.f.run, self.f.vault), encoding="utf-8")
                r = self.f.check()
                self.assertTrue(any(e["code"] == "DASHBOARD_STALE" for e in r["errors"]), r)

    def test_missing_manifest_member_is_rejected(self):
        self.f.write()
        self.f.state["manifest"].pop("demo-evidence.md")
        old = self.f.plan.read_text(encoding="utf-8")
        start = old.index("```json swarm-research-state\n") + len("```json swarm-research-state\n")
        end = old.index("\n```", start)
        self.f.plan.write_text(old[:start] + json.dumps(self.f.state) + old[end:], encoding="utf-8")
        self.invalid(self.f.check())

    def test_open_critical_finding_prevents_complete(self):
        self.f.state["reviews"][0]["findings"] = [{"id": "F001", "severity": "critical", "status": "open", "resolution_artifacts": []}]
        self.f.write()
        self.invalid(self.f.check())

    def test_review_coverage_must_include_every_material_claim(self):
        self.f.state["reviews"][0]["scope_claims"] = []
        self.f.write()
        self.assertTrue(self.f.check()["unverified"] or self.f.check()["errors"])

    def test_self_review_is_not_independent_verification(self):
        self.f.state["reviews"][0]["independent"] = False
        self.f.write()
        self.assertTrue(self.f.check()["unverified"])

    def test_independent_review_needs_a_reviewer_identity(self):
        self.f.state["reviews"][0]["reviewer"] = ""
        self.f.write()
        self.invalid(self.f.check())

    def test_legacy_format_is_unverified_and_not_modified(self):
        self.f.write()
        old = "# Legacy plan without structured records\n"
        self.f.plan.write_text(old, encoding="utf-8")
        r = self.f.check()
        self.assertTrue(r["unverified"], r)
        self.assertEqual(old, self.f.plan.read_text(encoding="utf-8"))

    def test_unknown_schema_is_unverified(self):
        self.f.state["schema_version"] = 99
        self.f.write()
        self.assertTrue(self.f.check()["unverified"])

    def test_runtime_save_status_cannot_contradict_committed_snapshot(self):
        self.f.state["save_state"] = "pending"
        self.f.write()
        self.invalid(self.f.check())

    def test_source_counts_change_with_records(self):
        second = deepcopy(self.f.source)
        second.update(id="S002", url="https://example.org/second", lineage="second")
        self.f.sources.append(second)
        self.f.write()
        self.assertEqual(2, self.f.check()["counts"]["sources"])

    def test_validator_leaves_every_input_byte_unchanged(self):
        self.f.write()
        files = list(self.f.vault.rglob("*.md")) + list(self.f.exports.rglob("*.md"))
        before = {p: p.read_bytes() for p in files}
        self.f.check()
        self.assertEqual(before, {p: p.read_bytes() for p in files})

    def test_cli_returns_json_and_zero_for_valid_snapshot(self):
        self.f.write()
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = validator.main(["--plan", str(self.f.plan), "--vault-root", str(self.f.vault), "--export-dir", str(self.f.exports), "--phase", "final"])
        self.assertEqual(0, code, stream.getvalue())
        self.assertEqual([], json.loads(stream.getvalue())["errors"])

    def test_cli_returns_two_for_legacy_format(self):
        self.f.write()
        self.f.plan.write_text("# Legacy\n", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            code = validator.main(["--plan", str(self.f.plan), "--vault-root", str(self.f.vault), "--export-dir", str(self.f.exports), "--phase", "final"])
        self.assertEqual(2, code)

    def test_cli_returns_one_for_detected_error(self):
        self.f.claim["evidence"][0]["locator"] = ""
        self.f.write()
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = validator.main(["--plan", str(self.f.plan), "--vault-root", str(self.f.vault), "--export-dir", str(self.f.exports), "--phase", "final"])
        self.assertEqual(1, code)
        self.assertTrue(json.loads(stream.getvalue())["errors"])


if __name__ == "__main__":
    unittest.main()
