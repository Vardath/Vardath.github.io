"""DeepThorT desktop v9: offline coding workspace with visible, durable work.

This is a supervised local coding assistant, not a verified autonomous game builder.
Routine trusted-catalog software installation/upgrade uses a visible persistent
user preference; Windows elevation remains under UAC. Approved source edits and fixed tests may use job-bound, reversible authority;
arbitrary scripts and unverified tools retain separate safeguards. All AI inference
is local to 127.0.0.1.
"""
from __future__ import annotations

import json
import hashlib
import re
import uuid
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener

from deepthort_local.diagnostics import inspect_local_setup, format_diagnostic
from deepthort_local.client import LocalModelClient
from deepthort_local.capability_library import CapabilityLibrary, attach_capability_context
from deepthort_local.tool_acquisition import ToolAcquisition
from deepthort_local.specification_library import SpecificationIndex, generate_indexed_plan, MAX_STORED_REQUEST_CHARS
from deepthort_local.hierarchical_planning import HierarchicalPlanStore
from deepthort_local.semantic_reconciliation import capture_verified_sources
from deepthort_local.verification_evidence import assess_verification, attach_verification
from deepthort_local.engine_acceptance import audit_engine_project
from deepthort_local.engine_environment import godot_executable
from deepthort_local.large_input import imported_source, resolve_import
from deepthort_local.chat_timeline import merged_chat_timeline
from deepthort_local.agent_plan import parse_build_plan, build_plan_prompt, build_budgeted_plan_prompt, budgeted_file_step_prompt, validate_project_plan, generate_model_plan, MAX_PLAN_ATTEMPTS, PlanError, project_kind
from deepthort_local.x4_sources import (inspect_x4_sources, automatic_x4_preflight, is_x4_inspection_request, x4_request_in_context,
                                      format_x4_inspection, x4_evidence_for_prompt,
                                        likely_installations, find_catalog_tool, catalog_extraction_command)
from deepthort_local.media_tools import (classify, validate_attachment, composed_prompt,
        validate_image_output_path, cli_image_args)
from deepthort_local.computer_inventory import (INSTALL_CATALOG, format_inventory,
        plan_tool_needs, scan_computer, winget_command)
from deepthort_local.disk_gate import DiskGate
from deepthort_local.isolated_gui import (
    IsolatedGuiStore, IsolatedGuiError, plan_isolated_gui, run_isolated_gui,
    assert_plan_unchanged)
from deepthort_local.quiet_playtest import (
    QuietTestStore, QuietPlaytestError, plan_godot_scene, quiet_creationflags,
    is_capped_windows_process, PLAYTEST_SECONDS, QuietPressureGuard, WindowsPressureSampler)
from deepthort_local.job_queue import ChatRegistry, JobStore
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.flight_recorder import record, install_crash_hooks, export_diagnostics
from deepthort_local.diagnostic_evidence import (summarize_x4_report, summarize_inventory,
    save_snapshot, read_snapshot, matches_project)
from deepthort_local.process_metrics import Meter
from deepthort_local.janus_engine import JanusStore
from deepthort_local.janus_interface import addressed_to_janus, janus_state_reply
from deepthort_local.watchdog import SentinelStore
from deepthort_local.tasks import TaskBoard
from deepthort_local.ui_help import install_tooltips
from deepthort_local.tool_sources import official_source
from deepthort_local.tool_verification import (ToolVerificationStore, verify_catalog_tool,
    refreshed_path)
from deepthort_local.software_autonomy import (
    load_policy, set_policy, project_tool_plans, verify_plan, audit_record,
    already_attempted, MIN_FREE_BYTES)

from deepthort_local.project_authority import (
    GrantError, load_policy as load_project_policy, set_policy as set_project_policy,
    issue_grant, authorize_file, record_file, authorize_test, revoke_grant,
    authorize_repair_context, authorize_repair, record_repair)

from deepthort_local.task_graph import TaskGraphStore, GraphError
from deepthort_local.source_checkpoints import SourceCheckpoints, CheckpointError

from deepthort_local.development_cycle import (
    DevelopmentCycleStore, CycleError, build_repair_prompt, parse_repair_response,
    MAX_TEST_ATTEMPTS, MAX_REPAIR_ATTEMPTS, isolated_verification_environment)

from deepthort_local.reviewed_install import (prepare_reviewed_install, exact_consent_phrase, approval_receipt)
from deepthort_local.online_tool_search import (winget_search_command, winget_show_command,
    validate_package_id, inspect_show_output, format_inspection, MAX_INSPECTION_BYTES)
from deepthort_local.inspection_exclusions import InspectionExclusions
from deepthort_local.plan_continuation import PlanContinuation
from deepthort_local.workspace import (WorkspaceError, apply_approved_file,
        list_project_files, read_project_file, safe_target, strip_single_code_fence)

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state'
BG, PANEL, INPUT, TEXT, MUTED, ACCENT = '#121822','#1b2532','#182333','#e8eef8','#a9b6c8','#6fb7ff'
GREEN, YELLOW = '#79cfad','#ffcd78'
MAX_INFERENCE_PROMPT = 7500  # current ONNX endpoint requires <=8000 / message


def local_server_status(timeout=1.3):
    """Fetch actual local ONNX readiness/stage without accepting cloud addresses."""
    try:
        opener = build_opener(ProxyHandler({}))
        with opener.open(Request('http://127.0.0.1:8765/health'), timeout=timeout) as r:
            response = json.load(r)
        return response if isinstance(response, dict) and response.get('model') == 'deepthort-qwen-coder-onnx' and response.get('offline') is True else None
    except (URLError,OSError,ValueError,TimeoutError):
        return None


def local_server_healthy(timeout=1.8):
    current = local_server_status(timeout)
    return bool(current and current.get('ready') is True)


