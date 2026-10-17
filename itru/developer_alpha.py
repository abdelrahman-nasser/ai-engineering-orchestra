"""Local Alpha application composition. Only exact approved repository reads."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict
import os
from pathlib import Path
import secrets

from itru.alpha_config import (canonical, digest, load_config, read_json, text,
                               validate_work, write_private)
from itru.alpha_provider import plan_task
from itru.alpha_authority import AlphaExecution, Clock
from itru import task_run_state as state
from itru.sqlite_task_run_state import SqliteTaskRunStateStore, _plain, _security
from itru.task_scheduler import SchedulingSnapshot, evaluate_schedule, prepare_assignment_handoff
from itru.assignment import Assignment
from itru.agent_execution_contract import AgentExecutionContract
from itru.agent_execution_run import AgentExecutionRun
from itru.agent_operation_tool_binding import AgentOperationToolBinding
from itru.authorization_domain_ownership import AuthorizationDomainIdentity
from itru.agent_execution_result import _is_authoritative_result
from itru.sqlite_agent_execution_journal_store import (
    SqliteExecutionJournalStore, SqliteExecutionJournalConfiguration, JournalCursor,
)
from itru.sqlite_agent_execution_dispatch_admission_store import SqliteAgentExecutionDispatchAdmissionStoreConfiguration
from itru import windows_local_authorization_domain_owner as windows

TOOL = 'tool::itru-native-repository-file-read::v1'


def example_work():
    return {'format_version': 1, 'tasks': [
        {'id': 'read-a', 'objective': 'Inspect the example input', 'resource': 'input.txt', 'dependencies': []},
        {'id': 'read-b', 'objective': 'Independently inspect the example input', 'resource': 'input.txt', 'dependencies': []},
        {'id': 'read-c', 'objective': 'Inspect after both prerequisites have governance closure',
         'resource': 'input.txt', 'dependencies': ['read-a', 'read-b']}]}


def initialize(directory):
    if os.name != 'nt':
        raise OSError('Developer Alpha controlled execution requires Windows local NTFS')
    root = Path(directory).absolute()
    if root.exists() or root.resolve() != root:
        raise ValueError('init requires an exact new workspace directory')
    for parent in root.parents:
        _plain(parent, directory=True)
    root.mkdir()
    _security(root, directory=True, establish=True)
    for name in ('repository', 'ledger', 'journal'):
        path = root/name
        path.mkdir()
        _security(path, directory=True, establish=True)
    nonce = secrets.token_hex(16)
    cfg = dict(format_version=1, workspace=str(root), max_concurrency=2,
        **{key: 'itru-alpha::' + nonce + '::' + key for key in
           ('project_id', 'runtime_id', 'environment_id', 'domain_id', 'ledger_id', 'journal_id', 'store_id')},
        provider=dict(kind='demo', endpoint='', model='offline-demo', key_env='', timeout_seconds=30))
    conf = SqliteAgentExecutionDispatchAdmissionStoreConfiguration(root/'ledger'/'admission.sqlite3',
        cfg['domain_id'], cfg['ledger_id'], 1)
    admin = windows.WindowsLocalAuthorizationDomainAdministration(clock=Clock())
    provisioned = admin.provision(conf)
    if provisioned.outcome.value != 'provisioned':
        raise RuntimeError('ledger provisioning failed: ' + provisioned.outcome.value)
    admin.register(conf)
    identity = admin.activate(cfg['domain_id'])
    with closing(SqliteTaskRunStateStore.provision(root/'state', store_id=cfg['store_id'], project_id=cfg['project_id'])):
        pass
    SqliteExecutionJournalStore.provision(SqliteExecutionJournalConfiguration(
        root/'journal'/'journal.sqlite3', root/'journal', cfg['journal_id'], identity), metadata_authorized=True)
    (root/'repository'/'input.txt').write_text('ITRU Developer Alpha nonsecret example\n', encoding='utf-8')
    write_private(root/'example-work.json', example_work())
    write_private(root/'alpha.json', cfg)
    return {'status': 'initialized', 'config': str(root/'alpha.json'),
            'example_work': str(root/'example-work.json'), 'provider': 'offline demo; no inference'}


def open_state(cfg, authorizer=None):
    return SqliteTaskRunStateStore(Path(cfg['workspace'])/'state', store_id=cfg['store_id'],
        project_id=cfg['project_id'], continuation_authorizer=authorizer)


def load_work(cfg, path):
    work = read_json(path)
    graph = validate_work(work)
    target = Path(cfg['workspace'])/'work.json'
    if target.exists():
        if read_json(target) != work:
            raise ValueError('loaded work is immutable; use a new workspace for changed definitions')
    else:
        write_private(target, work)
    with closing(open_state(cfg)) as store:
        for node in graph.nodes:
            store.enroll(node.task_id, definition_reference=node.definition_reference)
    return {'status': 'loaded', 'tasks': [node.task_id for node in graph.nodes]}


def context(cfg, store):
    work = read_json(Path(cfg['workspace'])/'work.json')
    graph = validate_work(work)
    snapshot = SchedulingSnapshot(cfg['store_id'], cfg['project_id'],
        tuple(task for node in graph.nodes if (task := store.get_task(node.task_id)) is not None))
    decision = evaluate_schedule(graph, snapshot, max_concurrency=cfg['max_concurrency'])
    return work, graph, snapshot, decision


def make_plan(cfg, store, action='run', task_id=None, reference=None):
    work, graph, snapshot, decision = context(cfg, store)
    selected = decision.selected_task_ids
    if action in ('resume', 'complete'):
        task = next((task for task in snapshot.tasks if task.task_id == task_id), None)
        if task is None:
            raise ValueError('exact enrolled task required')
        if action == 'resume':
            dep = next(e.dependencies for e in decision.evaluations if e.task_id == task_id)
            if (not state.continuation_eligible(task) or dep.state != 'ready'
                    or decision.state != 'evaluated'
                    or len(decision.occupied_run_ids) >= cfg['max_concurrency']):
                raise ValueError('resume is unsafe, ineligible or dependency/capacity blocked')
        else:
            text(reference)
            if (task.state != 'in_progress' or not task.runs or task.runs[-1].state != 'succeeded'
                    or any(run.state in state.UNFINISHED | state.UNSAFE for run in task.runs)):
                raise ValueError('Task is not eligible for governance completion')
        selected = (task_id,)
    elif action != 'run' or task_id is not None or reference is not None:
        raise ValueError('invalid plan subject')
    subject = {'config': cfg, 'work': work, 'snapshot': asdict(snapshot), 'action': action,
               'selected': list(selected), 'reference': reference}
    tasks = {task['id']: task for task in work['tasks']}
    return {'status': 'approval_required' if selected else 'no_runnable_tasks',
        'action': action, 'selected': list(selected), 'approval': digest(subject) if selected else None,
        'selected_subjects': [{'task_id': key, 'objective': tasks[key]['objective'],
                               'resource': tasks[key]['resource']} for key in selected],
        'tasks': [asdict(e) for e in decision.evaluations],
        'workers': cfg['max_concurrency'], 'tool_execution': 'serialized',
        'reference': reference}


def require_approval(plan, supplied):
    if not supplied or not plan['approval'] or not secrets.compare_digest(plan['approval'], supplied):
        raise ValueError('fresh exact Human approval required; inspect alpha plan and pass its digest with --approve')


def _run_value(cfg, task):
    return AgentExecutionRun('run::' + secrets.token_hex(32), AgentExecutionContract(
        task['id'], 'standard-change', 'implement', 'software-engineer', 'agent::itru-alpha-reader',
        cfg['runtime_id'], 'option::alpha-configured', cfg['environment_id'],
        'repository_file_read', task['resource'], 'deep'))


def execute(cfg, approval, *, resume_task=None):
    # One Store owner serializes evaluation/registration, across every command.
    with closing(open_state(cfg)) as store:
        plan = make_plan(cfg, store, 'resume' if resume_task else 'run', resume_task)
        require_approval(plan, approval)
        work, graph, snapshot, decision = context(cfg, store)
        tasks = {t['id']: t for t in work['tasks']}
        reference = 'human-cli::sha256::' + approval
        runtime = AlphaExecution(cfg, reference)
        try:
            runs = []
            for task_id in plan['selected']:
                # Refresh complete domain/capacity while this caller holds owner.
                _, _, fresh, current = context(cfg, store)
                run = _run_value(cfg, tasks[task_id])
                binding = AgentOperationToolBinding(run, TOOL)
                if resume_task:
                    checkpoint = store.checkpoint(task_id)
                    def authorize(request):
                        if (request.checkpoint != checkpoint or request.binding != binding
                                or request.ledger_identity != runtime.session.identity
                                or request.reason != reference):
                            return None
                        return state.ContinuationApproval(request.session_nonce, request.request_nonce,
                            'human', runtime.identity.issuer, reference)
                    store._authorizer = authorize
                    registered = store.continue_task(checkpoint, binding, runtime.session.identity, reason=reference)
                else:
                    assignment = Assignment(task_id, 'standard-change', 'implement',
                                            'software-engineer', run.contract.actor_id)
                    handoff = prepare_assignment_handoff(graph, fresh, assignment, max_concurrency=cfg['max_concurrency'])
                    registered = store.register_run(binding, runtime.session.identity,
                                                    expected_revision=handoff.checkpoint.revision)
                runtime.approve_run(run)
                runs.append((run, registered))
            # Provider workers cannot reach authority, lifecycle or Tool APIs.
            results, failures = [], False
            with ThreadPoolExecutor(max_workers=cfg['max_concurrency']) as workers:
                futures = {run.run_id: workers.submit(plan_task, cfg['provider'], tasks[run.contract.task_id])
                           for run, _ in runs}
                for run, registered in runs:
                    try:
                        advisory = futures[run.run_id].result()
                    except Exception:
                        store.transition(run.contract.task_id, expected_revision=registered.revision,
                                         operation='stop', reference='provider_failed_before_tool')
                        results.append({'task_id': run.contract.task_id, 'run_id': run.run_id,
                                        'outcome': 'provider_failed_before_tool'})
                        failures = True
                        continue
                    running = store.start_run(run.contract.task_id, run.run_id, expected_revision=registered.revision)
                    outcome = runtime.invoke(run, reference)
                    if outcome.result is None or not _is_authoritative_result(outcome.result):
                        store.transition(run.contract.task_id, expected_revision=running.revision,
                                         operation='stop', reference='no_original_result')
                        raise RuntimeError('no authoritative original Result; attempt remains unresolved')
                    observed = store.record_result(outcome.result, expected_revision=running.revision)
                    receipt = outcome.journal_receipt
                    journal_ok = receipt is not None and receipt.outcome in ('appended', 'already_recorded')
                    row = {'task_id': run.contract.task_id, 'run_id': run.run_id,
                        'outcome': outcome.result.outcome, 'result_identity': list(outcome.result.identity),
                        'journal': receipt.outcome if receipt else 'missing',
                        'task_state': observed.state, 'advisory_plan': advisory,
                        'byte_count': outcome.result.payload.byte_count if outcome.result.payload else None}
                    if outcome.result.diagnostic:
                        row['diagnostic'] = outcome.result.diagnostic.code
                    results.append(row)
                    failures |= outcome.result.outcome != 'succeeded' or not journal_ok
            return {'status': 'attention_required' if failures else 'runs_succeeded_governance_pending',
                    'results': results, 'workers': cfg['max_concurrency'], 'tool_execution': 'serialized'}
        finally:
            runtime.close()


def history(cfg, store, after=0):
    work, graph, snapshot, decision = context(cfg, store)
    directory = Path(cfg['workspace'])/'journal'
    journal = SqliteExecutionJournalStore(SqliteExecutionJournalConfiguration(directory/'journal.sqlite3',
        directory, cfg['journal_id'], AuthorizationDomainIdentity(cfg['domain_id'], cfg['ledger_id'], 1)))
    _, initial = journal.page(limit=1)
    records, cursor = journal.page(cursor=JournalCursor(cfg['journal_id'], initial.high_water, after), limit=100)
    return {'status': 'descriptive_history', 'tasks': [asdict(task) for task in snapshot.tasks],
        'journal': [record.document for record in records],
        'journal_more': cursor.last_sequence < cursor.high_water, 'journal_after': cursor.last_sequence,
        'selected': list(decision.selected_task_ids)}


def command(args):
    if args.alpha_command == 'init':
        return initialize(args.directory)
    cfg = load_config(args.config)
    action = args.alpha_command
    if action == 'load':
        return load_work(cfg, args.work)
    if action in ('run', 'resume'):
        return execute(cfg, args.approve, resume_task=args.task if action == 'resume' else None)
    with closing(open_state(cfg)) as store:
        if action == 'plan':
            return make_plan(cfg, store, args.action, args.task, args.reference)
        if action == 'history':
            return history(cfg, store, args.after)
        if action == 'complete':
            plan = make_plan(cfg, store, 'complete', args.task, args.reference)
            require_approval(plan, args.approve)
        elif action != 'stop':
            raise ValueError('unknown Alpha command')
        text(args.reference)
        current = store.get_task(args.task)
        if current is None:
            raise ValueError('unknown enrolled Task')
        updated = store.transition(args.task, expected_revision=current.revision,
            operation='complete' if action == 'complete' else 'stop', reference=args.reference)
        return {'status': updated.state, 'task_id': updated.task_id, 'revision': updated.revision}
