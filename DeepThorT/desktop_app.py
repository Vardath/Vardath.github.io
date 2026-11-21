"""DeepThorT desktop v9: offline coding workspace with visible, durable work.

This is a supervised local coding assistant, not a verified autonomous game builder.
No program is downloaded, installed, executed or project file modified without
specific human approval. All AI inference is local to 127.0.0.1.
"""
from __future__ import annotations

import json
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
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener

from deepthort_local.diagnostics import inspect_local_setup, format_diagnostic
from deepthort_local.client import LocalModelClient
from deepthort_local.chat_timeline import merged_chat_timeline
from deepthort_local.agent_plan import parse_build_plan, build_plan_prompt, build_budgeted_plan_prompt, budgeted_file_step_prompt, validate_project_plan, PlanError, project_kind
from deepthort_local.x4_sources import (inspect_x4_sources, automatic_x4_preflight, is_x4_inspection_request, x4_request_in_context,
                                      format_x4_inspection, x4_evidence_for_prompt,
                                        likely_installations, find_catalog_tool, catalog_extraction_command)
from deepthort_local.media_tools import (classify, validate_attachment, composed_prompt,
        validate_image_output_path, cli_image_args)
from deepthort_local.computer_inventory import (INSTALL_CATALOG, format_inventory,
        plan_tool_needs, scan_computer, winget_command)