class DeepThorTDesktop(tk.Tk):
    def __init__(self):
        super().__init__()
        STATE.mkdir(exist_ok=True)
        install_crash_hooks(STATE, 'desktop')
        record(STATE,'desktop','desktop_init',version='48',pid=os.getpid())
        self._last_queue_gate = None
        self._last_queue_gate_at = 0.0
        self._last_telemetry_at = 0.0
        self._last_activity_message = None
        self._last_activity_at = 0.0
        self.title('DeepThorT — Local Coding Agent Workspace')
        self.geometry('1320x860')
        self.minsize(1000,650)
        self.configure(bg=BG)
        self.events = queue.Queue()
        self.node = None
        self.node_ready = False
        self.node_loading = False
        self.node_started = 0.0
        self.last_ai_error = ""
        self.recent_ai_logs = []
        self.current_loading_stage = ''
        self._last_health_stage = ''
        self.last_server_health = {}
        self.installing = False
        self.install_process = None
        self.tool_process = None
        self._pending_package_inspection = None
        self.last_package_inspection = None
        self._pending_reviewed_install = None
        self._autonomy_policy = load_policy(STATE/'routine-software-policy.json')
        self._project_policy = load_project_policy(STATE/'project-work-policy.json')
        self._auto_verification_in_flight = None
        self._stopped_auto_tests = set()
        self._graph_test_leases = {}
        self._graph_repair_leases = {}
        self._auto_tool_history = read_snapshot(STATE/'routine-software-history.json') or {}
        self._auto_tool_queue = []
        self._auto_tool_active = None
        self._auto_tool_waiting = []
        self._tool_verification = ToolVerificationStore(STATE/'tool-verification-v43.json')
        self._tool_probe_queue = []
        self._tool_probe_active = None
        self.quiet_tests = QuietTestStore(STATE/'quiet-playtests-v44.json')
        stale_quiet = self.quiet_tests.interrupt_stale()
        if stale_quiet:
            record(STATE,'desktop','quiet_test_interrupted',
                   project_name=Path(stale_quiet['project']).name)
        self._quiet_test_stopped = False
        self._quiet_test_stop_reason = ''
        self._quiet_test_active = None
        self.gui_tests = IsolatedGuiStore(STATE/'isolated-gui-v45.json')
        stale_gui = self.gui_tests.interrupt_stale()
        if stale_gui:
            record(STATE,'desktop','isolated_gui_interrupted',
                   executable=stale_gui.get('executable_name'))
        self._gui_test_active = None
        self._gui_test_stop = threading.Event()
        self._manual_catalog_install = None
        prior_auto = read_snapshot(STATE/'last-routine-software.json')
        if isinstance(prior_auto,dict) and prior_auto.get('status')=='launch_requested':
            prior_auto['status']='interrupted_unverified'
            prior_auto['reusable_approval']=False
            save_snapshot(STATE/'last-routine-software.json',prior_auto)
        # Never replay installation permissions after app restart. A prior
        # launch may still have a child installer running: state is unknown.
        prior_install=read_snapshot(STATE/'last-reviewed-install.json')
        if isinstance(prior_install,dict) and prior_install.get('status')=='launch_requested':
            prior_install['status']='interrupted_unverified'
            prior_install['reusable_approval']=False
            save_snapshot(STATE/'last-reviewed-install.json',prior_install)
        self.media_process = None
        self.sentinel_process = None
        self._sentinel_started = False
        self.last_sentinel_log_id = 0
        self.last_janus_advice_id = 0
        self.last_sentinel_advice_id = 0
        self.active_job = None
        self.active_conversation = None
        # A cancelled reply must release the single-flight ONNX worker before
        # another chat can run. Restart is requested only for this intervention.
        self._restart_cancelled_node_pid = None
        self._explicit_model_stop = False
        self._unexpected_model_exits = 0
        self._model_transport_retries = {}
        self._model_transport_waiting = False
        self._quitting = False
        self.reply_stage = ''
        self.reply_started = 0.0
        self.reply_outcome = None
        self.active_started = 0.0
        self.queue_paused = False
        self.project = None
        self.current_file = None
        self.proposed = None
        self.proposal_job = None
        self.proposal_step = None
        self.attachments = []
        self.imported_spec_source = None
        self.image_photo = None
        self.chat_ids = []
        self.current_chat = None
        self.inventory = None
        self.meter=Meter()
        self.client = LocalModelClient(STATE/'sessions.sqlite3')
        self.capabilities = CapabilityLibrary(STATE/'capabilities.sqlite3')
        self.tool_learning = ToolAcquisition(STATE/'tool_acquisition.sqlite3')
        self.specifications = SpecificationIndex(STATE/'specification_index.sqlite3')
        self.inspection_exclusions = InspectionExclusions(STATE/'project-inspection-exclusions-v46.json')
        self.plan_continuations = PlanContinuation(STATE)
        self.hierarchies = HierarchicalPlanStore(STATE/'hierarchical_plans.sqlite3')
        self.jobs = JobStore(STATE/'jobs.sqlite3')
        self.cycles = DevelopmentCycleStore(STATE/'development-cycles.sqlite3')
        self.graphs = TaskGraphStore(STATE/'task-graph.sqlite3')
        self.checkpoints = SourceCheckpoints(STATE/'source-checkpoints')
        interrupted_graph_actions = self.graphs.interrupted()
        for interrupted_id in set(interrupted_graph_actions):
            j = self.jobs.get(interrupted_id)
            if j and j['state'] not in ('complete','cancelled','failed'):
                self.jobs.change(interrupted_id,'needs_input',
                    'Interrupted graph lease: inspect source/test evidence; do not replay blindly',
                    allowed=('queued','running','paused','waiting_verification','waiting_repair','needs_input'))
        interrupted_cycles = self.cycles.interrupted()
        if interrupted_cycles:
            record(STATE,'desktop','development_cycles_interrupted',
                   count=len(interrupted_cycles),job_ids=interrupted_cycles[:30])
        self.conversations = ConversationStore(STATE/'conversations.sqlite3')
        self.conversations.invalidate_incompatible_drafts()
        self._migrate_unapproved_requests()
        self.conversations.restore_legacy_creation_times(self.jobs.get)
        self.jobs.freeze_unapproved_legacy_builds()
        self.chats = ChatRegistry(STATE/'chats.sqlite3')
        self.tasks = TaskBoard(STATE/'tasks.sqlite3')
        self.janus = JanusStore(STATE/'janus.sqlite3')
        self.sentinel = SentinelStore(STATE/'sentinel.sqlite3')
        self.disk_gate = DiskGate(game_names_path=ROOT/'game_executables.txt',game_flag=STATE/'game-active.flag')
        self.settings_file = STATE/'desktop.json'
        self.x4_settings_file = STATE/'x4-sources.json'
        self.x4_game_dir = ''
        self.x4_reference_dir = ''
        self.x4_catalog_tool = ''
        self.x4_report = None
        self._x4_report_project = None
        try:
            x4_settings=json.loads(self.x4_settings_file.read_text('utf-8'))
            if isinstance(x4_settings,dict):
                self.x4_game_dir=str(x4_settings.get('game_dir') or '')
                self.x4_reference_dir=str(x4_settings.get('reference_dir') or '')
                self.x4_catalog_tool=str(x4_settings.get('catalog_tool') or '')
        except (OSError, ValueError):pass
        self._theme()
        self._make_ui()
        self._tooltip_handles = install_tooltips(self)
        self.bind_all('<F1>',lambda _event: self._open_user_guide(),add='+')
        self._restore_project()
        self._refresh_chats()
        self._refresh_jobs()
        self.after(125, self._handle_events)
        self.after(1000, self._scheduler)
        self.after(1700, self._automatic_tool_tick)
        self.after(2300, self._tool_probe_tick)
        self.after(1900, self._project_work_tick)
        self.after(2200, self._poll_server)
        self.after(1000, self._poll_reply_notice)
        # Preserve the original button arrangement when Windows reduces window height.
        self.bind('<Configure>', self._fit_chat_to_window)
        self.after(2000, self._process_snapshot)
        self.after(1500, self._auto_start_if_installed)
        self.after(700, self._start_sentinel)
        self.after(3000, self._refresh_janus_view)
        self.protocol('WM_DELETE_WINDOW',self._quit)
        self._log('Desktop opened. Local ONNX only. Routine catalog tool management: '+
                  ('ENABLED' if self._autonomy_policy['enabled'] else 'OFF')+
                  '; bounded project work: '+('ENABLED' if self._project_policy['enabled'] else 'OFF')+
                   '; arbitrary scripts and third-party installations remain controlled.')
        self._log('Select a project and use Computer & Tools to inspect this machine. Auto-save happens only after specific consent.')
        self._refresh_inventory()

    def _theme(self):
        s=ttk.Style(self);s.theme_use('clam')
        s.configure('TFrame',background=BG)
        s.configure('Panel.TFrame',background=PANEL)
        s.configure('TLabel',background=BG,foreground=TEXT,font=('Segoe UI',10))
        s.configure('Muted.TLabel',background=BG,foreground=MUTED)
        s.configure('TButton',padding=(10,6),font=('Segoe UI',10),background='#243448',foreground=TEXT,borderwidth=0)
        s.configure('TCheckbutton',background=BG,foreground=TEXT,font=('Segoe UI',10))
        s.map('TCheckbutton',background=[('active',BG)],foreground=[('disabled',MUTED)])
        s.map('TButton',background=[('active','#34465c')])
        s.configure('TNotebook',background=BG,borderwidth=0)
        s.configure('TNotebook.Tab',padding=(12,8),background=PANEL,foreground=MUTED)
        s.map('TNotebook.Tab',background=[('selected','#293c52')],foreground=[('selected',TEXT)])
        s.configure('Treeview',background=PANEL,foreground=TEXT,fieldbackground=PANEL,rowheight=26,borderwidth=0)
        s.map('Treeview',background=[('selected','#31465c')])
        s.configure('Treeview.Heading',background='#243448',foreground=TEXT)
        s.configure('TCombobox',fieldbackground=INPUT)

    def _text(self,parent,*,readonly=False,height=10,font=('Consolas',10),wrap='word'):
        w=tk.Text(parent,height=height,wrap=wrap,font=font,bg=INPUT,fg=TEXT,
                  insertbackground=TEXT,relief='flat',padx=10,pady=9,
                  selectbackground='#31465c',undo=not readonly)
        if readonly:w.config(state='disabled')
        return w

    def _make_ui(self):
        top=ttk.Frame(self);top.pack(fill='x',padx=14,pady=(11,7))
        tk.Label(top,text='DeepThorT',font=('Segoe UI Semibold',21),bg=BG,fg=ACCENT).pack(side='left')
        tk.Label(top,text='  •  OFFLINE / PERSISTENT',font=('Segoe UI',9),bg=BG,fg=MUTED).pack(side='left',pady=(9,0))
        ttk.Button(top,text='Install AI',command=self._install_ai).pack(side='right',padx=4)
        ttk.Button(top,text='User guide',command=self._open_user_guide).pack(side='right',padx=4)
        ttk.Button(top,text='Self-diagnose',command=self._diagnose).pack(side='right',padx=4)
        ttk.Button(top,text='Export diagnostics',command=self._export_diagnostics).pack(side='right',padx=4)
        ttk.Button(top,text='Stop AI',command=self._stop_ai).pack(side='right',padx=4)
        ttk.Button(top,text='Start AI',command=self._start_ai).pack(side='right',padx=4)
        self.model_status=tk.StringVar(value='AI: not started')
        ttk.Label(top,textvariable=self.model_status,style='Muted.TLabel').pack(side='right',padx=12)

        body=ttk.Panedwindow(self,orient='horizontal');body.pack(fill='both',expand=True,padx=12,pady=(0,9))
        left=ttk.Frame(body,style='Panel.TFrame',width=290);right=ttk.Frame(body)
        body.add(left,weight=1);body.add(right,weight=5)
        tk.Label(left,text='PROJECT WORKSPACE',font=('Segoe UI Semibold',11),fg=TEXT,bg=PANEL).pack(anchor='w',padx=11,pady=(15,5))
        ttk.Button(left,text='Choose folder…',command=self._choose_project).pack(fill='x',padx=10,pady=3)
        self.project_label=tk.Label(left,text='General chat — no project selected',font=('Segoe UI',9),
                  bg=PANEL,fg=MUTED,justify='left',wraplength=255)
        self.project_label.pack(anchor='w',padx=11,pady=(5,8))
        ttk.Button(left,text='Refresh project files',command=self._refresh_files).pack(fill='x',padx=10,pady=3)
        tk.Label(left,text='PROJECT FILES',fg=TEXT,bg=PANEL).pack(anchor='w',padx=11,pady=(9,4))
        self.files=ttk.Treeview(left,show='tree',selectmode='browse');self.files.pack(fill='both',expand=True,padx=9,pady=(0,8))
        self.files.bind('<<TreeviewSelect>>',self._on_file)
        self.files.bind('<Button-3>',self._project_file_context_menu)
        # On macOS Ctrl+click is the conventional secondary click.
        if sys.platform == 'darwin':
            self.files.bind('<Control-Button-1>',self._project_file_context_menu)
        ttk.Button(left,text='Propose new project file…',command=self._new_file).pack(fill='x',padx=10,pady=(0,11))

        self.tabs=ttk.Notebook(right);self.tabs.pack(fill='both',expand=True)
        chat,queue_tab,files_tab,tasks_tab,process_tab,janus_tab,hardware_tab,media_tab=(ttk.Frame(self.tabs) for _ in range(8))
        for frame,title in ((chat,'Chats'),(queue_tab,'Work queue'),(files_tab,'File review'),
                (tasks_tab,'Tasks'),(process_tab,'Processes'),(janus_tab,'JANUS & Sentinel'),(hardware_tab,'Computer & Tools'),(media_tab,'Files & Images')):
            self.tabs.add(frame,text=title)
        # CHAT: separate persisted sessions and a tall, scrollable prompt editor.
        chatbar=ttk.Frame(chat);chatbar.pack(fill='x',pady=(4,3))
        ttk.Button(chatbar,text='+ New chat',command=self._new_chat).pack(side='left')
        ttk.Button(chatbar,text='Rename chat',command=self._rename_chat).pack(side='left',padx=5)
        ttk.Button(chatbar,text='Close chat',command=self._close_chat).pack(side='left',padx=3)
        ttk.Button(chatbar,text='Attach files…',command=self._add_attachments).pack(side='left',padx=5)
        ttk.Button(chatbar,text='Clear attachments',command=self._clear_attachments).pack(side='left',padx=5)
        self.attach_file=tk.BooleanVar(value=False)
        tk.Checkbutton(chatbar,text='Include selected project file',variable=self.attach_file,
                       bg=BG,fg=TEXT,selectcolor=PANEL,activebackground=BG,activeforeground=TEXT).pack(side='right')
        self.attachment_status=tk.StringVar(value='No attachments; text, DOCX, PDF and images supported')
        ttk.Label(chat,textvariable=self.attachment_status,style='Muted.TLabel').pack(anchor='w',pady=2)
        # Reuse the original v10.9 connection/status line. A separate packed
        # banner pushes the two bottom action rows below the window on Windows.
        self._model_connection_message="AI offline: use Start AI or Self-diagnose to check setup"
        self.chat_connection=tk.StringVar(value=self._model_connection_message)
        self.reply_notice=self.chat_connection  # compatibility for existing status checks
        tk.Label(chat,textvariable=self.chat_connection,bg=BG,fg=YELLOW,anchor="w").pack(fill="x",pady=(2,4))
        self.chat_tabs=ttk.Notebook(chat);self.chat_tabs.pack(fill='x',pady=4)
        self.chat_tabs.bind('<<NotebookTabChanged>>',self._chat_changed)
        self.chat_tabs.bind('<Button-3>',self._chat_tab_menu)
        self.chat_history=self._text(chat,readonly=True,height=13,font=('Segoe UI',10))
        self.chat_history.pack(fill='both',expand=True)
        for role,color in (('user',ACCENT),('assistant',GREEN),('warning',YELLOW)):
            self.chat_history.tag_configure(role,foreground=color)
        tk.Label(chat,text='PROMPT / SPECIFICATION — Ctrl+Enter sends chat; only approved plans enter the work queue',
                 bg=BG,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',pady=(7,3))
        self.input=self._text(chat,height=12,font=('Segoe UI',11));self.input.pack(fill='both',expand=False)
        self.input.bind('<Control-Return>',lambda e:self._send())
        # Keyboard/context-menu access avoids another button row in the
        # original window geometry, which users need for remote desktop.
        self.input.bind('<Control-Shift-O>',self._import_large_specification)
        self.input.bind('<Control-Shift-o>',self._import_large_specification)
        self.input.bind('<Button-3>',self._show_spec_import_menu)
        ca=ttk.Frame(chat);ca.pack(fill='x',pady=7)
        self.chat_actions=ca
        chat_controls=ttk.Frame(ca);chat_controls.pack(fill='x',pady=(0,3))
        plan_controls=ttk.Frame(ca);plan_controls.pack(fill='x')
        ttk.Button(chat_controls,text='Send message',command=self._send).pack(side='left')
        ttk.Button(chat_controls,text='Diagnose AI',command=self._diagnose).pack(side='left',padx=5)
        ttk.Button(chat_controls,text='Retry failed reply',command=self._retry_conversation).pack(side='left',padx=5)
        ttk.Button(chat_controls,text='Stop reply',command=self._stop_chat_reply).pack(side='left',padx=5)
        ttk.Button(plan_controls,text='Draft project plan',command=lambda:self._queue_input('plan')).pack(side='left')
        ttk.Button(plan_controls,text='Approve plan & queue',command=self._approve_conversation_plan).pack(side='left',padx=5)
        ttk.Button(plan_controls,text='Revise existing file',command=lambda:self._queue_input('edit')).pack(side='left',padx=5)
        ttk.Label(ca,text='Conversation first. Only your approved plan becomes an executable job.',style='Muted.TLabel').pack(anchor='w',pady=2)

        # REAL PERSISTENT WORK QUEUE
        qhead=ttk.Frame(queue_tab);qhead.pack(fill='x',pady=8)
        self.queue_summary=tk.StringVar(value='No queued work')
        ttk.Label(qhead,textvariable=self.queue_summary,style='Muted.TLabel').pack(side='left',padx=4)
        self.pause_queue=ttk.Button(qhead,text='Pause queue',command=self._toggle_queue)
        self.pause_queue.pack(side='right',padx=4)
        ttk.Button(qhead,text='Refresh',command=self._refresh_jobs).pack(side='right',padx=4)
        qt=ttk.Frame(queue_tab);qt.pack(fill='x',pady=4)
        ttk.Button(qt,text='Cancel selected',command=self._cancel_job).pack(side='left',padx=3)
        ttk.Button(qt,text='Resume selected',command=self._resume_job).pack(side='left',padx=3)
        ttk.Button(qt,text='Review legacy plan',command=self._approve_build_plan).pack(side='left',padx=3)
        ttk.Button(qt,text='Verify build',command=self._verify_build).pack(side='left',padx=3)
        ttk.Button(qt,text='Load prompt into editor',command=self._load_job_prompt).pack(side='left',padx=3)
        workbar=ttk.Frame(queue_tab);workbar.pack(fill='x',pady=(0,5))
        self.project_work_enabled=tk.BooleanVar(value=self._project_policy['enabled'])
        ttk.Checkbutton(workbar,text='Continue approved file steps and fixed tests without repeated prompts',
                        variable=self.project_work_enabled,command=self._set_project_work_policy).pack(side='left',padx=3)
        ttk.Button(workbar,text='Revoke selected job automation',
                   command=self._revoke_selected_project_work).pack(side='left',padx=8)
        restorebar=ttk.Frame(queue_tab);restorebar.pack(fill='x',pady=(0,3))
        ttk.Button(restorebar,text='Restore source checkpoint…',
                   command=self._restore_source_checkpoint).pack(side='left',padx=3)
        ttk.Button(restorebar,text='Quiet Godot scene test',
                   command=self._run_quiet_scene).pack(side='left',padx=7)
        ttk.Button(restorebar,text='Stop quiet test',
                   command=self._stop_quiet_scene).pack(side='left',padx=3)
        guibar=ttk.Frame(queue_tab);guibar.pack(fill='x',pady=(0,3))
        ttk.Button(guibar,text='Isolated GUI smoke test…',
                   command=self._run_isolated_gui).pack(side='left',padx=3)
        ttk.Button(guibar,text='Stop isolated GUI test',
                   command=self._stop_isolated_gui).pack(side='left',padx=3)
        ttk.Label(queue_tab,text='v45: Windows programs can be observed on a separate desktop with no input takeover. '
                  'Shares the original 20% CPU job cap; NOT visual proof, VM isolation or game playtesting.', 
                  style='Muted.TLabel').pack(anchor='w',pady=(0,5))
        self.job_tree=ttk.Treeview(queue_tab,columns=('state','mode','chat','detail'),show='headings',height=12)
        for column,title,width in (('state','Status',125),('mode','Type',70),('chat','Chat',120),('detail','Work and progress',540)):
            self.job_tree.heading(column,text=title);self.job_tree.column(column,width=width,stretch=column=='detail')
        self.job_tree.pack(fill='both',expand=True)
        self.job_tree.bind('<<TreeviewSelect>>',self._job_selected)
        self.job_details=self._text(queue_tab,readonly=True,height=10)
        self.job_details.pack(fill='both',expand=False,pady=(6,0))

        # FILE REVIEW
        fhead=ttk.Frame(files_tab);fhead.pack(fill='x',pady=7)
        self.file_title=tk.StringVar(value='Choose a file or request a new file proposal')
        ttk.Label(fhead,textvariable=self.file_title).pack(side='left')
        ttk.Button(fhead,text='Apply approved change',command=self._apply_proposal).pack(side='right')
        self.file_preview=self._text(files_tab,height=25,wrap='none')
        self.file_preview.pack(fill='both',expand=True)
        self._preview('Select a file on the left.\n\nRequest a proposed edit in Chats.\n'
                      'Approved unattended jobs may save only exact authorized files with backups; '
                       'other changes require individual file review.')

        # TASK BOARD (distinct from execution queue)
        tbar=ttk.Frame(tasks_tab);tbar.pack(fill='x',pady=9)
        ttk.Button(tbar,text='Add task',command=self._add_task).pack(side='left',padx=3)
        ttk.Button(tbar,text='Complete / reopen',command=self._toggle_task).pack(side='left',padx=3)
        ttk.Button(tbar,text='Send to prompt',command=self._task_to_chat).pack(side='left',padx=3)
        self.task_tree=ttk.Treeview(tasks_tab,columns=('state','description'),show='headings')
        for x,title,w in (('state','Status',130),('description','Task / project plan',700)):
            self.task_tree.heading(x,text=title);self.task_tree.column(x,width=w,stretch=x=='description')
        self.task_tree.pack(fill='both',expand=True)
        ttk.Label(tasks_tab,text='Tasks are a durable plan. Only verified completed work should be marked complete.',style='Muted.TLabel').pack(anchor='w',pady=8)

        # TRUE PROCESS STATUS, NO INVENTED TOKEN PROGRESS
        self.process_info=self._text(process_tab,readonly=True,height=8)
        self.process_info.pack(fill='x',pady=(6,4))
        pbar=ttk.Frame(process_tab);pbar.pack(fill='x',pady=3)
        ttk.Button(pbar,text='Cancel running job',command=self._cancel_active).pack(side='left',padx=3)
        ttk.Button(pbar,text='Stop tool / install process',command=self._cancel_tool).pack(side='left',padx=3)
        tk.Label(process_tab,text='ACTIVITY AND WORK LOG (actual events)',bg=BG,fg=MUTED).pack(anchor='w',pady=(10,4))
        self.activity=self._text(process_tab,readonly=True,height=18)
        self.activity.pack(fill='both',expand=True)

        # JANUS coordinator and bounded read-only Sentinel watchdog.
        janus_bar=ttk.Frame(janus_tab);janus_bar.pack(fill='x',pady=7)
        ttk.Button(janus_bar,text='Refresh status',command=self._show_janus_status).pack(side='left',padx=3)
        ttk.Button(janus_bar,text='Set primary goal…',command=self._set_janus_goal).pack(side='left',padx=3)
        ttk.Button(janus_bar,text='Inspect 22 core states',command=self._inspect_janus_cores).pack(side='left',padx=3)
        ttk.Button(janus_bar,text='Pause JANUS',command=lambda:self._set_janus_paused(True)).pack(side='left',padx=3)
        ttk.Button(janus_bar,text='Resume JANUS',command=lambda:self._set_janus_paused(False)).pack(side='left',padx=3)
        ttk.Button(janus_bar,text='Cancel selected approved process',command=self._cancel_janus_action).pack(side='left',padx=3)
        ttk.Label(janus_tab,text='Two independent 11-core societies (77 internal Fano faculties each). JANUS executes approved work; Sentinel checks task adherence and health. Local-model ideas are review-only.',style='Muted.TLabel').pack(anchor='w',pady=4)
        self.janus_status_text=self._text(janus_tab,readonly=True,height=11)
        self.janus_status_text.pack(fill='x',pady=(4,7))
        self.janus_action_tree=ttk.Treeview(janus_tab,columns=('id','state','kind','label'),show='headings',height=7)
        for col,title,width in (('id','ID',55),('state','Status',125),('kind','Kind',90),('label','Approved process',550)):
            self.janus_action_tree.heading(col,text=title)
            self.janus_action_tree.column(col,width=width,stretch=col=='label')
        self.janus_action_tree.pack(fill='both',expand=True)
        ttk.Label(janus_tab,text='Sentinel events and JANUS cycles (durable, actual observations)',style='Muted.TLabel').pack(anchor='w',pady=(6,3))
        self.janus_events_text=self._text(janus_tab,readonly=True,height=12)
        self.janus_events_text.pack(fill='both',expand=True)

        # MACHINE DISCOVERY, PLANNING, OPT-IN INSTALLER AND TESTING TOOLS
        hwbar=ttk.Frame(hardware_tab);hwbar.pack(fill='x',pady=7)
        ttk.Button(hwbar,text='Scan this computer',command=self._refresh_inventory).pack(side='left',padx=3)
        ttk.Button(hwbar,text='Check tools needed for prompt',command=self._plan_tools).pack(side='left',padx=3)
        ttk.Button(hwbar,text='Investigate app…',command=self._investigate_tool).pack(side='left',padx=3)
        ttk.Button(hwbar,text='Learn procedure…',command=self._draft_tool_procedure).pack(side='left',padx=3)
        ttk.Button(hwbar,text='Run learned procedure…',command=self._run_learned_procedure).pack(side='left',padx=3)
        xr=ttk.Frame(hardware_tab);xr.pack(fill='x',pady=(4,4))
        ttk.Button(xr,text='Inspect X4 sources',command=self._inspect_x4_sources).pack(side='left',padx=3)
        ttk.Button(xr,text='Choose X4 game folder…',command=self._choose_x4_game).pack(side='left',padx=3)
        ttk.Button(xr,text='Choose extracted X4 XML…',command=self._choose_x4_refs).pack(side='left',padx=3)
        ttk.Button(xr,text='Extract X4 XML (approval required)…',command=self._extract_x4_references).pack(side='left',padx=3)
        self.x4_source_info=self._text(hardware_tab,readonly=True,height=10)
        self.x4_source_info.pack(fill='both',expand=False,pady=(4,8))
        self._show(self.x4_source_info,'X4 sources not inspected. Use Inspect X4 sources to discover your installed game and any extracted XML. No downloads or changes occur during inspection.')
        self.machine_text=self._text(hardware_tab,readonly=True,height=20)
        self.machine_text.pack(fill='both',expand=True)
        action=ttk.Frame(hardware_tab);action.pack(fill='x',pady=(9,4))
        ttk.Label(action,text='Local software tools:',style='Muted.TLabel').pack(side='left',padx=4)
        self.install_choice=tk.StringVar(value='Godot')
        self.install_menu=ttk.Combobox(action,textvariable=self.install_choice,values=sorted(INSTALL_CATALOG),state='readonly',width=20)
        self.install_menu.pack(side='left',padx=5)
        ttk.Button(action,text='Install selected catalog tool…',command=self._approve_tool_install).pack(side='left',padx=3)
        ttk.Button(action,text='Find official tool page…',command=self._find_official_tool_page).pack(side='left',padx=3)
        ttk.Button(action,text='Search packages online…',command=self._search_online_tools).pack(side='left',padx=3)
        autonomy=ttk.Frame(hardware_tab);autonomy.pack(fill='x',pady=(2,6))
        self.autonomy_enabled=tk.BooleanVar(value=self._autonomy_policy['enabled'])
        self.autonomy_upgrades=tk.BooleanVar(value=self._autonomy_policy['allow_upgrades'])
        ttk.Checkbutton(autonomy,text='Automatically manage routine project tools',
                        variable=self.autonomy_enabled,command=self._set_tool_autonomy).pack(side='left',padx=3)
        ttk.Checkbutton(autonomy,text='Allow tool upgrades',
                        variable=self.autonomy_upgrades,command=self._set_tool_autonomy).pack(side='left',padx=12)
        checks=ttk.Frame(hardware_tab);checks.pack(fill='x',pady=(3,10))
        ttk.Label(checks,text='Approved local project checks:',style='Muted.TLabel').pack(side='left',padx=4)
        self.check_choice=tk.StringVar(value='Git: status')
        self.check_menu=ttk.Combobox(checks,textvariable=self.check_choice,state='readonly',width=24,
            values=('Git: status','Python: unit tests','Node.js: npm test','Godot: validate project','.NET: tests','Blender: version'))
        self.check_menu.pack(side='left',padx=4)
        ttk.Button(checks,text='Review & run…',command=self._run_project_check).pack(side='left',padx=3)
        acquire=ttk.Frame(hardware_tab);acquire.pack(fill='x',pady=(0,5))
        ttk.Label(acquire,text='Discovered software — separate review:',style='Muted.TLabel').pack(side='left',padx=4)
        ttk.Button(acquire,text='Inspect package ID…',command=self._inspect_package_id).pack(side='left',padx=5)
        ttk.Button(acquire,text='Install inspected package…',command=self._approve_inspected_install).pack(side='left',padx=5)
        tk.Label(hardware_tab,text='After approving a build plan, recognised project tools can install/upgrade automatically. Windows UAC remains active. Unknown software is never automatically executed.',
                 bg=BG,fg=MUTED,wraplength=750).pack(anchor='w',pady=(0,7))

        # MEDIA: explicit local file and image handling. No cloud image calls.
        media_head=ttk.Frame(media_tab);media_head.pack(fill='x',pady=8)
        ttk.Button(media_head,text='Attach documents / pictures…',command=self._add_attachments).pack(side='left',padx=3)
        ttk.Button(media_head,text='Clear selection',command=self._clear_attachments).pack(side='left',padx=3)
        ttk.Button(media_head,text='Read selected image',command=self._analyze_image).pack(side='left',padx=3)
        self.media_summary=tk.StringVar(value='Choose files; local model downloads are opt-in.')
        ttk.Label(media_tab,textvariable=self.media_summary,style='Muted.TLabel').pack(anchor='w',pady=(0,5))
        media_actions=ttk.Frame(media_tab);media_actions.pack(fill='x',pady=6)
        ttk.Button(media_actions,text='Install PDF reader…',command=self._install_pdf_reader).pack(side='left',padx=3)
        ttk.Button(media_actions,text='Install Vision Model…',command=self._install_vision).pack(side='left',padx=3)
        ttk.Button(media_actions,text='Install Image Generator…',command=self._install_image_generator).pack(side='left',padx=3)
        ttk.Button(media_actions,text='Generate image from prompt',command=self._queue_image).pack(side='left',padx=3)
        self.refine_image=tk.BooleanVar(value=True)
        tk.Checkbutton(media_tab,text='Ask local coding model to refine image description before generation',
                       variable=self.refine_image,bg=BG,fg=TEXT,selectcolor=PANEL,
                       activebackground=BG,activeforeground=TEXT).pack(anchor='w',pady=(0,4))
        self.image_preview=tk.Label(media_tab,text='Selected image preview',bg=PANEL,fg=MUTED,height=17)
        self.image_preview.pack(fill='both',expand=True,pady=6)
        self.image_info=self._text(media_tab,readonly=True,height=9)
        self.image_info.pack(fill='both',expand=False,pady=(4,6))
        self._show(self.image_info,'Image reading uses a separate local Florence ONNX vision model after user-approved installation. '
            'Image generation uses a separate offline Stable Diffusion model and CPU diffusers after user-approved installation. '
            'Image operations may run very slowly and cannot guarantee the visual quality of a cloud service. '
            'Installation and heavy generation should run when games are closed.')

        foot=ttk.Frame(self);foot.pack(fill='x',padx=13,pady=(0,8))
        self.status=tk.StringVar(value='Idle • 20% total CPU allocation + 20% memory-commit budget')
        ttk.Label(foot,textvariable=self.status,style='Muted.TLabel').pack(side='left')
        ttk.Label(foot,text='GPU inference off · Offline generation · No cloud fallback',style='Muted.TLabel').pack(side='right')

    # ----------- basic GUI data and project/chat selection ------------
    def _show(self,box,text):
        box.config(state='normal');box.delete('1.0','end');box.insert('1.0',text);box.config(state='disabled')
    def _preview(self,text):
        self.file_preview.delete('1.0','end');self.file_preview.insert('1.0',text)
    def _log(self,info):
        if str(info) == self._last_activity_message and time.monotonic()-self._last_activity_at<30:
            return  # Suppress repetitive GUI notices; underlying queue/worker events stay logged.
        self._last_activity_message=str(info)
        self._last_activity_at=time.monotonic()
        record(STATE,'desktop','activity',message=str(info))
        self.activity.config(state='normal')
        stamp=datetime.now().strftime('%H:%M:%S')
        self.activity.insert('end',f'[{stamp}] {info}\n');self.activity.see('end')
        self.activity.config(state='disabled')
    def report_callback_exception(self, exc_type, exc, tb):
        """Tk normally prints callbacks to an invisible stderr; always record them."""
        details=''.join(traceback.format_exception(exc_type,exc,tb))
        record(STATE,'desktop','tk_callback_failed',level='ERROR',exception_type=exc_type.__name__,stack=details[-12000:])
        self._log(f'GUI callback failed ({exc_type.__name__}); use Export diagnostics.')
        try:
            messagebox.showerror('DeepThorT internal error',
                f'A desktop action failed: {exc_type.__name__}. Use Export diagnostics to share the evidence.')
        except Exception:pass

    def _export_diagnostics(self):
        """A single local ZIP for support; no automatic uploads or raw chat content."""
        base=ROOT / ('DeepThorT-Diagnostics-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.zip')
        dest=filedialog.asksaveasfilename(parent=self,title='Save DeepThorT diagnostics ZIP',
             initialdir=str(ROOT),initialfile=base.name,defaultextension='.zip',
             filetypes=[('Diagnostic ZIP','*.zip')])
        if not dest:return
        try:
            status=local_server_status(timeout=.6)
            counts=self.jobs.count(self._project_key())
            saved_x4 = read_snapshot(STATE/'last-x4-inspection.json')
            if (self.x4_report and (getattr(self,'_x4_report_project',None)==str(self.project)
                 or matches_project(saved_x4, self.project))):
                x4_snapshot = summarize_x4_report(self.x4_report,
                    game_dir=self.x4_game_dir, reference_dir=self.x4_reference_dir,
                    project_dir=self.project)
            elif matches_project(saved_x4, self.project):
                x4_snapshot = saved_x4
            else:
                x4_snapshot = summarize_x4_report(None, game_dir=self.x4_game_dir,
                    reference_dir=self.x4_reference_dir, project_dir=self.project)
            saved_inventory = read_snapshot(STATE/'last-engine-inventory.json')
            if self.inventory and matches_project(summarize_inventory(self.inventory),self.project):
                inventory_snapshot = summarize_inventory(self.inventory)
            elif matches_project(saved_inventory,self.project):
                inventory_snapshot = saved_inventory
            else:
                inventory_snapshot = summarize_inventory(None)
            state={'x4_source_inspection':x4_snapshot, 'engine_readiness_scan':inventory_snapshot,
                   'model_pid':self.node.pid if self.node and self.node.poll() is None else None,
                   'model_ready':self.node_ready,'model_loading':self.node_loading,
                   'model_status':status,'active_job':self.active_job,
                   'queue_paused':self.queue_paused,'visible_project_jobs':counts,
                   'development_cycles':self.cycles.summary(self._project_key()),
                   'task_graph':self.graphs.summary(self._project_key()),
                   'quiet_scene_tests':self.quiet_tests.snapshot(),
                   'isolated_gui_tests':self.gui_tests.snapshot(),
                   'current_project_name':Path(self._project_key()).name,
                   'sentinel_pid':self.sentinel_process.pid if self.sentinel_process and self.sentinel_process.poll() is None else None,
                   'loading_stage':self.current_loading_stage, 'last_ai_error':self.last_ai_error,
                   'active_conversation':self.active_conversation,
                   'pending_conversations':len([x for x in self.conversations.thread(self.current_chat) if x['state']=='pending'])}
            record(STATE,'desktop','diagnostics_export_requested')
            export_diagnostics(STATE,Path(dest),app_root=ROOT,app_state=state)
            self._log('Diagnostic ZIP saved: '+str(dest))
            messagebox.showinfo('Diagnostic ZIP created',
                'The diagnostic file is ready:\n'+str(dest)+'\n\n'
                'Attach that one ZIP in ChatGPT for troubleshooting. It contains local logs and metadata; '
                'review it before sharing. Full prompts and model weights are excluded.',parent=self)
        except Exception as error:
            record(STATE,'desktop','diagnostics_export_failed',level='ERROR',error=str(error))
            messagebox.showerror('Export failed',str(error),parent=self)

    def _chat_line(self,role,message):
        # The durable database owns full text, NOT the timeline widget. Millions
        # of words rendered into Tk on every tab switch would hang Windows.
        # Every preview explicitly states what remains stored and how much.
        if len(message)>12000:
            from hashlib import sha256
            original_length=len(message)
            fingerprint=sha256(message.encode('utf-8')).hexdigest()[:20]
            message=(f'[LARGE STORED TEXT — {original_length:,} characters; '
                     f'SHA-256 prefix {fingerprint}; this is a display PREVIEW only. '
                     'The complete original remains in local SQLite. No text was '
                     'removed from the saved request.]\n\n'
                     +message[:3500]+'\n\n[... DISPLAY ONLY: middle not rendered ...]\n\n'
                     +message[-1200:])
        self.chat_history.config(state='normal')
        label='You' if role=='user' else 'DeepThorT' if role=='assistant' else 'Notice'
        self.chat_history.insert('end',f'{label}:\n',role if role in ('user','assistant') else 'warning')
        self.chat_history.insert('end',message+'\n\n')
        self.chat_history.see('end');self.chat_history.config(state='disabled')
    def _project_key(self):
        return str(self.project) if self.project else '(general)'
    # ----------------- Local document / image UI ------------------
    def _add_attachments(self):
        chosen=filedialog.askopenfilenames(title='Choose local files or pictures to attach')
        if not chosen:return
        try:
            for path in chosen:
                resolved=str(validate_attachment(path))
                if resolved not in self.attachments:self.attachments.append(resolved)
            if len(self.attachments)>8:raise ValueError('Select at most eight attachments')
        except Exception as e:
            messagebox.showwarning('Unsupported attachment',str(e));self.attachments=self.attachments[:8]
        self._attachment_refresh()
        if self.attachments and classify(self.attachments[-1])=='image':
            self._display_image(Path(self.attachments[-1]))
    def _clear_attachments(self):
        self.attachments=[];self._attachment_refresh()
    def _attachment_refresh(self):
        names=', '.join(Path(x).name for x in self.attachments)
        self.attachment_status.set(names if names else 'No attachments; text, DOCX, PDF and images supported')
        self.media_summary.set(f'{len(self.attachments)} attached file(s). Pictures require optional local vision model for description.')
    def _display_image(self,path):
        self.image_photo=None
        try:
            from PIL import Image, ImageTk
            with Image.open(path) as image:
                image.thumbnail((680,410))
                self.image_photo=ImageTk.PhotoImage(image.copy(),master=self)
        except ImportError:
            try:self.image_photo=tk.PhotoImage(file=str(path),master=self)
            except Exception:pass
        except Exception as e:self._log('Image preview problem: '+str(e))
        self.image_preview.config(image=self.image_photo,
                                  text='' if self.image_photo else f'Image selected: {path.name} (preview requires Pillow for JPEG/WebP)')
    def _analyze_image(self):
        if len(self.attachments)!=1 or classify(self.attachments[0])!='image':
            messagebox.showinfo('Select one picture','Use Attach files to select one image (.png, .jpg, .webp etc).');return
        self._queue_special('vision','Describe the selected image using the local Florence vision engine',self.attachments)
    def _queue_image(self):
        if not self.project:
            messagebox.showinfo('Choose a project','Choose a local project folder where the generated picture will be saved.');return
        description=self.input.get('1.0','end').strip()
        if not description:
            description=simpledialog.askstring('Describe the image','Image prompt:',parent=self) or ''
        if not description:return
        if len(description)>2000:
            messagebox.showwarning('Image prompt too long','Use a description under 2,000 characters.');return
        if not messagebox.askyesno('Confirm image-generation job',
            'Generate this image with the local model and save it inside the selected project?\n\n'
            'This is an explicit image-generation task, not an ordinary chat message.',parent=self):return
        self._queue_special('image',description,[])
        self.tabs.select(1)
    def _queue_special(self,mode,description,files):
        target=f'generated/deepthort-{uuid.uuid4().hex[:12]}.png' if mode=='image' else None
        try:ident=self.jobs.submit(self._project_key(),self.current_chat,mode,description,target,attachments=files)
        except Exception as e:messagebox.showerror('Cannot queue',str(e));return
        self._log(f'{mode.capitalize()} job #{ident} queued; inference runs locally.')
        self._refresh_jobs()
    def _install_pdf_reader(self):
        if self.disk_gate.gaming():
            messagebox.showinfo('Gaming priority','Close your game before installing packages.');return
        if not messagebox.askyesno('Install optional offline PDF reader',
            'Install the local pypdf Python package?\n\nThis is only for extracting selectable PDF text. '
            'Scanned PDF images still need OCR and may not be readable.\n\nApprove?',parent=self):return
        self.tabs.select(4)
        self._start_command([sys.executable,'-m','pip','install','--no-input','pypdf>=5,<7'],
                            cwd=ROOT,label='Install pypdf',kind='installation')
    def _install_vision(self):
        if self.disk_gate.gaming():
            messagebox.showinfo('Gaming priority','Close your game before a large model download.');return
        if not messagebox.askyesno('Install offline image reader',
            'Download the Florence-2-base-ft ONNX vision model (several hundred MB) from Hugging Face?\n\n'
            'This is a separate local vision model; it does not use an online inference API.\n'
            'It runs only when asked to read a picture. Approve download?',parent=self):return
        self.tabs.select(4)
        self._start_command([sys.executable,str(ROOT/'download_vision.py')],cwd=ROOT,
                            label='Install local vision model',kind='installation')
    def _install_image_generator(self):
        if self.disk_gate.gaming():
            messagebox.showinfo('Gaming priority','Close your game before a large model download.');return
        if not messagebox.askyesno('Install offline image generator',
            'Install CPU PyTorch, Diffusers and Stable Diffusion 1.5 model weights?\n\n'
            'This downloads several GB and can use substantial temporary disk space and memory. '
            'Inference will run offline and CPU-only under the 20% launcher limits.\n\n'
            'It can be extremely slow and can fail if physical RAM usage exceeds the allowed budget.\n'
            'Approve this one-time installation?',parent=self):return
        self.tabs.select(4)
        self._start_command([sys.executable,str(ROOT/'install_image_engine.py')],cwd=ROOT,
                            label='Install local image generator',kind='installation')

    def _restore_project(self):
        try:
            settings=json.loads(self.settings_file.read_text('utf-8'))
            p=Path(settings.get('project',''))
            if p.is_dir():self._set_project(p)
        except (OSError,ValueError,TypeError):pass
    def _choose_project(self):
        chosen=filedialog.askdirectory(title='Select your existing coding or game project')
        if chosen:self._set_project(Path(chosen))
    def _set_project(self,path):
        self.project=Path(path).resolve()
        self.current_file=None;self.proposed=None;self.proposal_job=None;self.proposal_step=None
        for row in self.files.get_children():self.files.delete(row)
        self.project_label.config(text=str(self.project))
        self.settings_file.write_text(json.dumps({'project':str(self.project)},indent=2),encoding='utf-8')
        self._log('Selected project: '+str(self.project))
        self._refresh_files();self._refresh_tasks();self._refresh_chats();self._refresh_jobs();self._refresh_inventory()
    def _refresh_chats(self):
        project=self._project_key()
        threads=self.chats.list(project)
        if not threads:
            self.current_chat=self.chats.create(project,'Chat 1');threads=self.chats.list(project)
        old=self.current_chat
        for tab in self.chat_tabs.tabs():self.chat_tabs.forget(tab)
        self.chat_ids=[]
        for ident,title in threads:
            frame=ttk.Frame(self.chat_tabs)
            self.chat_tabs.add(frame,text=title[:32]);self.chat_ids.append(ident)
        self.current_chat = old if old in self.chat_ids else self.chat_ids[0]
        self.chat_tabs.select(self.chat_ids.index(self.current_chat))
        self._reload_chat()
    def _chat_changed(self,_event=None):
        if not self.chat_ids:return
        idx=self.chat_tabs.index('current')
        if 0<=idx<len(self.chat_ids):
            self.current_chat=self.chat_ids[idx]
            self._reload_chat()
    def _new_chat(self):
        threads=self.chats.list(self._project_key())
        self.current_chat=self.chats.create(self._project_key(),f'Chat {len(threads)+1}')
        self._refresh_chats();self.input.focus_set()
    def _rename_chat(self):
        if not self.current_chat:return
        name=simpledialog.askstring('Rename chat','New chat title:',parent=self)
        if name:
            self.chats.rename(self.current_chat,name);self._refresh_chats()
    def _chat_tab_menu(self, event):
        """Reopen archived chats without adding another permanently packed row."""
        menu=tk.Menu(self,tearoff=False)
        menu.add_command(label='Close selected chat',command=self._close_chat)
        archived=self.chats.closed(self._project_key())
        if archived:
            menu.add_separator()
            for ident,title in archived[-15:]:
                menu.add_command(label='Reopen: '+title[:48],
                                 command=lambda ident=ident:self._reopen_chat(ident))
        try:menu.tk_popup(event.x_root,event.y_root)
        finally:menu.grab_release()

    def _reopen_chat(self, ident):
        if self.chats.reopen(ident,self._project_key()):
            self.current_chat=ident
            self._refresh_chats()
            self._log('Closed chat reopened; its existing history was preserved.')

    def _interrupt_cancelled_inference(self):
        """Terminate supervised single-flight ONNX inference and reload it once.

        A Python HTTP request cannot cancel a running ONNX generator. Killing its
        supervised server/worker is the real interruption boundary; a new server
        will be started *after* the old process exits, never concurrently.
        """
        proc=self.node
        if not proc or proc.poll() is not None:
            return
        self._restart_cancelled_node_pid=proc.pid
        self.node_ready=False
        self.node_loading=False
        self.node_started=0.0
        self.model_status.set('AI: stopping cancelled reply')
        self._set_connection_status('Cancelling local inference; other chats will resume after model reload.')
        try:
            proc.terminate()
        except OSError as exc:
            self._restart_cancelled_node_pid=None
            self._log('Could not stop ONNX worker: '+str(exc))
            self._set_connection_status('ONNX cancellation failed; use Stop AI and inspect Processes.')

    def _cancel_chat_replies(self, chat_id, *, reason):
        active=self.conversations.get(self.active_conversation) if self.active_conversation is not None else None
        active_in_chat=bool(active and active['chat_id']==chat_id)
        cancelled=self.conversations.cancel_chat_requests(chat_id,reason)
        if active_in_chat:
            self.active_conversation=None
            self.reply_stage=''
            self._interrupt_cancelled_inference()
        if cancelled:
            self._log(f'Stopped {len(cancelled)} unfinished reply request(s) in chat; no retry will be queued.')
        self.reply_outcome={'chat_id':chat_id,'message':f'STOPPED — {len(cancelled)} request(s) cancelled; history retained.'}
        self._render_reply_notice()
        return cancelled

    def _stop_chat_reply(self):
        if not self.current_chat:return
        cancelled=self._cancel_chat_replies(self.current_chat,reason='Stopped by user; retry requires explicit action')
        if not cancelled:
            messagebox.showinfo('No active reply','This chat has no running or waiting reply.',parent=self)
        self._reload_chat()

    def _close_chat(self):
        """Close the visible tab and stop only its conversation, not approved jobs."""
        chat_id=self.current_chat
        if not chat_id:return
        active=self.conversations.get(self.active_conversation) if self.active_conversation is not None else None
        running=bool(active and active['chat_id']==chat_id)
        pending=any(r['state'] in ('pending','running','waiting_sources')
                    for r in self.conversations.thread(chat_id,limit=1000))
        detail=(' Its outstanding replies will be stopped, including current ONNX generation. '
                'The model must reload before other chats can proceed.' if running else
                ' Its queued replies will be cancelled.' if pending else '')
        if not messagebox.askyesno('Close chat',
            'Close this chat tab?'+detail+'\n\n'
            'History and drafts are preserved and can be reopened with a right-click '
            'on the chat tabs. Approved work queue jobs are not deleted.',parent=self):
            return
        self._cancel_chat_replies(chat_id,reason='Chat closed by user; no automatic retry')
        if self.chats.close(chat_id,self._project_key()):
            self.current_chat=None
            self._refresh_chats()
            self._log('Chat tab closed; durable history retained and approved jobs untouched.')

    def _reload_chat(self):
        if not self.current_chat:return
        self._show(self.chat_history,'')
        conversation=self.conversations.thread(self.current_chat)
        projects=self.jobs.items(self._project_key())
        approved=[j for j in projects if j['chat_id']==self.current_chat]
        for event in merged_chat_timeline(self.client.display_history(self.current_chat),
                                          conversation,approved):
            if event['kind']=='legacy':
                for role,content in event['messages']:
                    self._chat_line(role,content)
                continue
            if event['kind']=='job':
                j=event['row']
                self._chat_line('user',j['prompt'])
                self._chat_line('warning',f"Job #{j['id']} [{j['state']}] {j['detail']}")
                continue
            turn=event['row']
            self._chat_line('user',turn['prompt'])
            if turn['mode']=='draft_plan' and turn['state']=='responded':
                try:
                    plan=parse_build_plan(turn['response'],Path(turn['project']),request=turn['prompt'])
                    listing='\n'.join(f"{i}. {x['path']} — {x['description']}" for i,x in enumerate(plan,1))
                    draft=self.conversations.latest_draft(turn['chat_id'],turn['project'])
                    appendix='\nUse Approve plan & queue only after agreement.' if draft else '\n(This plan is no longer the current draft.)'
                    self._chat_line('assistant','DRAFT IMPLEMENTATION PLAN — no work queued\n'+listing+appendix)
                except Exception:self._chat_line('warning','Draft plan could not be displayed; review in diagnostics.')
            elif turn['state']=='responded':
                self._chat_line('assistant',turn['response'])
            else:
                self._chat_line('warning',f"Conversation [{turn['state']}]: {turn['detail']}")
        self.chat_history.see('end')  # chronological messages, newest at bottom
    def _refresh_files(self):
        if not self.project:return
        target=self.project
        def worker():
            try:
                if self.disk_gate.gaming():
                    self.events.put(('log','Game active: heavy project file scan deferred.'))
                    return
                paths=self.inspection_exclusions.filter(target,list_project_files(target))
                self.events.put(('files',target,paths))
            except Exception as e:self.events.put(('log','Project scan failed: '+str(e)))
        threading.Thread(target=worker,daemon=True).start()
    def _project_file_context_menu(self, event):
        """Right-click inspection list. Never mutate a project/game file."""
        row=self.files.identify_row(event.y)
        if row:
            self.files.selection_set(row)
            self.files.focus(row)
        menu=tk.Menu(self,tearoff=False)
        if row and self.project:
            relative=self.files.item(row,'text')
            menu.add_command(label='Exclude from inspection (keep file on disk)',
                             command=lambda r=relative:self._exclude_project_file(r))
        menu.add_command(label='Restore excluded project files…',command=self._restore_project_files)
        menu.add_separator()
        menu.add_command(label='Refresh project file list',command=self._refresh_files)
        try:menu.tk_popup(event.x_root,event.y_root)
        finally:menu.grab_release()

    def _exclude_project_file(self, relative):
        if not self.project:return
        try:
            self.inspection_exclusions.exclude(self.project,relative)
            self.capabilities.exclude_project_paths(self.project,[relative])
        except (ValueError,OSError) as exc:
            messagebox.showerror('Inspection exclusion failed',str(exc),parent=self);return
        for row in self.files.get_children():
            if self.files.item(row,'text').casefold()==relative.casefold():
                self.files.delete(row)
        if self.current_file and self.current_file.casefold()==relative.casefold():
            self.current_file=None;self.proposed=None;self.proposal_job=None;self.proposal_step=None
            self.file_title.set('File excluded from inspection (unchanged on disk)')
            self._preview('Removed from the inspection list only. Original file remains in '
                          +str(self.project)+'. Right-click and restore to inspect it again.')
        record(STATE,'desktop','project_file_excluded_from_inspection',
               project_name=self.project.name,excluded_total=len(self.inspection_exclusions.paths(self.project)))
        self._log('Excluded '+relative+' from future project inspection (file remains on disk).')

    def _restore_project_files(self):
        if not self.project:return
        try:excluded=sorted(self.inspection_exclusions.paths(self.project))
        except (OSError,ValueError) as exc:
            messagebox.showerror('Inspection exclusions unavailable',str(exc),parent=self);return
        if not excluded:
            messagebox.showinfo('No excluded files','All project files are visible in inspection.',parent=self)
            return
        dlg=tk.Toplevel(self);dlg.title('Restore excluded project files');dlg.geometry('580x370')
        dlg.transient(self);dlg.configure(bg=BG)
        tk.Label(dlg,text='Select file(s) to inspect again. No project files are modified.',
                 bg=BG,fg=TEXT,wraplength=550).pack(anchor='w',padx=12,pady=8)
        frame=ttk.Frame(dlg);frame.pack(fill='both',expand=True,padx=12,pady=4)
        sc=ttk.Scrollbar(frame,orient='vertical')
        names=tk.Listbox(frame,selectmode='extended',bg=INPUT,fg=TEXT,
                         selectbackground='#31465c',yscrollcommand=sc.set)
        for relative in excluded:names.insert('end',relative)
        names.pack(side='left',fill='both',expand=True);sc.configure(command=names.yview)
        sc.pack(side='right',fill='y')
        bar=ttk.Frame(dlg);bar.pack(fill='x',padx=12,pady=12)
        def restore(selected):
            try:
                for relative in selected:self.inspection_exclusions.restore(self.project,relative)
            except (OSError,ValueError) as exc:
                messagebox.showerror('Restore failed',str(exc),parent=dlg);return
            dlg.destroy();self._refresh_files()
        ttk.Button(bar,text='Restore selected',command=lambda:restore(
            [excluded[i] for i in names.curselection()])).pack(side='left',padx=3)
        ttk.Button(bar,text='Restore all',command=lambda:restore(excluded)).pack(side='left',padx=3)
        ttk.Button(bar,text='Cancel',command=dlg.destroy).pack(side='right')

    def _on_file(self,_event=None):
        chosen=self.files.selection()
        if not chosen or not self.project:return
        name=self.files.item(chosen[0],'text')
        self.current_file=name;self.proposed=None;self.proposal_job=None;self.proposal_step=None
        self.file_title.set('Preview: '+name)
        try:self._preview(read_project_file(self.project,name))
        except Exception as e:self._preview('Cannot preview: '+str(e))
    def _new_file(self):
        if not self.project:
            messagebox.showinfo('Project needed','Select a project folder first.');return
        name=simpledialog.askstring('New file','Relative path in this project:',parent=self)
        if not name:return
        try:safe_target(self.project,name)
        except WorkspaceError as e:messagebox.showerror('Unsafe path',str(e));return
        self.current_file=name.replace('\\','/');self.proposed=None;self.proposal_job=None;self.proposal_step=None
        self.file_title.set('Propose new file: '+self.current_file)
        self._preview('New file, not created. Go to Chats and describe what it should contain.')
        self.tabs.select(0);self.input.focus_set()

    def _fit_chat_to_window(self, event):
        """Shrink only the editor's visible rows if the existing controls would clip.

        Both text widgets remain scrollable; tabs, buttons and control order stay
        unchanged. At the original 860px window height the v10.9 row count (12)
        is preserved. Keep the two action rows accessible on shorter displays.
        """
        if event.widget is not self or not hasattr(self,'input'):
            return
        height=max(0,self.winfo_height())
        if height < 100:
            return
        target=max(3, min(12, 12 - max(0,(860-height+19)//20)))
        if int(self.input.cget('height')) != target:
            self.input.configure(height=target)

    # ----------- truthful, persistent reply-activity notification -----------
    def _set_reply_stage(self, ident, stage):
        """Only the UI thread may update Tk. Ignore late events from old turns."""
        if ident != self.active_conversation:
            return
        self.reply_stage=str(stage)[:180]
        self._render_reply_notice()

    def _render_reply_notice(self):
        if not hasattr(self,'reply_notice'):
            return
        active=self.active_conversation
        if active is not None:
            req=self.conversations.get(active)
            mode='Draft plan' if req and req['mode']=='draft_plan' else 'Reply'
            elapsed=max(0,int(time.monotonic()-self.reply_started)) if self.reply_started else 0
            stage=self.reply_stage or 'Preparing local request'
            health=self.last_server_health if isinstance(self.last_server_health,dict) else {}
            if health.get('inference_busy') and stage.startswith('Waiting for local model'):
                stage='Local ONNX model is generating a response (output is unavailable until completion)'
            current_chat=bool(req and req['chat_id']==self.current_chat)
            prefix='' if current_chat else 'Other chat — '
            # One concise line; the original label must not grow vertically.
            self.reply_notice.set(f'{prefix}{mode} #{active} IN PROGRESS — '
                                  f'{stage[:98]} | {elapsed//60}m {elapsed%60:02d}s')
            return
        try:
            current=self.conversations.thread(self.current_chat,50) if self.current_chat else []
            outstanding=next((r for r in reversed(current) if r['state'] in
                       ('pending','waiting_sources','running')),None)
        except (OSError,ValueError):
            outstanding=None
        if outstanding:
            detail=str(outstanding.get('detail') or '')[:170]
            state=outstanding['state']
            if state=='pending':
                label='WAITING FOR REPLY — queued for local AI'
            elif state=='waiting_sources':
                label='WAITING FOR X4 REFERENCE EXTRACTION/VERIFICATION'
            else:
                label='PROCESSING — restoring active request status'
            self.reply_notice.set(f'{label} (request #{outstanding["id"]}). {detail}')
        elif self.active_job is not None:
            self.reply_notice.set(f'APPROVED PROJECT JOB #{self.active_job} IN PROGRESS. '
                                  'Open Work queue or Processes for actual progress.')
        elif self.reply_outcome is not None and self.reply_outcome['chat_id']==self.current_chat:
            self.reply_notice.set(self.reply_outcome['message'])
        else:
            self.reply_notice.set(getattr(self,'_model_connection_message',
                'AI offline: use Start AI or Self-diagnose to check setup'))

    def _poll_reply_notice(self):
        try:
            self._render_reply_notice()
        finally:
            self.after(1000,self._poll_reply_notice)

    # ----------- conversation and explicit plan approval ------------
    def _migrate_unapproved_requests(self):
        """Move pre-10.4 queued chat/plan/edit records out of the execution queue.

        Existing job IDs remain in the database for audit, marked cancelled only
        after the original content has been durably copied. Restart is idempotent.
        """
        migrated=0
        for row in self.jobs.pending_conversation_jobs():
            mode='draft_plan' if row['mode'] in ('plan','edit') else 'chat'
            self.conversations.submit(row['chat_id'],row['project'],mode,row['prompt'],
                                      attachments=json.loads(row.get('attachments_json') or '[]'),
                                      source_job_id=row['id'])
            if self.jobs.change(row['id'],'cancelled',
                'Migrated to conversation; not an approved execution job',
                allowed=('queued','paused','needs_input','failed')):
                migrated+=1
        if migrated:
            record(STATE,'desktop','legacy_jobs_migrated',count=migrated)

    def _send(self):
        self._queue_input('chat')

    def _show_spec_import_menu(self,event):
        menu=tk.Menu(self,tearoff=False)
        menu.add_command(label='Import large specification (TXT / MD / JSON)…',
                         command=self._import_large_specification)
        if self.imported_spec_source:
            menu.add_command(label='Clear imported specification',
                             command=self._clear_imported_specification)
        menu.tk_popup(event.x_root,event.y_root)
        menu.grab_release()

    def _import_large_specification(self,event=None):
        chosen=filedialog.askopenfilename(parent=self,title='Import full offline project specification',
            filetypes=[('Text specifications','*.txt *.md *.rst *.json *.yaml *.yml'),('All files','*.*')])
        if not chosen:return 'break'
        try:
            source=imported_source(chosen)
        except (OSError,ValueError,UnicodeError) as exc:
            messagebox.showerror('Cannot import specification',str(exc),parent=self)
            return 'break'
        self.imported_spec_source=source
        self.attachment_status.set(
            f'FULL specification selected: {Path(chosen).name} ({source["characters"]:,} characters). '
            'Type extra requirements below or draft the plan. Source remains read-only.')
        self.status.set('Specification selected and hash-checked; no work queued.')
        return 'break'

    def _clear_imported_specification(self):
        self.imported_spec_source=None
        self.attachment_status.set('No imported specification; text, DOCX, PDF and images supported')

    def _queue_input(self,mode):
        """Accept conversation requests, NEVER create executable jobs here."""
        prompt=self.input.get('1.0','end').strip()
        if self.imported_spec_source:
            try:
                prompt=resolve_import(self.imported_spec_source,prompt)
            except (OSError,ValueError,UnicodeError) as exc:
                messagebox.showerror('Specification source changed or is unreadable',str(exc),parent=self)
                return
        if not prompt:return
        if mode=='chat' and self._is_local_diagnostic_request(prompt):
            self.input.delete('1.0','end')
            self._diagnose(prompt=prompt)
            return
        if mode=='edit':
            if not self.project or not self.current_file:
                messagebox.showinfo('Choose a file','Select a project file before drafting an edit plan.');return
            prompt=f'Revise {self.current_file} while preserving unspecified behavior. User requirements: {prompt}'
        if mode in ('plan','build','edit') and not self.project:
            messagebox.showinfo('Choose project','Choose a project folder to draft its implementation plan.');return
        kind='chat' if mode=='chat' else 'draft_plan'
        try:
            attachments=[str(validate_attachment(x)) for x in self.attachments]
            ident=self.conversations.submit(self.current_chat,self._project_key(),kind,prompt,
                                            attachments=attachments)
        except Exception as exc:
            messagebox.showerror('Cannot save conversation',str(exc));return
        self.input.delete('1.0','end')
        self._clear_imported_specification()
        # JANUS's existing Front/Interface can report observed project state
        # without claiming to be a second language model. Explicitly addressed
        # chat requests bypass the occupied ONNX worker and work queue.
        if kind=='chat' and addressed_to_janus(prompt) and not attachments:
            try:
                actions=self.janus.actions(limit=1)
                recommendations=self.janus.recommendations(limit=1)
                answer=janus_state_reply(
                    prompt, status=self.janus.status(), goal=self.janus.goal(),
                    sentinel=self.sentinel.snapshot(),
                    job_counts=self.jobs.count(self._project_key()),
                    model_health=self.last_server_health,
                    active_reply=self.active_conversation is not None,
                    latest_action=actions[0] if actions else None,
                    latest_recommendation=recommendations[0] if recommendations else None)
                if self.conversations.change(ident,'responded',
                        'JANUS Interface supplied observed local state; no model inference',
                        response=answer,allowed=('pending',)):
                    record(STATE,'desktop','janus_interface_reply',request_id=ident,
                           model_called=False,approved_job_queued=False)
                    self._reload_chat()
                    self.reply_outcome={'chat_id':self.current_chat,
                          'message':'JANUS replied from recorded state; Qwen was not used.'}
                    self._render_reply_notice()
                    self.status.set('JANUS Interface responded locally; no work was approved or queued.')
                    return
            except Exception as exc:
                # Never silently fall through to Qwen and block the user. This
                # failed local request stays visible with its original text.
                self.conversations.change(ident,'failed',
                    'JANUS Interface status unavailable: '+str(exc)[:300],allowed=('pending',))
                self._reload_chat()
                self.status.set('JANUS Interface status unavailable; inspect JANUS & Sentinel.')
                return
        self._reload_chat()
        self.reply_outcome=None
        self._render_reply_notice()
        self.status.set(f'{"Draft plan" if kind=="draft_plan" else "Chat"} #{ident} saved. No job was queued.')
        # Software provisioning begins only after approval of a real build job,
        # not when merely asking for a draft plan or revising a prompt.
        # First read-only discovery starts on the user's INITIAL prompt, even if
        # the local ONNX model is still loading. The original request is retained.
        if project_kind(prompt)=='x4' or x4_request_in_context(
                prompt,project_dir=self._project_key(),
                previous_prompts=[r['prompt'] for r in self.conversations.thread(self.current_chat,10)]):
            project=self._project_key(); game=self.x4_game_dir;refs=self.x4_reference_dir;tool=self.x4_catalog_tool
            def scan_initial():
                try:
                    report=automatic_x4_preflight(project_dir=project,app_root=ROOT,game_dir=game,
                                                  reference_dir=refs,catalog_tool=tool)
                    self.events.put(('x4_auto_report',report))
                    record(STATE,'desktop','x4_initial_prompt_inspected',request_id=ident,
                           game_found=bool(report['game_dir']),references_ready=report['ready_for_planning'],
                           project_files=len(report['project_files']))
                except Exception as exc:
                    record(STATE,'desktop','x4_initial_scan_error',request_id=ident,
                           level='ERROR',error=str(exc))
            threading.Thread(target=scan_initial,daemon=True,name='X4InitialPromptScan').start()
        # Large requests are persisted in full. Their section index contains
        # only offsets, SHA-256 hashes and model-authored scoped proposals.
        # It is NOT an inference truncation or an approval shortcut.
        if len(prompt) > MAX_INFERENCE_PROMPT - 1000:
            try:
                progress = self.specifications.index(ident,prompt)
                record(STATE,'desktop','large_specification_indexed',request_id=ident,
                       characters=progress['characters'],sections=progress['sections'])
                if kind == 'chat':
                    message = (f'Your full {progress["characters"]:,}-character specification was saved '
                               f'without truncation and indexed into {progress["sections"]:,} sections. '
                               'No single response can reliably address it all. '
                               'Use Draft project plan to process the sections in resumable batches; '
                               'no plan or execution has been approved.')
                    self.conversations.change(ident,'responded',
                        'Full large specification stored and indexed; no model inference',
                        response=message,allowed=('pending',))
                    self._reload_chat()
                else:
                    self.status.set(f'Large specification indexed: {progress["sections"]:,} exact sections; '
                                    'planning is resumable, no work approved.')
            except Exception as exc:
                self.conversations.change(ident,'failed',
                    'Could not index large specification: '+str(exc)[:400],allowed=('pending',))
                self._reload_chat()
                messagebox.showerror('Specification indexing failed',str(exc))
                return
        if not self.node_ready and not self.node_loading and not self.installing:
            self._auto_start_if_installed()

    def _retry_conversation(self):
        rows=self.conversations.thread(self.current_chat)
        failed=next((r for r in reversed(rows) if r['state']=='failed'),None)
        if not failed:
            messagebox.showinfo('Nothing to retry','There is no failed conversation request in this chat.');return
        if self.conversations.change(failed['id'],'pending','Retry requested by user',allowed=('failed',)):
            self.reply_outcome=None
            self._reload_chat();self._render_reply_notice()

    def _approve_hierarchical_milestone(self, root_request_id):
        """Explicit, per-milestone approval using the original toolbar button."""
        req=self.conversations.get(root_request_id)
        if not req or req['state']!='responded' or req['mode']!='draft_plan':
            messagebox.showwarning('Milestone roadmap unavailable',
                'The source plan is not in a completed, reviewable state.',parent=self)
            return
        try:
            state=self.hierarchies.reconcile_jobs(
                self.specifications,root_request_id,req['prompt'],self.jobs)
            if state['chat_id']!=self.current_chat or state['project']!=str(Path(self._project_key()).resolve()):
                raise PlanError('Milestone roadmap belongs to another chat or project')
            if state['complete']:
                messagebox.showinfo('Milestones completed',
                    f'All {state["milestones_total"]} milestones have approved verification records. '
                    'This does not prove every game requirement is satisfied.',parent=self)
                return
            ordinal=state['next_approvable']
            if ordinal is None:
                messagebox.showinfo('Next milestone is blocked',
                    state['blocked_reason']+'\n\nFinish and verify the previous milestone before proceeding.',parent=self)
                return
            milestone=self.hierarchies.milestone(
                self.specifications,root_request_id,req['prompt'],ordinal)
            display='\n'.join(f"{i}. {step['path']}: {step['description']}"
                               for i,step in enumerate(milestone['steps'],1))
            section_ids=', '.join(str(i) for i in milestone['source_sections'])
            contracts=self.hierarchies.acceptance_contract_report(
                self.specifications,root_request_id,req['prompt'])
            acceptance_summary=(f"Declared source contracts: {contracts['model_declared_contracts']}; "
                f"labelled requirements without test links: "
                f"{len(contracts['unlinked_labelled_requirements'])}; "
                f"current static issues: {len(contracts['issues'])}. "
                'These are planning checks, NOT proof of correct behavior.\n\n')
            if not messagebox.askyesno('Approve this milestone for execution?',
                f"Milestone {ordinal}/{state['milestones_total']}: {milestone['title']}\n"
                f"Master specification SHA-256: {state['specification_sha256'][:24]}…\n"
                f"Exact source sections: {section_ids}\n\n"
                +acceptance_summary+
                f"FILES ({len(milestone['steps'])}):\n{display[:2300]}\n\n"
                'This is an independently scoped milestone. The full original specification '
                'is preserved, but Qwen will only receive the listed exact source sections '
                'while generating these files. Later milestones remain blocked until an '
                'approved verification check succeeds.\n\n'
                'Queue this milestone? With unattended project work enabled, this approval '
                 'authorizes reversible writes for these exact planned files and fixed local '
                 'tests plus up to two bounded ONNX repairs (maximum three tests). '
                'Tests run generated code with your Windows user rights. Switch unattended work OFF in Work queue before approval to keep per-file/test '
                 'confirmations. Tool installs follow a separate policy and normal UAC.',parent=self):
                self._log(f'Milestone {ordinal}: user declined approval; no files changed.')
                return
            jobid=self.jobs.submit_approved_milestone_build(
                milestone['project'],milestone['chat_id'],milestone['scope_prompt'],
                milestone['steps'],milestone['approval_key'],
                master_prompt=req['prompt'], master_steps=milestone['master_steps'])
            self.hierarchies.link_job(
                self.specifications,root_request_id,req['prompt'],ordinal,jobid)
        except Exception as exc:
            record(STATE,'desktop','hierarchical_milestone_approval_error',level='ERROR',
                   request_id=root_request_id,error_type=type(exc).__name__,detail=str(exc)[:450])
            messagebox.showerror('Cannot approve milestone',str(exc),parent=self)
            return
        self._grant_project_job(jobid)
        if self._routine_tools_enabled():
            self._autonomy_queue_request(req['prompt'],state['project'])
        self._log(f'Explicitly approved milestone {ordinal}/{state["milestones_total"]}; '
                  f'queued job #{jobid} ({len(milestone["steps"])} scoped files).')
        self._refresh_jobs();self._reload_chat();self.tabs.select(1)
        self.status.set(f'Milestone {ordinal} queued as job #{jobid}; later milestones require verification.')

    def _approve_conversation_plan(self):
        """The only GUI path that turns a draft or milestone into a build job."""
        draft=self.conversations.latest_draft(self.current_chat,self._project_key())
        root_id=self.hierarchies.latest_for_chat(self.current_chat,self._project_key())
        if root_id and (draft is None or root_id>draft['request_id']):
            # Revoked/failed attempts must not revive a historical roadmap.
            previous=self.conversations.thread(self.current_chat,1000)
            recent=max((r['id'] for r in previous if r['mode']=='draft_plan'
                        and r['project']==self._project_key()),default=None)
            if root_id==recent:
                self._approve_hierarchical_milestone(root_id)
                return
        if not draft:
            messagebox.showinfo('No draft plan',
                'Use Draft project plan first, discuss any uncertainties in Chats, then approve it.');return
        original_turn=self.conversations.get(draft['request_id'])
        if original_turn and 'fallback' in (original_turn.get('detail') or '').lower():
            # v11/v12 could save prewritten, non-model drafts. Retain their chat
            # history but never allow them to be mistaken for model-authored work.
            self.conversations.discard(draft['id'])
            messagebox.showwarning('Old generated template blocked',
                'This earlier plan was substituted by a built-in fallback, not authored '
                'by the local AI. It has been removed from approval. '
                'Please request a new model-generated plan.',parent=self)
            self._reload_chat()
            return
        try:
            if project_kind(draft['original_prompt'])=='x4':
                refs=inspect_x4_sources(project_dir=draft['project'],
                              game_dir=self.x4_game_dir,reference_dir=self.x4_reference_dir)
                if not refs['ready_for_planning']:
                    raise PlanError('Cannot approve an X4 mod without inspected vanilla ship, weapon and turret references. '
                                    +' '.join(refs['blocked_reasons']))
            validate_project_plan(draft['steps'], draft['original_prompt'])
        except PlanError as exc:
            self.conversations.discard(draft['id'])
            record(STATE,'desktop','invalid_draft_blocked',draft_id=draft['id'],detail=str(exc)[:500])
            messagebox.showwarning('Plan rejected by requirements check',str(exc),parent=self)
            self._reload_chat()
            return
        summary='\n'.join(f"{i}. {step['path']}: {step['description']}" for i,step in enumerate(draft['steps'],1))
        if not messagebox.askyesno('Approve this plan for execution?',
            f"Project: {draft['project']}\n\n{summary[:3600]}\n\n"
            'Approve these file-generation stages and place them into the execution queue?\n'
            'With unattended project work enabled, this ONE approval also authorizes exact '
            'planned file writes with backups, fixed local project tests, and up to two repairs after failed tests.\n'
            'These tests can execute generated code with your Windows user rights. Disable '
            'unattended work in Work queue BEFORE approving if you want each file '
            'and test confirmed separately. Software installation has its own '
            'policy; Windows UAC remains active.',parent=self):
            self.conversations.discard(draft['id'])
            self._log(f'User rejected draft #{draft["id"]}; it cannot be queued. No files changed.')
            self._reload_chat()
            return
        try:
            jobid=self.jobs.submit_approved_build(draft['project'],draft['chat_id'],draft['original_prompt'],
                                                  draft['steps'],approval_key=f"draft:{draft['id']}")
            self.conversations.approve(draft['id'],jobid)
        except Exception as exc:
            record(STATE,'desktop','plan_approval_failed',level='ERROR',error=str(exc))
            messagebox.showerror('Cannot queue approved plan',str(exc));return
        self._grant_project_job(jobid)
        if self._routine_tools_enabled():
            self._autonomy_queue_request(draft['original_prompt'],draft['project'])
        self._log(f'User explicitly approved draft #{draft["id"]}. Created job #{jobid} with {len(draft["steps"])} steps.')
        self._reload_chat();self._refresh_jobs();self.tabs.select(1)
        self.status.set(f'Approved plan became job #{jobid}; auto-work authority is listed in Work queue.')

    def _execute_conversation(self,request):
        ident=request['id']
        if not self.conversations.change(ident,'running','Local model processing conversation',allowed=('pending',)):
            return
        self.active_conversation=ident
        self.reply_started=time.monotonic()
        self.reply_stage='Preparing attached files and local context'
        self.reply_outcome=None
        self._render_reply_notice()
        self._log(f'Local conversation #{ident} started ({request["mode"]}); no executable job.')
        def work():
            def cancelled():
                current=self.conversations.get(ident)
                return not current or current['state']!='running'
            try:
                if cancelled():return
                original=request['prompt']
                learning=self.tool_learning.learning_request(ident)
                if learning:
                    self.events.put(('conversation_stage',ident,
                                     'Preparing approved local tool help for model-authored procedure'))
                    source_prompt=self.tool_learning.learning_prompt(ident,self.janus)
                    if cancelled():return
                    self.events.put(('conversation_stage',ident,'Drafting UNVERIFIED tool procedure using local model'))
                    response=self.client.chat(f'tool-learn-{ident}-{request["chat_id"]}',
                                              source_prompt,max_tokens=768,visible_prompt=original)
                    if cancelled():return
                    recipe_id=self.tool_learning.propose_recipe(ident,response)
                    if cancelled():return
                    self.events.put(('conversation_reply',ident,
                         f'LOCAL TOOL PROCEDURE CANDIDATE #{recipe_id} SAVED (NOT RUN).\n'
                         f'Tool: {learning["name"]}\nGoal: {learning["goal"]}\n'
                         'Computer & Tools → Run learned procedure… will first offer a full '
                         'script review if code was proposed, then separately ask to approve '
                         'execution. Procedure is not verified until a '
                         'matching approved execution produces a checked artifact.'))
                    return
                paths=json.loads(request.get('attachments') or '[]')
                # No Tk calls on background threads.
                pictures=[x for x in paths if classify(x)=='image']
                if len(pictures)>1:
                    raise RuntimeError('This local vision setup supports one image per request')
                if pictures:
                    node=shutil.which('node')
                    if not node:raise RuntimeError('Node is needed for the local image reader')
                    output=self._capture_media_process([node,str(ROOT/'vision_caption.mjs'),pictures[0]],'Read chat picture')
                    line=next((x for x in output.splitlines() if x.startswith('IMAGE_CAPTION_JSON: ')),None)
                    if not line:raise RuntimeError('Local vision model did not produce a caption')
                    original+='\n\nAttached image description: '+json.loads(line.split('IMAGE_CAPTION_JSON: ',1)[1])['caption']
                    paths=[x for x in paths if classify(x)!='image']
                if cancelled():return
                self.events.put(('conversation_stage',ident,'Preparing the complete request and attachment context'))
                large_spec = len(original) > MAX_INFERENCE_PROMPT - 1000
                if large_spec and paths:
                    raise ValueError('Large specification indexed, but attached documents need separate scoped extraction; no attachments were silently omitted.')
                prompt=original if large_spec else composed_prompt(original,paths)
                original_evidence=''
                capability_evidence=''
                if request['mode']=='draft_plan':
                    # Read-only, bounded inventory of the SELECTED workspace.
                    # A project document is observed evidence, not an approved skill.
                    # Discovery failures may not block pre-existing planning.
                    try:
                        discovery=self.capabilities.inspect_project(
                            request['project'],exclude_paths=self.inspection_exclusions.paths(request['project']))
                        capability_evidence=self.capabilities.retrieval_context(
                            request['project'],original,max_chars=650)
                        capability_evidence += self.tool_learning.context(
                            request['project'],self.janus,original,max_chars=350)
                        record(STATE,'desktop','capability_discovery_completed',
                               request_id=ident,files_scanned=discovery['files_scanned'],
                               references_indexed=discovery['references_indexed'],
                               local_reference_documents=discovery.get('reference_documents_indexed',0),
                               tools_detected=len(discovery['tools_detected']),
                               evidence_characters=len(capability_evidence))
                    except Exception as discovery_error:
                        record(STATE,'desktop','capability_discovery_unavailable',level='WARNING',
                               request_id=ident,error_type=type(discovery_error).__name__)
                # X4 source inspection is part of the INITIAL request, never a
                # manual task delegated back to the user or an AI hallucination.
                prior=[r['prompt'] for r in self.conversations.thread(request['chat_id'],10)
                       if r['id']!=ident]
                x4_context=x4_request_in_context(original,project_dir=request['project'],
                                                  previous_prompts=prior)
                if x4_context and not (request['mode']=='draft_plan' and project_kind(original)=='android_game'):
                    self.events.put(('conversation_stage',ident,'Inspecting installed X4 files and verified vanilla XML'))
                    record(STATE,'desktop','x4_auto_preflight_started',request_id=ident,mode=request['mode'])
                    report=automatic_x4_preflight(
                        project_dir=request['project'],app_root=ROOT,game_dir=self.x4_game_dir,
                        reference_dir=self.x4_reference_dir,catalog_tool=self.x4_catalog_tool,
                        exclude_project_paths=self.inspection_exclusions.paths(request['project']))
                    if cancelled():return
                    self.events.put(('x4_auto_report', report))
                    record(STATE,'desktop','x4_auto_preflight_complete',request_id=ident,
                           game_found=bool(report['game_dir']),references_ready=report['ready_for_planning'],
                           tool_found=bool(report['catalog_tool']),project_files=len(report['project_files']))
                    if not report['ready_for_planning']:
                        self.events.put(('x4_preflight_needed', ident, report))
                        return
                    if request['mode']=='chat' and is_x4_inspection_request(original,x4_context=x4_context):
                        self.events.put(('x4_inspection_reply',ident,report))
                        return
                    if request['mode']=='draft_plan' and not large_spec:
                        self.events.put(('conversation_stage',ident,'Selecting verified X4 evidence within the model context limit'))
                        original_evidence=x4_evidence_for_prompt(report)
                        prompt=build_budgeted_plan_prompt(
                            prompt,self.inventory,x4_evidence=original_evidence,
                            max_chars=MAX_INFERENCE_PROMPT)
                        record(STATE,'desktop','x4_plan_evidence_budgeted',
                               request_id=ident,model_input_characters=len(prompt),
                               verified_evidence_characters=len(original_evidence),
                               full_specification_preserved=True)
                    else:
                        prompt += ('\n\nLOCAL X4 FILE INSPECTION (verified):\n'
                                   +x4_evidence_for_prompt(report))
                elif request['mode']=='draft_plan' and not large_spec:
                    prompt=build_plan_prompt(prompt,self.inventory)
                if request['mode']=='draft_plan' and not large_spec:
                    prompt=attach_capability_context(prompt,capability_evidence,
                                                     max_chars=MAX_INFERENCE_PROMPT)
                if not large_spec and len(prompt)>MAX_INFERENCE_PROMPT:
                    raise ValueError(f'Model input of {len(prompt):,} characters exceeds {MAX_INFERENCE_PROMPT:,}; original is saved')
                if cancelled():return
                session=request['chat_id'] if request['mode']=='chat' else f'plan-{ident}-{request["chat_id"]}'
                self.events.put(('conversation_stage',ident,'Waiting for local model inference (response not yet returned)'))
                if request['mode']=='chat' and not large_spec:
                    answer=self.client.chat(session,prompt,max_tokens=128,visible_prompt=request['prompt'])
                elif large_spec:
                    answer, _ = generate_indexed_plan(
                        self.client,self.specifications,ident,session,original,
                        request['project'],max_rounds=MAX_PLAN_ATTEMPTS,
                        stage=lambda message: self.events.put(('conversation_stage',ident,message)),
                        cancelled=cancelled, hierarchy=self.hierarchies,
                        chat_id=request['chat_id'])
                else:
                    answer, _ = generate_model_plan(
                        self.client, session, original, request['project'], prompt,
                        x4_evidence=original_evidence, max_chars=MAX_INFERENCE_PROMPT,
                        max_rounds=MAX_PLAN_ATTEMPTS,
                        stage=lambda message: self.events.put(('conversation_stage',ident,message)),
                        cancelled=cancelled,continuation=self.plan_continuations,
                        chat_id=request['chat_id'])
                    record(STATE,'desktop','model_plan_validated',request_id=ident,
                           model_authored=True,files=len(_),prewritten_fallback=False)
                if cancelled():return
                self.events.put(('conversation_stage',ident,'Model finished; verifying reply and project requirements'))
                self.events.put(('conversation_reply',ident,answer))
            except Exception as exc:
                record(STATE,'desktop','conversation_worker_exception',level='ERROR',request_id=ident,
                       error_type=type(exc).__name__,stack=traceback.format_exc()[-12000:])
                if isinstance(exc, (ConnectionResetError, ConnectionAbortedError,
                                    BrokenPipeError, TimeoutError)):
                    self.events.put(('conversation_transport_lost',ident,type(exc).__name__,str(exc)))
                else:
                    self.events.put(('conversation_error',ident,str(exc)))
        threading.Thread(target=work,daemon=True,name=f'Conversation-{ident}').start()

    def _conversation_reply(self,ident,answer):
        req=self.conversations.get(ident)
        if not req or req['state']!='running':return
        self._set_reply_stage(ident,'Checking the response against the original requirements')
        outcome='REPLY RECEIVED — local model finished.'
        if req['mode']=='draft_plan':
            try:
                # Existing model plan parsing accepts one complete JSON object
                # preceded by explanatory prose. Do not regress that behavior.
                try:
                    structured=json.loads(answer)
                except (ValueError,TypeError):
                    structured={}
                is_hierarchy=(isinstance(structured,dict) and 'hierarchy_ready' in structured)
                if is_hierarchy:
                    if len(req['prompt'])<=MAX_INFERENCE_PROMPT-1000:
                        raise PlanError('Model returned an untrusted roadmap marker; no indexed plan exists')
                    verified=self.hierarchies.status(self.specifications,ident,req['prompt'])
                    if structured['hierarchy_ready']!=verified:
                        raise PlanError('Roadmap marker does not match the saved, fully indexed requirements')
                    self.conversations.change(ident,'responded',
                        f'Hierarchical roadmap ready: {verified["milestones_total"]} sequential, '
                        'individually approvable milestones; no jobs queued',
                        response=answer,allowed=('running',))
                    outcome=(f'ROADMAP READY — {verified["milestones_total"]} milestones, '
                             f'{verified["sections_reviewed"]} exact sections traced. '
                             'Review and approve the FIRST milestone individually. No job was queued.')
                    self._log(f'Hierarchical roadmap request #{ident} prepared; no jobs queued.')
                else:
                    validated=parse_build_plan(answer,Path(req['project']),request=req['prompt'])
                    draft_id=self.conversations.save_draft(ident,validated)
                    self.conversations.change(ident,'responded',
                        f'Draft #{draft_id} ready; discuss, revise or explicitly approve it',
                        response=answer,allowed=('running',))
                    outcome=f'DRAFT PLAN #{draft_id} READY — review and explicitly approve before any job runs.'
                    self._log(f'Draft #{draft_id} generated in Chats; NO job queued.')
            except Exception as exc:
                # Never replace a rejected model plan with a hardcoded plan.
                # The user's plan approval must assess the model's own result.
                self.conversations.change(ident,'failed','Invalid proposal: '+str(exc),
                    response=answer,allowed=('running',))
                self._log(f'Planning requires revision: {exc}. No substitute draft was created.')
                outcome='DRAFT FAILED — model proposal did not pass validation. No job was queued.'
        else:
            self.conversations.change(ident,'responded','Local conversation replied',
                                      response=answer,allowed=('running',))
        self.active_conversation=None
        self.reply_stage=''
        self.reply_outcome={'chat_id':req['chat_id'],'message':outcome}
        if req['chat_id']==self.current_chat and req['project']==self._project_key():
            self._reload_chat()
        self._render_reply_notice()
        self.status.set('Conversation updated. Project work requires explicit plan approval.')

    def _conversation_transport_lost(self, ident, error_type, error):
        """Pause failed localhost inference; never replay while worker is busy.

        No completed answer is assumed. Exact saved per-pass exchanges will be
        restored by the planner if inference later restarts successfully.
        """
        req = self.conversations.get(ident)
        if not req or req['state'] != 'running':
            return
        count = self._model_transport_retries.get(ident, 0) + 1
        self._model_transport_retries[ident] = count
        record(STATE, 'desktop', 'onnx_transport_interrupted', level='WARNING',
               request_id=ident, error_type=error_type, retry_count=count,
               server_exit_code=(self.node.poll() if self.node else None),
               note='Model exit cause is not established by an HTTP reset')
        if count > 2:
            self._conversation_error(ident,
                'ONNX connection failed repeatedly; stopped after two supervised recovery attempts. '
                'Inspect Processes and export diagnostics. Last transport error: '+str(error)[:180])
            return
        self.conversations.change(ident, 'pending',
            f'ONNX connection interrupted ({error_type}); saved exchanges will resume when '
            'the local model is ready. No new build authorization.', allowed=('running',))
        if self.active_conversation == ident:
            self.active_conversation = None
            self.reply_stage = ''
        self.node_ready = False
        self._model_transport_waiting = True
        self._log(f'Conversation #{ident}: local ONNX transport reset, recovery {count}/2. '
                  'Request retained; waiting for a healthy, idle supervised worker.')
        self._reload_chat(); self._render_reply_notice()
        # A still-live worker may be finishing the old request; only the health
        # poll can declare it idle. A dead worker is handled by node_end.
        if self.node and self.node.poll() is None:
            self.after(3000, self._resume_transport_if_idle)

    def _resume_transport_if_idle(self):
        if self._explicit_model_stop or self._quitting or not self.node or self.node.poll() is not None:
            return
        health = local_server_status()
        if isinstance(health, dict) and health.get('ready') and not health.get('inference_busy'):
            self._model_transport_waiting = False
            self.node_ready = True
            self._log('ONNX worker verified healthy and idle after transport interruption; '
                      'resuming saved planning requests.')
        elif isinstance(health, dict) and health.get('inference_busy'):
            self.after(5000, self._resume_transport_if_idle)
        # A missing/unhealthy server needs node_end/restart diagnosis.

    def _conversation_error(self,ident,error):
        req=self.conversations.get(ident)
        # A terminated old HTTP call may report an error *after* cancellation
        # and after another chat has become active. It must not clear that chat.
        if not req or req['state']!='running':
            return
        self.conversations.change(ident,'failed','Local model request failed: '+error[:500],
                                  allowed=('running',))
        if self.active_conversation is not None and self.active_conversation!=ident:
            # A different conversation owns the model now. Keep its status.
            self._log(f'Late error recorded for conversation #{ident}; current reply was not disturbed.')
            return
        self.active_conversation=None
        self.reply_stage=''
        planning_incomplete = str(error).startswith('Indexed X4 roadmap remains incomplete')
        notice = ('PLAN STILL INCOMPLETE — reviewed sections and valid corrections saved; '
                  'retry continues missing X4 files.' if planning_incomplete else
                  f'REPLY FAILED — {str(error)[:180]}. Request preserved for retry.')
        self.reply_outcome={'chat_id':req['chat_id'] if req else self.current_chat,
             'message':notice}
        self._render_reply_notice()
        self._log(f'Conversation #{ident} failed: {error[:300]}')
        if req and req['chat_id']==self.current_chat:self._reload_chat()

    def _refresh_jobs(self):
        if not hasattr(self,'job_tree'):return
        for item in self.job_tree.get_children():self.job_tree.delete(item)
        project=self._project_key()
        rows=[j for j in self.jobs.items(project) if j['mode'] not in ('chat','plan','edit')]
        for j in rows:
            graph=self.graphs.status(j['id'])
            if graph:
                ready=sum(node['state'] in ('approved','available','saved','passed','recorded')
                          for node in graph['nodes'])
                j['detail']+=f' [Graph: {ready}/{len(graph["nodes"])} observed]'
            cycle=self.cycles.get(j['id'])
            if cycle:
                j['detail'] += (f" [Cycle: {cycle['phase']}; "
                                f"tests {cycle['tests']}/{MAX_TEST_ATTEMPTS}; "
                                f"repairs {cycle['repairs']}/{MAX_REPAIR_ATTEMPTS}]")
            if j['id']==self.active_job:
                detail=f"{j['detail']} — {int(time.monotonic()-self.active_started)}s elapsed"
            else:detail=j['detail']
            self.job_tree.insert('','end',iid=str(j['id']),values=(j['state'],j['mode'],j['chat_id'][-7:],detail))
        count={}
        for j in rows:count[j['state']]=count.get(j['state'],0)+1
        summary='   '.join(f'{k}: {v}' for k,v in sorted(count.items())) or 'No approved jobs'
        self.queue_summary.set(('PAUSED  |  ' if self.queue_paused else 'ACTIVE  |  ')+summary)
    def _selected_job(self):
        x=self.job_tree.selection()
        return self.jobs.get(int(x[0])) if x else None
    def _job_selected(self,_event=None):
        job=self._selected_job()
        if not job:return
        if job['state']=='waiting_approval' and job['mode'] in ('build','edit') and job['result']:
            steps=self.jobs.steps(job['id'])
            chosen=next((x for x in steps if x['state']=='proposed'),None)
            target=chosen['path'] if chosen else job['target']
            if target and job['project']==self._project_key():
                self.proposed=(target,strip_single_code_fence(job['result']))
                self.proposal_job=job['id']
                self.proposal_step=chosen['id'] if chosen else None
                self.file_title.set('Review pending job: '+str(target))
                self._preview('PROPOSED CODE — edit below before approving\n\n'+self.proposed[1])
        events='\n'.join(f'[{stamp}] {note}' for stamp,note in self.jobs.events(job['id']))
        cycle=self.cycles.get(job['id'])
        if cycle:
            cycle_log='\n'.join(f"[{e['stamp']}] {e['phase']}: {e['message']}"
                                for e in reversed(self.cycles.events(job['id'])))
            events += (f"\n\nDEVELOPMENT CYCLE: {cycle['phase']} | "
                f"tests {cycle['tests']}/{MAX_TEST_ATTEMPTS} | "
                f"repairs {cycle['repairs']}/{MAX_REPAIR_ATTEMPTS}"
                f"\nLAST DIAGNOSTIC (local evidence):\n{cycle['diagnostic'][-1600:]}"
                f"\nCYCLE EVENTS:\n{cycle_log}")
        graph=self.graphs.status(job['id'])
        if graph:
            graph_lines='\n'.join('  '+node['node']+' ['+node['state']+'] '+node['title']+
                (' — '+node['note'] if node['note'] else '') for node in graph['nodes'])
            deps='\n'.join('  '+edge['node']+' <- '+edge['depends_on'] for edge in graph['edges'])
            events+='\n\nTASK GRAPH ('+graph['state']+'):\n'+graph_lines+'\nDEPENDENCIES:\n'+deps
        try:
            revisions=self.checkpoints.list(job['id'])
            if revisions:
                last=revisions[-1]
                events+=(f'\n\nSOURCE CHECKPOINTS: {len(revisions)} immutable revisions; '
                         f'latest {last["id"]} ({last["reason"]}). '
                         'Use Restore source checkpoint… to select an earlier source state.')
        except CheckpointError as exc:
            events+='\n\nCHECKPOINT INTEGRITY ERROR: '+str(exc)
        steps=self.jobs.steps(job['id'])
        step_text='\n'.join(f"{i+1}. [{x['state']}] {x['path']}: {x['description']}" for i,x in enumerate(steps)) or '(No plan yet)'
        detail=(f"Job #{job['id']} | {job['state']} | {job['mode']}\n"
                f"Created: {job['created_at']}\nProject: {job['project']}\nTarget: {job['target'] or '-'}\n"
                f"Message: {job['detail']}\n\nPLAN STEPS:\n{step_text}\n\nREQUEST:\n{job['prompt'][:8000] + (' [DISPLAY PREVIEW ONLY; full request is stored in SQLite]' if len(job['prompt'])>8000 else '')}\n\nRESULT:\n{job['result']}\n\nEVENTS:\n{events}")
        self._show(self.job_details,detail)
    def _cancel_active(self):
        if self.active_job is None:return
        self._cancel_id(self.active_job)
    def _cancel_job(self):
        j=self._selected_job()
        if not j:return
        self._cancel_id(j['id'])
    def _cancel_id(self,ident):
        job=self.jobs.get(ident)
        if not job or job['state'] not in (
                'queued','running','paused','needs_input','waiting_approval',
                'waiting_verification','waiting_repair'):
            return
        if job['state']=='running' and self._auto_verification_in_flight==ident:
            if not messagebox.askyesno('Stop approved project test',
                    'Cancel this running local project verification?\n\n'
                    'Generated files and backups remain. The incomplete test will NOT '
                    'start a repair automatically.',parent=self):
                return
            self._stopped_auto_tests.add(ident)
            self.jobs.cancel(ident)
            if self.tool_process and self.tool_process.poll() is None:
                self.tool_process.terminate()
            self._log(f'Job #{ident}: cancelled local test; local Qwen stays running.')
        elif job['state']=='running' and self.active_job==ident:
            if not messagebox.askyesno('Cancel local inference',
                    'Cancel this active job? The ONNX worker will stop, but previous '
                    'approved files and backups remain.',parent=self):
                return
            cycle=self.cycles.get(ident)
            if cycle and cycle['phase']=='repairing':
                try:self.cycles.block(ident,'User cancelled local repair before acceptance')
                except CycleError:pass
            lease=self._graph_repair_leases.pop(ident,None)
            if lease:
                try:self.graphs.finish_action(lease,ident,'interrupted')
                except GraphError:pass
            self.jobs.cancel(ident)
            if self.media_process and self.media_process.poll() is None:
                self.media_process.terminate()
            elif self.node and self.node.poll() is None:
                self.node.terminate()
                self.node_ready=False;self.node_loading=False
                self.model_status.set('AI: stopped after cancellation')
            self.active_job=None
            self._log(f'Job #{ident}: stopped active local inference.')
        else:
            if job['state']=='running':
                messagebox.showinfo('Process still running',
                    'Use Processes > Stop tool / install process for this running task.',parent=self)
                return
            cycle=self.cycles.get(ident)
            if cycle and cycle['phase'] in ('repair_ready','repairing','testing','repair_saved'):
                try:self.cycles.block(ident,'User cancelled approved job')
                except CycleError:pass
            self.jobs.cancel(ident)
            self._log(f'Job #{ident} cancelled; approved files and backups kept.')
        self._refresh_jobs();self._job_selected()
    def _resume_job(self):
        j=self._selected_job()
        if j and (graph:=self.graphs.status(j['id'])) and graph['state']=='invalidated':
            messagebox.showwarning('Previous plan was invalidated',
                'This source was restored or this approval was invalidated. '
                'Create and explicitly approve a new plan before running more work.',parent=self)
            return
        if j and self.jobs.resume(j['id']):
            self._log(f"Job #{j['id']} resumed by user.");self._refresh_jobs()
    def _load_job_prompt(self):
        j=self._selected_job()
        if j:
            self.input.delete('1.0','end');self.input.insert('1.0',j['prompt'])
            if j['chat_id'] in self.chat_ids:self.chat_tabs.select(self.chat_ids.index(j['chat_id']))
            self.tabs.select(0);self.input.focus_set()
    def _approve_build_plan(self):
        j=self._selected_job()
        if not j or j['mode']!='build' or j['state']!='needs_input' or not self.jobs.steps(j['id']):
            messagebox.showinfo('Select a build plan','Choose a staged build with a generated plan that needs approval.');return
        plan=self.jobs.steps(j['id'])
        summary='\n'.join(f"{n+1}. {x['path']}: {x['description'][:100]}" for n,x in enumerate(plan))
        if not messagebox.askyesno('Approve project plan',
                f'Approve these {len(plan)} bounded file steps?\n\n{summary[:2000]}\n\n'
                'With unattended project work enabled, this single approval also authorizes '
                'exact file writes with backups, fixed local project tests and up to two same-file repairs. Tests '
                'may execute generated code with your Windows user rights. Software '
                'installation still has a separate policy and normal UAC.',parent=self):return
        self.jobs.resume(j['id'])
        self._grant_project_job(j['id'])
        if self._routine_tools_enabled():
            self._autonomy_queue_request(j['prompt'],str(self.project))
        self._log(f"Build plan #{j['id']} approved. The queue will work on its first file.")
        self._refresh_jobs()

    def _run_quiet_scene(self):
        """User-initiated fixed CLI headless scene check; no GUI/game focus changes."""
        if self._quitting or self.queue_paused:
            self._log('Quiet scene test deferred: the work queue is paused.')
            return
        if self._gui_test_active or self._quiet_test_active or any(p and p.poll() is None for p in
            (self.tool_process,self.install_process,self.media_process)):
            self._log('Quiet scene test deferred: another tool/process is active.')
            return
        if self.active_job is not None or self._auto_verification_in_flight is not None:
            self._log('Quiet scene test deferred: an approved job/test is active.')
            return
        try:
            if not is_capped_windows_process():
                raise QuietPlaytestError('Only available under the capped Windows DeepThorT.exe launcher. '
                    'A Python development launch cannot guarantee the shared 20% CPU/memory limit.')
            project=Path(self.project or '')
            exe=godot_executable(tools=getattr(self,'inventory',None))
            if not exe:
                raise QuietPlaytestError('Godot executable not found; run the v43 tool check first.')
            plan=plan_godot_scene(project,exe)
            # A scene executes user/project code with normal user privileges.
            # The click is the explicit choice; there is no model-selected command.
            self.quiet_tests.begin(plan)
            self._quiet_test_active=plan
            self._quiet_test_stopped=False
            self._quiet_test_stop_reason=''
            if not self._start_command(list(plan.argv),cwd=plan.project,
                    label='Quiet Godot scene simulation',kind='quiet_playtest'):
                self.quiet_tests.finish(None,error='The process was not launched')
                self._quiet_test_active=None
                return
            self._log(f'{plan.display()}. No visual assertions; game window and audio are disabled. '
                      'Input focus will remain with the foreground application.')
        except (QuietPlaytestError,OSError,ValueError) as exc:
            self._log('Quiet scene test unavailable: '+str(exc))
            self.status.set('Quiet scene test blocked: '+str(exc)[:150])

    def _stop_quiet_scene(self):
        if self._quiet_test_active is None:
            return
        self._quiet_test_stopped=True
        self._quiet_test_stop_reason='User stopped quiet test'
        p=self.tool_process
        if p and p.poll() is None:
            p.terminate()
        else:
            # Launch may still be in flight. Worker will see stop flag before Popen.
            self._log('Quiet test cancellation requested; launch not yet confirmed.')
        self._log('Quiet scene test stopping; no automatic replay.')

    def _run_isolated_gui(self):
        """User-approved program on a separate Windows desktop, no input injection."""
        if self._quitting or self.queue_paused:
            self._log('Isolated GUI test deferred: work queue paused or desktop closing.')
            return
        if self._gui_test_active or self._quiet_test_active or self.active_job is not None or \
                self._auto_verification_in_flight is not None or self._auto_tool_active or self._tool_probe_active or \
                any(p and p.poll() is None for p in
                    (self.tool_process, self.install_process, self.media_process)):
            self._log('Isolated GUI test deferred: another supervised action is running.')
            return
        try:
            if not is_capped_windows_process():
                raise IsolatedGuiError('Requires Windows and the capped DeepThorT.exe launcher.')
            if not self.project or not Path(self.project).is_dir():
                raise IsolatedGuiError('Select a project directory first.')
            chosen=filedialog.askopenfilename(parent=self,title='Select project-local Windows .exe to observe',
                initialdir=str(self.project),filetypes=[('Windows programs','*.exe')])
            if not chosen:return
            plan=plan_isolated_gui(self.project,chosen)
            if not messagebox.askyesno('Approve background Windows program smoke test',
                'Launch this project executable on a separate Windows desktop for up to 25 seconds?\n\n'
                +plan.executable+'\n\n'
                'It will run with your current Windows account permissions. This is NOT a security sandbox. '
                'It may access project files, use GPU and fail if the app needs the input desktop. '
                'No keyboard, mouse or foreground window will be manipulated by DeepThorT. '
                'A nested job terminates the child process tree at the end.\n\n'
                'Only run an executable you trust.',parent=self):
                return
            assert_plan_unchanged(plan)
            self.gui_tests.begin(plan)
            self._gui_test_stop=threading.Event()
            self._gui_test_active=plan
            def runner():
                try:
                    result=run_isolated_gui(plan,self._gui_test_stop,
                                             foreground_game=self.disk_gate.gaming)
                except (OSError,ValueError,RuntimeError) as exc:
                    result={'status':'launch_failed','detail':str(exc)[:250],'windows':[]}
                except BaseException as exc:
                    result={'status':'launch_failed','detail':'Native GUI supervision error: '+str(exc)[:200],
                            'windows':[]}
                self.events.put(('isolated_gui_done',result))
            threading.Thread(target=runner,daemon=True,name='isolated-gui-v45').start()
            self._log('Isolated GUI smoke test started: '+Path(plan.executable).name+
                      '; no desktop switching/input; no visual/gameplay acceptance implied.')
        except (IsolatedGuiError,OSError,ValueError) as exc:
            self._log('Isolated GUI test blocked: '+str(exc))
            self.status.set('Isolated GUI test blocked: '+str(exc)[:150])

    def _stop_isolated_gui(self):
        if self._gui_test_active:
            self._gui_test_stop.set()
            self._log('Isolated GUI test cancellation requested; nested process job will close.')

    def _verification_command(self,project):
        # Only deterministic local test entry points. No model-created shell commands.
        if (project/'project.godot').exists():
            # Real file discovery: a registry install hint is not executable.
            # This also supports a manually configured GODOT_EXECUTABLE path.
            godot=godot_executable(tools=getattr(self,'inventory',None))
            if not godot:return None
            # Only use a test framework confirmed to exist in the project.
            # Otherwise report only editor load, not passing gameplay tests.
            gut=project/'addons/gut/gut_cmdln.gd'
            dirs=[]
            if gut.is_file():
                for name in ('test','tests'):
                    base=project/name
                    if base.is_dir() and any(p.is_file() and p.stat().st_size<=220_000 and
                           re.search(r'(?m)^\s*func\s+test_\w+\s*\(',p.read_text(encoding='utf-8',errors='replace'))
                           for p in list(base.rglob('test_*.gd'))[:100]):
                        dirs.append('res://'+name)
            if dirs:
                return [godot,'--headless','--path',str(project),'-s',
                        'addons/gut/gut_cmdln.gd','-gdir='+','.join(dirs),
                        '-ginclude_subdirs','-gexit']
            return [godot,'--headless','--path',str(project),'--editor','--quit']
        if (project/'content.xml').is_file():
            # Prefer actual approved tests when present; the independent X4
            # artifact audit is also required before marking the job complete.
            if (project/'tests').is_dir() or list(project.glob('test_*.py')):
                return [sys.executable,'-m','unittest','discover']
            return [sys.executable,str(ROOT/'engine_acceptance_cli.py'),str(project),'--summary']
        if (project/'package.json').exists(): return ['npm.cmd' if os.name=='nt' else 'npm','test']
        if (project/'pyproject.toml').exists() or (project/'tests').is_dir() or list(project.glob('test_*.py')):
            return [sys.executable,'-m','unittest','discover']
        if list(project.glob('*.sln')): return ['dotnet','test','--no-restore']
        return None

    def _project_work_is_enabled(self):
        return bool(getattr(self, '_project_policy', {}).get('enabled') is True)

    def _set_project_work_policy(self):
        try:
            self._project_policy = set_project_policy(
                STATE/'project-work-policy.json', bool(self.project_work_enabled.get()))
        except (OSError, ValueError) as exc:
            self.project_work_enabled.set(self._project_work_is_enabled())
            messagebox.showerror('Could not save project work setting', str(exc), parent=self)
            return
        self._log('Unattended approved project steps ' + (
            'ENABLED for job-bound grants' if self._project_work_is_enabled()
            else 'DISABLED; manual file/test review remains available'))
        self._refresh_jobs()

    def _grant_project_job(self, jobid):
        if not self._project_work_is_enabled():
            return
        job = self.jobs.get(jobid)
        try:
            steps=self.jobs.steps(jobid)
            grant = issue_grant(STATE/'project-grants', job, steps)
            try:
                self.checkpoints.capture(job,steps,'approval_baseline',baseline=True)
                self.graphs.create(job,steps)
                key=str(job.get('approval_key') or '')
                if key.startswith('milestone:'):
                    rootid=int(key.split(':')[1])
                    rootreq=self.conversations.get(rootid)
                    # The master request is already validated before milestone approval.
                    # Do not force a million-character rehash through the small gaming
                    # budget on every milestone; the durable indexed source remains
                    # available for full review and linking in a future pass.
                    if rootreq and len(rootreq.get('prompt') or '')<=2_000_000:
                        provenance=self.hierarchies.graph_provenance(
                            rootid,[st['path'] for st in steps])
                        actual_hash=hashlib.sha256(rootreq['prompt'].encode('utf-8')).hexdigest()
                        if (provenance['root_source_sha256']!=actual_hash or
                            provenance['root_project']!=str(Path(job['project']).resolve())):
                            raise GraphError('Milestone requirement root hash or project changed')
                        self.graphs.attach_hierarchy(job,steps,provenance)
                        if provenance['truncated']:
                            self._log(f'Job #{jobid}: requirement graph shows only the first '
                                      f'{len(provenance["requirements"])} of '
                                      f'{provenance["total_linked_requirements"]} exact source traces; '
                                      'the complete indexed hierarchy is preserved elsewhere.')
            except (CheckpointError,GraphError,WorkspaceError,OSError,ValueError):
                revoke_grant(STATE/'project-grants',jobid)
                if self.graphs.exists(jobid):
                    self.graphs.invalidate(jobid,'Initial graph/checkpoint approval evidence incomplete')
                raise
            self._log(f"Job #{jobid}: unattended authority granted for "
                      f"{len(grant['files'])} exact files and fixed local project tests. "
                      "Existing files fingerprinted; source backups retained.")
            record(STATE, 'desktop', 'project_authority_issued', job_id=jobid,
                   paths=len(grant['files']), plan_sha256=grant['plan_sha256'])
        except (GrantError, GraphError, CheckpointError, ValueError, OSError) as exc:
            # Never fabricate a grant when project scope/plan is incompatible.
            self._log(f'Job #{jobid}: no unattended grant: {exc}. '
                      'Individual file/test review remains required.')
            record(STATE, 'desktop', 'project_authority_declined', job_id=jobid,
                   reason=str(exc)[:400])

    def _revoke_selected_project_work(self):
        job = self._selected_job()
        if not job:
            messagebox.showinfo('Select approved job',
                'Select an approved build in Work queue first.', parent=self)
            return
        try:
            result = revoke_grant(STATE/'project-grants', job['id'])
        except OSError as exc:
            messagebox.showerror('Cannot revoke grant', str(exc), parent=self)
            return
        self._log(f'Job #{job["id"]}: ' + (
            'unattended authority REVOKED; subsequent file/test actions need review.'
            if result else 'no active unattended authority found.'))
        if self._auto_verification_in_flight == job['id']:
            self._log('Already running test may continue. Stop tool / install process to interrupt it.')
        self._refresh_jobs()

    def _restore_source_checkpoint(self):
        job=self._selected_job()
        if not job or job['mode']!='build':
            messagebox.showinfo('Select an approved build','Choose a build in Work queue.',parent=self)
            return
        if (self.active_job is not None or self._auto_verification_in_flight is not None
            or self.active_conversation is not None or self.disk_gate.gaming()
            or any(p and p.poll() is None for p in
                   (self.tool_process,self.media_process,self.install_process))):
            messagebox.showwarning('Work is active',
                'Stop active work and finish gaming before restoring source files.',parent=self)
            return
        try:
            revisions=self.checkpoints.list(job['id'])
            if len(revisions)<2:
                raise CheckpointError('No prior revision to restore; approved baseline is the only snapshot')
            labels='\n'.join(f'{i+1}. {r["reason"]} — {r["id"]}'
                             for i,r in enumerate(revisions))
            index=simpledialog.askinteger('Restore source checkpoint',
                f'Choose a revision number from this exact approved job:\n\n{labels[-2800:]}\n\n'
                '1 is the original approval baseline.',parent=self,
                minvalue=1,maxvalue=len(revisions))
            if index is None:return
            selected=revisions[index-1]['id']
            steps=self.jobs.steps(job['id'])
            review=self.checkpoints.restore_preview(job,steps,selected)
            detail='\n'.join(review['changed'][:24])
            if not messagebox.askyesno('Confirm irreversible authorization invalidation',
                f'Roll back {len(review["changed"])} exact project source files?\n\n{detail}\n\n'
                'Files created since the selected revision will be QUARANTINED, not deleted. '
                'A separate recovery snapshot will be kept. This revokes unattended permissions '
                'and invalidates prior test/verification results; a new plan approval is required. '
                'Do not continue until the restored program has been retested.',parent=self):
                return
            # Revoke authority BEFORE changing any project file.
            revoke_grant(STATE/'project-grants',job['id'])
            self.graphs.invalidate(job['id'],'User explicitly restored an older source revision')
            try:self.cycles.invalidate(job['id'],'Source checkpoint restored; old tests no longer valid')
            except (CycleError,OSError):pass
            self.jobs.change(job['id'],'needs_input',
                'Source rollback requested; old build verification invalid. New plan approval required',
                allowed=('queued','paused','waiting_verification','waiting_repair',
                         'needs_input','complete','failed','cancelled'))
            receipt=self.checkpoints.rollback(job,steps,selected,explicit_approval=True)
            self._log(f'Job #{job["id"]}: restored source checkpoint {selected}; '
                      f'{len(receipt["actions"])} changes; emergency {receipt["emergency"]}. '
                      'Permission and previous verification invalidated.')
            self.status.set('Source checkpoint restored. Prior verification is invalid; approve a new plan.')
            self._refresh_files();self._refresh_jobs();self._job_selected()
        except (CheckpointError,GraphError,GrantError,WorkspaceError,OSError,ValueError) as exc:
            self._log('Source checkpoint restoration refused or incomplete: '+str(exc))
            messagebox.showerror('Source restore needs inspection',
                str(exc)+'\n\nIf rollback began, inspect its emergency checkpoint under state/source-checkpoints.',
                parent=self)

    def _project_work_tick(self):
        try:
            self._project_work_once()
        except Exception as exc:
            record(STATE, 'desktop', 'project_work_scheduler_error', level='ERROR',
                   error_type=type(exc).__name__, detail=str(exc)[:500])
            self._log('Unattended project scheduler problem: ' + str(exc)[:200])
        finally:
            if not self._quitting:
                self.after(1800, self._project_work_tick)

    def _claim_autonomous_repair(self, job):
        """Launch one local Qwen proposal; this does not write project files."""
        jobid=job['id']
        steps=self.jobs.steps(jobid)
        authorize_repair_context(STATE/'project-grants',job,steps,enabled=True)
        cycle=self.cycles.get(jobid)
        if not cycle or cycle['phase']!='repair_ready':
            raise CycleError('No authorized bounded repair is pending')
        prompt,candidates=build_repair_prompt(job,steps,cycle['diagnostic'])
        lease=None
        if self.graphs.exists(jobid):
            lease=self.graphs.begin_action(job,steps,'repair','verify')
        try:self.cycles.claim_repair(jobid)
        except BaseException:
            if lease:
                try:self.graphs.finish_action(lease,jobid,'blocked')
                except GraphError:pass
            raise
        if lease:self._graph_repair_leases[jobid]=lease
        if not self.jobs.change(jobid,'running',
                'Diagnosing test failure with local ONNX (bounded repair)',
                allowed=('waiting_repair',)):
            self.cycles.block(jobid,'Repair was not claimed by the expected job state')
            raise CycleError('Repair job state changed before generation')
        self.active_job=jobid
        self.active_started=time.monotonic()
        self._log(f"Job #{jobid}: local ONNX repair {cycle['repairs']+1}/{MAX_REPAIR_ATTEMPTS} "
                  f"after test {cycle['tests']}/{MAX_TEST_ATTEMPTS}. "
                  'Only exact approved file replacements can be saved.')
        self._refresh_jobs()
        def worker():
            try:
                result=self.client.chat(job['chat_id'],prompt,max_tokens=768)
                self.events.put(('repair_answer',jobid,result,candidates))
            except Exception as exc:
                record(STATE,'desktop','repair_model_error',level='ERROR',job_id=jobid,
                       error_type=type(exc).__name__,detail=str(exc)[:400])
                self.events.put(('repair_error',jobid,str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def _repair_answer(self,jobid,answer,candidates):
        job=self.jobs.get(jobid)
        if not job or job['state']!='running' or self.active_job!=jobid:
            self._log(f'Ignored stale or cancelled repair response for job #{jobid}.')
            return
        self.active_job=None
        try:
            target,code=parse_repair_response(answer,candidates)
            steps=self.jobs.steps(jobid)
            matching=[x for x in steps if x['path']==target and x['state']=='saved']
            if len(matching)!=1:
                raise CycleError('Local model selected an unavailable approved file')
            stage=matching[0]
            authority=authorize_repair(STATE/'project-grants',job,steps,stage,enabled=True)
            if self.graphs.exists(jobid):
                if not self.checkpoints.list(jobid):
                    raise CheckpointError('Repair requires an intact v42 source baseline')
            dest=apply_approved_file(Path(job['project']),target,code,
                STATE/'backups',expected_existing_sha=authority['before_sha256'])
            receipt=record_repair(STATE/'project-grants',job,steps,stage,enabled=True)
            if self.graphs.exists(jobid):
                self.graphs.record_repaired_artifact(job,steps,stage,receipt['sha256'])
                check=self.checkpoints.capture(job,steps,'repair_saved')
                if check['files'].get(receipt['path'])!=receipt['sha256']:
                    raise CheckpointError('Repaired source changed before the checkpoint was recorded')
            self.cycles.finish_repair(jobid,target,receipt['sha256'])
            lease=self._graph_repair_leases.pop(jobid,None)
            if lease:self.graphs.finish_action(lease,jobid,'saved')
            self.jobs.change(jobid,'waiting_verification',
                f'Repair saved with backup: {target}; retest not yet run',allowed=('running',))
            self._log(f'Job #{jobid}: one authorized repair saved to {dest}; '
                      f'SHA256 {receipt["sha256"][:16]}…; retest will be scheduled when idle.')
            self._refresh_files()
        except (CycleError,GraphError,CheckpointError,GrantError,WorkspaceError,OSError,ValueError) as exc:
            lease=self._graph_repair_leases.pop(jobid,None)
            if lease:
                try:self.graphs.finish_action(lease,jobid,'interrupted')
                except GraphError:pass
            self._block_repair(jobid,'Repair rejected: '+str(exc))
        self._refresh_jobs()

    def _repair_error(self,jobid,message):
        job=self.jobs.get(jobid)
        if not job or job['state']!='running' or self.active_job!=jobid:
            return
        self.active_job=None
        lease=self._graph_repair_leases.pop(jobid,None)
        if lease:
            try:self.graphs.finish_action(lease,jobid,'blocked')
            except GraphError:pass
        self._block_repair(jobid,'Local ONNX repair failed: '+str(message)[:350])
        self._refresh_jobs()

    def _block_repair(self,jobid,reason):
        try:self.cycles.block(jobid,reason)
        except CycleError:pass
        self.jobs.change(jobid,'needs_input',reason[:700],allowed=('running','waiting_repair'))
        self._log(f'Job #{jobid}: autonomous repair blocked; {reason[:250]}')
        self.status.set(f'Job #{jobid} needs attention. See Work queue / Development cycle evidence.')

    def _project_work_once(self):
        """One global serial dispatch: repair, then verification; never both."""
        if (not self._project_work_is_enabled() or self.queue_paused
            or self.__dict__.get('_quiet_test_active') is not None
            or self.__dict__.get('_gui_test_active') is not None
            or self._auto_verification_in_flight is not None
            or self._auto_tool_active is not None or bool(self._auto_tool_queue)
            or self.active_job is not None or self.active_conversation is not None
            or self.disk_gate.gaming()
            or any(p and p.poll() is None for p in
                   (self.tool_process, self.install_process, self.media_process))
            or self.janus.status().get('paused')):
            return
        # Only previously failed, observed local tests of approved jobs can
        # enter a bounded repair. Every candidate is checked against its grant.
        if self.node_ready and self.node and self.node.poll() is None:
            for jobid in self.cycles.pending_repairs(limit=20):
                job=self.jobs.get(jobid)
                if not job or job['state']!='waiting_repair':
                    continue
                try:
                    self._claim_autonomous_repair(job)
                except (CycleError,GrantError,WorkspaceError,OSError,ValueError) as exc:
                    self._block_repair(jobid,'Repair cannot start safely: '+str(exc))
                    self._refresh_jobs()
                return
        # Tests are deterministic fixed profiles from the v40 authorization
        # framework, never commands supplied by diagnostics or the model.
        for job in self.jobs.pending_verifications(limit=40):
            project=Path(job['project'])
            cmd=self._verification_command(project)
            if not cmd:
                continue
            steps=self.jobs.steps(job['id'])
            lease=None
            try:
                authorize_test(STATE/'project-grants',job,steps,list(cmd),enabled=True)
                if self.graphs.exists(job['id']):
                    self.graphs.ready_to_test(job,steps,list(cmd))
                    lease=self.graphs.begin_action(job,steps,'test','verify')
                self.cycles.begin_test(job,steps,list(cmd))
                if lease:self._graph_test_leases[job['id']]=lease
            except GrantError:
                continue  # Project needs manual review or authority was revoked.
            except (CycleError,GraphError,CheckpointError,OSError,ValueError) as exc:
                if lease:
                    try:self.graphs.finish_action(lease,job['id'],'blocked')
                    except GraphError:pass
                self.jobs.change(job['id'],'needs_input',
                    'Autonomous test blocked: '+str(exc)[:450],
                    allowed=('waiting_verification',))
                self._log(f"Job #{job['id']}: test requires attention: {exc}")
                self._refresh_jobs()
                continue
            if not self.jobs.change(job['id'],'running',
                    'Running recorded fixed verification attempt',
                    allowed=('waiting_verification',)):
                self.cycles.block(job['id'],'Job changed state before test launch')
                if lease:
                    self._graph_test_leases.pop(job['id'],None)
                    try:self.graphs.finish_action(lease,job['id'],'interrupted')
                    except GraphError:pass
                continue
            self._auto_verification_in_flight=job['id']
            if not self._start_command(cmd,cwd=project,
                    label=f"Verify job #{job['id']} (development cycle)",
                    kind='verification',job_id=job['id']):
                self._auto_verification_in_flight=None
                self.cycles.block(job['id'],'Could not launch test; result is unknown')
                if lease:
                    self._graph_test_leases.pop(job['id'],None)
                    try:self.graphs.finish_action(lease,job['id'],'interrupted')
                    except GraphError:pass
                self.jobs.change(job['id'],'needs_input',
                    'Automatic test did not launch; manual inspection required',allowed=('running',))
                self._refresh_jobs()
                return
            cycle=self.cycles.get(job['id'])
            self._log(f"Job #{job['id']}: test {cycle['tests']}/{MAX_TEST_ATTEMPTS} "
                      'running under a job-bound fixed command; not yet verified.')
            self._refresh_jobs()
            return

    def _verify_build(self):
        if self.__dict__.get('_quiet_test_active') is not None or self.__dict__.get('_gui_test_active') is not None:
            self._log('Manual verification deferred while quiet scene test is running')
            return
        if any(p and p.poll() is None for p in (self.tool_process,self.install_process,self.media_process)):
            messagebox.showwarning('Tool already running',
                'A local tool, installation or media task is already running. Verification will remain queued for manual approval.');return
        j=self._selected_job()
        if j and (graph:=self.graphs.status(j['id'])) and graph['state']=='invalidated':
            messagebox.showwarning('Old approval invalidated',
                'The previous source checkpoint has been restored. Approve a NEW build plan '
                'before further verification.',parent=self)
            return
        if not j or j['mode']!='build' or j['state']!='waiting_verification':
            messagebox.showinfo('Nothing to verify','Select a build whose files were generated but not tested.');return
        project=Path(j['project']);cmd=self._verification_command(project)
        if not cmd:
            messagebox.showwarning('Verification needs attention',
                'No supported automatic test command was detected or its engine is missing. '
                'Add tests to this project or use Computer & Tools to run an approved check. '
                'The build remains unverified.');return
        if self.disk_gate.gaming():
            messagebox.showinfo('Gaming priority','Game detected; verification deferred.');return
        if not messagebox.askyesno('Approve build verification',
            f'Run this local project test/build?\n\n{subprocess.list2cmdline(cmd)}\n\n'
            'Tests may execute code from the project. The result will be recorded in the job queue.',parent=self):return
        self.jobs.change(j['id'],'running','Running approved project verification',allowed=('waiting_verification',))
        self._refresh_jobs();self.tabs.select(4)
        self._start_command(cmd,cwd=project,label=f"Verify job #{j['id']}",kind='verification',job_id=j['id'])

    def _toggle_queue(self):
        self.queue_paused=not self.queue_paused
        self.pause_queue.config(text='Resume queue' if self.queue_paused else 'Pause queue')
        self._log('Queue '+('paused (running work continues until stopped)' if self.queue_paused else 'resumed'))
        self._refresh_jobs()
    def _scheduler(self):
        """Keep the queue timer alive even if a callback fails unexpectedly."""
        try:
            self._scheduler_once()
        except Exception as exc:
            record(STATE,'desktop','queue_scheduler_exception',level='ERROR',
                   error_type=type(exc).__name__,stack=traceback.format_exc()[-12000:])
            self._log('Queue scheduler failed but will retry; export diagnostics for details.')
        finally:
            self.after(1100,self._scheduler)

    def _scheduler_once(self):
        tool_busy=(self.__dict__.get('_gui_test_active') is not None or
                   self.__dict__.get('_quiet_test_active') is not None or
                   any(p and p.poll() is None for p in (self.tool_process,self.install_process,self.media_process)))
        model_alive=bool(self.node and self.node.poll() is None)
        gate = ('paused' if self.queue_paused else
                'tool_busy' if tool_busy else
                'active_job' if self.active_job is not None else
                'model_transport_wait' if self._model_transport_waiting else
                'model_not_ready' if not self.node_ready else
                'model_process_not_running' if not model_alive else 'dispatch_enabled')
        now=time.monotonic()
        if gate != self._last_queue_gate or now-self._last_queue_gate_at>45:
            self._last_queue_gate=gate;self._last_queue_gate_at=now
            counts=self.jobs.count(self._project_key())
            record(STATE,'desktop','queue_dispatch_gate',reason=gate,
                   project_name=Path(self._project_key()).name,
                   counts=counts,node_ready=self.node_ready,model_alive=model_alive,
                   model_loading=self.node_loading,model_pid=self.node.pid if model_alive else None,
                   active_job=self.active_job)
        if gate=='dispatch_enabled':
            if self.active_conversation is None:
                incoming=self.conversations.next_pending()
                if incoming:
                    record(STATE,'desktop','conversation_dispatch',request_id=incoming['id'],mode=incoming['mode'])
                    self._execute_conversation(incoming)
                    return
            else:
                return
            games=self.disk_gate.gaming()
            skipped=('chat','plan','edit','build','image') if games else ('chat','plan','edit')
            j=self.jobs.next_any_queued(skip_modes=skipped)
            if j:
                record(STATE,'desktop','queue_dispatch',job_id=j['id'],mode=j['mode'],game_detected=games)
                self._execute_job(j)

    def _execute_job(self,j):
        jobid=j['id']
        if j['mode']=='build':
            graph=self.graphs.status(jobid)
            if graph and graph['state']=='invalidated':
                self.jobs.change(jobid,'needs_input',
                    'Previous graph approval was invalidated; approve a NEW project plan',
                    allowed=('queued',))
                self._log(f'Job #{jobid}: cancelled old plan execution after source rollback.')
                self._refresh_jobs()
                return
        record(STATE,'desktop','job_claim_attempt',job_id=jobid,mode=j['mode'])
        if not self.jobs.change(jobid,'running','Processing local job',allowed=('queued',)):
            return
        self.active_job=jobid;self.active_started=time.monotonic()
        self._log(f'Job #{jobid} started ({j["mode"]}). Local-only processing.')
        self.status.set(f'Job #{jobid} running locally. View Work queue / Processes for progress.')
        self._refresh_jobs()
        # Capture all Tk widget state on the GUI thread.
        include_file=self.attach_file.get() and j['project']==self._project_key()
        refine_image=self.refine_image.get()
        selected=self.current_file
        inventory=self.inventory
        def work():
            try:
                prompt=j['prompt']
                paths=json.loads(j.get('attachments_json') or '[]')
                # An attached picture in an ordinary chat is actually read by
                # Florence locally; its caption joins the model's text context.
                # Never replace the picture with filename-only pseudo-understanding.
                if j['mode'] not in ('vision','image'):
                    pictures=[x for x in paths if classify(x)=='image']
                    if len(pictures)>1:
                        raise RuntimeError('Only one image can be analyzed per small-model request. Separate them into queued jobs.')
                    if pictures:
                        node=shutil.which('node')
                        if not node:raise RuntimeError('Node.js is required for offline image reading')
                        output=self._capture_media_process([node,str(ROOT/'vision_caption.mjs'),pictures[0]],'Read attached image')
                        line=next((x for x in output.splitlines() if x.startswith('IMAGE_CAPTION_JSON: ')),None)
                        if not line:raise RuntimeError('Local vision engine did not return a caption; install the vision model first')
                        cap=json.loads(line.split('IMAGE_CAPTION_JSON: ',1)[1])['caption']
                        prompt += f'\n\nUSER-ATTACHED IMAGE {Path(pictures[0]).name} was described offline by the local Florence model:\n{cap}'
                        paths=[x for x in paths if classify(x)!='image']
                if j['mode']=='vision':
                    if len(paths)!=1 or classify(paths[0])!='image':
                        raise ValueError('Read Image requires exactly one selected picture')
                    node=shutil.which('node')
                    if not node:raise RuntimeError('Node.js not installed')
                    program=[node,str(ROOT/'vision_caption.mjs'),paths[0]]
                    output=self._capture_media_process(program,'Local image analysis')
                    line=next((x for x in output.splitlines() if x.startswith('IMAGE_CAPTION_JSON: ')),None)
                    if not line:raise RuntimeError('Vision model returned no verified caption; inspect Processes log.')
                    caption=json.loads(line.split('IMAGE_CAPTION_JSON: ',1)[1])['caption']
                    self.events.put(('job_answer',jobid,caption))
                    return
                if j['mode']=='image':
                    if not j['project'] or j['project']=='(general)':raise ValueError('Choose a project to save the image')
                    target=j['target'] or f'generated/image-{jobid}.png'
                    output_path=validate_image_output_path(j['project'],target)
                    modeldir=ROOT/'models'/'stable-diffusion-v1-5'
                    if refine_image:
                        draft=self.client.chat(j['chat_id'],
                            'Refine this into a concise, high-quality descriptive text-to-image prompt. '
                            'Return only the image description (no explanation):\n'+prompt,
                            max_tokens=160).strip()
                        if 5<len(draft)<1500:
                            self.events.put(('log',f'Image job #{jobid}: image prompt prepared by local Qwen model.'))
                            prompt=draft
                    command=cli_image_args(sys.executable,ROOT/'run_image.py',modeldir,prompt,output_path,384,384,15)
                    output=self._capture_media_process(command,'Image generation')
                    if not output_path.is_file():raise RuntimeError('Image engine did not save an image; inspect Processes log')
                    self.events.put(('job_answer',jobid,str(output_path)))
                    return
                if j['mode']=='build':
                    if paths:
                        prompt=composed_prompt(prompt,paths)
                    steps=self.jobs.steps(jobid)
                    if not steps:
                        answer=self.client.chat(j['chat_id'],build_plan_prompt(prompt,inventory),max_tokens=640)
                        self.events.put(('job_plan',jobid,answer))
                        return
                    step=self.jobs.next_step(jobid)
                    if not step:
                        self.events.put(('build_files_done',jobid))
                        return
                    project=Path(j['project'])
                    dest=safe_target(project,step['path'])
                    old=read_project_file(project,step['path']) if dest.is_file() else ''
                    if len(old)>3500:raise RuntimeError('Existing file too large for safe one-pass local edit. Split the file.')
                    request=budgeted_file_step_prompt(prompt,step['path'],step['description'],old,steps,max_chars=MAX_INFERENCE_PROMPT)
                    answer=self.client.chat(j['chat_id'],request,max_tokens=768)
                    self.events.put(('job_answer',jobid,answer))
                    return
                if j['mode']=='edit':
                    if not j['target'] or not j['project'] or j['project']=='(general)':
                        raise RuntimeError('Edit requires a selected project and target file')
                    target=j['target'];project=Path(j['project'])
                    old=read_project_file(project,target) if safe_target(project,target).is_file() else ''
                    if len(old)>3500:raise RuntimeError('File too large for safe one-pass local editing; split the task')
                    prompt=(f'Update file: {target}. Return ONLY the complete replacement file. '
                            f'Preserve unspecified behaviour.\nREQUEST:\n{j["prompt"]}\nCURRENT:\n{old}')
                elif j['mode']=='plan':
                    tools=', '.join(t['name'] for t in (inventory or {}).get('tools',[]) if t['found'])
                    needed=plan_tool_needs(j['prompt'],inventory or {})
                    missing=', '.join(t['name'] for t in needed if not t['found'])
                    prompt=(f'Plan the project in small verifiable steps. Only discovered software: {tools}. '
                            f'Tools requiring permission: {missing}. Do not claim to have run commands.\n'
                            f'PROJECT REQUEST:\n{j["prompt"]}')
                elif j['mode']=='chat' and j['project']!='(general)' and include_file and selected:
                    old=read_project_file(Path(j['project']),selected)
                    prompt=f'Project file {selected}:\n{old}\n\nUser request: {prompt}'
                prompt=composed_prompt(prompt,paths)
                if len(prompt)>MAX_INFERENCE_PROMPT:
                    raise ValueError(f'Full request/context is {len(prompt):,} characters. Maximum is {MAX_INFERENCE_PROMPT:,}; no text was truncated.')
                answer=self.client.chat(j['chat_id'],prompt,max_tokens=768 if j['mode']=='edit' else 384)
                self.events.put(('job_answer',jobid,answer))
            except Exception as exc:
                record(STATE,'desktop','job_worker_exception',level='ERROR',job_id=jobid,
                       error_type=type(exc).__name__, stack=traceback.format_exc()[-12000:])
                self.events.put(('job_error',jobid,str(exc)))
        threading.Thread(target=work,daemon=True).start()

    def _capture_media_process(self,command,label):
        """Read-only thread; managed child inherits GUI Job Object hard cap."""
        flags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0
        lines=[]
        with subprocess.Popen(command,cwd=str(ROOT),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
             text=True,encoding='utf-8',errors='replace',creationflags=flags,shell=False) as proc:
            self.media_process=proc
            try:
                for line in proc.stdout:
                    lines.append(line.rstrip())
                    self.events.put(('log',f'[{label}] {line.rstrip()}'))
                    if len(lines)>5000:lines.pop(0)
                code=proc.wait()
            finally:self.media_process=None
        if code:raise RuntimeError(f'{label} returned exit code {code}; see Processes')
        return '\n'.join(lines)

    def _job_plan(self,jobid,text):
        j=self.jobs.get(jobid)
        if not j or j['state']!='running':return
        self.active_job=None
        try:
            plan=parse_build_plan(text,Path(j['project']))
            self.jobs.add_plan(jobid,plan)
            self.jobs.change(jobid,'needs_input','Plan ready for review; select job and click Approve build plan',result=text,allowed=('running',))
            self._log(f'Job #{jobid}: prepared {len(plan)} source-file stages. Waiting for plan approval.')
            self.tabs.select(1)
            messagebox.showinfo('Approve build plan',
                f'DeepThorT drafted {len(plan)} file steps for job #{jobid}.\n\n'
                'Open Work queue, select the job, inspect the file plan and approve it.\n'
                'No files have been changed.')
        except Exception as e:
            self.jobs.change(jobid,'needs_input','Model plan invalid: '+str(e),result=text,allowed=('running',))
            self._log(f'Job #{jobid}: plan needs advice: {e}')
            self.tabs.select(1)
            messagebox.showwarning('Project plan needs correction',f'Job #{jobid}: {e}\nSee Work queue for the raw model result.')
        self._refresh_jobs()

    def _build_files_done(self,jobid):
        j=self.jobs.get(jobid)
        if not j or j['state']!='running':return
        self.active_job=None
        steps=self.jobs.steps(jobid)
        saved=sum(x['state']=='saved' for x in steps)
        if saved!=len(steps):
            self.jobs.change(jobid,'needs_input','Some file stages are incomplete; review the plan',allowed=('running',))
        else:
            self.jobs.change(jobid,'waiting_verification',f'{saved} source files saved with backups. Awaiting actual project tests.',allowed=('running',))
            self._log(f'Job #{jobid}: {saved} file stages saved; NOT verified.')
            self.tabs.select(1)
            unattended_test = False
            if self._project_work_is_enabled():
                cmd = self._verification_command(Path(j['project']))
                if cmd:
                    candidate = self.jobs.get(jobid)
                    try:
                        unattended_test = authorize_test(
                            STATE/'project-grants', candidate, self.jobs.steps(jobid),
                            list(cmd), enabled=True)
                    except (GrantError, OSError, ValueError):
                        unattended_test = False
            if unattended_test:
                self._log(f'Job #{jobid}: saved-file fingerprints match; '
                          'fixed local verification will be scheduled automatically.')
            else:
                messagebox.showinfo('Build requires verification',
                    f'Job #{jobid} saved {saved} proposed files.\n\n'
                    'Source generation is NOT proof of a working app or game.\n'
                    'Select Verify build to run a separately approved local test.')
        self._refresh_jobs()

    def _job_answer(self,jobid,answer):
        j=self.jobs.get(jobid)
        if not j or j['state']!='running':
            self._log(f'Ignored stale answer for cancelled/paused job #{jobid}.');return
        self.active_job=None
        if j['mode']=='build':
            step=self.jobs.next_step(jobid)
            if not step:
                self.jobs.change(jobid,'needs_input','No active step; inspect build plan',result=answer,allowed=('running',))
            else:
                code=strip_single_code_fence(answer)
                if not code.strip() or len(code)>280_000:
                    self.jobs.change(jobid,'needs_input','Model supplied empty/oversized code. Ask for correction.',result=answer,allowed=('running',))
                else:
                    authority = None
                    if self._project_work_is_enabled():
                        try:
                            authority = authorize_file(STATE/'project-grants', j,
                                self.jobs.steps(jobid), step, enabled=True)
                        except (GrantError, OSError, ValueError) as exc:
                            # No generic auto-write permission is inferred.
                            self._log(f'Job #{jobid}: manual review for '
                                      f'{step["path"]}: {str(exc)[:180]}')
                    if authority is not None:
                        try:
                            steps_now=self.jobs.steps(jobid)
                            lease=None
                            if self.graphs.exists(jobid):
                                # Graph lease is recorded BEFORE filesystem mutation.
                                lease=self.graphs.begin_action(j,steps_now,'write',f'file:{step["id"]}')
                            try:
                                dest = apply_approved_file(Path(j['project']), step['path'], code,
                                    STATE/'backups', expected_existing_sha=authority['before_sha256'])
                                evidence = record_file(STATE/'project-grants', j,
                                    self.jobs.steps(jobid), step, enabled=True)
                                if lease:
                                    self.graphs.record_artifact(j,self.jobs.steps(jobid),step,evidence['sha256'])
                                    check=self.checkpoints.capture(j,self.jobs.steps(jobid),'artifact_saved')
                                    if check['files'].get(evidence['path'])!=evidence['sha256']:
                                        raise CheckpointError('Source changed between approval and checkpoint receipt')
                                    self.graphs.finish_action(lease,jobid,'saved')
                            except BaseException:
                                if lease:
                                    try:self.graphs.finish_action(lease,jobid,'interrupted')
                                    except GraphError:pass
                                raise
                            self.jobs.set_step(step['id'], 'saved',
                                'Job-authorized reversible write; SHA-256 recorded; not tested')
                            self.jobs.change(jobid, 'queued',
                                f'Saved {step["path"]}; next exact approved stage queued',
                                result=answer, allowed=('running',))
                            self._log(f'Job #{jobid}: authorized source write {dest}; '
                                      f'SHA256 {evidence["sha256"][:16]}…; backup retained.')
                            self._refresh_files()
                        except (GrantError, GraphError, CheckpointError, WorkspaceError, OSError, ValueError) as exc:
                            self.jobs.change(jobid, 'needs_input',
                                'Automatic file write needs attention: ' + str(exc),
                                result=answer, allowed=('running',))
                            self._log(f'Job #{jobid}: unattended write failed closed: {exc}')
                    else:
                        self.proposed = (step['path'], code)
                        self.proposal_job = jobid
                        self.proposal_step = step['id']
                        self.jobs.set_step(step['id'], 'proposed', 'Awaiting individual file review')
                        self.jobs.change(jobid, 'waiting_approval',
                            f'Review proposed {step["path"]} ({len(self.jobs.steps(jobid))} planned files)',
                            result=answer, allowed=('running',))
                        self.file_title.set('Proposed: ' + step['path'])
                        self._preview('PROPOSED CODE — edit below before approving\n\n' + code)
                        self.tabs.select(2)
                        messagebox.showinfo('Build needs file review',
                            f'Job #{jobid} proposed {step["path"]}. Review it and approve saving. '
                            'The next stage will queue automatically.')
        elif j['mode']=='vision':
            self.jobs.change(jobid,'responded','Local image was described by vision model',result=answer,allowed=('running',))
            self._show(self.image_info,answer)
            if self.current_chat==j['chat_id']:self._chat_line('assistant','Image description: '+answer)
            self.tabs.select(7)
        elif j['mode']=='image':
            self.jobs.change(jobid,'complete','Offline image generated and saved: '+answer,result=answer,allowed=('running',))
            self._show(self.image_info,'Image created: '+answer)
            self._display_image(Path(answer))
            self.tabs.select(7)
        elif answer.strip().startswith('NEED_USER_DECISION:'):
            self.jobs.change(jobid,'needs_input','Model requested user advice',result=answer,allowed=('running',))
            self._log(f'Job #{jobid} needs advice: '+answer[:200])
            messagebox.showwarning('DeepThorT needs advice',f'Job #{jobid}:\n\n{answer[:750]}\n\nOpen the Work queue to review the problem.')
        elif j['mode']=='edit':
            try:
                code=strip_single_code_fence(answer)
                self.proposed=(j['target'],code)
                self.proposal_job=jobid
                self.jobs.change(jobid,'waiting_approval','Generated code is awaiting file-review approval',result=answer,allowed=('running',))
                self.file_title.set('Approve or revise: '+str(j['target']))
                self._preview('PROPOSED CODE — edit below before approving\n\n'+code)
                self.tabs.select(2)
                self._log(f'Job #{jobid}: proposed file content prepared, NOT saved.')
                messagebox.showinfo('Review proposed file',f'Job #{jobid} completed generation.\n\nReview the code and explicitly approve any file write.')
            except Exception as e:
                self.jobs.change(jobid,'needs_input','Could not safely parse file proposal: '+str(e),result=answer,allowed=('running',))
                messagebox.showwarning('Needs review',f'The model response could not be used safely: {e}')
        else:
            self.jobs.change(jobid,'responded',
                'Plan drafted; not executed or verified' if j['mode']=='plan' else 'Local response generated (not code-verified)',
                result=answer,allowed=('running',))
            if self.current_chat==j['chat_id'] and self._project_key()==j['project']:
                self._chat_line('assistant',answer)
                self.tabs.select(0)
            self._log(f'Job #{jobid} finished. Response stored; no build/test success is implied.')
            self.bell()
        self.status.set(f'Job #{jobid} updated. Review real progress in Chats or Work queue.')
        self._refresh_jobs();self._reload_chat()
    def _job_error(self,jobid,reason):
        j=self.jobs.get(jobid)
        if not j or j['state']!='running':return
        self.active_job=None
        state='needs_input' if any(w in reason.casefold() for w in ('too large','maximum','revise','divide','context')) else 'failed'
        self.jobs.change(jobid,state,reason,allowed=('running',))
        self._log(f'Job #{jobid}: {state}: '+reason)
        self.status.set(f'Job #{jobid} needs attention. See Work queue.')
        self._refresh_jobs();self.tabs.select(1)
        messagebox.showwarning('DeepThorT needs attention',
                  f'Job #{jobid} stopped:\n\n{reason[:900]}\n\nInspect the Work queue. You may revise the prompt, resume or cancel.')
    def _apply_proposal(self):
        if not self.proposed or not self.project:
            messagebox.showinfo('Nothing to apply','Generate a proposed file edit and review it first.');return
        target,_=self.proposed
        code=self.file_preview.get('1.0','end-1c')
        if code.startswith('PROPOSED CODE —'):code=code.split('\n',2)[-1]
        if not messagebox.askyesno('Approve this file write',
                   f'Write the reviewed code to:\n{self.project / target}\n\n'
                   'Existing files will be backed up. This does NOT execute the code.',parent=self):return
        try:
            dest=apply_approved_file(self.project,target,code,STATE/'backups')
        except Exception as e:
            self._log('File write refused: '+str(e));messagebox.showerror('Write blocked',str(e));return
        if self.proposal_job is not None:
            parent=self.jobs.get(self.proposal_job)
            if parent and parent['mode']=='build' and self.proposal_step is not None:
                if self.graphs.exists(parent['id']):
                    steps=self.jobs.steps(parent['id'])
                    matching=[x for x in steps if x['id']==self.proposal_step and x['path']==target]
                    try:
                        if len(matching)!=1:raise GraphError('Manual review step no longer matches approved graph')
                        receipt=record_file(STATE/'project-grants',parent,steps,matching[0],enabled=True)
                        self.graphs.record_artifact(parent,steps,matching[0],receipt['sha256'])
                        check=self.checkpoints.capture(parent,steps,'manual_review_save')
                        if check['files'].get(receipt['path'])!=receipt['sha256']:
                            raise CheckpointError('Manually reviewed source changed before checkpoint evidence')
                    except (GrantError,GraphError,CheckpointError,WorkspaceError,OSError,ValueError) as exc:
                        self.jobs.change(parent['id'],'needs_input',
                            'Manually reviewed source was saved, but graph/approval evidence failed: '+str(exc)[:240],
                            allowed=('waiting_approval',))
                        self._log(f'Job #{parent["id"]}: manual source saved; graph must be reconciled: {exc}')
                    else:
                        self.jobs.set_step(self.proposal_step,'saved','User approved; graph SHA recorded; not yet tested')
                        self.jobs.change(self.proposal_job,'queued',
                            f'Saved {target}; graph evidence recorded; next stage queued',allowed=('waiting_approval',))
                else:
                    self.jobs.set_step(self.proposal_step,'saved','User approved; not yet tested')
                    self.jobs.change(self.proposal_job,'queued',f'Saved {target}; next build stage queued',allowed=('waiting_approval',))
            else:
                self.jobs.change(self.proposal_job,'waiting_verification','User saved proposed file; code NOT tested',allowed=('waiting_approval',))
        self._log('User-approved project file saved: '+str(dest))
        self.proposed=None;self.proposal_job=None;self.proposal_step=None
        self.file_title.set('Saved: '+target)
        self.status.set('Saved file, not yet tested. Run an approved project check to verify it.')
        self._refresh_files();self._refresh_jobs()
        messagebox.showinfo('File saved','The approved file was written. Existing contents were backed up.\n\nThis does not verify the code works.')

    # ----------- task list ------------
    def _add_task(self):
        if not self.project:
            messagebox.showinfo('Select project','Choose a project folder first.');return
        title=simpledialog.askstring('New project task','Describe the work step:',parent=self)
        if title:self.tasks.add(str(self.project),title);self._refresh_tasks()
    def _refresh_tasks(self):
        if not hasattr(self,'task_tree'):return
        for x in self.task_tree.get_children():self.task_tree.delete(x)
        if self.project:
            for i,title,done in self.tasks.items(str(self.project)):
                self.task_tree.insert('','end',iid=str(i),values=('Done' if done else 'Planned',title))
    def _selected_task(self):
        pick=self.task_tree.selection()
        if not pick or not self.project:return None
        return next((x for x in self.tasks.items(str(self.project)) if x[0]==int(pick[0])),None)
    def _toggle_task(self):
        t=self._selected_task()
        if t:self.tasks.mark(str(self.project),t[0],not t[2]);self._refresh_tasks()
    def _task_to_chat(self):
        t=self._selected_task()
        if t:
            self.input.insert('end','\nPlease implement and verify this project task: '+t[1])
            self.tabs.select(0)

    # ----------- resource discovery / developer tools ------------
    def _refresh_inventory(self):
        self._show(self.machine_text,'Scanning computer hardware, drives and known program locations…')
        path=self.project
        game_dir=self.x4_game_dir
        reference_dir=self.x4_reference_dir
        def worker():
            try:
                inventory=scan_computer(ROOT,path,include_gpu=not self.disk_gate.gaming(),
                    x4_game_dir=game_dir,x4_reference_dir=reference_dir)
                self.events.put(('inventory',inventory))
            except Exception as exc:self.events.put(('inventory_error',str(exc)))
        threading.Thread(target=worker,daemon=True).start()
    def _save_x4_paths(self):
        self.x4_settings_file.write_text(json.dumps({
            'game_dir':self.x4_game_dir,'reference_dir':self.x4_reference_dir,
            'catalog_tool':self.x4_catalog_tool},indent=2),encoding='utf-8')

    def _inspect_x4_sources(self):
        self._show(self.x4_source_info,'Inspecting known X4 paths and selected XML references (read-only)…')
        project=self.project;game=self.x4_game_dir;ref=self.x4_reference_dir
        def worker():
            try:
                result=inspect_x4_sources(project_dir=project,game_dir=game,reference_dir=ref)
                self.events.put(('x4_sources',result))
            except Exception as exc:self.events.put(('x4_sources_error',str(exc)))
        threading.Thread(target=worker,daemon=True,name='X4Inspection').start()

    def _x4_preflight_needs_sources(self, ident, report):
        """On the GUI thread, carry out missing discovery/approval, not instructions."""
        req=self.conversations.get(ident)
        if not req or req['state']!='running':return
        self.x4_report=report
        game=report.get('game_dir')
        if game and not self.x4_game_dir:
            self.x4_game_dir=game;self._save_x4_paths()
        if report.get('reference_dir') and not self.x4_reference_dir:
            self.x4_reference_dir=report['reference_dir'];self._save_x4_paths()
        if not game:
            # Only ask for a location when automatic Steam/GOG discovery failed.
            selected=filedialog.askdirectory(
                title='X4 was not located automatically. Select its installed game folder',parent=self)
            if selected and (Path(selected)/'X4.exe').is_file():
                self.x4_game_dir=str(Path(selected).resolve());self._save_x4_paths()
                self.conversations.change(ident,'pending','Game located; automatic X4 inspection will resume',
                                          allowed=('running',))
                self.active_conversation=None;self._reload_chat()
            else:
                self._conversation_error(ident,
                    'Automatic X4 inspection could not locate the installation. No files were changed. '
                    'Select the game folder containing X4.exe when prompted; original request is saved.')
            return
        if self.disk_gate.gaming():
            self._conversation_error(ident,
                'Game running: X4 asset extraction deferred to protect gaming performance. '
                'The game and request have been located; retry after gaming. No files changed.')
            return
        if not report.get('can_offer_extraction'):
            self._conversation_error(ident,'X4 was inspected automatically, but usable PE references are unavailable. '
                +' '.join(report.get('blocked_reasons') or [])+' No work was queued.')
            return
        tool=report.get('catalog_tool') or ''
        if not tool:
            # Manual intervention is for permission/tool provision, not discovery.
            selected=filedialog.askopenfilename(
                title='Official XRCatTool.exe required to read packed X4 catalogs',
                filetypes=[('Egosoft XRCatTool','XRCatTool.exe'),('Executables','*.exe')],parent=self)
            tool=find_catalog_tool(selected=selected,game_dir=game) if selected else None
            if not tool:
                self._conversation_error(ident,
                    'X4 game and packed catalogs were inspected automatically. The official '
                    'XRCatTool.exe is not installed or selected, so extraction cannot proceed. '
                    'Install it from Egosoft X Tools and retry the SAVED request. No files changed.')
                return
        output=ROOT/'reference'/'x4'
        try:cmd=catalog_extraction_command(tool,game,output)
        except (OSError,ValueError) as exc:
            self._conversation_error(ident,'Cannot prepare verified X4 extraction: '+str(exc));return
        if not messagebox.askyesno('Allow DeepThorT to inspect packed X4 XML?',
            'DeepThorT automatically found your X4 game and its catalogs. To continue '
            'your original request, the official extraction tool must read packed XML.\n\n'
            f'Read-only game input: {game}\nExtractor: {tool}\n'
            f'Extracted reference output: {output}\n\n'
            'This can use significant disk I/O and overwrite previously extracted reference XML. '
            'It will not modify game files or execute the requested mod work.\n\n'
            'Approve extraction and automatically resume your original request when done?',parent=self):
            self._conversation_error(ident,
                'Automatic X4 inspection found packed references; you declined extraction. '
                'The request was saved, no project job queued and no game files changed.')
            return
        output.mkdir(parents=True,exist_ok=True)
        self.x4_catalog_tool=str(tool);self.x4_reference_dir=str(output)
        self._save_x4_paths()
        if not self.conversations.change(ident,'waiting_sources',
                'Approved game XML extraction in progress; original request will resume',
                allowed=('running',)):return
        self.active_conversation=None
        record(STATE,'desktop','x4_auto_extraction_approved',request_id=ident,
               source=str(game),output=str(output),tool=str(tool))
        self._reload_chat()
        started=self._start_command(cmd,cwd=ROOT,label='Approved X4 XML extraction',
                                    kind='x4_preflight_extraction',job_id=ident)
        if not started:
            self.conversations.change(ident,'failed',
                'Another tool is currently running. Retry saved request to inspect sources.',
                allowed=('waiting_sources',))
            self._reload_chat()

    def _x4_preflight_extract_finished(self,ident,code):
        if code!=0:
            self.conversations.change(ident,'failed',
                f'Official X4 XML extraction failed (exit {code}); see Processes and Export diagnostics',
                allowed=('waiting_sources',))
            self._reload_chat();return
        # Verification also runs off the GUI thread so the app remains responsive.
        def check():
            try:
                report=automatic_x4_preflight(
                    project_dir=(self.conversations.get(ident) or {}).get('project'),
                    app_root=ROOT,game_dir=self.x4_game_dir,reference_dir=self.x4_reference_dir,
                    catalog_tool=self.x4_catalog_tool)
                self.events.put(('x4_extract_checked',ident,report))
            except Exception as exc:
                self.events.put(('x4_extract_check_error',ident,str(exc)))
        threading.Thread(target=check,daemon=True,name='X4VerifiedExtraction').start()

    def _x4_preflight_extract_checked(self,ident,report):
        self.x4_report=report
        self._show(self.x4_source_info,format_x4_inspection(report))
        if report['ready_for_planning']:
            self.conversations.change(ident,'pending',
                'Local X4 XML verified; automatically resuming original request',
                allowed=('waiting_sources',))
            record(STATE,'desktop','x4_auto_extraction_verified',request_id=ident)
            self._log(f'X4 XML verified; original conversation #{ident} will resume automatically.')
        else:
            self.conversations.change(ident,'failed',
                'Extraction completed but mandatory Xenon PE references remain unverified: '
                +' '.join(report['blocked_reasons']),allowed=('waiting_sources',))
            record(STATE,'desktop','x4_auto_extraction_incomplete',request_id=ident,
                   missing=report['blocked_reasons'][:6])
        self._reload_chat()

    def _choose_x4_game(self):
        selected=filedialog.askdirectory(title='Select folder containing X4.exe and numbered .cat archives',parent=self)
        if not selected:return
        path=Path(selected)
        if not (path/'X4.exe').is_file() and not (path/'01.cat').is_file():
            messagebox.showwarning('Not an X4 game folder','Choose the X4 Foundations installation directory, not the extensions or project folder.',parent=self);return
        self.x4_game_dir=str(path.resolve());self._save_x4_paths();self._inspect_x4_sources()

    def _choose_x4_refs(self):
        selected=filedialog.askdirectory(title='Select EXTRACTED X4 XML folder containing assets/, libraries/, index/',parent=self)
        if not selected:return
        path=Path(selected)
        if not (path/'assets'/'units').is_dir():
            messagebox.showwarning('Not extracted X4 references',
                'This needs extracted vanilla XML files, not CAT archives. Use the Egosoft X Catalog Tool to extract the assets.',parent=self);return
        self.x4_reference_dir=str(path.resolve());self._save_x4_paths();self._inspect_x4_sources()

    def _extract_x4_references(self):
        if self.disk_gate.gaming():
            messagebox.showinfo('Gaming priority','Please close X4 or any configured game before extracting large game catalogs.',parent=self);return
        game=Path(self.x4_game_dir) if self.x4_game_dir else None
        if not game or not (game/'X4.exe').is_file():
            messagebox.showinfo('Find X4 first','Click Inspect X4 sources or Choose X4 game folder first.',parent=self);return
        tool=find_catalog_tool(selected=self.x4_catalog_tool,game_dir=game)
        if not tool:
            selection=filedialog.askopenfilename(title='Select officially installed XRCatTool.exe',filetypes=[('Egosoft XRCatTool','XRCatTool.exe'),('Executables','*.exe')],parent=self)
            if not selection:return
            tool=find_catalog_tool(selected=selection,game_dir=game)
            if not tool:
                messagebox.showwarning('Official extractor required',
                    'Select XRCatTool.exe from the Egosoft X Tools installation. DeepThorT will not download third-party executables automatically.',parent=self);return
        output=ROOT/'reference'/'x4'
        try:cmd=catalog_extraction_command(tool,game,output)
        except (OSError,ValueError) as exc:
            messagebox.showerror('Cannot extract',str(exc),parent=self);return
        if not messagebox.askyesno('Approve local X4 XML extraction?',
            f'READ from: {game}\nWRITE extracted XML to: {output}\nTOOL: {tool}\n'
            f'Base catalogs: {len([x for x in cmd if x.lower().endswith(".cat")])}\n\n'
            'Only XML matching ship/equipment/library/MD paths is requested; there are no downloads, but copying and decompressing may cause heavy disk I/O.\n'
            'Existing reference files may be overwritten by the extractor. X4 installation files will not be changed.\n\n'
            'Approve this extraction?',parent=self):return
        output.mkdir(parents=True,exist_ok=True)
        self.x4_catalog_tool=tool
        self.x4_reference_dir=str(output)
        self._save_x4_paths()
        self.tabs.select(4)
        self._log('User approved X4 XML extraction; launching official XRCatTool with path filters.')
        self._start_command(cmd,cwd=ROOT,label='Extract X4 reference XML',kind='x4_extraction')

    def _routine_tools_enabled(self):
        policy=getattr(self,'_autonomy_policy',None)
        return isinstance(policy,dict) and policy.get('enabled') is True

    def _set_tool_autonomy(self):
        """One standing local preference, not a new confirmation for each tool."""
        enabled=self.autonomy_enabled.get()
        upgrades=self.autonomy_upgrades.get()
        try:
            policy=set_policy(STATE/'routine-software-policy.json',
                              enabled=enabled,allow_upgrades=upgrades)
        except (OSError,ValueError) as exc:
            self.autonomy_enabled.set(self._autonomy_policy['enabled'])
            self.autonomy_upgrades.set(self._autonomy_policy['allow_upgrades'])
            messagebox.showwarning('Could not save preference',str(exc),parent=self)
            return
        self._autonomy_policy=policy
        if not enabled:
            self._auto_tool_queue.clear()
            self._auto_tool_waiting.clear()
            self._tool_probe_queue.clear()
        record(STATE,'desktop','routine_tool_policy_changed',enabled=enabled,upgrades=upgrades)
        self._log('Routine project software management '+('ENABLED' if enabled else 'DISABLED')+
                  ('; approved upgrades allowed.' if enabled and upgrades else '.'))

    def _autonomy_queue_request(self,prompt,project):
        """Only original user BUILD/EDIT requests can trigger catalog provisioning."""
        if not self._autonomy_policy['enabled'] or str(self.project)!=project:return
        if not isinstance(self.inventory,dict):
            if len(self._auto_tool_waiting)<8:
                self._auto_tool_waiting.append((prompt,project))
            self._refresh_inventory()
            return
        try:
            plans=project_tool_plans(prompt,self.inventory,project,self._autonomy_policy,
                           self._auto_tool_history,which=shutil.which)
            pending={(p['package_id'],p['operation']) for p in self._auto_tool_queue}
            if self._auto_tool_active:
                pending.add((self._auto_tool_active['package_id'],self._auto_tool_active['operation']))
            for plan in plans:
                ident=(plan['package_id'],plan['operation'])
                if ident not in pending and len(self._auto_tool_queue)<12:
                    self._auto_tool_queue.append(plan)
                    pending.add(ident)
                    self._log('Project tool queued: '+plan['name']+' ('+plan['operation']+
                              '); Windows UAC may request elevation. No arbitrary installer commands.')
        except (OSError,ValueError,TypeError) as exc:
            self._log('Routine tool management unavailable: '+str(exc))

    def _record_automatic_software(self,plan,status,exit_code=None):
        row=audit_record(plan,status,exit_code=exit_code)
        if not save_snapshot(STATE/'last-routine-software.json',row):
            raise OSError('Could not record the supervised software action; no new action authorized')
        history=dict(self._auto_tool_history)
        history[row['package_id']+':'+row['operation']]=row
        # Bound future desktop snapshots, do not retain unlimited history.
        if len(history)>90:
            history=dict(list(history.items())[-90:])
        if not save_snapshot(STATE/'routine-software-history.json',history):
            raise OSError('Could not persist the routine software action history')
        self._auto_tool_history=history
        return row

    def _automatic_tool_tick(self):
        """Bounded serial dispatch. No child starts unless policy and state allow."""
        if not self._quitting:
            self.after(2200,self._automatic_tool_tick)
        if self._quitting or not self._autonomy_policy['enabled'] or os.name!='nt':return
        if (self.queue_paused or self.__dict__.get('_quiet_test_active') is not None
            or self.__dict__.get('_gui_test_active') is not None or self._auto_tool_active or
            getattr(self, '_auto_verification_in_flight', None) is not None or not self._auto_tool_queue or
            self.disk_gate.gaming()):return
        if self.install_process and self.install_process.poll() is None:return
        if self.tool_process and self.tool_process.poll() is None:return
        plan=self._auto_tool_queue.pop(0)
        try:
            if str(self.project)!=plan['project']:
                self._log('Routine software work deferred: project changed; no command run.')
                return
            if plan['operation']=='upgrade' and not self._autonomy_policy['allow_upgrades']:
                self._log('Routine tool upgrade blocked by current preference.')
                return
            verify_plan(plan,which=shutil.which)
            if shutil.disk_usage(ROOT).free<MIN_FREE_BYTES:
                self._log('Routine tool installation deferred: less than 1 GiB free.')
                self._auto_tool_queue.insert(0,plan)
                return
            if already_attempted(self._auto_tool_history.get(plan['package_id']+':'+plan['operation']),
                                 plan['package_id'],plan['operation']):
                return
            self._record_automatic_software(plan,'launch_requested')
            self._auto_tool_active=plan
            if not self._start_command(plan['argv'],cwd=ROOT,
                     label='Routine '+plan['operation']+' '+plan['name'],kind='automatic_software'):
                self._record_automatic_software(plan,'failed')
                self._auto_tool_active=None
                return
            self._log('Routine '+plan['operation']+' launched via fixed WinGet catalog ID '+
                      plan['package_id']+'. Standard Windows UAC remains in force.')
        except (OSError,ValueError,TypeError) as exc:
            self._auto_tool_active=None
            self._log('Routine software action did not launch: '+str(exc))

    def _automatic_tool_finished(self,code):
        plan=self._auto_tool_active
        self._auto_tool_active=None
        if not plan:
            self._log('Unmatched automatic software result; inspect Processes.')
            return
        status='completed_unverified' if code==0 else 'failed'
        try:
            self._record_automatic_software(plan,status,exit_code=code)
        except (OSError,ValueError,TypeError) as exc:
            self._log('Routine software audit could not be persisted: '+str(exc))
        self._log('Routine '+plan['operation']+' '+plan['package_id']+': '+status+
                  '; follow-up tool scan is required for actual capability verification.')
        if code==0:
            self._queue_catalog_verification(plan['name'],project=plan['project'],
                plan_sha256=plan['plan_sha256'],install_exit_code=code)
            self._refresh_inventory()

    def _queue_catalog_verification(self,name,*,project='',plan_sha256='',install_exit_code=None):
        """Queue only catalog checks. Never run model-selected programs."""
        if name not in INSTALL_CATALOG:return
        if any(row['name']==name for row in self._tool_probe_queue):return
        if isinstance(self._tool_probe_active,dict) and self._tool_probe_active['name']==name:return
        if len(self._tool_probe_queue)>=12:
            self._log('Post-install verification queue is full; use Scan this computer.')
            return
        self._tool_probe_queue.append(dict(name=name,project=str(project or ''),
               plan_sha256=plan_sha256,install_exit_code=install_exit_code))
        self._log('Post-install capability check queued for '+name+
                  '; the version probe will not bypass Windows UAC or open a GUI app.')

    def _tool_probe_tick(self):
        if not self._quitting:
            self.after(2400,self._tool_probe_tick)
        if (self._quitting or not self._tool_probe_queue or self._tool_probe_active
            or self.__dict__.get('_quiet_test_active') is not None
            or self.__dict__.get('_gui_test_active') is not None
            or self.queue_paused or self.disk_gate.gaming()
            or self._auto_tool_active or self._auto_verification_in_flight is not None
            or self.active_job is not None or self.active_conversation is not None
            or any(p and p.poll() is None for p in
                   (self.install_process,self.tool_process,self.media_process))):
            return
        request=self._tool_probe_queue.pop(0)
        self._tool_probe_active=request
        def worker():
            try:
                row=verify_catalog_tool(request['name'],project=request['project'],
                    install_plan_sha256=request['plan_sha256'],
                    install_exit_code=request['install_exit_code'])
                self.events.put(('tool_probe_done',row))
            except Exception as exc:
                self.events.put(('tool_probe_error',request['name'],str(exc)[:280]))
        threading.Thread(target=worker,daemon=True).start()

    def _tool_probe_finished(self,row):
        self._tool_probe_active=None
        try:self._tool_verification.record(row)
        except (ValueError,OSError) as exc:
            self._log('Tool probe evidence not saved: '+str(exc))
            return
        status=row['status']
        self._log('Independent tool check '+row['tool']+': '+status+
                  (('; '+row['version']) if row['version'] else '')+
                  (('; '+row['executable']) if row['executable'] else '')+
                  '. This is NOT publisher-signature verification or application playtesting.')
        if status=='version_verified':
            # Make a newly installed CLI discoverable to fixed project tests in
            # this desktop session; persist neither system nor registry PATH.
            exe=Path(row['executable'])
            folder=str(exe.parent)
            current=os.environ.get('PATH','').split(os.pathsep)
            if folder.casefold() not in {x.casefold() for x in current}:
                os.environ['PATH']=os.pathsep.join([*current,folder])
            if row['tool']=='Godot':
                os.environ.setdefault('GODOT_EXECUTABLE',str(exe))
            self._log('Verified tool available to eligible fixed project checks. '
                      'Existing approved jobs can resume when their other prerequisites permit.')
        self._refresh_inventory()

    def _plan_tools(self):
        if self.inventory is None:
            messagebox.showinfo('Scan first','Click Scan this computer first.');return
        prompt=self.input.get('1.0','end').strip()
        if not prompt:prompt=simpledialog.askstring('What should DeepThorT build?','Describe a software or game project:',parent=self)
        if not prompt:return
        needs=plan_tool_needs(prompt,self.inventory)
        if not needs:
            messagebox.showinfo('No specific tools identified','No exact tool category could be inferred. Use Plan project for a staged review.');return
        summary='\n'.join(('Installed: ' if n['found'] else 'Missing: ')+n['name']+(' (can request installation)' if n['proposed_install'] else '') for n in needs)
        self._log('Project tool needs identified; routine catalog tools are managed during BUILD/EDIT submissions when enabled.')
        messagebox.showinfo('Project tool needs',summary+'\n\nSubmit a BUILD/EDIT job to manage recognised tools automatically when the routine policy is enabled. Unknown tools remain manual.')
    # -------- Verified, supervised local application capability acquisition --------
    def _available_learnable_tools(self):
        if not isinstance(self.inventory,dict):
            raise ValueError('Click Scan this computer first')
        return self.tool_learning.discover(self.inventory.get('tools',[]))

    def _select_learnable_tool(self):
        found=self._available_learnable_tools()
        if not found:
            raise ValueError('No supported command-line applications with verified executable paths found')
        names=[row['name'] for row in found]
        choice=simpledialog.askstring('Choose local application',
              'Available tools: '+', '.join(names)+'\n\nEnter a tool name exactly:',parent=self)
        if choice is None:return None
        name=next((n for n in names if n.casefold()==choice.strip().casefold()),None)
        if not name:
            raise ValueError('Select one of the listed, actually installed applications')
        return name

    def _investigate_tool(self):
        if not self.project:
            messagebox.showinfo('Project needed','Select the project in which this app will be used.',parent=self);return
        try:
            name=self._select_learnable_tool()
            if name is None:return
            evidence=self.tool_learning.probe_evidence(name,self.janus)
            if evidence:
                messagebox.showinfo(name+' local help (approved)',
                    evidence['excerpt'][:1900]+'\n\nThis describes the interface only; no task was tested.',parent=self)
                return
            cmd=self.tool_learning.probe_command(name)
            if self.disk_gate.gaming():
                raise ValueError('Gaming priority: defer running tool help until the game is closed')
            if not messagebox.askyesno('Approve local application investigation',
                    'Run the installed app with its bounded command-line help flag?\n\n'
                    'Project: '+str(self.project)+'\nCommand: '+subprocess.list2cmdline(cmd)+
                    '\n\nThis starts a real local application; help output is untrusted documentation. '
                    'No generated commands or project scripts will be run.\n\nApprove?',parent=self):return
            ident=self.tool_learning.authorize_probe(name,self.project,self.janus,user_approved=True)
            self._log(f'User approved {name} help discovery as JANUS action #{ident}.')
            self.tabs.select(5)
            self._show_janus_status()
        except (ValueError,OSError,PermissionError,WorkspaceError) as exc:
            messagebox.showwarning('Tool investigation unavailable',str(exc),parent=self)

    def _draft_tool_procedure(self):
        if not self.project or not self.current_chat:
            messagebox.showinfo('Project/chat needed','Select a project and chat first.',parent=self);return
        try:
            name=self._select_learnable_tool()
            if name is None:return
            evidence=self.tool_learning.probe_evidence(name,self.janus)
            if not evidence:
                raise ValueError('Run Investigate app and let JANUS finish the help probe first')
            goal=simpledialog.askstring('Learn a specific app capability',
                    f'Describe what {name} should do in this project. '
                    'DeepThorT will draft a candidate, NOT run it:',parent=self)
            if goal is None:return
            if not 5<=len(goal.strip())<=1000:
                raise ValueError('Provide a concrete task (5–1000 characters)')
            prompt=f'Learn to use {name} for: {goal.strip()}'
            ident=self.conversations.submit(self.current_chat,self._project_key(),
                                            'chat',prompt)
            self.tool_learning.start_learning(ident,name,self.project,goal)
            self._reload_chat()
            self.reply_outcome=None
            self._render_reply_notice()
            self._log(f'Tool learning request #{ident} queued for local ONNX; no tool has run.')
            self.tabs.select(0)
        except (ValueError,OSError,PermissionError) as exc:
            messagebox.showwarning('Cannot draft tool procedure',str(exc),parent=self)

    def _approve_learned_script(self, review: dict) -> bool:
        """Full, scrollable proposed SOURCE and diff, not a truncated yes/no box.

        This modal approves writing one workspace file, never running it.
        The separate command approval must happen on a later interaction.
        """
        dialog=tk.Toplevel(self)
        dialog.title('Review UNTRUSTED generated automation script — write only')
        dialog.transient(self)
        w=max(490,min(1020,self.winfo_screenwidth()-100))
        h=max(380,min(720,self.winfo_screenheight()-120))
        dialog.geometry(f'{w}x{h}')
        dialog.protocol('WM_DELETE_WINDOW',dialog.destroy)
        ttk.Label(dialog,text=f'PROJECT FILE: {review["path"]} — NOT YET APPROVED OR RUN',
                  wraplength=w-60).pack(anchor='w',padx=12,pady=(12,4))
        ttk.Label(dialog,text='Review the entire generated source, including imports and file operations. '
                  'An approved script may later execute with your user permissions. '
                  'This dialog only writes the file; it does not execute it.',
                  wraplength=w-60).pack(anchor='w',padx=12,pady=(0,8))
        body=ttk.Frame(dialog);body.pack(fill='both',expand=True,padx=12,pady=4)
        text=tk.Text(body,wrap='none',font=('Consolas',10),undo=False)
        y=ttk.Scrollbar(body,orient='vertical',command=text.yview)
        x=ttk.Scrollbar(body,orient='horizontal',command=text.xview)
        text.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        text.grid(row=0,column=0,sticky='nsew')
        y.grid(row=0,column=1,sticky='ns')
        x.grid(row=1,column=0,sticky='ew')
        body.grid_rowconfigure(0,weight=1);body.grid_columnconfigure(0,weight=1)
        warning='\n'.join('- '+w for w in review.get('risk_warnings',[]))
        text.insert('1.0','SCRIPT REVIEW — NOT SANDBOXED\n'+warning+
                    '\n\nCOMPLETE PROPOSED SOURCE\n'+review['source']+
                    '\n\nFILE CHANGE / BACKUP PREVIEW\n'+review['diff'])
        text.configure(state='disabled')
        approved=[False]
        buttons=ttk.Frame(dialog);buttons.pack(fill='x',padx=12,pady=12)
        def consent():
            approved[0]=True;dialog.destroy()
        ttk.Button(buttons,text='Cancel',command=dialog.destroy).pack(side='right')
        ttk.Button(buttons,text='Approve WRITE ONLY',command=consent).pack(side='right',padx=8)
        dialog._tooltip_handles = install_tooltips(dialog)
        dialog.grab_set()
        self.wait_window(dialog)
        return approved[0]

    def _run_learned_procedure(self):
        if not self.project:
            messagebox.showinfo('Project needed','Choose the project before running an app recipe.',parent=self);return
        try:
            rows=self.tool_learning.recipes(self.project)
            if not rows:
                raise ValueError('No tool recipe candidates. Investigate an app and Learn procedure first.')
            summary='\n'.join(f"#{r['id']} {r['name']}: {r['title']} [{r['status']}]" for r in rows[:14])
            ident=simpledialog.askinteger('Select learned procedure',
                  summary+'\n\nEnter the recipe ID to review / check:',parent=self,minvalue=1)
            if ident is None:return
            row=next((r for r in rows if r['id']==ident),None)
            if row is None:raise ValueError('Recipe ID not found in selected project')
            if row['action_id']:
                result=self.tool_learning.reconcile(ident,self.project,self.janus)
                if result['status'] in ('running_or_queued','artifact_produced','command_completed'):
                    messagebox.showinfo('Learned app result',result['status']+'\n'+result['evidence'],parent=self)
                    if result['status']=='running_or_queued':return
            if self.tool_learning.script_needs_review(ident,self.project):
                review=self.tool_learning.script_review(ident,self.project)
                if not self._approve_learned_script(review):
                    self._log(f'Generated script for recipe #{ident} NOT approved; no file or action changed.')
                    return
                dest=self.tool_learning.stage_script(ident,self.project,STATE/'backups',
                                                      user_approved=True,
                                                      expected_proposal_sha=review['proposal_sha'],
                                                      expected_existing_sha=review['existing_sha'])
                self._log(f'User approved the generated script file {dest.name} for recipe #{ident}; '
                          'command execution still requires separate approval.')
                messagebox.showinfo('Script staged — NOT executed',
                     f'Approved source saved to {dest}.\n\n'
                     'No application has run. Inspect the saved script, then choose '
                     'Run learned procedure… again to review and authorize its command.',parent=self)
                return
            if self.disk_gate.gaming():
                raise ValueError('Gaming priority: do not run this application while a game is active')
            input_file=''
            if '{{input}}' in row['args_json']:
                input_file=simpledialog.askstring('Select recipe input',
                       'Enter the relative path of an existing input file in the project:',parent=self)
                if not input_file:return
            preview=self.tool_learning.preview_recipe(ident,self.project,input_file=input_file)
            if not messagebox.askyesno('Approve exact learned command',
                f"UNVERIFIED model-proposed recipe #{ident}: {preview['title']}\n\n"
                f"Purpose: {preview['purpose']}\n\n"
                f"Project: {self.project}\n\nCommand:\n"
                +subprocess.list2cmdline(preview['argv'])[:2500]+
                f"\n\nExpected output: {preview['artifact'] or '(none; informational only)'}\n\n"
                'This executes a REAL application with the exact command shown. '
                'Project scripts could modify files. No shell is used. '
                'Only approve code and projects you trust.\n\nAPPROVE?',parent=self):return
            action=self.tool_learning.authorize_recipe(ident,self.project,self.janus,
                             user_approved=True,input_file=input_file,
                             expected_argv=preview['argv'])
            self._log(f'Approved learned recipe #{ident} as JANUS process #{action}; output is not yet verified.')
            self.tabs.select(5)
            self._show_janus_status()
        except (ValueError,OSError,PermissionError,WorkspaceError) as exc:
            messagebox.showwarning('Cannot run learned procedure',str(exc),parent=self)

    def _open_user_guide(self):
        """Open shipped documentation locally; never fetch a remote help page."""
        guide = ROOT / 'USER_GUIDE.html'
        if not guide.is_file():
            messagebox.showwarning('Guide missing',
                'USER_GUIDE.html is missing from the DeepThorT installation. '
                'Re-extract the full release ZIP without deleting your state.',parent=self)
            return
        try:
            if not webbrowser.open(guide.resolve().as_uri()):
                messagebox.showinfo('Open user guide',
                    'Open this local file in your browser:\n'+str(guide),parent=self)
        except (OSError,ValueError) as exc:
            messagebox.showerror('Guide unavailable',str(exc),parent=self)

    def _find_official_tool_page(self):
        """Vendor information only. Never silently download, run or install."""
        name=self.install_choice.get()
        source=official_source(name)
        if source is None:
            messagebox.showinfo('Source unavailable',
                'No reviewed official download source for that catalog selection.',parent=self)
            return
        if not messagebox.askyesno('Open official software page',
            f'Software: {name}\nPublisher: {source["publisher"]}\n'
            f'Official page: {source["url"]}\n\n'
            'This opens your browser on an external website. No file will be '
            'downloaded or executed by DeepThorT. Installations still require '
            'separate approval.\n\nOpen this page?',parent=self):
            return
        webbrowser.open(source['url'])
        self._log(f'User opened official vendor page for {name}; no install was initiated.')

    def _search_online_tools(self):
        """Consent-gated, read-only search: results are not approved installers."""
        if self.disk_gate.gaming():
            messagebox.showwarning('Gaming priority',
                'A configured game is running. Online package search is deferred.',parent=self)
            return
        name=simpledialog.askstring('Search for installed-tool alternatives',
            'Enter a software name or capability to search in the Windows Package Manager catalog:',
            parent=self)
        if name is None:
            return
        try:
            cmd=winget_search_command(name)
        except (ValueError,OSError) as exc:
            messagebox.showwarning('Cannot search packages',str(exc),parent=self)
            return
        if not (DeepThorTDesktop._routine_tools_enabled(self) or messagebox.askyesno('Approve online software search',
            'This queries the Windows Package Manager community catalog over the internet.\n'
            'It may contact the catalog provider and accept its source agreements.\n\n'
            'Query: '+name.strip()+'\nSource: winget\nMaximum results: 20\n\n'
            'No software is downloaded or installed. Search results are untrusted '
            'information; installing any package requires a separate reviewed action.\n\n'
            'Approve this exact network search?',parent=self)):
            self._log('Online package search was declined by user.')
            return
        if self._start_command(cmd,cwd=ROOT,label='Online winget search',kind='tool'):
            self._log('Approved read-only online package search: '+name.strip())
            self.tabs.select(4)

    def _inspect_package_id(self):
        """Request explicit consent for a *single* read-only winget show probe."""
        if self.disk_gate.gaming():
            messagebox.showwarning('Gaming priority',
                'A configured game is running. Package inspection is deferred.',parent=self)
            return
        if self._pending_package_inspection or isinstance(self._pending_reviewed_install,dict):
            messagebox.showinfo('Software review in progress',
                'Finish the previous inspection or installation before trying again.',parent=self)
            return
        package_id=simpledialog.askstring('Inspect an exact WinGet package',
            'Enter an exact package ID from search results, for example FreeCAD.FreeCAD:\n'
            'This only reads catalog metadata. It does not download or install.',parent=self)
        if package_id is None:return
        try:
            package_id=validate_package_id(package_id.strip())
            cmd=winget_show_command(package_id)
        except (ValueError,OSError) as exc:
            messagebox.showwarning('Invalid package ID',str(exc),parent=self)
            return
        if not (DeepThorTDesktop._routine_tools_enabled(self) or messagebox.askyesno('Approve exact package inspection',
            f'Package ID: {package_id}\nCatalog: winget\nCommand:\n'
            f'{subprocess.list2cmdline(cmd)}\n\n'
            'This contacts the Windows Package Manager catalog over the internet '
            'to retrieve untrusted package metadata. The result is saved as an '
            'inspection receipt, NOT approval to download or install.\n\n'
            'Approve this one read-only query?',parent=self)):
            self._log('Exact-package metadata inspection declined.')
            return
        # Set before the thread starts: prevents interleaved inspection results.
        self._pending_package_inspection={'package_id':package_id,'argv':list(cmd)}
        if not self._start_command(cmd,cwd=ROOT,
                                   label='Inspect package '+package_id,kind='package_inspection'):
            self._pending_package_inspection=None
            return
        self._log('Read-only inspection approved for exact winget ID '+package_id)
        self.tabs.select(4)

    def _receive_package_inspection(self, code, output):
        """Reconcile one completed bounded CLI report; NEVER grant install rights."""
        pending=self._pending_package_inspection
        self._pending_package_inspection=None
        if not pending:
            self._log('Unmatched package inspection result ignored.')
            return
        try:
            if not isinstance(output,dict) or output.get('truncated'):
                raise ValueError('Package inspection output missing or exceeded safety budget')
            if output.get('argv')!=pending['argv']:
                raise ValueError('Package inspection command does not match approval')
            receipt=inspect_show_output(pending['package_id'],
                '\n'.join(output.get('lines') or []),exit_code=code)
            self.last_package_inspection=receipt
            saved=save_snapshot(STATE/'last-package-inspection.json',receipt)
            self._log('Read-only package inspection accepted for '+receipt['package_id']+
                      ' — claimed publisher '+receipt['publisher']+', version '+receipt['version']+
                      ('. Receipt saved.' if saved else '. Receipt could not be saved.'))
            record(STATE,'desktop','read_only_winget_inspection',
                   id=receipt['package_id'],version=receipt['version'],
                   output_sha256=receipt['output_sha256'],saved=saved)
            messagebox.showinfo('Unverified WinGet package details',
                format_inspection(receipt),parent=self)
        except (ValueError,TypeError,OSError) as exc:
            self.last_package_inspection=None
            save_snapshot(STATE/'last-package-inspection.json',
                {'schema':'deepthort-winget-show-inspection-v1',
                 'package_id':pending['package_id'],
                 'state':'inconclusive','install_authorized':False,
                 'download_authorized':False,'reason':str(exc)[:240]})
            self._log('Package inspection was not accepted: '+str(exc))
            messagebox.showwarning('Package inspection inconclusive',
                str(exc)+'\n\nReview the Processes log. No package was downloaded or installed.',parent=self)

    def _windows_reviewed_install_enabled(self):
        return os.name=='nt'

    def _approve_inspected_install(self):
        """Separate explicit approval for one exact-version community catalog install.

        No local ONNX/LLM model text can authorize this action. The inspection
        must come from the current desktop session and remain fresh. This does
        not independently authenticate a publisher or attest the installer.
        """
        if not self._windows_reviewed_install_enabled():
            messagebox.showwarning('Windows required',
                'Reviewed WinGet installations are available only on Windows.',parent=self)
            return
        if self.disk_gate.gaming():
            messagebox.showwarning('Gaming priority',
                'A configured game is running. Installation is deferred.',parent=self)
            return
        if self._pending_package_inspection or self._pending_reviewed_install:
            messagebox.showwarning('Review already in progress',
                'Finish the current inspection or installation before trying again.',parent=self)
            return
        if ((self.install_process and self.install_process.poll() is None) or
            (self.tool_process and self.tool_process.poll() is None)):
            messagebox.showwarning('Tool already running',
                'Stop or finish the current tool operation before installation.',parent=self)
            return
        if not self.last_package_inspection:
            messagebox.showinfo('Inspect first',
                'Use Inspect package ID… to obtain a fresh, exact-ID report in this session. '
                'Saved receipts are informational and cannot approve execution.',parent=self)
            return
        try:
            plan=prepare_reviewed_install(self.last_package_inspection,
                   standing_policy=DeepThorTDesktop._routine_tools_enabled(self))
            if shutil.disk_usage(ROOT).free < 1024**3:
                raise ValueError('Less than 1 GiB disk space available; installation is blocked')
        except (OSError,ValueError) as exc:
            messagebox.showwarning('Installation review unavailable',str(exc),parent=self)
            return
        command=subprocess.list2cmdline(plan['argv'])
        details=(f"Program: {plan['name']}\nExact WinGet ID: {plan['package_id']}\n"
                 f"Version PIN: {plan['version']}\nClaimed publisher: {plan['claimed_publisher']}\n"
                 f"Claimed publisher page: {plan['publisher_url']}\n"
                 f"Installer URL (catalog claim): {plan['installer_url']}\n"
                 f"Catalog installer SHA256: {plan['manifest_installer_sha256']}\n"
                 f"License: {plan['license'] or '(not supplied)'}\n"
                 f"License page: {plan['license_url'] or '(not supplied)'}\n\n"
                 f"Exact command:\n{command}\n\n"
                 'WARNING: Publisher, version, URL and SHA256 come from the community '
                 'catalog and have NOT been independently verified. This WILL download '
                 'and run a third-party installer, potentially requiring a Windows UAC '
                 'confirmation. It requests user scope but some packages may not support it. '
                 'WinGet checks its manifest hashes; this is not a malware sandbox. '
                 'By proceeding you agree that WinGet may accept the repository and '
                 'package license terms. No upgrade, force, hash bypass or model-created '
                 'shell command is permitted. There is no automatic rollback.\n\n'
                 'Have you checked the publisher, license and purpose yourself?')
        if not (DeepThorTDesktop._routine_tools_enabled(self) or
                messagebox.askyesno('Review an UNVERIFIED third-party installation',
                                    details,parent=self)):
            self._log('Inspected package installation review declined.')
            return
        if DeepThorTDesktop._routine_tools_enabled(self):
            # The user explicitly chose the exact package by ID, inspected its
            # metadata and clicked 'Install inspected package'. Their standing
            # preference authorizes this action; Windows UAC still governs elevation.
            consent=None
            authorization='explicit_install_click'
        else:
            phrase=exact_consent_phrase(plan)
            consent=simpledialog.askstring('Type exact installation approval',
                'To approve THIS ONE installation, type exactly:\n'+phrase+'\n\n'
                'Any other text cancels. No previous approval can be reused.',parent=self)
            if consent!=phrase:
                self._log('Reviewed installation declined: exact typed consent not provided.')
                messagebox.showinfo('Installation cancelled',
                    'No installer was started. The exact approval phrase did not match.',parent=self)
                return
            authorization='typed'
        try:
            audit=approval_receipt(plan,consent=consent,status='launch_requested',authorization=authorization)
            if not save_snapshot(STATE/'last-reviewed-install.json',audit):
                raise OSError('Could not persist the installation audit; no install started')
        except (OSError,ValueError) as exc:
            messagebox.showerror('Approval not recorded',str(exc),parent=self)
            return
        self._pending_reviewed_install={'plan':plan,'consent':consent,
                                        'authorization':authorization,
                                        'argv':list(plan['argv'])}
        if not self._start_command(list(plan['argv']),cwd=ROOT,
                                   label='Install inspected '+plan['package_id'],kind='reviewed_install'):
            self._complete_inspected_install(None)
            return
        self._log('Installation authorized by '+authorization+' for '+plan['package_id']+' '+plan['version']+
                  '. WinGet queued; success and publisher authenticity are NOT verified.')
        self.tabs.select(4)

    def _complete_inspected_install(self,exit_code):
        """Terminal audit; WinGet exit 0 is not independent install verification."""
        pending=self._pending_reviewed_install
        self._pending_reviewed_install=None
        if not pending:
            self._log('Unexpected inspected-install result: no matching active approval.')
            return
        status='completed_unverified' if exit_code==0 else 'failed'
        audit=approval_receipt(pending['plan'],consent=pending['consent'],status=status,
                               authorization=pending.get('authorization','typed'))
        audit['exit_code']=exit_code
        saved=save_snapshot(STATE/'last-reviewed-install.json',audit)
        self._log('Inspected package '+pending['plan']['package_id']+': '+status+
                  ('; audit saved.' if saved else '; audit persistence FAILED.'))
        if exit_code==0:
            self._refresh_inventory()
            messagebox.showinfo('WinGet exited successfully — verify software',
                'WinGet returned exit code 0. Independently verify the program is installed, '
                'trusted and functions before giving it a project task. No actual app '
                'capability check has been performed.',parent=self)

    def _approve_tool_install(self):
        name=self.install_choice.get()
        if name not in INSTALL_CATALOG:return
        if self.install_process and self.install_process.poll() is None:
            messagebox.showinfo('Installer busy','Another approved installation is already running.');return
        if self.disk_gate.gaming():
            messagebox.showwarning('Gaming priority','A configured game is running. Installation is deferred.');return
        try:cmd=winget_command(name)
        except (OSError,ValueError) as e:messagebox.showerror('Cannot install',str(e));return
        package,purpose=INSTALL_CATALOG[name]
        if not (DeepThorTDesktop._routine_tools_enabled(self) or messagebox.askyesno('Approve Windows software installation',
            f'Install program: {name}\nPurpose: {purpose}\nPackage ID: {package}\nSource: Windows Package Manager (winget)\n\n'
            f'Command:\n{" ".join(cmd)}\n\nThis downloads external software and may ask for Windows elevation. '
            'No model-generated shell command is accepted.\n\nDo you APPROVE this specific installation?',parent=self)):
            self._log(f'Installation of {name} declined by user.')
            return
        self.tabs.select(4)
        self._log(f'Approved installation of {name} via winget package ID {package}.')
        if self._start_command(cmd,cwd=ROOT,label=f'Install {name}',kind='installation'):
            self._manual_catalog_install=name
    def _run_project_check(self):
        if not self.project:
            messagebox.showinfo('Project needed','Choose a project folder before running local tools.');return
        if self.disk_gate.gaming():
            messagebox.showwarning('Gaming priority','A configured game is running. Project build/test I/O is deferred.');return
        choice=self.check_choice.get()
        if choice=='Git: status':cmd=['git','status','--short']
        elif choice=='Python: unit tests':cmd=[sys.executable,'-m','unittest','discover']
        elif choice=='Node.js: npm test':cmd=['npm.cmd','test'] if os.name=='nt' else ['npm','test']
        elif choice=='Godot: validate project':
            program=shutil.which('godot.exe') or shutil.which('godot')
            if not program:
                messagebox.showerror('Godot not on PATH','Select a Godot executable on PATH or install/enable it first.');return
            cmd=[program,'--headless','--path',str(self.project),'--editor','--quit']
        elif choice=='.NET: tests':cmd=['dotnet','test','--no-restore']
        elif choice=='Blender: version':
            program=shutil.which('blender.exe') or shutil.which('blender')
            if not program:messagebox.showerror('Blender not on PATH','Blender executable not found on PATH.');return
            cmd=[program,'--background','--version']
        else:return
        if not messagebox.askyesno('Approve local tool execution',
            f'Run the selected project check?\n\nProject: {self.project}\nCommand: {subprocess.list2cmdline(cmd)}\n\n'
            'This executes a local program. Tests or build scripts may themselves modify files. '
            'Only approve for a project you trust.',parent=self):return
        self.tabs.select(4)
        self._log('User-approved project tool check: '+subprocess.list2cmdline(cmd))
        try:
            action_id=self.janus.add_approved_action(argv=cmd,cwd=self.project,label=choice,
                                                       kind='verification',user_approved=True)
        except (OSError,ValueError,PermissionError) as exc:
            messagebox.showerror('Could not schedule JANUS check',str(exc),parent=self)
            return
        self._log(f'JANUS approved process #{action_id} queued. Sentinel monitors worker health; results are written to the JANUS tab.')
        self._show_janus_status()
    def _start_command(self,cmd,*,cwd,label,kind,job_id=None):
        if self.__dict__.get('_gui_test_active') is not None:
            self._log('Isolated GUI test owns the tool slot; deferred: '+label)
            return False
        if kind!='quiet_playtest' and self.__dict__.get('_quiet_test_active') is not None:
            self._log('A quiet headless test already owns the tool slot; deferred: '+label)
            return False
        if (self.install_process and self.install_process.poll() is None) or (self.tool_process and self.tool_process.poll() is None):
            messagebox.showwarning('Tool already running','Wait or stop the current tool process first.');return False
        def worker():
            try:
                from collections import deque
                captured=deque(maxlen=300)
                inspecting=(kind=='package_inspection')
                automatic=(kind=='automatic_software')
                output_bytes=0
                truncated=False
                # Do not conceal native WinGet/installer windows or Windows UAC
                # for standing-policy software actions. No runas/UAC bypass.
                flags=(quiet_creationflags() if kind=='quiet_playtest' else
                       getattr(subprocess,'CREATE_NO_WINDOW',0)
                       if os.name=='nt' and kind not in ('automatic_software','reviewed_install','installation') else 0)
                if kind=='quiet_playtest' and self._quiet_test_stopped:
                    self.events.put(('tool_end',label,kind,-1,job_id,
                                     {'argv':list(cmd),'lines':['Stopped before launch']}))
                    return
                verified_env=(isolated_verification_environment(list(cmd),STATE,job_id)
                              if kind=='verification' and job_id is not None else None)
                with subprocess.Popen(cmd,cwd=str(cwd),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                        text=True,encoding='utf-8',errors='replace',creationflags=flags,
                        shell=False,env=verified_env,
                        stdin=subprocess.DEVNULL if kind=='quiet_playtest' else None) as proc:
                    if kind=='quiet_playtest' and self._quiet_test_stopped:
                        proc.terminate()
                    if kind=='quiet_playtest' and not self._quiet_test_stopped:
                        def background_pressure():
                            sampler=WindowsPressureSampler()
                            guard=QuietPressureGuard()
                            while proc.poll() is None and not self._quiet_test_stopped:
                                time.sleep(3.0)
                                if proc.poll() is not None or self._quiet_test_stopped:
                                    break
                                game=self.disk_gate.gaming()
                                cpu,ram=sampler.read()
                                reason=guard.should_preempt(game_active=game,
                                                             cpu_busy_percent=cpu,
                                                             ram_available_percent=ram)
                                if reason:
                                    self._quiet_test_stop_reason=reason
                                    self._quiet_test_stopped=True
                                    self.events.put(('log','Quiet test preempted: '+reason))
                                    try:proc.terminate()
                                    except OSError:pass
                                    break
                        threading.Thread(target=background_pressure,daemon=True).start()
                    if kind in ('installation','reviewed_install','automatic_software'):self.install_process=proc
                    else:self.tool_process=proc
                    # Bounded network inspection and user-approved third-party setup.
                    # A timed-out installer may have launched child processes; its
                    # receipt remains UNVERIFIED and requires manual inspection.
                    max_runtime = PLAYTEST_SECONDS if kind=='quiet_playtest' else 90 if inspecting else 3600 if kind in ('reviewed_install','automatic_software') else 7200 if kind=='verification' else None
                    def on_timeout():
                        if proc.poll() is None:
                            if kind=='quiet_playtest':
                                self._quiet_test_stop_reason='Headless test exceeded 120-second runtime budget'
                                self._quiet_test_stopped=True
                            proc.kill()
                    timer=(threading.Timer(max_runtime,on_timeout)
                           if max_runtime is not None else None)
                    if timer:timer.start()
                    try:
                        if proc.stdout:
                            for line in proc.stdout:
                                if inspecting:
                                    output_bytes+=len(line.encode('utf-8',errors='replace'))
                                    if output_bytes>MAX_INSPECTION_BYTES or len(captured)>=300:
                                        truncated=True
                                        proc.kill()
                                        break
                                    captured.append(line.rstrip('\r\n'))
                                elif automatic:
                                    output_bytes+=len(line.encode('utf-8',errors='replace'))
                                    if output_bytes>2*1024*1024:
                                        truncated=True
                                        proc.kill()
                                        break
                                elif kind in ('verification','quiet_playtest'):
                                    output_bytes += len(line.encode('utf-8',errors='replace'))
                                    if kind=='quiet_playtest' and output_bytes>128*1024:
                                        truncated=True
                                        proc.kill()
                                        break
                                    captured.append(line.rstrip()[:2000])
                                self.events.put(('log',f'[{label}] {line.rstrip()[:2000]}'))
                        code=proc.wait()
                    finally:
                        if timer:timer.cancel()
                result=({'argv':list(cmd),'lines':list(captured),'truncated':truncated}
                        if kind in ('verification','package_inspection','quiet_playtest') else None)
                self.events.put(('tool_end',label,kind,code,job_id,result))
            except Exception as e:self.events.put(('tool_error',label,kind,str(e),job_id))
            finally:
                if kind in ('installation','reviewed_install','automatic_software'):self.install_process=None
                else:self.tool_process=None
        threading.Thread(target=worker,daemon=True).start()
        return True
    def _start_sentinel(self):
        # Running the desktop under the GUI-subsystem DeepThorT.exe is mandatory.
        # The child Sentinel and its JANUS worker inherit the SAME Windows Job Object.
        if os.name!='nt' or self._sentinel_started:
            return
        self._sentinel_started=True
        if not (os.environ.get('DEEPTHORT_UNCAPPED_TEST') is None):
            self._log('Sentinel disabled in explicitly marked test environment.')
            return
        cmd=[sys.executable,str(ROOT/'janus_sentinel.py'),
             '--sentinel',str(STATE/'sentinel.sqlite3'),
             '--janus',str(STATE/'janus.sqlite3'),
             '--jobs',str(STATE/'jobs.sqlite3'),
             '--games',str(ROOT/'game_executables.txt'),
             '--heartbeat',str(STATE/'desktop-heartbeat.json')]
        try:
            flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
            self.sentinel_process=subprocess.Popen(cmd,cwd=str(ROOT),
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                creationflags=flags,shell=False)
            self._log(f'JANUS Sentinel supervising the persistent execution worker (PID {self.sentinel_process.pid}).')
        except OSError as exc:
            self._log('JANUS Sentinel could not start: '+str(exc))
            self.sentinel.event('error',f'Failed to start Sentinel: {exc}')

    def _set_janus_paused(self, value):
        self.janus.set_paused(bool(value))
        self._log('JANUS '+('paused: new approved actions deferred' if value else 'resumed'))
        self._show_janus_status()

    def _cancel_janus_action(self):
        sel=self.janus_action_tree.selection()
        if not sel:return
        ident=int(self.janus_action_tree.item(sel[0],'values')[0])
        entry=self.janus.action(ident)
        if not entry or entry['status'] not in ('approved','running'):
            messagebox.showinfo('Already finished','Only approved or running processes can be cancelled.',parent=self);return
        if not messagebox.askyesno('Cancel JANUS process',
            f'Cancel process #{ident}: {entry["label"]}?\nIf already running, the worker will stop its process tree.',parent=self):return
        self.janus.cancel_action(ident)
        self._log(f'JANUS action #{ident} cancellation requested.')
        self._show_janus_status()

    def _set_janus_goal(self):
        current=self.janus.goal()
        goal=simpledialog.askstring('JANUS primary goal',
            'Describe the primary project objective JANUS must keep tracking.\n'
            'Clear the field to follow the current work queue instead.\n'
            'This does not authorize executing programs or modifying files.',
            initialvalue=current,parent=self)
        if goal is None:return
        try:self.janus.set_goal(goal)
        except ValueError as exc:
            messagebox.showerror('Invalid goal',str(exc),parent=self);return
        self._show_janus_status()

    def _inspect_janus_cores(self):
        """Inspect factual appraisals, not a fabricated model thought transcript."""
        try:
            main=json.loads(self.janus.status().get('cores_json') or '{}')
            watch=json.loads(self.sentinel.snapshot().get('society_json') or '{}')
        except (ValueError,TypeError) as exc:
            messagebox.showerror('Could not read cores',str(exc),parent=self);return
        dialogue=tk.Toplevel(self)
        dialogue.title('JANUS & Sentinel — 22 outer / 154 inner faculties')
        dialogue.geometry('960x740');dialogue.configure(bg=BG)
        out=self._text(dialogue,readonly=True,height=34,font=('Consolas',9))
        out.pack(fill='both',expand=True,padx=10,pady=10)
        payload={'JANUS':main,'SENTINEL':watch.get('cores',{}),
                 'Explanation':'Recorded appraisals and observations, not private neural chain-of-thought'}
        self._show(out,json.dumps(payload,indent=2,ensure_ascii=False)[:250000])

    def _show_janus_status(self):
        try:
            status=self.janus.status();watch=self.sentinel.snapshot()
            counts=self.jobs.count(self._project_key())
            actions=self.janus.actions(limit=60)
            main_core=json.loads(status.get('cores_json') or '{}')
            watch_core=json.loads(watch.get('society_json') or '{}')
            main_front=main_core.get('Front',{})
            watch_front=(watch_core.get('cores') or {}).get('Front',{})
            text=(f'JANUS: {"PAUSED" if status["paused"] else "ACTIVE"} | 11 cores × 7 faculties | Cycle {status["cycle"]}\n'
                  f'Primary goal: {self.janus.goal() or main_front.get("goal") or "No goal set"}\n'
                  f'Front focus: {status["last_focus"]} | Intention: {status["last_action"]}\n'
                  f'Front posture: {main_front.get("posture","(no cycles)")}\n'
                  f'SENTINEL: {watch["state"]} | 11 cores × 7 faculties | Cycle {watch.get("cycle",0)}\n'
                  f'Supervisor focus: {watch_front.get("focus", "startup")} | {watch["detail"]}\n'
                  f'Sentinel PID: {watch["sentinel_pid"] or "none"} | JANUS PID: {watch["janus_pid"] or "none"} | Restarts: {watch["restart_count"]}\n'
                  f'Work queue: {counts}\n'
                  'Both use retained observations and separate Front states. Local Qwen may propose corrections; proposals cannot execute themselves.\n'
                  'Only explicitly approved tools/file changes run. Watchdog never duplicates execution.')
            self._show(self.janus_status_text,text)
            for k in self.janus_action_tree.get_children():self.janus_action_tree.delete(k)
            for a in actions:
                self.janus_action_tree.insert('','end',values=(a['id'],a['status'],a['kind'],a['label']))
            lines=['JANUS PROPOSED REPAIRS (advisory, not executed):']
            for item in self.janus.recommendations(limit=5):
                lines.append(f"{item['origin']}: {item['problem'][:180]} -> {item['proposal'][:550]}")
            lines.append('')
            lines.append('SENTINEL OVERSIGHT RECOMMENDATIONS:')
            for item in self.sentinel.recommendations(limit=5):
                lines.append(f"{item['origin']}: {item['finding'][:180]} -> {item['proposal'][:550]}")
            lines.extend(['','SENTINEL EVENTS:'])
            lines.extend(f"[{x['stamp']}] {x['level'].upper()} {x['description']}" for x in self.sentinel.events(limit=14))
            lines.extend(['','JANUS EVENTS:'])
            lines.extend(f"[{x['stamp']}] {x['message']}" for x in self.janus.events(limit=14))
            lines.extend(['','RECENT FOCUS:'])
            lines.extend(f"[{x['stamp']}] cycle {x['cycle']}: {x['focus']} -> {x['decision']}" for x in self.janus.history(limit=8))
            self._show(self.janus_events_text,'\n'.join(lines))
        except Exception as exc:
            self._log(f'JANUS/Sentinel status refresh problem: {exc}')

    def _refresh_janus_view(self):
        if not self.winfo_exists():return
        self._show_janus_status()
        # Notify once per newly observed finding; no modal popups during games.
        try:
            main=self.janus.recommendations(limit=1)
            sent=self.sentinel.recommendations(limit=1)
            changed=((main and main[0]['id']>self.last_janus_advice_id) or
                     (sent and sent[0]['id']>self.last_sentinel_advice_id))
            if main:self.last_janus_advice_id=max(self.last_janus_advice_id,main[0]['id'])
            if sent:self.last_sentinel_advice_id=max(self.last_sentinel_advice_id,sent[0]['id'])
            if changed:
                self.status.set('JANUS or Sentinel needs your attention. Review proposed repairs in JANUS & Sentinel.')
                self._log('JANUS/Sentinel recorded an evidence-based issue or proposed alternative; review required.')
        except Exception as exc:self._log(f'JANUS recommendation check failed: {exc}')
        self.after(5000,self._refresh_janus_view)

    def _write_desktop_heartbeat(self):
        data={'stamp':datetime.now().isoformat(timespec='seconds'),
              'pid':os.getpid(),'model_pid':self.node.pid if self.node and self.node.poll() is None else None,
              'model_loading':bool(self.node_loading),
              'model_loading_seconds':max(0,int(time.monotonic()-self.node_started)) if self.node_loading and self.node_started else 0,
              'model_ready':bool(self.node_ready),
              'active_job_id':self.active_job,'queue_paused':self.queue_paused}
        try:
            path=STATE/'desktop-heartbeat.json'
            temp=STATE/'desktop-heartbeat.tmp'
            temp.write_text(json.dumps(data),encoding='utf-8')
            os.replace(temp,path)
        except OSError:
            pass

    def _cancel_tool(self):
        procs=[p for p in (self.tool_process,self.install_process,self.media_process) if p and p.poll() is None]
        if not procs:return
        if messagebox.askyesno('Stop process','Stop the running tool or installation? Partial changes from an installer cannot be automatically rolled back.',parent=self):
            if (self._auto_verification_in_flight is not None and
                self.tool_process in procs):
                self._stopped_auto_tests.add(self._auto_verification_in_flight)
            if self._quiet_test_active is not None and self.tool_process in procs:
                self._quiet_test_stopped=True
            for p in procs:p.terminate()
            self._log('User stopped external tool/installer process; no automatic repair will follow a stopped test.')

    @staticmethod
    def _is_local_diagnostic_request(text):
        # Explicit app-health phrases only; general questions still go to the model.
        text=text.casefold().strip()
        return bool(re.search(r'\bself[- ]?diagnos(?:is|e|tic|tics)\b',text)
            or (re.search(r'\bdiagnos(?:e|is|tic|tics)\b',text)
                and re.search(r'\b(?:deepthort|yourself|the app|the ai|this app|the model)\b',text)))

    def _set_connection_status(self, message):
        # Health updates must not replace an active reply notification.
        # On idle, this is the original v10.9 connection-status text.
        self._model_connection_message=str(message)
        if hasattr(self, 'chat_connection'):
            self._render_reply_notice()

    def _diagnose(self, prompt=None):
        info = inspect_local_setup(ROOT)
        running = bool(self.node and self.node.poll() is None)
        report = format_diagnostic(info, model_running=running, model_ready=self.node_ready,
                 model_loading=self.node_loading, loading_seconds=(max(0, int(time.monotonic()-self.node_started)) if self.node_loading and self.node_started else 0), queued=self.jobs.count(self._project_key()).get('queued',0)+sum(x['state']=='pending' for x in self.conversations.thread(self.current_chat)),
                 recent_logs=self.recent_ai_logs)
        try:
            j=self.janus.status();w=self.sentinel.snapshot()
            report+=('\n\nJANUS/SENTINEL CHECK\n'
                 +f'JANUS cycle: {j["cycle"]}; focus: {j["last_focus"]}; paused: {bool(j["paused"])}\n'
                 +f'Sentinel: {w["state"]}; {w["detail"]}\n'
                 +'This is local process telemetry, not a neural-model-generated answer.')
        except (OSError,ValueError) as exc:
            report+='\nJANUS/SENTINEL CHECK: diagnostic unavailable: '+str(exc)
        local_status=local_server_status(timeout=0.75)
        if isinstance(local_status,dict) and self.node_loading:
            report += ('\n\nONNX WORKER STATUS (direct localhost measurement)\n'
                + 'Phase: '+str(local_status.get('phase') or 'unknown')+'\n'
                + 'Stage: '+str(local_status.get('stage') or 'unknown')+'\n'
                + 'Time since model initialization began: '+str(local_status.get('loading_seconds',0))+'s\n'
                + 'Time since last actual model-stage event: '+str(local_status.get('seconds_since_progress',0))+'s\n'
                + ('CAUTION: no new model-stage event for over four minutes. The OS CPU/memory counters must be checked before deciding this is a stall.'
                   if local_status.get('stalled') else 'Model worker is running; readiness is not yet verified.')
                + ('\nWorker error: '+str(local_status['error']) if local_status.get('error') else ''))
        if isinstance(local_status,dict) and local_status.get('inference_busy'):
            report += ('\n\nACTIVE INFERENCE REQUEST (local telemetry)\n'
                 +f"Generation elapsed: {local_status.get('inference_elapsed_seconds',0)}s; "
                 +f"output limit: {local_status.get('inference_max_tokens','?')} tokens.\n"
                 +'This is an accepted local request, not yet a finished reply. '
                 +'At the 20% CPU limit it may take several minutes.')
        self.client.record_local_exchange(self.current_chat, prompt or 'Run local DeepThorT self-diagnosis', report)
        self._reload_chat()
        self._log('Local self-diagnosis requested; no model call or cloud connection used.')
        self.tabs.select(0)
        self.status.set('Local self-diagnosis shown in Chats. Resolve reported blockers to receive AI replies.')
        return report

    def _auto_start_if_installed(self):
        if self.node_ready or self.node_loading or self.installing or (self.node and self.node.poll() is None):
            return
        info = inspect_local_setup(ROOT)
        if info['ready_to_launch']:
            self._start_ai(automatic=True)
        else:
            self.model_status.set('AI: not installed / incomplete')
            self._set_connection_status('AI unavailable: click Install AI, or Diagnose AI for exact missing components.')
            self.status.set('Local AI is not installed completely; queued messages are preserved.')

    # ----------- model lifecycle + health / process tracking ------------
    def _install_ai(self):
        if self.installing:
            messagebox.showinfo('Install running','Installation is already running. See Processes.');return
        if self.node and self.node.poll() is None:
            messagebox.showinfo('AI active','Stop AI first.');return
        if self.disk_gate.gaming():
            messagebox.showwarning('Game active','Finish gaming before installation and downloading.');return
        if not shutil.which('node') or not (shutil.which('npm.cmd') or shutil.which('npm')):
            messagebox.showerror('Node.js missing','Install Node.js LTS from nodejs.org. The optional Visual Studio development tool installer is unnecessary.');return
        if not messagebox.askyesno('Approve local AI installation',
             'Install ONNX/Transformers.js dependencies and the Qwen2.5-Coder 1.5B model?\n\n'
             'This requires one-time external downloads of roughly 2 GB and will write to this app folder. '
             'Inference is offline afterwards. No cloud-model fallback.\n\nApprove installation?',parent=self):return
        self.installing=True;self.model_status.set('AI: installing…');self.tabs.select(4)
        def worker():
            try:
                flags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0
                npm='npm.cmd' if os.name=='nt' else 'npm'
                for cmd,label in (([npm,'install','--no-fund','--no-audit'],'ONNX dependencies'),
                                  ([sys.executable,str(ROOT/'download_model.py')],'ONNX model')):
                    self.events.put(('log','Installing '+label+'…'))
                    with subprocess.Popen(cmd,cwd=str(ROOT),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                            text=True,encoding='utf-8',errors='replace',creationflags=flags) as proc:
                        self.install_process=proc
                        if proc.stdout:
                            for line in proc.stdout:self.events.put(('log',line.rstrip()))
                        if proc.wait()!=0:raise RuntimeError(label+' failed; view Processes for details')
                self.events.put(('install_done',))
            except Exception as e:self.events.put(('install_error',str(e)))
            finally:self.install_process=None
        threading.Thread(target=worker,daemon=True).start()
    def _start_ai(self, automatic=False):
        if self.node and self.node.poll() is None:
            self._log('AI is already running.');return
        if local_server_status() is not None:
            self._set_connection_status('A local ONNX server is already running outside DeepThorT supervision; close it first.')
            if not automatic:
                messagebox.showerror('Uncapped model process',
                    'A local AI server is already present. Stop it before starting here. '
                    'DeepThorT refuses to connect to a server outside its supervised resource budget.')
            return
        model=ROOT/'models'/'onnx-community'/'Qwen2.5-Coder-1.5B-Instruct'/'onnx'/'model_q4.onnx'
        if not model.exists() or model.stat().st_size<1_700_000_000:
            self.model_status.set('AI: model missing')
            self._set_connection_status('AI model missing. Click Install AI; pending chat is preserved.')
            if not automatic:messagebox.showinfo('Install model','Model file missing or incomplete. Click Install AI.')
            return
        node=shutil.which('node')
        if not node or not (ROOT/'node_modules'/'@huggingface'/'transformers').is_dir():
            self.model_status.set('AI: runtime missing')
            self._set_connection_status('AI runtime missing. Click Install AI or Diagnose AI for details.')
            if not automatic:messagebox.showinfo('Install AI runtime','Node.js or ONNX dependencies missing. Click Install AI.')
            return
        try:
            if not automatic:
                self._unexpected_model_exits = 0
            self._explicit_model_stop = False
            kwargs={'creationflags':getattr(subprocess,'CREATE_NO_WINDOW',0)} if os.name=='nt' else {}
            self.node=subprocess.Popen([node,str(ROOT/'inference_server.mjs')],cwd=str(ROOT),
                    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1,**kwargs)
            self.node_ready=False;self.node_loading=True
            self._model_transport_waiting=False
            self.node_started=time.monotonic()
            self.recent_ai_logs=[]
            self.last_ai_error=''
            self.model_status.set('AI: loading…')
            self._set_connection_status('AI loading under 20% CPU cap. Conversations stay separate from approved jobs.')
            self._log('Starting offline ONNX model. CPU-only; loading may take time.')
            process=self.node
            def output():
                try:
                    for line in process.stdout:self.events.put(('log','[AI] '+line.rstrip()))
                except Exception as e:self.events.put(('log','AI log error: '+str(e)))
                self.events.put(('node_end',process.poll(),process.pid))
            threading.Thread(target=output,daemon=True).start()
        except Exception as e:
            self.last_ai_error=str(e)
            self.model_status.set('AI: startup failed')
            self._set_connection_status('AI startup failed; click Diagnose AI or open Processes.')
            self._log('Could not start local model: '+str(e))
            if not automatic:messagebox.showerror('Start AI failed',str(e))
    def _stop_ai(self):
        self._explicit_model_stop = True
        self._restart_cancelled_node_pid=None  # Explicit global stop overrides automatic reload.
        if self.active_conversation is not None:
            self.conversations.change(self.active_conversation,'pending',
                'Paused by user; will retry when local AI starts',allowed=('running',))
            self.active_conversation=None
        if self.active_job is not None:
            cycle=self.cycles.get(self.active_job)
            if cycle and cycle['phase']=='repairing':
                try:self.cycles.block(self.active_job,'User stopped local model during repair')
                except CycleError:pass
            self.jobs.change(self.active_job,'paused','Model stopped by user before result; resume this job when ready',allowed=('running',))
            self.active_job=None;self._refresh_jobs()
        if self.media_process and self.media_process.poll() is None:
            self.media_process.terminate()
        if self.node and self.node.poll() is None:self.node.terminate()
        self.node_ready=False;self.node_loading=False;self.node_started=0.0
        self.model_status.set('AI: stopped')
        self._set_connection_status('AI stopped. Start it to resume pending chat replies and approved jobs.')
        self._log('AI stopped; queued jobs and histories preserved.')
    def _poll_server(self):
        if self.node and self.node.poll() is not None:
            # The stdout-reader sends node_end with diagnostic text. Let that event
            # classify the exit; otherwise this poll can erase startup-failure state.
            pass
        elif self.node_loading:
            elapsed = max(0, int(time.monotonic()-self.node_started)) if self.node_started else 0
            self.model_status.set(f'AI: loading {elapsed//60}m {elapsed%60:02d}s')
            stage=(self.current_loading_stage or 'Waiting for local ONNX status')[:150]
            if elapsed >= 180:
                self._set_connection_status(
                    f'AI loading {elapsed//60}m {elapsed%60:02d}s — {stage}. '
                    'Check Processes and Diagnose AI for progress or a failure.')
            else:
                self._set_connection_status(
                    f'AI loading {elapsed//60}m {elapsed%60:02d}s — {stage}. '
                    'Chat requests are safely queued.')
        if self.node_ready and self.node and self.node.poll() is None:
            threading.Thread(target=lambda:self.events.put(('health_detail',local_server_status())),daemon=True).start()
        elif self.node_loading:
            threading.Thread(target=lambda:self.events.put(('health_detail',local_server_status())),daemon=True).start()
        self.after(3500,self._poll_server)
    def _process_snapshot(self):
        model_pid=self.node.pid if self.node and self.node.poll() is None else None
        tool=self.tool_process if self.tool_process and self.tool_process.poll() is None else None
        install=self.install_process if self.install_process and self.install_process.poll() is None else None
        active=self.jobs.get(self.active_job) if self.active_job is not None else None
        elapsed=int(time.monotonic()-self.active_started) if active else 0
        media=getattr(self,'media_process',None)
        loading_seconds = max(0, int(time.monotonic()-self.node_started)) if self.node_loading and self.node_started else 0
        self._write_desktop_heartbeat()
        try:
            sentinel_health=self.sentinel.snapshot()
            worker_pid=sentinel_health.get('janus_pid')
        except (OSError,ValueError):
            sentinel_health={};worker_pid=None
        measured=self.meter.read({'DeepThorT UI':os.getpid(),
            **({'Qwen inference':model_pid} if model_pid else {}),
            **({'JANUS Sentinel':self.sentinel_process.pid} if self.sentinel_process and self.sentinel_process.poll() is None else {}),
            **({'JANUS worker':worker_pid} if worker_pid else {}),
            **({'Build / tool':tool.pid} if tool else {}),
            **({'Installer':install.pid} if install else {}),
            **({'Image / vision':media.pid} if media and media.poll() is None else {})})
        if time.monotonic()-self._last_telemetry_at >= 60:
            self._last_telemetry_at=time.monotonic()
            summary=[{'name':x['name'],'pid':x['pid'],
                      'cpu_percent':round(x['system_cpu_percent'],2),
                      'resident_mib':round(x['working_set_bytes']/2**20,1),
                      'private_mib':round(x['private_bytes']/2**20,1)} for x in measured]
            record(STATE,'desktop','resource_status',model_pid=model_pid,
                   node_ready=self.node_ready,loading=self.node_loading,
                   loading_seconds=loading_seconds,active_job=self.active_job,
                   active_conversation=self.active_conversation,
                   queue_paused=self.queue_paused,
                   queued=self.jobs.count(self._project_key()).get('queued',0),
                   measured_processes=summary)
        actual='\n'.join(f"  {x['name']}: {x['system_cpu_percent']:.1f}% system CPU; "
                         f"{x['working_set_bytes']/2**20:.0f} MiB resident; "
                         f"{x['private_bytes']/2**20:.0f} MiB private" for x in measured)
        text=(f"Application PID: {os.getpid()}\n"
              f"Model server PID: {model_pid or 'not running'} | State: {'ready' if self.node_ready else 'loading' if self.node_loading else 'stopped'}"
              + (f' | Loading {loading_seconds//60}m {loading_seconds%60:02d}s' if self.node_loading else '') + '\n'
              f"Current approved job: {('#'+str(active['id'])+' '+active['mode']+' ('+str(elapsed)+'s elapsed)') if active else 'none'}\n"
              f"Local tool PID: {tool.pid if tool else 'none'} | Installer PID: {install.pid if install else 'none'} | Media PID: {media.pid if media and media.poll() is None else 'none'}\n"
              f"Queue: {'paused' if self.queue_paused else 'running if model ready'}; pending: {self.jobs.count(self._project_key()).get('queued',0)}\n"
              f"Supervision: 20% aggregate CPU cap, 20% RAM commit limit under DeepThorT.exe\n"
              f"Quiet Godot: {'running' if self._quiet_test_active else 'inactive'}; headless, dummy audio; low priority, no visual proof\n"
              f"Isolated GUI: {'running' if self._gui_test_active else 'inactive'}; separate desktop, project-owned window metadata only\n"
              f"GPU: CPU-only ONNX inference | Disk: game-aware cooperative gate, no strict 20% cap\n"
              f"Measured resource use (tracked PIDs only):\n{actual or '  Not available on this OS'}\n"
              f'Last actual ONNX stage: {(self.current_loading_stage or "none observed")[:200]}\n'
              'Inference output is only known at completion; no fictitious token progress.')
        gui_history=self.gui_tests.snapshot()['history']
        if gui_history:
            last=gui_history[-1]
            text+=(f"\nLATEST ISOLATED GUI TEST: {last['status']} — "
                   f"{last.get('executable_name','project program')}; {last.get('detail','')}\n")
            for win in last.get('windows',[])[:6]:
                text+=f"  Project window: {win.get('title','')[:100]} {win.get('bounds',[])}"+(
                    ' [not responding]\n' if win.get('hung') else '\n')
        active_health=self.last_server_health if isinstance(self.last_server_health,dict) else {}
        if active_health.get('inference_busy'):
            text += (f"\nLOCAL AI GENERATION: running "
                     f"{active_health.get('inference_elapsed_seconds',0)}s; "
                     f"maximum {active_health.get('inference_max_tokens') or '?'} output tokens. "
                     'Real token progress is unavailable until the model returns.\n')
        cycle_job=self.active_job or self._auto_verification_in_flight
        if cycle_job is not None:
            cycle=self.cycles.get(cycle_job)
            if cycle:
                text += (f"\nAUTONOMOUS DEVELOPMENT CYCLE — JOB #{cycle_job}: {cycle['phase']}\n"
                         f"  tests {cycle['tests']}/{MAX_TEST_ATTEMPTS}; "
                         f"repairs {cycle['repairs']}/{MAX_REPAIR_ATTEMPTS}; "
                         'observed attempts, not guaranteed progress\n')
        text+=f"\nActive conversation request: {self.active_conversation or 'none'} | Stage: {self.reply_stage or 'none'}\n"
        text+='\nJANUS Sentinel: '+str(sentinel_health.get('state','not started'))+(
            ' | '+str(sentinel_health.get('detail','')) if sentinel_health else '')+'\n'
        text+='JANUS worker PID: '+str(worker_pid or 'not running')+' | Sentinel PID: '+str(sentinel_health.get('sentinel_pid') or 'not running')+'\n'
        self._show(self.process_info,text)
        if self.active_job is not None:self._refresh_jobs()
        self.after(2200,self._process_snapshot)

    def _handle_events(self):
        for _ in range(100):
            try:event=self.events.get_nowait()
            except queue.Empty:break
            kind=event[0]
            if kind=='log':
                self._log(event[1])
                if event[1].startswith('[AI] '):
                    self.recent_ai_logs.append(event[1][5:])
                    self.recent_ai_logs=self.recent_ai_logs[-24:]
            elif kind=='inventory':
                self.inventory=event[1]
                try:
                    enrolled=self.tool_learning.discover(self.inventory.get('tools',[]))
                    record(STATE,'desktop','tools_discovered_for_learning',count=len(enrolled))
                except (ValueError,OSError) as exc:
                    self._log('Tool learning inventory unavailable: '+str(exc)[:180])
                summary=format_inventory(self.inventory)
                proof_notes=[]
                for tool in self.inventory.get('tools',[]):
                    result=self._tool_verification.get(tool['name'])
                    if result:
                        current=self._tool_verification.current(tool['name'])
                        status='version verified' if current else ('stale/changed' if result['status']=='version_verified' else result['status'].replace('_',' '))
                        proof_notes.append(f"  {tool['name']}: {status}"+
                            (f" — {result['version']}" if current else ''))
                if proof_notes:summary+='\n\nPost-install CLI checks (NOT playtesting):\n'+'\n'.join(proof_notes)
                self._show(self.machine_text,summary)
                (STATE/'computer-inventory.json').write_text(json.dumps(self.inventory,indent=2),encoding='utf-8')
                snapshot=summarize_inventory(self.inventory)
                save_snapshot(STATE/'last-engine-inventory.json',snapshot)
                record(STATE,'desktop','engine_inventory_snapshot',
                       tools_detected=snapshot.get('tools_detected',0),
                       project_engine=(snapshot.get('engine_preflight') or {}).get('engine','unknown'),
                       missing_count=len((snapshot.get('engine_preflight') or {}).get('missing_prerequisites',[])))
                found=sum(x['found'] for x in self.inventory['tools'])
                self._log(f'Local capability scan complete: {found} tools detected; {len(self.inventory["drives"])} fixed drives. No installs performed.')
                if self._auto_tool_waiting and self._autonomy_policy['enabled']:
                    pending=self._auto_tool_waiting[:]
                    self._auto_tool_waiting.clear()
                    for prompt, project in pending:
                        if str(self.project)==project:
                            self._autonomy_queue_request(prompt,project)
            elif kind=='tool_probe_done':
                self._tool_probe_finished(event[1])
            elif kind=='tool_probe_error':
                self._tool_probe_active=None
                self._log('Post-install version verification error for '+event[1]+': '+event[2])
            elif kind=='inventory_error':
                self._log('Computer scan problem: '+event[1]);self._show(self.machine_text,'Discovery error: '+event[1])
            elif kind=='x4_auto_report':
                self.x4_report=event[1]
                self._x4_report_project=str(self.project)
                snapshot=summarize_x4_report(self.x4_report,
                    game_dir=self.x4_game_dir,reference_dir=self.x4_reference_dir,project_dir=self.project)
                save_snapshot(STATE/'last-x4-inspection.json',snapshot)
                record(STATE,'desktop','x4_inspection_evidence',
                       ready=snapshot['ready_for_planning'], pe_macro=snapshot['pe_macro_verified'],
                       pe_slots=snapshot['pe_component_verified'],
                       candidates=snapshot['candidate_counts'],blocked=snapshot['blocked_reasons'])
                if self.x4_report.get('game_dir') and not self.x4_game_dir:
                    self.x4_game_dir=self.x4_report['game_dir'];self._save_x4_paths()
                if self.x4_report.get('reference_dir') and not self.x4_reference_dir:
                    self.x4_reference_dir=self.x4_report['reference_dir'];self._save_x4_paths()
                self._show(self.x4_source_info,format_x4_inspection(self.x4_report))
                self._log('X4 initial-request preflight: game '+
                          ('found' if self.x4_report['game_dir'] else 'not found')+
                          ', extracted references '+
                          ('verified' if self.x4_report['ready_for_planning'] else 'missing'))
            elif kind=='x4_preflight_needed':
                self._x4_preflight_needs_sources(event[1],event[2])
            elif kind=='x4_inspection_reply':
                self._conversation_reply(event[1],
                    'LOCAL X4 FILE INSPECTION (read-only, not model-generated):\n'+
                    format_x4_inspection(event[2]))
            elif kind=='x4_extract_checked':
                self._x4_preflight_extract_checked(event[1],event[2])
            elif kind=='x4_extract_check_error':
                self.conversations.change(event[1],'failed',
                    'X4 extraction verification failed: '+event[2],allowed=('waiting_sources',))
                self._reload_chat()
            elif kind=='x4_sources':
                self.x4_report=event[1]
                self._x4_report_project=str(self.project)
                snapshot=summarize_x4_report(self.x4_report,
                    game_dir=self.x4_game_dir,reference_dir=self.x4_reference_dir,project_dir=self.project)
                save_snapshot(STATE/'last-x4-inspection.json',snapshot)
                record(STATE,'desktop','x4_inspection_evidence',
                       ready=snapshot['ready_for_planning'], pe_macro=snapshot['pe_macro_verified'],
                       pe_slots=snapshot['pe_component_verified'],
                       candidates=snapshot['candidate_counts'],blocked=snapshot['blocked_reasons'])
                if self.x4_report.get('game_dir') and not self.x4_game_dir:
                    self.x4_game_dir=self.x4_report['game_dir'];self._save_x4_paths()
                self._show(self.x4_source_info,format_x4_inspection(self.x4_report))
                self._log('X4 source inspection: '+('reference candidates found' if self.x4_report['ready_for_planning'] else 'vanilla references not yet available'))
            elif kind=='x4_sources_error':
                self._show(self.x4_source_info,'X4 inspection failed: '+event[1])
                self._log('X4 inspection failed: '+event[1])
            elif kind=='files':
                if event[1]==self.project:
                    for x in self.files.get_children():self.files.delete(x)
                    visible=self.inspection_exclusions.filter(self.project,event[2])
                    for path in visible:self.files.insert('','end',text=path)
                    self._log(f'Project file inventory refreshed: {len(visible)} visible files; '
                              f'{len(self.inspection_exclusions.paths(self.project))} excluded from inspection.')
            elif kind=='conversation_stage':self._set_reply_stage(event[1],event[2])
            elif kind=='conversation_reply':self._conversation_reply(event[1],event[2])
            elif kind=='conversation_error':self._conversation_error(event[1],event[2])
            elif kind=='conversation_transport_lost':
                self._conversation_transport_lost(event[1],event[2],event[3])
            elif kind=='job_plan':self._job_plan(event[1],event[2])
            elif kind=='build_files_done':self._build_files_done(event[1])
            elif kind=='job_answer':self._job_answer(event[1],event[2])
            elif kind=='job_error':self._job_error(event[1],event[2])
            elif kind=='repair_answer':self._repair_answer(event[1],event[2],event[3])
            elif kind=='repair_error':self._repair_error(event[1],event[2])
            elif kind in ('health', 'health_detail'):
                detail=event[1] if kind=='health_detail' else None
                if isinstance(detail,dict):
                    self.last_server_health=detail
                    if self.active_conversation is not None:
                        self._render_reply_notice()
                is_ready=(bool(detail.get('ready')) if isinstance(detail,dict) else bool(event[1]))
                if isinstance(detail,dict) and not is_ready and self.node_loading:
                    stage=str(detail.get('stage') or 'Initializing local ONNX model')[:240]
                    self.current_loading_stage=stage
                    if stage!=self._last_health_stage:
                        self._last_health_stage=stage
                        self._log('ONNX startup stage: '+stage)
                    if detail.get('stalled'):
                        self._set_connection_status('ONNX has not reported a new stage for over four minutes. '
                          'This does not prove a crash; inspect CPU/RAM in Processes, or Stop AI and diagnose.')
                    if detail.get('phase')=='failed':
                        self.last_ai_error=str(detail.get('error') or 'ONNX worker failure')
                if is_ready and self.node and self.node.poll() is None and self._restart_cancelled_node_pid is None:
                    newly_ready=not self.node_ready
                    if newly_ready:
                        self._log('Local AI ready: 127.0.0.1:8765; offline.')
                    if not self._model_transport_waiting or not detail or not detail.get('inference_busy'):
                        self._model_transport_waiting=False
                        self.node_ready=True
                    self.node_loading=False;self.model_status.set('AI: ready')
                    if newly_ready:
                        record(STATE,'desktop','model_ready_event',model_pid=self.node.pid,health=detail or {})
                    if not (isinstance(detail,dict) and detail.get('inference_busy')):
                        self._set_connection_status('AI READY — chat replies run outside the execution queue. Jobs need plan approval.')
            elif kind=='node_end':
                exited_pid=event[2] if len(event)>2 else (self.node.pid if self.node else None)
                # An old process must never change the status of a newer server.
                if self.node and exited_pid is not None and exited_pid!=self.node.pid:
                    continue
                if self._restart_cancelled_node_pid is not None and exited_pid==self._restart_cancelled_node_pid:
                    self._restart_cancelled_node_pid=None
                    self.node=None
                    self.node_ready=False;self.node_loading=False;self.node_started=0.0
                    self.model_status.set('AI: restarting after reply cancellation')
                    self._set_connection_status('Reply stopped. Reloading local AI for other queued chats.')
                    self._log('Cancelled ONNX worker exited; starting a fresh supervised model for other chats.')
                    if not self._quitting:
                        self.after(350,lambda:self._start_ai(automatic=True))
                    continue
                was_loading=self.node_loading
                unexpected = (not was_loading and not self._explicit_model_stop
                              and not self._quitting)
                self._log('AI process exited. Exit status: '+str(event[1]))
                record(STATE,'desktop','onnx_supervised_process_exit',level='WARNING',
                       exit_code=event[1],unexpected=unexpected,
                       was_loading=was_loading,
                       note='HTTP ConnectionResetError alone cannot establish OOM or a Windows job kill')
                if was_loading:
                    self.last_ai_error='\n'.join(self.recent_ai_logs[-12:]) or f'Local inference process exited with code {event[1]}'
                self.node_ready=False;self.node_loading=False;self.node_started=0.0
                self.model_status.set('AI: STARTUP FAILED' if was_loading else 'AI: stopped')
                self._set_connection_status('AI failed to start. Click Diagnose AI to see the exact problem; queued messages were preserved.')
                if was_loading:
                    messagebox.showerror('DeepThorT local AI could not start',
                       'The local model exited before becoming ready. Your chat message is safely queued.\n\n'
                       +self.last_ai_error[-1100:]+'\n\nUse Diagnose AI / Processes for details.')
                if self.active_conversation is not None:
                    c=self.active_conversation
                    self.conversations.change(c,'pending','Model process exited; will retry when available',allowed=('running',))
                    self.active_conversation=None
                    self.reply_stage=''
                    self._reload_chat();self._render_reply_notice()
                if self.active_job is not None:
                    j=self.active_job
                    self.jobs.change(j,'paused','Model process exited during inference',allowed=('running',))
                    self.active_job=None;self._refresh_jobs()
                if unexpected:
                    self._unexpected_model_exits += 1
                    if self._unexpected_model_exits <= 2:
                        self._set_connection_status(
                            f'ONNX exited unexpectedly; supervised restart '
                            f'{self._unexpected_model_exits}/2 is scheduled. '
                            'Progress and completed passes remain saved.')
                        self._log('Unexpected local ONNX exit; attempting bounded, '
                                  'game-capped relaunch without changing the 40-pass budget.')
                        self.after(5000,lambda:self._start_ai(automatic=True)
                                   if not self._explicit_model_stop and not self._quitting else None)
                    else:
                        self._set_connection_status('Repeated ONNX exits: automatic restart stopped. '
                          'Inspect model, RAM/commit limit and Windows events; no result was fabricated.')
                        self._log('ONNX restarted twice but continued exiting; stopped automatically.')
            elif kind=='install_done':
                self.installing=False;self.model_status.set('AI: installed')
                self._log('Local AI installed. Starting the model now.')
                self._auto_start_if_installed()
                messagebox.showinfo('Installed','ONNX coding model installed. DeepThorT is starting the model automatically; your queued chat will resume when ready.')
            elif kind=='install_error':
                self.installing=False;self.model_status.set('AI: installation failed')
                self._log('Installation failed: '+event[1]);messagebox.showerror('Install failed',event[1])
            elif kind=='isolated_gui_done':
                result=event[1] if isinstance(event[1],dict) else {
                    'status':'launch_failed','detail':'Malformed worker result','windows':[]}
                receipt=self.gui_tests.finish(result)
                self._gui_test_active=None
                self._gui_test_stop.set()
                if receipt:
                    self._log('Isolated GUI: '+receipt['status']+'; '+receipt['detail']+
                              f"; {len(receipt.get('windows', []))} project windows observed. "
                              'No gameplay acceptance implied.')
                    self.status.set('Isolated GUI: '+receipt['status']+
                                    '; details in Processes and diagnostics.')
            elif kind=='tool_end':
                label,tooltype,code,job_id=event[1:5]
                verification_output=event[5] if len(event)>5 else None
                self._log(f'{label} ended, exit code {code}. '+
                          ('Checking untrusted package metadata (not installation authorization).'
                           if tooltype=='package_inspection' and code==0 else
                           'WinGet exited 0; installation and publisher are not independently verified.'
                           if tooltype=='reviewed_install' and code==0 else
                           'Succeeded.' if code==0 else 'Check output for failure.'))
                self.status.set(f'{label}: exit code {code} (see Processes log)')
                if tooltype=='quiet_playtest':
                    stopped=self._quiet_test_stopped
                    lines=(verification_output or {}).get('lines') if isinstance(verification_output,dict) else []
                    reason=self._quiet_test_stop_reason
                    receipt=self.quiet_tests.finish(code,lines=lines or [],
                        stopped=stopped and not reason,preempted=(reason if reason and
                        reason!='User stopped quiet test' else ''),
                        error='Excessive process output' if isinstance(verification_output,dict)
                        and verification_output.get('truncated') else '')
                    self._quiet_test_active=None
                    self._quiet_test_stopped=False
                    self._quiet_test_stop_reason=''
                    self._log('Quiet scene check '+(receipt['status'] if receipt else 'finished without receipt')+
                              '; headless engine result only, not verified visual gameplay.')
                if tooltype=='installation':
                    name=self._manual_catalog_install
                    self._manual_catalog_install=None
                    if code==0:
                        if name in INSTALL_CATALOG:
                            self._queue_catalog_verification(name,project=str(self.project or ''),
                                install_exit_code=code)
                        self._refresh_inventory()
                if tooltype=='reviewed_install':
                    pending=self._pending_reviewed_install
                    if code==0 and isinstance(pending,dict):
                        package_id=pending.get('plan',{}).get('package_id')
                        for name,(catalog_id,_purpose) in INSTALL_CATALOG.items():
                            if package_id==catalog_id:
                                self._queue_catalog_verification(name,
                                     project=str(self.project or ''),install_exit_code=code)
                                break
                    self._complete_inspected_install(code)
                if tooltype=='automatic_software':self._automatic_tool_finished(code)
                if tooltype=='package_inspection':
                    self._receive_package_inspection(code,verification_output)
                if tooltype=='x4_extraction' and code==0:
                    self._inspect_x4_sources()
                if tooltype=='x4_preflight_extraction' and job_id is not None:
                    self._x4_preflight_extract_finished(job_id,code)
                was_auto_verification=(tooltype=='verification' and job_id is not None
                                       and self._auto_verification_in_flight==job_id)
                if was_auto_verification:
                    self._auto_verification_in_flight=None
                if tooltype=='verification' and job_id is not None:
                    snapshot=None
                    check=None
                    if isinstance(verification_output,dict):
                        check=assess_verification(verification_output.get('argv') or [],
                                                  code,verification_output.get('lines') or [])
                    if code==0 and (check is None or check['accepted']):
                        try:
                            current_job=self.jobs.get(job_id)
                            if current_job is None:
                                raise ValueError('Approved job is missing')
                            snapshot=capture_verified_sources(
                                current_job['project'],self.jobs.steps(job_id))
                            if check is not None:
                                engine=audit_engine_project(current_job['project'],
                                                            self.jobs.steps(job_id))
                                snapshot=attach_verification(snapshot,check,
                                    verification_output['argv'],engine_report=engine)
                        except (OSError,ValueError) as exc:
                            self._log(f'Approved test exited 0 but source evidence was not captured: {exc}')
                    current_job=self.jobs.get(job_id)
                    outcome=(code==0 and snapshot is not None)
                    cycle_result=None
                    was_stopped=(was_auto_verification and job_id in self._stopped_auto_tests)
                    if was_auto_verification:
                        lease=self._graph_test_leases.pop(job_id,None)
                        if lease:
                            try:
                                self.graphs.finish_action(lease,job_id,
                                    'interrupted' if was_stopped else 'passed' if outcome else 'failed')
                                if not was_stopped and self.graphs.exists(job_id):
                                    self.graphs.test_finished(current_job,self.jobs.steps(job_id),
                                        bool(outcome),snapshot if outcome else None,
                                        check['assurance'] if check else '')
                            except (GraphError,OSError,ValueError) as exc:
                                self._log(f'Job #{job_id}: task graph test evidence incomplete: {exc}')
                                outcome=False
                    if was_stopped:
                        self._stopped_auto_tests.discard(job_id)
                        try:self.cycles.block(job_id,'User explicitly stopped the test; no automatic repair')
                        except CycleError:pass
                        outcome=False
                    elif was_auto_verification:
                        try:
                            cycle_result=self.cycles.finish_test(job_id,code,outcome,
                                (verification_output or {}).get('lines') or [],
                                reason=(check['reason'] if check and not check['accepted'] else ''))
                        except (CycleError,OSError,ValueError) as exc:
                            self._log(f'Job #{job_id}: durable test outcome was not recorded: {exc}')
                    if outcome and (not was_auto_verification or
                                    cycle_result and cycle_result['phase']=='verified'):
                        assurance=('; '+check['assurance'] if check is not None else '')
                        self.jobs.change(job_id,'complete',
                            f'Verified: test command exited 0 ({label}); source hashes captured{assurance}',
                            result=json.dumps(snapshot,sort_keys=True),allowed=('running',))
                    elif was_auto_verification and cycle_result and cycle_result['phase']=='repair_ready':
                        self.jobs.change(job_id,'waiting_repair',
                            f'Test {cycle_result["tests"]}/{MAX_TEST_ATTEMPTS} failed; '
                            'bounded local ONNX repair available (not yet executed)',
                            allowed=('running',))
                        self._log(f'Job #{job_id}: test failure recorded; next idle step may '
                                  'propose one bounded repair. See Work queue evidence.')
                    else:
                        failure=(check['reason'] if check is not None and not check['accepted'] else
                                 f'Build test failed with exit {code}; inspect Processes log and repair the project'
                                 if code else 'Test exited 0 but source snapshot failed; verify generated files and rerun the approved test')
                        self.jobs.change(job_id,'needs_input',failure,allowed=('running',))
                    job=self.jobs.get(job_id)
                    if job and str(job.get('approval_key') or '').startswith('milestone:'):
                        try:
                            root_id=int(job['approval_key'].split(':')[1])
                            root_req=self.conversations.get(root_id)
                            if root_req:
                                summary=self.hierarchies.reconcile_jobs(
                                    self.specifications,root_id,root_req['prompt'],self.jobs)
                                self._log(f'Milestone roadmap #{root_id}: '
                                          f'{summary["milestones_verified"]}/{summary["milestones_total"]} '
                                          'milestones verified; no automatic approval of next milestone.')
                        except Exception as exc:
                            self._log(f'Milestone verification reconciliation needs attention: {exc}')
                    self._refresh_jobs()
                if code!=0 and tooltype not in ('package_inspection','automatic_software','quiet_playtest'):
                    if was_auto_verification:
                        self._log(f'Unattended job #{job_id} test returned a failure; inspect the '
                                  'durable cycle record for a bounded repair or manual blocker.')
                    else:
                        messagebox.showwarning('Tool reported failure',f'{label} failed, exit code {code}. See Processes log.')
            elif kind=='tool_error':
                was_auto_error=(len(event)>4 and event[4] is not None and
                                event[4]==self._auto_verification_in_flight and
                                event[2]=='verification')
                if was_auto_error:
                    self._auto_verification_in_flight=None
                    lease=self._graph_test_leases.pop(event[4],None)
                    if lease:
                        try:self.graphs.finish_action(lease,event[4],'interrupted')
                        except GraphError:pass
                    self._stopped_auto_tests.discard(event[4])
                    try:self.cycles.block(event[4],
                        'Test process failed to launch: '+str(event[3])[:250])
                    except CycleError:pass
                if event[2]=='quiet_playtest':
                    self.quiet_tests.finish(None,error=str(event[3]),
                                          stopped=self._quiet_test_stopped)
                    self._quiet_test_active=None
                    self._quiet_test_stopped=False
                    self._quiet_test_stop_reason=''
                self._log(f'{event[1]} error: {event[3]}')
                if event[2]=='reviewed_install':
                    self._complete_inspected_install(None)
                if event[2]=='automatic_software':
                    self._automatic_tool_finished(None)
                if event[2]=='package_inspection':
                    self._pending_package_inspection=None
                    self.last_package_inspection=None
                if event[2]=='x4_preflight_extraction' and len(event)>4 and event[4] is not None:
                    self.conversations.change(event[4],'failed',
                        'Could not launch approved X4 source extraction: '+str(event[3]),
                        allowed=('waiting_sources',))
                    self._reload_chat()
                if len(event)>4 and event[4] is not None:
                    self.jobs.change(event[4],'needs_input','Test process failed to launch: '+event[3],allowed=('running',))
                    self._refresh_jobs()
                if not was_auto_error and event[2]!='quiet_playtest':
                    messagebox.showerror('Tool error',event[3])
        self.after(125,self._handle_events)
    def _quit(self):
        self._quitting=True
        self._restart_cancelled_node_pid=None
        record(STATE,'desktop','desktop_shutdown',active_job=self.active_job,active_conversation=self.active_conversation)
        if self.active_conversation is not None:
            self.conversations.change(self.active_conversation,'pending',
                'Application closed; will retry when model is available',allowed=('running',))
        if self.active_job is not None:
            self.jobs.change(self.active_job,'paused','Application closed before reply; resume to retry',allowed=('running',))
        if self._gui_test_active is not None:
            self._gui_test_stop.set()
            self.gui_tests.interrupt_stale()
        if self._quiet_test_active is not None:
            self.quiet_tests.interrupt_stale()
        for proc in (self.node,self.tool_process,self.install_process,self.media_process,self.sentinel_process):
            if proc and proc.poll() is None:
                try:proc.terminate()
                except OSError:pass
        self.destroy()


if __name__=='__main__':
    if os.name!='nt':
        raise SystemExit('Run DeepThorT.exe on Windows, where resource-limit supervision is available.')
    try:DeepThorTDesktop().mainloop()
    except BaseException:
        detail=traceback.format_exc()
        try:
            STATE.mkdir(exist_ok=True)
            (STATE/'launch-error.txt').write_text(detail,encoding='utf-8')
            import ctypes
            ctypes.windll.user32.MessageBoxW(0,'DeepThorT encountered an error.\n\n'+detail[-1300:]+'\n\nSee state\\launch-error.txt',
                                         'DeepThorT startup error',0x10)
        except Exception:pass
        raise SystemExit(1)
