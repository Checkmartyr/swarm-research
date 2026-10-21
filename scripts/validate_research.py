#!/usr/bin/env python3
"""Read-only structural/review-record/snapshot checks. No source-truth certification."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

try:
    import yaml
except ImportError:
    yaml = None

OWNED = ('title', 'created', 'updated', 'type', 'tags', 'sources', 'swarm_owner',
         'run_id', 'checkpoint_revision', 'research_status')
TOPICS = {'decision', 'audience', 'terms', 'scope', 'time', 'geography',
          'constraints', 'assumptions', 'deliverables', 'acceptance'}
BLOCK = r'(?m)^```json swarm-research-%s\s*\n(.*?)^```[ \t]*$'


def normalized(text):
    return text.replace('\r\n', '\n').replace('\r', '\n')


def sha(text):
    return hashlib.sha256(normalized(text).encode('utf-8')).hexdigest()


def managed_body(text):
    text = normalized(text)
    starts = list(re.finditer(r'^# Swarm Research[ \t]*(?:\n|$)', text, re.M))
    ends = list(re.finditer(r'^# Personal Notes[ \t]*(?:\n|$)', text, re.M))
    if len(starts) != 1:
        raise ValueError('Expected one managed heading')
    if len(ends) != 1 or ends[0].start() < starts[0].end():
        raise ValueError('Expected one personal heading')
    # Retain the heading's trailing newline as part of the historical LF hash contract.
    return text[starts[0].end() - (1 if text[starts[0].end()-1:starts[0].end()] == '\n' else 0):ends[0].start()]


def managed_digest(text):
    return sha(managed_body(text))


def metadata_digest(meta):
    return sha(json.dumps({k: meta[k] for k in OWNED}, ensure_ascii=False,
                          sort_keys=True, separators=(',', ':')))


def claim_paragraphs(cid, report):
    return [p for p in re.split(r'\n\s*\n', managed_body(report)) if re.search(
        r'(?:\]\([^)]*#|\[\[[^\]]*#)' + re.escape(cid.lower()) + r'(?:[)|\]])', p, re.I)]


def claim_digest(claim, report, sources):
    ids = {e['source_id'] for e in claim['evidence']}
    ids.update(claim.get('fact_check', {}).get('counter_search', {}).get('source_ids', []))
    referenced = {sid: sources.get(sid) for sid in sorted(ids)}
    return sha(json.dumps({'record': claim, 'passages': claim_paragraphs(claim['id'], report),
                          'sources': referenced},
                          ensure_ascii=False, sort_keys=True, separators=(',', ':')))


def requirement_digest(requirement, docs):
    sections = []
    for item in requirement['artifacts']:
        text = managed_body(docs[item['path']])
        match = re.search(r'<a\s+id=[\"\']' + re.escape(item['anchor']) + r'[\"\']\s*></a>', text)
        if not match:
            raise ValueError('Missing requirement section')
        tail = text[match.end():]
        next_anchor = re.search(r'(?m)^<a\s+id=[\"\'][^\"\']+[\"\']\s*></a>', tail)
        sections.append(tail[:next_anchor.start()] if next_anchor else tail)
    return sha(json.dumps({'record': requirement, 'sections': sections}, ensure_ascii=False,
                          sort_keys=True, separators=(',', ':')))


def frontmatter(text):
    m = re.match(r'\A---\n(.*?)\n---(?:\n|$)', normalized(text), re.S)
    if not m:
        raise ValueError('Missing YAML frontmatter')
    meta = yaml.safe_load(m[1])
    if not isinstance(meta, dict):
        raise ValueError('Frontmatter must be a mapping')
    return meta


def blocks(text, kind):
    return [json.loads(m) for m in re.findall(BLOCK % kind, managed_body(text), re.S)]


def contained(root, relative):
    # Resolve existing junction/symlink components and check path components.
    p = Path(relative)
    if p.is_absolute() or p.drive or '\\' in str(relative) or ':' in str(relative):
        raise ValueError('Expected portable relative path')
    target = (root / p).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Path escapes root')
    return target


def export_text(text, run_dir, vault_root):
    """The storage contract's wikilink conversion, retaining ordinary Markdown."""
    def link(m):
        name, _, heading = m[1].partition('#')
        path = contained(vault_root, name + ('' if name.endswith('.md') else '.md'))
        if path.is_relative_to(run_dir.resolve()):
            target = path.relative_to(run_dir.resolve()).as_posix()
        else:
            target = path.as_posix()
        if heading:
            target += '#' + heading.lower()
        return '[' + (m[2] or Path(name).name) + '](' + target + ')'
    return re.sub(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', link, normalized(text))


def table_cells(line):
    # Wiki aliases contain pipes that are not table-cell delimiters.
    protected = re.sub(r'\[\[[^\]]+\]\]', lambda m: m[0].replace('|', '\x00'), line.strip().strip('|'))
    return [cell.replace('\x00', '|').replace('\\|', '|').strip() for cell in re.split(r'(?<!\\)\|', protected)]


def validate(plan, vault_root, export_dir, phase='final'):
    plan, vault_root, export_dir = Path(plan), Path(vault_root), Path(export_dir)
    result = {'structure': 'passed', 'content': 'unverified',
              'persistence': {'project': 'unverified', 'dashboard': 'unverified', 'exports': 'unverified'},
              'counts': {}, 'errors': [], 'warnings': [], 'unverified': []}

    def error(code, message):
        result['errors'].append({'code': code, 'message': message})

    def unknown(code, message):
        result['unverified'].append({'code': code, 'message': message})

    def need(obj, names, label):
        missing = [k for k in names if k not in obj]
        if missing:
            error('MISSING_FIELDS', f'{label}: {", ".join(missing)}')
        return not missing

    def finish():
        result['structure'] = 'failed' if result['errors'] else ('unverified' if result['unverified'] else 'passed')
        result['exit_code'] = 1 if result['errors'] else (2 if result['unverified'] else 0)
        return result

    if yaml is None:
        unknown('DEPENDENCY', 'PyYAML is unavailable; no files were changed')
        return finish()
    try:
        plan_text = plan.read_text(encoding='utf-8-sig')
        states = blocks(plan_text, 'state')
    except (OSError, ValueError) as exc:
        unknown('PLAN_UNREADABLE', f'{type(exc).__name__}: cannot read/parse plan')
        return finish()
    if len(states) != 1 or not isinstance(states[0], dict) or states[0].get('schema_version') != 1:
        unknown('UNVERIFIED_FORMAT', 'Expected one schema-1 state block; legacy artifacts remain untouched')
        return finish()
    state = states[0]
    if not need(state, ('run_id', 'revision', 'research_status', 'brief', 'budget', 'events',
                        'tasks', 'requirements', 'artifacts', 'reviews', 'manifest'), 'state'):
        return finish()
    if any(k in state for k in ('save_state', 'persistence_note', 'assignments_used', 'followup_rounds_remaining')):
        error('DUPLICATED_RUNTIME_STATE', 'Derive usage from events and persistence from readback receipts')
    run_dir = plan.parent.resolve()
    if phase == 'final' and not plan.resolve().is_relative_to(vault_root.resolve()):
        error('PLAN_NOT_IN_VAULT', 'Final plan must be the authoritative vault copy')
    if not isinstance(state['revision'], int) or isinstance(state['revision'], bool) or state['revision'] < 1:
        error('REVISION', 'Revision must be a positive integer')
    if state['research_status'] not in ('pending', 'running', 'review', 'complete', 'partial', 'blocked', 'cancelled'):
        error('RESEARCH_STATUS', 'Unknown research status')
    if not state['requirements']:
        error('MISSING_REQUIREMENTS', 'At least one observable requirement is required')

    docs = {plan.name: plan_text}
    art = state['artifacts']
    if not need(art, ('report', 'ledger', 'parts', 'review', 'dashboard'), 'artifacts'):
        return finish()
    project_names = [art['report'], art['ledger'], *art['parts'], art['review']]
    if len(set(project_names)) != len(project_names) or plan.name in project_names:
        error('ARTIFACT_COLLISION', 'Each project artifact has a distinct path')
    for name in project_names:
        try:
            docs[name] = contained(run_dir, name).read_text(encoding='utf-8-sig')
        except (OSError, ValueError):
            (error if phase == 'final' else unknown)('ARTIFACT_UNREADABLE', f'Cannot read project artifact {name}')

    def ref(item, label):
        if not isinstance(item, dict) or not item.get('path') or not item.get('anchor'):
            error('ARTIFACT_REFERENCE', f'{label}: path and explicit anchor required')
            return
        text = docs.get(item['path'])
        try:
            text = managed_body(text) if text is not None else ''
        except ValueError:
            text = ''
        if not re.search(r'<a\s+id=[\"\']' + re.escape(item['anchor']) + r'[\"\']\s*></a>', text):
            error('ARTIFACT_REFERENCE', f'{label}: missing artifact/anchor {item["path"]}#{item["anchor"]}')

    for name, text in docs.items():
        try:
            meta = frontmatter(text)
            if not need(meta, OWNED, name):
                continue
            if (meta['swarm_owner'], meta['run_id'], meta['checkpoint_revision'], meta['research_status']) != (
                    'swarm-research', state['run_id'], state['revision'], state['research_status']):
                error('SNAPSHOT_METADATA', f'{name}: ownership/revision/status mismatch')
            if not all(isinstance(meta[k], str) for k in ('created', 'updated')):
                error('METADATA_TIMESTAMP', f'{name}: quote ISO timestamps as strings')
            digest = managed_digest(text)
            if len(text.splitlines()) > 250:
                result['warnings'].append(f'{name}: over 250 lines; split or document a user-content/stub exception')
            if name != plan.name:
                expected = state['manifest'].get(name)
                if expected != {'managed_sha256': digest, 'owned_metadata_sha256': metadata_digest(meta)}:
                    error('MANIFEST_MISMATCH', f'{name}: content/metadata differs from plan manifest')
        except (ValueError, KeyError, TypeError, yaml.YAMLError):
            error('NOTE_FORMAT', f'{name}: invalid metadata or managed regions')
    if set(state['manifest']) != set(project_names):
        error('MANIFEST_COVERAGE', 'Manifest must cover every non-plan project artifact exactly')

    # Validate current references, including split-note anchors, rather than just headings existing.
    for name, text in docs.items():
        try:
            text = managed_body(text)
        except ValueError:
            continue
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if target.startswith(('https://', 'http://', 'mailto:')):
                continue
            target = target.strip('<>')
            path, _, anchor = target.partition('#')
            try:
                dest = contained(run_dir, path) if path else run_dir / name
                if not dest.is_file():
                    raise ValueError()
                if anchor and f'id="{anchor}"' not in dest.read_text(encoding='utf-8-sig'):
                    error('BROKEN_LINK', f'{name}: missing explicit anchor in {target}')
            except (ValueError, OSError):
                error('BROKEN_LINK', f'{name}: invalid local target {target}')
        for target in re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', text):
            path, _, anchor = target.partition('#')
            try:
                dest = contained(vault_root, path + ('' if path.endswith('.md') else '.md'))
                if not dest.is_file():
                    raise ValueError()
                if anchor and not re.search(r'<a id="' + re.escape(anchor.lower()) + '">', dest.read_text(encoding='utf-8-sig')):
                    error('BROKEN_LINK', f'{name}: missing wikilink anchor {target}')
            except (ValueError, OSError):
                error('BROKEN_LINK', f'{name}: missing wikilink target {target}')

    branches = state['brief'].get('branches', [])
    if state['brief'].get('status') != 'settled' or TOPICS - {b.get('topic') for b in branches}:
        error('BRIEF_OPEN', 'Settle and scenario-test all ten core brief topics')
    for branch in branches:
        if branch.get('status') != 'settled' or any(not branch.get(k) for k in ('resolution', 'basis', 'scenario_check')):
            error('BRIEF_OPEN', f'{branch.get("id", "?")}: unresolved or untested branch')
    branch_map = {branch.get('id'): branch for branch in branches}
    if len(branch_map) != len(branches):
        error('BRIEF_DEPENDENCY', 'Duplicate brief branch ID')
    b_seen, b_active = set(), set()
    def branch_walk(bid):
        if bid in b_active:
            error('BRIEF_DEPENDENCY', f'{bid}: branch cycle')
            return
        if bid in b_seen:
            return
        b_active.add(bid)
        for dep in branch_map[bid].get('depends_on', []):
            if dep not in branch_map:
                error('BRIEF_DEPENDENCY', f'{bid}: unknown branch {dep}')
            else:
                branch_walk(dep)
        b_active.remove(bid)
        b_seen.add(bid)
    for bid in branch_map:
        branch_walk(bid)
    tasks = {}
    for task in state['tasks']:
        if task.get('id') in tasks:
            error('DUPLICATE_TASK', str(task.get('id')))
        tasks[task.get('id')] = task
        need(task, ('kind', 'depends_on', 'question', 'scope', 'method', 'output_location', 'acceptance', 'status'), str(task.get('id')))
        if task.get('kind') not in ('research', 'synthesis', 'review', 'recheck'):
            error('TASK_KIND', f'{task.get("id")}: unknown task kind')
        if task.get('status') not in ('pending', 'running', 'complete', 'partial', 'failed', 'blocked', 'cancelled'):
            error('TASK_STATUS', f'{task.get("id")}: unknown task status')
        if state['research_status'] == 'complete' and task.get('status') != 'complete':
            if task.get('status') != 'cancelled' or not task.get('failure_or_gap'):
                error('INCOMPLETE_TASK', f'{task.get("id")}: incomplete task prevents complete outcome')
    visited, active = set(), set()

    def walk(tid):
        if tid in active:
            error('DEPENDENCY_CYCLE', str(tid))
            return
        if tid in visited:
            return
        active.add(tid)
        for dep in tasks[tid].get('depends_on', []):
            if dep not in tasks:
                error('UNKNOWN_DEPENDENCY', f'{tid} -> {dep}')
            else:
                walk(dep)
                if tasks[tid].get('status') == 'complete' and tasks[dep].get('status') != 'complete':
                    error('UNSATISFIED_DEPENDENCY', f'{tid} completed before {dep} acceptance')
        active.remove(tid)
        visited.add(tid)
    for tid, task in tasks.items():
        walk(tid)
        if task.get('status') == 'complete':
            if not task.get('acceptance'):
                error('TASK_ACCEPTANCE', f'{tid}: no observable acceptance')
            for criterion in task.get('acceptance', []):
                if criterion.get('status') != 'met' or not criterion.get('text'):
                    error('TASK_ACCEPTANCE', f'{tid}: completed with unmet criterion')
                ref(criterion.get('evidence'), f'{tid} acceptance')

    events, event_ids, rounds, attempts = Counter(), set(), set(), {}
    for event in state['events']:
        if not need(event, ('id', 'kind', 'task_id', 'attempt', 'round', 'at'), 'event'):
            continue
        kind, tid = event['kind'], event['task_id']
        if event['id'] in event_ids:
            error('DUPLICATE_EVENT', str(event['id']))
        event_ids.add(event['id'])
        expected_kind = {'research_dispatch': 'research', 'review_dispatch': 'review', 'recheck_dispatch': 'recheck'}.get(kind)
        if not expected_kind or tid not in tasks or tasks[tid].get('kind') != expected_kind:
            error('DISPATCH_KIND', f'{tid}: event/task kind mismatch')
        events[kind] += 1
        try:
            if datetime.fromisoformat(event['at'].replace('Z', '+00:00')).tzinfo is None:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            error('EVENT_TIMESTAMP', f'{tid}: expected ISO timestamp with timezone')
        if not isinstance(event['round'], int) or isinstance(event['round'], bool) or event['round'] < 0 or (kind != 'research_dispatch' and event['round'] != 0):
            error('ROUND_ACCOUNTING', f'{tid}: invalid round')
        elif kind == 'research_dispatch' and event['round']:
            rounds.add(event['round'])
        expected_attempt = attempts.get(tid, 0) + 1
        if not isinstance(event['attempt'], int) or isinstance(event['attempt'], bool) or event['attempt'] != expected_attempt:
            error('ATTEMPT_ACCOUNTING', f'{tid}: attempt must be {expected_attempt}')
        attempts[tid] = expected_attempt
    if rounds != set(range(1, len(rounds) + 1)):
        error('ROUND_ACCOUNTING', 'Positive follow-up rounds must be consecutive')
    b = state['budget']
    for label, used, limit_key in [('assignments', events['research_dispatch'], 'assignment_limit'),
                                   ('rounds', len(rounds), 'round_limit'),
                                   ('reviews', events['review_dispatch'], 'review_limit'),
                                   ('rechecks', events['recheck_dispatch'], 'recheck_limit')]:
        limit = b.get(limit_key)
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0 or used > limit:
            error('BUDGET_EXCEEDED', f'{label}: used {used}, invalid/exceeded limit {limit}')
        result['counts'][label] = {'used': used, 'limit': limit, 'remaining': limit - used if isinstance(limit, int) else None}
    for tid, task in tasks.items():
        if task.get('kind') != 'synthesis' and task.get('status') not in ('pending', 'blocked') and tid not in attempts:
            error('MISSING_DISPATCH', f'{tid}: no budget event')

    sources, claims = {}, {}
    for label, registry in [('sources', sources), ('claims', claims)]:
        for name in [art['ledger'], *art['parts']]:
            try:
                for records in blocks(docs.get(name, ''), label):
                    if not isinstance(records, list):
                        raise ValueError()
                    for record in records:
                        rid = record.get('id', '')
                        if not re.fullmatch(('S' if label == 'sources' else 'C') + r'\d{3,}', rid):
                            error('RECORD_ID', f'{name}: invalid {label} ID')
                        if rid in registry:
                            error('DUPLICATE_RECORD', rid)
                        registry[rid] = record
                        ref({'path': name, 'anchor': rid.lower()}, rid)
            except (ValueError, AttributeError):
                error('RECORD_FORMAT', f'{name}: invalid {label} array')
    if phase == 'final' and (not sources or not claims):
        unknown('MISSING_RECORDS', 'Final ledger needs structured source and claim records')
    access_counts, groups = Counter(), Counter()
    for sid, source in sources.items():
        need(source, ('title', 'publisher', 'url', 'published_at', 'accessed_at', 'version', 'kind',
                      'lineage', 'inspection', 'access_scope', 'locator', 'limitations'), sid)
        inspection, scope = source.get('inspection'), source.get('access_scope')
        if source.get('kind') not in ('primary', 'secondary', 'repository', 'marketplace', 'search-excerpt'):
            error('SOURCE_KIND', f'{sid}: unknown source kind')
        try:
            if datetime.fromisoformat(source.get('accessed_at', '').replace('Z', '+00:00')).tzinfo is None:
                raise ValueError()
            if source.get('published_at') is not None:
                datetime.fromisoformat(source['published_at'].replace('Z', '+00:00'))
        except (ValueError, TypeError, AttributeError):
            error('SOURCE_DATE', f'{sid}: invalid publication/access date')
        if inspection not in ('inspected', 'discovery-only', 'inaccessible') or scope not in ('full', 'partial', 'abstract', 'search-excerpt', 'none'):
            error('SOURCE_ACCESS', f'{sid}: unknown inspection/access scope')
        if inspection != 'inspected' and scope != 'none':
            error('SOURCE_ACCESS', f'{sid}: uninspected target cannot have inspected access')
        if inspection == 'inspected' and (scope == 'none' or not source.get('locator')):
            error('SOURCE_ACCESS', f'{sid}: inspected evidence needs access and locator')
        if (scope == 'search-excerpt') != (source.get('kind') == 'search-excerpt'):
            error('SOURCE_ACCESS', f'{sid}: distinguish excerpt from target page')
        if not source.get('lineage') or not source.get('url'):
            error('SOURCE_PROVENANCE', f'{sid}: missing lineage or URL/path')
        access_counts[f'{inspection}/{scope}'] += 1
        if source.get('group'):
            groups[json.dumps(source['group'], sort_keys=True, ensure_ascii=False)] += 1
    result['counts'].update({'tasks': len(tasks), 'tasks_complete': sum(t.get('status') == 'complete' for t in tasks.values()),
                             'sources': len(sources), 'claims': len(claims), 'source_access': dict(access_counts), 'source_groups': dict(groups)})

    report = docs.get(art['report'], '')
    material = set()
    for cid, claim in claims.items():
        need(claim, ('statement', 'material', 'type', 'nature', 'scope', 'assessment', 'qualified', 'numeric', 'evidence', 'fact_check'), cid)
        if claim.get('type') not in ('source-reported', 'direct-observation', 'inference', 'proposal') or claim.get('nature') not in ('descriptive', 'comparative', 'causal', 'trend'):
            error('CLAIM_TYPE', f'{cid}: unknown type/nature')
        if not all(isinstance(claim.get(k), bool) for k in ('material', 'qualified', 'numeric')):
            error('CLAIM_FLAGS', f'{cid}: material/qualified/numeric must be booleans')
        if claim.get('assessment') not in ('supported', 'partially-supported', 'disputed', 'unresolved'):
            error('CLAIM_ASSESSMENT', f'{cid}: unknown assessment')
        support, supported_sources, cited_sources = set(), [], []
        for evidence in claim.get('evidence', []):
            sid = evidence.get('source_id')
            if sid not in sources:
                error('UNKNOWN_SOURCE', f'{cid}: {sid}')
                continue
            if evidence.get('relation') not in ('support', 'contradiction', 'context') or not evidence.get('locator') or not evidence.get('paraphrase'):
                error('EVIDENCE_LOCATOR', f'{cid}: evidence needs relation, locator and paraphrase')
            source = sources[sid]
            cited_sources.append(source)
            if evidence.get('relation') == 'support':
                supported_sources.append(source)
                if source.get('inspection') != 'inspected':
                    error('UNINSPECTED_SUPPORT', f'{cid}: {sid} cannot establish a finding')
                elif source.get('access_scope') not in ('none', 'search-excerpt') and source.get('kind') != 'search-excerpt':
                    support.add(source.get('lineage'))
        if not claim.get('material'):
            continue
        material.add(cid)
        fc = claim.get('fact_check', {})
        if not all(fc.get(k) for k in ('method', 'verified_by', 'independence_note', 'conclusion_impact')):
            error('FACT_CHECK_INCOMPLETE', f'{cid}: incomplete coordinator fact-check')
        cs = fc.get('counter_search', {})
        if not cs.get('query') or not cs.get('outcome') or not isinstance(cs.get('source_ids'), list):
            error('COUNTEREVIDENCE_SEARCH', f'{cid}: record query and bounded outcome')
        for sid in cs.get('source_ids', []):
            if sid not in sources:
                error('UNKNOWN_SOURCE', f'{cid}: counter-search {sid}')
        if claim.get('numeric') and fc.get('numeric_check', '').strip().lower() in ('', 'n/a', 'not applicable'):
            error('NUMERIC_CHECK', f'{cid}: consequential arithmetic not checked')
        if claim.get('type') != 'proposal' and claim.get('assessment') in ('supported', 'partially-supported') and not supported_sources:
            error('CLAIM_EVIDENCE', f'{cid}: supported finding lacks support')
        if claim.get('assessment') == 'supported' and claim.get('type') != 'proposal':
            if not support:
                error('EXCERPT_ONLY_SUPPORT', f'{cid}: excerpts alone cannot fully support a material claim')
            elif len(support) < 2:
                authoritative = any(s.get('kind') in ('primary', 'repository') and s.get('inspection') == 'inspected' for s in supported_sources)
                if claim.get('nature') != 'descriptive' or not authoritative or not fc.get('single_source_reason'):
                    error('CORROBORATION', f'{cid}: qualify claim or establish independent support')
        if any(e.get('relation') == 'contradiction' for e in claim.get('evidence', [])) and claim.get('assessment') == 'supported' and not fc.get('conflict_resolution'):
            error('CONFLICT_UNRESOLVED', f'{cid}: supported verdict needs reconciliation')
        if claim.get('assessment') != 'supported' and claim.get('qualified') is not True:
            error('UNQUALIFIED_CLAIM', f'{cid}: disclose unresolved/limited evidence in report')
        paras = claim_paragraphs(cid, report)
        if not paras:
            error('REPORT_CLAIM_LINK', f'{cid}: missing report-to-ledger link')
        elif claim.get('type') != 'proposal' and cited_sources and not any(any(s.get('url', '') in p for s in cited_sources if s.get('url')) for p in paras):
            error('REPORT_DIRECT_CITATION', f'{cid}: direct source URL required beside claim link')

    requirement_ids = set()
    for requirement in state['requirements']:
        rid = requirement.get('id')
        if rid in requirement_ids:
            error('DUPLICATE_REQUIREMENT', str(rid))
        requirement_ids.add(rid)
        need(requirement, ('id', 'text', 'obligation', 'status', 'tasks', 'artifacts', 'review_disposition', 'limitation'), str(rid))
        if not requirement.get('tasks'):
            error('REQUIREMENT_TASK', f'{rid}: requirement needs an accountable task')
        if requirement.get('obligation') not in ('required', 'target', 'conditional') or requirement.get('status') not in ('met', 'limited', 'unmet'):
            error('REQUIREMENT_STATUS', str(rid))
        for tid in requirement.get('tasks', []):
            if tid not in tasks:
                error('REQUIREMENT_TASK', f'{rid}: {tid}')
        if requirement.get('status') == 'met' and not requirement.get('artifacts'):
            error('REQUIREMENT_ARTIFACT', f'{rid}: met without deliverable evidence')
        for item in requirement.get('artifacts', []):
            ref(item, str(rid))
        if requirement.get('status') != 'met' and not requirement.get('limitation'):
            error('REQUIREMENT_LIMITATION', str(rid))
        if state['research_status'] == 'complete' and requirement.get('obligation') == 'required' and requirement.get('status') != 'met':
            error('INCOMPLETE_DELIVERABLE', f'{rid}: mandatory deliverable prevents complete')
        if phase == 'final' and requirement.get('review_disposition') not in ('passed', 'limited'):
            unknown('REQUIREMENT_REVIEW', f'{rid}: not reviewed')

    reviews = state['reviews']
    covered_claims, covered_requirements = set(), set()
    for review in reviews:
        need(review, ('kind', 'reviewer', 'independent', 'status', 'report_sha256', 'scope_claims', 'scope_requirements', 'claim_digests', 'requirement_digests', 'findings'), 'review')
        if not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip():
            error('REVIEWER_IDENTITY', 'Record the actual reviewer identity')
        if review.get('independent') is not True:
            unknown('REVIEW_INDEPENDENCE', 'Self-review does not establish independent content review')
        if review.get('kind') not in ('review', 'recheck') or review.get('status') not in ('passed', 'limited', 'failed'):
            error('REVIEW_STATUS', 'Unknown review kind/status')
        for cid in review.get('scope_claims', []):
            if cid not in claims:
                error('REVIEW_SCOPE', f'Unknown reviewed claim {cid}')
            elif review.get('claim_digests', {}).get(cid) == claim_digest(claims[cid], report, sources):
                covered_claims.add(cid)
        for rid in review.get('scope_requirements', []):
            requirement = next((r for r in state['requirements'] if r.get('id') == rid), None)
            if requirement is None:
                error('REVIEW_SCOPE', f'Unknown reviewed requirement {rid}')
            else:
                try:
                    if review.get('requirement_digests', {}).get(rid) == requirement_digest(requirement, docs):
                        covered_requirements.add(rid)
                except (KeyError, ValueError):
                    pass
        for finding in review.get('findings', []):
            if finding.get('severity') not in ('critical', 'high', 'medium', 'low') or finding.get('status') not in ('open', 'resolved', 'accepted-limit'):
                error('FINDING_STATUS', str(finding.get('id')))
            if finding.get('status') in ('resolved', 'accepted-limit'):
                if not finding.get('resolution_artifacts'):
                    error('FINDING_RESOLUTION', str(finding.get('id')))
                for item in finding.get('resolution_artifacts', []):
                    ref(item, str(finding.get('id')))
            if finding.get('status') == 'open' or (finding.get('severity') in ('critical', 'high') and finding.get('status') != 'resolved'):
                unknown('OPEN_REVIEW_FINDING', str(finding.get('id')))
                if state['research_status'] == 'complete':
                    error('UNRESOLVED_REVIEW', 'Complete with unresolved consequential finding')
    for kind in ('review', 'recheck'):
        if len([r for r in reviews if r.get('kind') == kind]) > events[kind + '_dispatch']:
            error('REVIEW_ACCOUNTING', f'{kind}: no corresponding dispatch budget')
    if phase == 'final':
        if not any(r.get('kind') == 'review' for r in reviews):
            unknown('MISSING_INITIAL_REVIEW', 'Recheck cannot replace a missing initial review record')
        if not reviews or material - covered_claims or requirement_ids - covered_requirements:
            unknown('REVIEW_COVERAGE', 'Independent dispositions must cover all material claims and requirements')
        if reviews:
            try:
                if reviews[-1].get('report_sha256') != managed_digest(report):
                    error('REVIEW_REPORT_CHANGED', 'Current report differs from last reviewed body')
            except ValueError:
                pass
            if reviews[-1].get('status') not in ('passed', 'limited'):
                unknown('REVIEW_NOT_PASSED', 'Last content review did not pass')
        if not result['unverified'] and not result['errors'] and reviews:
            result['content'] = 'limited' if (any(r.get('status') == 'limited' for r in reviews) or any(c.get('assessment') != 'supported' for c in claims.values())) else 'recorded-review-passed'
    project_codes = {'MANIFEST_MISMATCH', 'MANIFEST_COVERAGE', 'NOTE_FORMAT', 'SNAPSHOT_METADATA', 'ARTIFACT_UNREADABLE', 'PLAN_NOT_IN_VAULT'}
    result['persistence']['project'] = 'verified' if not any(e['code'] in project_codes for e in result['errors']) and not any(e['code'] == 'ARTIFACT_UNREADABLE' for e in result['unverified']) else 'unverified'
    if phase == 'final':
        try:
            dashboard = contained(vault_root, art['dashboard']).read_text(encoding='utf-8-sig')
            rows = [line for line in dashboard.splitlines() if line.startswith('| ' + state['run_id'] + ' |')]
            lines = dashboard.splitlines()
            header = next((line for line in lines if line.startswith('| Run |') and 'Revision' in line), '')
            keys = table_cells(header)
            cells = table_cells(rows[0]) if len(rows) == 1 else []
            row = dict(zip(keys, cells))
            expected_tasks = f'{result["counts"]["tasks_complete"]}/{len(tasks)}'
            expected_assignments = f'{events["research_dispatch"]}/{b["assignment_limit"]}'
            if (len(rows) != 1 or row.get('Revision') != str(state['revision']) or row.get('Status') != state['research_status']
                    or row.get('Tasks') != expected_tasks or row.get('Assignments') != expected_assignments):
                error('DASHBOARD_STALE', 'Expected one row with current run, status and revision')
                result['persistence']['dashboard'] = 'stale'
            else:
                result['persistence']['dashboard'] = 'fresh'
        except (ValueError, OSError):
            dashboard = None
            error('DASHBOARD_UNREADABLE', 'Cannot verify dashboard')
        exports_ok = True
        for name, text in list(docs.items()) + ([('dashboard.md', dashboard)] if dashboard is not None else []):
            try:
                actual = contained(export_dir, name).read_text(encoding='utf-8-sig')
                if normalized(actual) != export_text(text, run_dir, vault_root):
                    raise ValueError()
            except (OSError, ValueError):
                exports_ok = False
                error('EXPORT_STALE', f'{name}: absent or differs from confirmed snapshot')
        result['persistence']['exports'] = 'fresh' if exports_ok else 'stale'
    return finish()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--vault-root', type=Path, required=True)
    parser.add_argument('--export-dir', type=Path, required=True)
    parser.add_argument('--phase', choices=('draft', 'final'), default='final')
    args = parser.parse_args(argv)
    try:
        result = validate(args.plan, args.vault_root, args.export_dir, args.phase)
    except (KeyError, TypeError, ValueError, AttributeError, RecursionError) as exc:
        result = {'structure': 'failed', 'content': 'unverified',
                  'persistence': {'project': 'unverified', 'dashboard': 'unverified', 'exports': 'unverified'},
                  'counts': {}, 'errors': [{'code': 'INVALID_SCHEMA', 'message': type(exc).__name__ + ': malformed structured records'}],
                  'warnings': [], 'unverified': [], 'exit_code': 1}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result['exit_code']


if __name__ == '__main__':
    sys.exit(main())