from deepthort_local.disk_gate import DiskGate
from deepthort_local.job_queue import ChatRegistry, JobStore
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.flight_recorder import record, install_crash_hooks, export_diagnostics
from deepthort_local.process_metrics import Meter
from deepthort_local.janus_engine import JanusStore
from deepthort_local.watchdog import SentinelStore
from deepthort_local.tasks import TaskBoard
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
        record(STATE,'desktop','desktop_init',version='10.9.1',pid=os.getpid())
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
        self.media_process = None
        self.sentinel_process = None
        self._sentinel_started = False
        self.last_sentinel_log_id = 0
        self.last_janus_advice_id = 0
        self.last_sentinel_advice_id = 0
        self.active_job = None
        self.active_conversation = None
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
        self.image_photo = None
        self.auto_save_allowed = set()  # In-memory explicit consent per job, never assumed after restart.
        self.chat_ids = []
        self.current_chat = None
        self.inventory = None
        self.meter=Meter()
        self.client = LocalModelClient(STATE/'sessions.sqlite3')
        self.jobs = JobStore(STATE/'jobs.sqlite3')
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
        try:
            x4_settings=json.loads(self.x4_settings_file.read_text('utf-8'))
            if isinstance(x4_settings,dict):
                self.x4_game_dir=str(x4_settings.get('game_dir') or '')
                self.x4_reference_dir=str(x4_settings.get('reference_dir') or '')
                self.x4_catalog_tool=str(x4_settings.get('catalog_tool') or '')
        except (OSError, ValueError):pass
        self._theme()
        self._make_ui()
        self._restore_project()
        self._refresh_chats()
        self._refresh_jobs()
        self.after(125, self._handle_events)
        self.after(1000, self._scheduler)
        self.after(2200, self._poll_server)
        self.after(1000, self._poll_reply_notice)
        self.after(2000, self._process_snapshot)
        self.after(1500, self._auto_start_if_installed)
        self.after(700, self._start_sentinel)
        self.after(3000, self._refresh_janus_view)
        self.protocol('WM_DELETE_WINDOW',self._quit)
        self._log('Desktop opened. No cloud models or llama.cpp. App installers and external tool execution need approval.')
        self._log('Select a project and use Computer & Tools to inspect this machine. Auto-save happens only after specific consent.')
        self._refresh_inventory()

    def _theme(self):
        s=ttk.Style(self);s.theme_use('clam')
        s.configure('TFrame',background=BG)
        s.configure('Panel.TFrame',background=PANEL)
        s.configure('TLabel',background=BG,foreground=TEXT,font=('Segoe UI',10))
        s.configure('Muted.TLabel',background=BG,foreground=MUTED)
        s.configure('TButton',padding=(10,6),font=('Segoe UI',10),background='#243448',foreground=TEXT,borderwidth=0)
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
        ttk.Button(chatbar,text='Attach files…',command=self._add_attachments).pack(side='left',padx=5)
        ttk.Button(chatbar,text='Clear attachments',command=self._clear_attachments).pack(side='left',padx=5)
        self.attach_file=tk.BooleanVar(value=False)
        tk.Checkbutton(chatbar,text='Include selected project file',variable=self.attach_file,
                       bg=BG,fg=TEXT,selectcolor=PANEL,activebackground=BG,activeforeground=TEXT).pack(side='right')
        self.attachment_status=tk.StringVar(value='No attachments; text, DOCX, PDF and images supported')
        ttk.Label(chat,textvariable=self.attachment_status,style='Muted.TLabel').pack(anchor='w',pady=2)
        self.chat_connection=tk.StringVar(value="AI offline: use Start AI or Self-diagnose to check setup")
        tk.Label(chat,textvariable=self.chat_connection,bg=BG,fg=YELLOW,anchor="w").pack(fill="x",pady=(2,3))
        # A reply has its own lifecycle. Model health (AI: ready) must never
        # overwrite the visible waiting/generation/validation notification.
        self.reply_notice=tk.StringVar(value='No reply pending.')
        self.reply_banner=tk.Label(chat,textvariable=self.reply_notice,bg=PANEL,fg=YELLOW,
                         justify='left',anchor='w',wraplength=900,padx=9,pady=5)
        self.reply_banner.pack(fill='x',pady=(0,4))
        self.chat_tabs=ttk.Notebook(chat);self.chat_tabs.pack(fill='x',pady=4)
        self.chat_tabs.bind('<<NotebookTabChanged>>',self._chat_changed)
        self.chat_history=self._text(chat,readonly=True,height=13,font=('Segoe UI',10))
        self.chat_history.pack(fill='both',expand=True)
        for role,color in (('user',ACCENT),('assistant',GREEN),('warning',YELLOW)):
            self.chat_history.tag_configure(role,foreground=color)
        tk.Label(chat,text='PROMPT / SPECIFICATION — Ctrl+Enter sends chat; only approved plans enter the work queue',
                 bg=BG,fg=MUTED,font=('Segoe UI',9)).pack(anchor='w',pady=(7,3))
        self.input=self._text(chat,height=12,font=('Segoe UI',11));self.input.pack(fill='both',expand=False)
        self.input.bind('<Control-Return>',lambda e:self._send())
        ca=ttk.Frame(chat);ca.pack(fill='x',pady=7)
        chat_controls=ttk.Frame(ca);chat_controls.pack(fill='x',pady=(0,3))
        plan_controls=ttk.Frame(ca);plan_controls.pack(fill='x')
        ttk.Button(chat_controls,text='Send message',command=self._send).pack(side='left')
        ttk.Button(chat_controls,text='Diagnose AI',command=self._diagnose).pack(side='left',padx=5)
        ttk.Button(chat_controls,text='Retry failed reply',command=self._retry_conversation).pack(side='left',padx=5)
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
                      'Every file modification requires explicit approval; a backup is made first.')

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
        ttk.Label(action,text='Optional installation — always ask first:',style='Muted.TLabel').pack(side='left',padx=4)
        self.install_choice=tk.StringVar(value='Godot')
        self.install_menu=ttk.Combobox(action,textvariable=self.install_choice,values=sorted(INSTALL_CATALOG),state='readonly',width=20)
        self.install_menu.pack(side='left',padx=5)
        ttk.Button(action,text='Review & approve install…',command=self._approve_tool_install).pack(side='left',padx=3)
        checks=ttk.Frame(hardware_tab);checks.pack(fill='x',pady=(3,10))
        ttk.Label(checks,text='Approved local project checks:',style='Muted.TLabel').pack(side='left',padx=4)
        self.check_choice=tk.StringVar(value='Git: status')
        self.check_menu=ttk.Combobox(checks,textvariable=self.check_choice,state='readonly',width=24,
            values=('Git: status','Python: unit tests','Node.js: npm test','Godot: validate project','.NET: tests','Blender: version'))
        self.check_menu.pack(side='left',padx=4)
        ttk.Button(checks,text='Review & run…',command=self._run_project_check).pack(side='left',padx=3)
        tk.Label(hardware_tab,text='No background installs. Local program discovery does not grant execution permission.',
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
            state={'model_pid':self.node.pid if self.node and self.node.poll() is None else None,
                   'model_ready':self.node_ready,'model_loading':self.node_loading,
                   'model_status':status,'active_job':self.active_job,
                   'queue_paused':self.queue_paused,'visible_project_jobs':counts,
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
                paths=list_project_files(target)
                self.events.put(('files',target,paths))
            except Exception as e:self.events.put(('log','Project scan failed: '+str(e)))
        threading.Thread(target=worker,daemon=True).start()
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
            self.reply_notice.set(f'{prefix}{mode} #{active} IN PROGRESS — {stage} '
                                  f'| elapsed {elapsed//60}m {elapsed%60:02d}s. '
                                  'No executable job is queued until plan approval.')
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
            self.reply_notice.set('No reply pending. Model availability is shown above.')

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

    def _queue_input(self,mode):
        """Accept conversation requests, NEVER create executable jobs here."""
        prompt=self.input.get('1.0','end').strip()
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
        self._reload_chat()
        self.reply_outcome=None
        self._render_reply_notice()
        self.status.set(f'{"Draft plan" if kind=="draft_plan" else "Chat"} #{ident} saved. No job was queued.')
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
        if len(prompt)>MAX_INFERENCE_PROMPT:
            self.conversations.change(ident,'failed',
               f'This local model accepts at most {MAX_INFERENCE_PROMPT:,} characters per inference. '
               'Your full prompt is saved; divide it into shorter requests.',allowed=('pending',))
            self._reload_chat()
            messagebox.showwarning('Prompt saved but exceeds model context',
                'Your complete prompt was preserved in Chats, NOT the Work queue. '
                'Split it into smaller messages or revise the plan.')
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

    def _approve_conversation_plan(self):
        """The only GUI path that turns a draft into an executable build job."""
        draft=self.conversations.latest_draft(self.current_chat,self._project_key())
        if not draft:
            messagebox.showinfo('No draft plan',
                'Use Draft project plan first, discuss any uncertainties in Chats, then approve it.');return
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
            'No external installations or test commands are approved by this step.\n'
            'Individual generated file changes still require review.',parent=self):
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
        self._log(f'User explicitly approved draft #{draft["id"]}. Created job #{jobid} with {len(draft["steps"])} steps.')
        self._reload_chat();self._refresh_jobs();self.tabs.select(1)
        self.status.set(f'Approved plan became job #{jobid}; files require review.')

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
            try:
                original=request['prompt']
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
                self.events.put(('conversation_stage',ident,'Preparing the complete request and attachment context'))
                prompt=composed_prompt(original,paths)
                # X4 source inspection is part of the INITIAL request, never a
                # manual task delegated back to the user or an AI hallucination.
                prior=[r['prompt'] for r in self.conversations.thread(request['chat_id'],10)
                       if r['id']!=ident]
                x4_context=x4_request_in_context(original,project_dir=request['project'],
                                                  previous_prompts=prior)
                if x4_context:
                    self.events.put(('conversation_stage',ident,'Inspecting installed X4 files and verified vanilla XML'))
                    record(STATE,'desktop','x4_auto_preflight_started',request_id=ident,mode=request['mode'])
                    report=automatic_x4_preflight(
                        project_dir=request['project'],app_root=ROOT,game_dir=self.x4_game_dir,
                        reference_dir=self.x4_reference_dir,catalog_tool=self.x4_catalog_tool)
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
                    if request['mode']=='draft_plan':
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
                elif request['mode']=='draft_plan':
                    prompt=build_plan_prompt(prompt,self.inventory)
                if len(prompt)>MAX_INFERENCE_PROMPT:
                    raise ValueError(f'Model input of {len(prompt):,} characters exceeds {MAX_INFERENCE_PROMPT:,}; original is saved')
                session=request['chat_id'] if request['mode']=='chat' else 'planning-'+request['chat_id']
                self.events.put(('conversation_stage',ident,'Waiting for local model inference (response not yet returned)'))
                if request['mode']=='chat':
                    answer=self.client.chat(session,prompt,max_tokens=128,visible_prompt=request['prompt'])
                else:
                    answer=self.client.chat(session,prompt,max_tokens=640)
                self.events.put(('conversation_stage',ident,'Model finished; verifying reply and project requirements'))
                self.events.put(('conversation_reply',ident,answer))
            except Exception as exc:
                record(STATE,'desktop','conversation_worker_exception',level='ERROR',request_id=ident,
                       error_type=type(exc).__name__,stack=traceback.format_exc()[-12000:])
                self.events.put(('conversation_error',ident,str(exc)))
        threading.Thread(target=work,daemon=True,name=f'Conversation-{ident}').start()

    def _conversation_reply(self,ident,answer):
        req=self.conversations.get(ident)
        if not req or req['state']!='running':return
        self._set_reply_stage(ident,'Checking the response against the original requirements')
        outcome='REPLY RECEIVED — local model finished.'
        if req['mode']=='draft_plan':
            try:
                validated=parse_build_plan(answer,Path(req['project']),request=req['prompt'])
                draft_id=self.conversations.save_draft(ident,validated)
                self.conversations.change(ident,'responded',
                    f'Draft #{draft_id} ready; discuss, revise or explicitly approve it',
                    response=answer,allowed=('running',))
                outcome=f'DRAFT PLAN #{draft_id} READY — review and explicitly approve before any job runs.'
                self._log(f'Draft #{draft_id} generated in Chats; NO job queued.')
            except Exception as exc:
                # Preserve the failed model output as a separate local chat history
                # record. Salvage a *draft*, not a job, only with VERIFIED X4 sources.
                recovered=False
                if project_kind(req['prompt'])=='x4':
                    try:
                        report=self.x4_report or {}
                        if not report.get('ready_for_planning'):
                            report=automatic_x4_preflight(project_dir=req['project'],app_root=ROOT,
                                game_dir=self.x4_game_dir,reference_dir=self.x4_reference_dir,
                                catalog_tool=self.x4_catalog_tool)
                        from deepthort_local.agent_plan import source_grounded_pe_plan
                        fixed=source_grounded_pe_plan(req['prompt'],report)
                        rendered=json.dumps({'files':fixed},ensure_ascii=False)
                        validated=parse_build_plan(rendered,Path(req['project']),request=req['prompt'])
                        draft_id=self.conversations.save_draft(ident,validated)
                        self.conversations.change(ident,'responded',
                            f'Model proposal rejected; source-grounded fallback draft #{draft_id} prepared for approval',
                            response=rendered,allowed=('running',))
                        record(STATE,'desktop','x4_draft_salvaged',request_id=ident,
                               model_rejection=str(exc)[:320],draft_id=draft_id,
                               verified_pe=True)
                        self._log(f'Model plan rejected: {exc}; verified X4 draft #{draft_id} substituted. No job queued.')
                        outcome=(f'DRAFT PLAN #{draft_id} READY — local model output failed validation; '
                                 'verified-source fallback prepared. Review it before approval.')
                        recovered=True
                    except (ValueError, KeyError, TypeError, OSError) as recovery_error:
                        record(STATE,'desktop','x4_draft_salvage_blocked',request_id=ident,
                               reason=str(recovery_error)[:500])
                if not recovered:
                    self.conversations.change(ident,'failed','Invalid proposal: '+str(exc),
                        response=answer,allowed=('running',))
                    self._log(f'Planning requires revision: {exc}')
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

    def _conversation_error(self,ident,error):
        req=self.conversations.get(ident)
        if req and req['state']=='running':
            self.conversations.change(ident,'failed','Local model request failed: '+error[:500],
                                      allowed=('running',))
        self.active_conversation=None
        self.reply_stage=''
        self.reply_outcome={'chat_id':req['chat_id'] if req else self.current_chat,
             'message':f'REPLY FAILED — {str(error)[:180]}. Request preserved for retry.'}
        self._render_reply_notice()
        self._log(f'Conversation #{ident} failed: {error[:300]}')
        if req and req['chat_id']==self.current_chat:self._reload_chat()

    def _refresh_jobs(self):
        if not hasattr(self,'job_tree'):return
        for item in self.job_tree.get_children():self.job_tree.delete(item)
        project=self._project_key()
        rows=[j for j in self.jobs.items(project) if j['mode'] not in ('chat','plan','edit')]
        for j in rows:
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
        steps=self.jobs.steps(job['id'])
        step_text='\n'.join(f"{i+1}. [{x['state']}] {x['path']}: {x['description']}" for i,x in enumerate(steps)) or '(No plan yet)'
        detail=(f"Job #{job['id']} | {job['state']} | {job['mode']}\n"
                f"Created: {job['created_at']}\nProject: {job['project']}\nTarget: {job['target'] or '-'}\n"
                f"Message: {job['detail']}\n\nPLAN STEPS:\n{step_text}\n\nREQUEST:\n{job['prompt']}\n\nRESULT:\n{job['result']}\n\nEVENTS:\n{events}")
        self._show(self.job_details,detail)
    def _cancel_active(self):
        if self.active_job is None:return
        self._cancel_id(self.active_job)
    def _cancel_job(self):
        j=self._selected_job()
        if not j:return
        self._cancel_id(j['id'])
    def _cancel_id(self,ident):
        j=self.jobs.get(ident)
        if not j or j['state'] not in ('queued','running','paused','needs_input','waiting_approval'):
            return
        if j['state']=='running':
            if not messagebox.askyesno('Cancel local inference',
                     'Cancel this running job?\n\nThe ONNX server must be stopped to interrupt CPU inference; '
                     'you can click Start AI afterwards to continue other queued jobs.',parent=self):return
            self.jobs.cancel(ident)
            if self.media_process and self.media_process.poll() is None:
                self.media_process.terminate()
                self._log(f'Job #{ident}: stopped local media subprocess.')
            elif self.node and self.node.poll() is None:
                self.node.terminate()
                self.node_ready=False;self.node_loading=False
                self.model_status.set('AI: stopped after cancellation')
            self.active_job=None
            self._log(f'Job #{ident} cancelled; interrupted local inference.')
        else:
            self.jobs.cancel(ident);self._log(f'Job #{ident} cancelled.')
        self._refresh_jobs();self._job_selected()
    def _resume_job(self):
        j=self._selected_job()
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
                'This does not approve downloading/installing software or executing tools.',parent=self):return
        self.jobs.resume(j['id']);self._log(f"Build plan #{j['id']} approved. The queue will work on its first file.")
        self._refresh_jobs()

    def _verification_command(self,project):
        # Only deterministic local test entry points. No model-created shell commands.
        if (project/'project.godot').exists():
            godot=shutil.which('godot.exe') or shutil.which('godot')
            return ([godot,'--headless','--path',str(project),'--editor','--quit'] if godot else None)
        if (project/'package.json').exists(): return ['npm.cmd' if os.name=='nt' else 'npm','test']
        if (project/'pyproject.toml').exists() or (project/'tests').is_dir() or list(project.glob('test_*.py')):
            return [sys.executable,'-m','unittest','discover']
        if list(project.glob('*.sln')): return ['dotnet','test','--no-restore']
        return None

    def _verify_build(self):
        if any(p and p.poll() is None for p in (self.tool_process,self.install_process,self.media_process)):
            messagebox.showwarning('Tool already running',
                'A local tool, installation or media task is already running. Verification will remain queued for manual approval.');return
        j=self._selected_job()
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
        tool_busy=any(p and p.poll() is None for p in (self.tool_process,self.install_process,self.media_process))
        model_alive=bool(self.node and self.node.poll() is None)
        gate = ('paused' if self.queue_paused else
                'tool_busy' if tool_busy else
                'active_job' if self.active_job is not None else
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
            self._log(f'Job #{jobid}: {saved} file stages saved; NOT verified. Choose Verify build.')
            self.tabs.select(1)
            messagebox.showinfo('Build requires verification',f'Job #{jobid} saved {saved} proposed files.\n\n'
                'Source generation is NOT proof of a working app or game.\n'
                'Select the job in Work queue and click Verify build to run an approved test.')
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
                elif jobid in self.auto_save_allowed:
                    try:
                        dest=apply_approved_file(Path(j['project']),step['path'],code,STATE/'backups')
                        self.jobs.set_step(step['id'],'saved','Auto-save approved for this job; not yet tested')
                        self.jobs.change(jobid,'queued',f'Saved {step["path"]}; next stage queued',result=answer,allowed=('running',))
                        self._log(f'Job #{jobid}: saved {dest} under prior explicit project approval; backup created.')
                        self._refresh_files()
                    except Exception as e:
                        self.jobs.change(jobid,'needs_input','Cannot save proposed file: '+str(e),result=answer,allowed=('running',))
                else:
                    self.proposed=(step['path'],code);self.proposal_job=jobid;self.proposal_step=step['id']
                    self.jobs.set_step(step['id'],'proposed','Awaiting user file review')
                    self.jobs.change(jobid,'waiting_approval',f'Review proposed {step["path"]} ({len(self.jobs.steps(jobid))} planned files)',result=answer,allowed=('running',))
                    self.file_title.set('Proposed: '+step['path'])
                    self._preview('PROPOSED CODE — edit below before approving\n\n'+code)
                    self.tabs.select(2)
                    messagebox.showinfo('Build needs file review',f'Job #{jobid} proposed {step["path"]}. Review it and approve saving. The next stage will queue automatically.')
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
        self.status.set(f'Job #{jobid} finished. Review results in Chats or Work queue.')
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
        def worker():
            try:
                inventory=scan_computer(ROOT,path,include_gpu=not self.disk_gate.gaming())
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
        self._log('Project tool inventory checked; no software installed automatically.')
        messagebox.showinfo('Suggested local tools — advisory only',summary+'\n\nReview the Computer & Tools tab before approving any installation.')
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
        if not messagebox.askyesno('Approve Windows software installation',
            f'Install program: {name}\nPurpose: {purpose}\nPackage ID: {package}\nSource: Windows Package Manager (winget)\n\n'
            f'Command:\n{" ".join(cmd)}\n\nThis downloads external software and may ask for Windows elevation. '
            'No model-generated shell command is accepted.\n\nDo you APPROVE this specific installation?',parent=self):
            self._log(f'Installation of {name} declined by user.')
            return
        self.tabs.select(4)
        self._log(f'Approved installation of {name} via winget package ID {package}.')
        self._start_command(cmd,cwd=ROOT,label=f'Install {name}',kind='installation')
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
        if (self.install_process and self.install_process.poll() is None) or (self.tool_process and self.tool_process.poll() is None):
            messagebox.showwarning('Tool already running','Wait or stop the current tool process first.');return False
        def worker():
            try:
                flags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0
                with subprocess.Popen(cmd,cwd=str(cwd),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                        text=True,encoding='utf-8',errors='replace',creationflags=flags,shell=False) as proc:
                    if kind=='installation':self.install_process=proc
                    else:self.tool_process=proc
                    if proc.stdout:
                        for line in proc.stdout:
                            self.events.put(('log',f'[{label}] {line.rstrip()}'))
                    code=proc.wait()
                self.events.put(('tool_end',label,kind,code,job_id))
            except Exception as e:self.events.put(('tool_error',label,kind,str(e),job_id))
            finally:
                if kind=='installation':self.install_process=None
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
            for p in procs:p.terminate()
            self._log('User stopped external tool/installer process.')

    @staticmethod
    def _is_local_diagnostic_request(text):
        # Explicit app-health phrases only; general questions still go to the model.
        text=text.casefold().strip()
        return bool(re.search(r'\bself[- ]?diagnos(?:is|e|tic|tics)\b',text)
            or (re.search(r'\bdiagnos(?:e|is|tic|tics)\b',text)
                and re.search(r'\b(?:deepthort|yourself|the app|the ai|this app|the model)\b',text)))

    def _set_connection_status(self, message):
        if hasattr(self, 'chat_connection'):
            self.chat_connection.set(message)

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
            kwargs={'creationflags':getattr(subprocess,'CREATE_NO_WINDOW',0)} if os.name=='nt' else {}
            self.node=subprocess.Popen([node,str(ROOT/'inference_server.mjs')],cwd=str(ROOT),
                    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1,**kwargs)
            self.node_ready=False;self.node_loading=True
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
                self.events.put(('node_end',process.poll()))
            threading.Thread(target=output,daemon=True).start()
        except Exception as e:
            self.last_ai_error=str(e)
            self.model_status.set('AI: startup failed')
            self._set_connection_status('AI startup failed; click Diagnose AI or open Processes.')
            self._log('Could not start local model: '+str(e))
            if not automatic:messagebox.showerror('Start AI failed',str(e))
    def _stop_ai(self):
        if self.active_conversation is not None:
            self.conversations.change(self.active_conversation,'pending',
                'Paused by user; will retry when local AI starts',allowed=('running',))
            self.active_conversation=None
        if self.active_job is not None:
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
              f"Supervision: 20% CPU cap, 20% RAM commit limit, idle priority under DeepThorT.exe\n"
              f"GPU: CPU-only ONNX inference | Disk: game-aware cooperative gate, no strict 20% cap\n"
              f"Measured resource use (tracked PIDs only):\n{actual or '  Not available on this OS'}\n"
              f'Last actual ONNX stage: {(self.current_loading_stage or 'none observed')[:200]}\n'
              'Inference output is only known at completion; no fictitious token progress.')
        active_health=self.last_server_health if isinstance(self.last_server_health,dict) else {}
        if active_health.get('inference_busy'):
            text += (f"\nLOCAL AI GENERATION: running "
                     f"{active_health.get('inference_elapsed_seconds',0)}s; "
                     f"maximum {active_health.get('inference_max_tokens') or '?'} output tokens. "
                     'Real token progress is unavailable until the model returns.\n')
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
                self._show(self.machine_text,format_inventory(self.inventory))
                (STATE/'computer-inventory.json').write_text(json.dumps(self.inventory,indent=2),encoding='utf-8')
                found=sum(x['found'] for x in self.inventory['tools'])
                self._log(f'Local capability scan complete: {found} tools detected; {len(self.inventory["drives"])} fixed drives. No installs performed.')
            elif kind=='inventory_error':
                self._log('Computer scan problem: '+event[1]);self._show(self.machine_text,'Discovery error: '+event[1])
            elif kind=='x4_auto_report':
                self.x4_report=event[1]
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
                    for path in event[2]:self.files.insert('','end',text=path)
                    self._log(f'Project file inventory refreshed: {len(event[2])} visible files.')
            elif kind=='conversation_stage':self._set_reply_stage(event[1],event[2])
            elif kind=='conversation_reply':self._conversation_reply(event[1],event[2])
            elif kind=='conversation_error':self._conversation_error(event[1],event[2])
            elif kind=='job_plan':self._job_plan(event[1],event[2])
            elif kind=='build_files_done':self._build_files_done(event[1])
            elif kind=='job_answer':self._job_answer(event[1],event[2])
            elif kind=='job_error':self._job_error(event[1],event[2])
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
                if is_ready and self.node and self.node.poll() is None:
                    newly_ready=not self.node_ready
                    if newly_ready:
                        self._log('Local AI ready: 127.0.0.1:8765; offline.')
                    self.node_ready=True;self.node_loading=False;self.model_status.set('AI: ready')
                    if newly_ready:
                        record(STATE,'desktop','model_ready_event',model_pid=self.node.pid,health=detail or {})
                    if not (isinstance(detail,dict) and detail.get('inference_busy')):
                        self._set_connection_status('AI READY — chat replies run outside the execution queue. Jobs need plan approval.')
            elif kind=='node_end':
                was_loading=self.node_loading
                self._log('AI process exited. Exit status: '+str(event[1]))
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
            elif kind=='install_done':
                self.installing=False;self.model_status.set('AI: installed')
                self._log('Local AI installed. Starting the model now.')
                self._auto_start_if_installed()
                messagebox.showinfo('Installed','ONNX coding model installed. DeepThorT is starting the model automatically; your queued chat will resume when ready.')
            elif kind=='install_error':
                self.installing=False;self.model_status.set('AI: installation failed')
                self._log('Installation failed: '+event[1]);messagebox.showerror('Install failed',event[1])
            elif kind=='tool_end':
                label,tooltype,code,job_id=event[1:]
                self._log(f'{label} ended, exit code {code}. '+('Succeeded.' if code==0 else 'Check output for failure.'))
                self.status.set(f'{label}: exit code {code} (see Processes log)')
                if tooltype=='installation' and code==0:self._refresh_inventory()
                if tooltype=='x4_extraction' and code==0:
                    self._inspect_x4_sources()
                if tooltype=='x4_preflight_extraction' and job_id is not None:
                    self._x4_preflight_extract_finished(job_id,code)
                if tooltype=='verification' and job_id is not None:
                    self.jobs.change(job_id,'complete' if code==0 else 'needs_input',
                        f'Verified: test command exited 0 ({label})' if code==0 else
                        f'Build test failed with exit {code}; inspect Processes log and repair the project',
                        allowed=('running',))
                    self._refresh_jobs()
                if code!=0:messagebox.showwarning('Tool reported failure',f'{label} failed, exit code {code}. See Processes log.')
            elif kind=='tool_error':
                self._log(f'{event[1]} error: {event[3]}')
                if event[2]=='x4_preflight_extraction' and len(event)>4 and event[4] is not None:
                    self.conversations.change(event[4],'failed',
                        'Could not launch approved X4 source extraction: '+str(event[3]),
                        allowed=('waiting_sources',))
                    self._reload_chat()
                if len(event)>4 and event[4] is not None:
                    self.jobs.change(event[4],'needs_input','Test process failed to launch: '+event[3],allowed=('running',))
                    self._refresh_jobs()
                messagebox.showerror('Tool error',event[3])
        self.after(125,self._handle_events)
    def _quit(self):
        record(STATE,'desktop','desktop_shutdown',active_job=self.active_job,active_conversation=self.active_conversation)
        if self.active_conversation is not None:
            self.conversations.change(self.active_conversation,'pending',
                'Application closed; will retry when model is available',allowed=('running',))
        if self.active_job is not None:
            self.jobs.change(self.active_job,'paused','Application closed before reply; resume to retry',allowed=('running',))
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
