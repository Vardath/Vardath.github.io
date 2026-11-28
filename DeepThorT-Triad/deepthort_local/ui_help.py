"""Offline contextual help for DeepThorT's Tk desktop.

Passive and UI-only: no model calls, file operations or external links.  Tooltips
never acquire focus and are removed on leave, click, destroy and Escape.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

TOOLTIPS = {
    'Quick navigation': 'Open any primary workspace, even when native notebook tabs overflow. Ctrl+F6 focuses the workspace selector.',
    'Selected job actions': 'Existing selected-job review and prompt loading commands.',
    'Refresh settings overview': 'Read existing saved policy values without changing settings or connecting external services.',
    'Refresh artifacts': 'Read the existing bounded workspace file snapshot; no new disk scan.',
    'Production categories': 'Navigate to original production controls filtered by category; no tool runs.',
    'Filter artifacts': 'Filter discovered workspace file formats without opening or executing files.',
    'Inspect artifact metadata': 'Read the selected file metadata within the current inspection scope.',
    'Inspect artifact / preview': 'Read bounded file metadata, plain text preview and matching historical source checkpoint evidence.',
    'Open exact job in Work queue': 'Navigate to the same job for the existing review and revoke controls; does not approve or revoke.',
    'Refresh assignment evidence': 'Inspect recorded workspace contracts and delegated stages, without starting or changing work.',
    'Memory receipts': 'Navigate to historical asynchronous memory receipts; does not request recall.',
    'Refresh memory overview': 'Read historical memory receipt metadata and observer counts without triggering recall.',
    'Filter memory receipts': 'Filter existing workspace receipt records without changing the memory index.',
    'Inspect memory receipt': 'Inspect a selected historical advisory receipt; not current relevance or approval.',
    'Refresh approvals': 'Read existing job and approved action records without creating any permissions.',
    'Existing permission controls': 'Navigate to the existing reviewed permission and process controls.',
    'Inspect selected record': 'Read the exact stored record and historical evidence without executing anything.',
    'Refresh overview': 'Read saved project queue and workspace job metadata without approving or executing anything.',
    'Go to workspace': 'Navigate to an existing workspace screen.',
    'Open selected job': 'Inspect an exact selected job from the current workspace; never approves or executes it.',
    'Filter tools': 'Filter existing computer scan results without scanning, installing or granting permission.',
    'Discover & learn': 'Investigate or explicitly enrol tools and review learned procedures.',
    'Design & share': 'Review local workflows and portable skills or procedures.',
    'Integrations': 'Review local MCP and asset import operations.',
    'Online discovery': 'Discover unverified software candidates; installation requires separate review.',
    'X4 paths & extraction': 'Configure X4 reference paths and separately approve extraction.',
    'Five operatives': 'Observed worker roles; Gemma activity is not a residency claim.',
    'Diagnostics & tests': 'Existing diagnostics, test and model recovery operations; no operation starts by opening this menu.',
    'Follow latest activity': 'Scroll to new desktop log entries as they arrive. Disable to read or search older entries.',
    'Inspect proposed diff…': 'Compare the current file and proposed editor buffer without granting a write or executing anything.',
    'Go to line': 'Navigate to a numbered source line without changing its contents.',
    'Filter jobs': 'Filter displayed jobs by observed state and text without changing their execution order.',
    'Filter tasks': 'Filter the manual task board without changing task completion or queue state.',
    'Scheduling & monitors': 'Existing scheduling, roadmap, network and monitor controls.',
    'Backups & checkpoints': 'Open reviewed backup, restore and source checkpoint operations.',
    'Development & testing': 'Access existing development tools and reviewed test operations.',
    'Recent projects…': 'Choose an existing saved workspace by exact path. Current drafts and attachments must be resolved before switching.',
    'Filter files': 'Filter the displayed workspace and verified reference paths only; no source changes or new file scan. Escape clears the filter.',
    'Open selected': 'Open the explicitly selected saved identity, not a matching name alone.',
    'Expand composer': 'Show more of the current draft without changing or submitting its text.',
    'System & maintenance': 'Install, diagnose, test, export diagnostics or review application updates; each action retains its own review.',
    'Specialist project actions': 'Access existing X4 and native draft operations for the selected workspace.',
    'Conversation': 'Rename, close or reopen saved conversations in this project.',
    'Conversation tools': 'Retry, diagnose, edit preferences or explicitly amend the specification.',
    'Attachments': 'Manage selected local attachments without deleting original files.',
    'Edit selected file…': 'Open a direct UTF-8 editor with undo, redo and search. Review the exact diff before a backed-up save; no code execution.',
    'Review & save…': 'Review exact source changes and check the original file has not changed before saving.',
    'Approve local commit': 'Queue the exact reviewed staged Git tree and message through JANUS. No staging, remote push or claim of test success.',
    'Project knowledge…': 'Open the current workspace document library; enroll, discover, search, reindex or forget local references without editing source files.',
    'Refresh knowledge': 'Recheck exact source fingerprints and list current or stale knowledge entries.',
    'Discover documents': 'Perform a bounded read-only scan for eligible workspace manuals; PDFs require explicit enrollment.',
    'Enroll documents…': 'Select supported files inside this workspace and index their reference text locally.',
    'Reindex selected': 'Re-read selected source documents and update their exact index evidence.',
    'Forget selected': 'Remove selected knowledge index entries without deleting original files.',
    'Search knowledge': 'Retrieve current quoted excerpts with file and line or page citations.',
    'Stop knowledge operation': 'Stop at the next bounded document or extraction boundary; completed entries remain saved.',
    "Review / materialize native draft": "Review the exact staged native assets and materialize only approved matching files into the project. This is not gameplay verification.",
    "Amend specification": "Append an explicit user correction to the current specification. Previous instructions remain in force except where overridden; old build approvals become stale.",
    "Roadmap automation": "Review and approve an exact ordered roadmap once, or pause its automatic advancement. Each successor requires current verification of predecessors.",
    "Enroll app…": "Register an explicitly selected installed Windows executable and documented help flag for later investigation. This does not run or install it.",
    "Tool workflows…": "Review and approve an ordered sequence of existing learned tool recipes, or stop an active workflow. Outputs are checked between stages.",
    "Asset import check…": "Review a required or optional headless Blender/Godot import test for a checked asset, approve its exact command, and inspect actual load evidence. Required imports hold roadmap advancement until verified.",
    "JANUS workflow…": "Ask JANUS to propose a specification-bound tool workflow, identify missing procedures, or review a finished draft. No model proposal authorizes execution.",
    "Discovered packages…": "Inspect exact package IDs from persisted read-only software discovery. Installation requires a separate action.",
    'User guide': 'Open the illustrated offline user guide in your default browser (F1). No internet connection is needed.',
    'Cancel': 'Dismiss this review without authorizing a change or command.',
    'Approve WRITE ONLY': 'Save the exact reviewed script in the selected workspace with a backup. This does not run the script.',
    'Install AI': 'Install the three local OpenVINO IR models and pinned CPU runtime. Review the installation consent dialog first.',
    'Start AI': 'Start the local OpenVINO IR inference worker. Readiness is shown beside these controls; this does not start a project job.',
    'Stop AI': 'Stop the local language-model worker. Saved conversations, approved jobs and other state remain on disk.',
    'Self-diagnose': 'Check local model and required dependencies. This does not run your project or install software.',
    'Export diagnostics': 'Save a local support ZIP with bounded health/log evidence. Nothing is uploaded automatically.',
    'Choose folder…': 'Select the project directory DeepThorT may inspect and use for explicitly approved file work.',
    'Refresh project files': 'Update the project file tree from disk; no project files are modified.',
    'Export latest draft mesh': 'Save the measured visual mesh as XMF or OBJ. Choose ZIP for the latest independent ship-component draft associated with that mesh request.',
    'Auto-discover X4 sources': 'Read-only lookup of the installed X4 game and previously extracted vanilla XML. Relevant verified references appear in the project sidebar; packed catalogs require separate approved extraction. Nothing is copied into your mod output folder.',
    'Show all workspace files': 'Reveal or hide unrelated files in the selected OUTPUT workspace. With this unchecked, the sidebar focuses on paths named by current plans/jobs plus a separate read-only X4 reference shortlist. No disk files are deleted or moved.',
    'Propose new project file…': 'Stage a new project file proposal for review. Saving to the project requires specific approval.',
    '+ New chat': 'Start a separate persistent conversation; your other chats remain available.',
    'Rename chat': 'Change the name of the selected saved conversation.',
    'Close chat': 'Close the selected conversation; it does not erase your project files.',
    'Attach files…': 'Select local supporting documents or images for this conversation. Files are not automatically executed.',
    'Clear attachments': 'Remove the current attachment selection without deleting the original files.',
    'Include selected project file': 'Include the highlighted project file as local context for your next request.',
    'Send message': 'Send the editor text to the offline model. This alone does not authorize a plan or file changes. Ctrl+Enter also sends.',
    'Diagnose AI': 'Inspect the local inference setup and explain problems starting or using Triad.',
    'Retry failed reply': 'Retry an unsuccessful conversation reply. Exact previously saved successful model passes may be reused.',
    'Stop reply': 'Stop the current model response; unrelated approved tasks are not automatically cancelled.',
    'Instruction to JANUS': 'Save your new message for independent JANUS/Sentinel interpretation on the separate JANUS and Sentinel OpenVINO IR workers, even while the primary model is busy. The current task continues. The translated next action is advisory and can join a later unapproved planning checkpoint; no source is edited. Ctrl+Shift+Enter.',
    'Draft project plan': 'Ask Triad to draft a staged implementation plan. 40 attempts means model planning calls in one batch, not 40 files. Large specifications use numbered sections and resumable review batches. No work is approved yet.',
    'Approve plan & queue': 'Review the proposed plan and explicitly authorize the next milestone. Later milestones remain gated.',
    'Revise existing file': 'Propose a change to a selected project file. Review the diff before approving the write.',
    'Pause queue': 'Pause dispatch of new queue jobs. Already-running work may continue until separately stopped.',
    'Resume queue': 'Allow new queued jobs to start after the pause; resource and approval rules still apply.',
    'Refresh': 'Reload the saved work queue and its actual statuses.',
    'Cancel selected': 'Cancel the selected queued job; this does not remove source files already written.',
    'Resume selected': 'Retry or resume a selected paused/blocked job, subject to its current permissions.',
    'Review legacy plan': 'Review an older build plan with the same explicit-approval safeguards.',
    'Verify build': 'Run a specifically approved static check or project test; a pass is not automatically proof of gameplay.',
    'Continue approved file steps and fixed tests without repeated prompts': 'After explicit plan approval, save exact approved files, run fixed tests, and attempt at most two one-file OpenVINO IR repairs followed by retests. Tests run under your Windows user rights and are NOT sandboxed; disable before approval for individual review.',
    'Isolated GUI smoke test…': 'Approve one trusted, project-owned Windows .exe and launch it on another desktop for 25 seconds without foreground input. Shared 30% CPU cap; window metadata only. NOT sandboxed, may still use GPU/audio; no gameplay proof.',
    'Stop isolated GUI test': 'Cancel the separately supervised project executable; the nested Windows job terminates test child processes. Does not stop your active game.',
    'Quiet Godot scene test': 'Runs the selected Godot project main scene in a headless, audio-free, no-focus background process. Requires the capped Windows launcher; shared 30% job CPU cap, IDLE priority and foreground pressure preemption. Records only a scene smoke result, NOT visual gameplay. Scene scripts run with your user privileges.',
    'Stop quiet test': 'Immediately request termination of the current headless Godot test. Does not stop your foreground game or other apps. No automatic replay.',
    'Restore source checkpoint…': 'Explicitly restore an older version of this approved job source. Confirms exact files and hashes; newly created files are quarantined, previous approvals/tests become invalid and a new approved plan is needed.',
    'Revoke selected job automation': 'Revoke future automatic source writes, local OpenVINO IR repairs and tests for this specific approved job. Already-running tests must be stopped separately in Processes.',
    'Load prompt into editor': 'Copy the selected queued job request back to the chat editor for editing.',
    'Apply approved change': 'After reviewing the proposed file, write the approved content with backup and workspace checks.',
    'Add task': 'Create a durable manual task for the selected project.',
    'Complete / reopen': 'Mark a selected task done or open; only verified work should be marked complete.',
    'Send to prompt': 'Place the selected task in the prompt editor without starting execution.',
    'Cancel running job': 'Request cancellation of the active build or inference job.',
    'Stop tool / install process': 'Request termination of a running supervised local tool or installer.',
    'Refresh status': 'Read the actual persisted JANUS, Sentinel and process states.',
    'Locate latest diagnostics': 'Read the saved export receipt, verify ZIP integrity and show the exact selected and retained paths. Optionally open the containing folder; never silently moves a file.',
    'Retry JANUS model': 'Manually reset failed Triad council readiness checks; does not interrupt current council inference, bypass the shared 30% cap or rewrite an approved job.',
    'Run latest test': 'Run the current signed-off, built-in acceptance checks from LATEST_TEST.json in the background. No game, installer, shell command or project file is executed. An automatic diagnostic ZIP and JSON report are saved for support.',
    'Stop latest test': 'Cancel remaining latest-test checks. An in-flight bounded OpenVINO IR inference call may finish before cancellation takes effect; the current game and coding work continue.',
    'Instruction inbox…': 'Inspect exact original user instructions, JANUS translations and Sentinel acceptance checks. Review scope-changing advice, retry failed neural interpretation or dismiss; no command or approved file plan is changed automatically.',
    'Retry latest failed JANUS instruction': 'One click retries only the latest failed JANUS neural translation for the selected project. It does not retry Chats, change approved plans or execute source files.',
    'Set primary goal…': 'Set JANUS’s persistent high-level goal. This does not bypass execution approval.',
    'Inspect 22 core states': 'View the separate JANUS and Sentinel eleven-core reasoning state summaries.',
    'Pause JANUS': 'Pause new JANUS approved-action dispatch; do not assume a running process is undone.',
    'Resume JANUS': 'Resume JANUS supervision of previously approved actions.',
    'Cancel selected approved process': 'Cancel the highlighted JANUS tool/verification action; partially written outputs may remain.',
    'Scan this computer': 'Read-only inventory of installed tools, resources and selected-project engine prerequisites.',
    'Check tools needed for prompt': 'Suggest local tool requirements based on the current prompt and software inventory. Advisory only.',
    'Investigate app…': 'With permission, run bounded CLI help for an actually installed supported tool. Does not execute a project task.',
    'Learn procedure…': 'Ask the offline model to draft an application procedure using observed help and documentation. Proposal only.',
    'Run learned procedure…': 'Review a proposed script or command. File writing and command execution each require separate consent.',
    'Search packages online…': 'Search WinGet on demand. Routine tool policy removes redundant DeepThorT confirmation; the search itself does not install software.',
    'Install inspected package…': 'Install an exact, recently inspected WinGet package after clicking this control. With routine management enabled the standing policy avoids repeated prompts; normal Windows UAC remains. Publisher claims remain unverified.',
    'Review inspected install…': 'Legacy review: manual mode retains per-package confirmation and typed approval.',
    'Inspect package ID…': 'Inspect one exact WinGet package ID and show catalog-supplied publisher/version/hash. Routine tool policy removes a second confirmation for the query; no install starts.',
    'Find official tool page…': 'Open a reviewed vendor download page for the selected catalog tool, after confirmation. No download or installation is performed.',
    'Inspect X4 sources': 'Read-only examination of game files and selected extracted XML; does not certify an X4 mod in-game.',
    'Choose X4 game folder…': 'Point DeepThorT to your actual installed X4: Foundations directory.',
    'Choose extracted X4 XML…': 'Select existing extracted vanilla X4 source XML/indexes for reference and static audits.',
    'Extract X4 XML (approval required)…': 'Review and authorize local extraction of X4 reference assets. The game installation is not modified.',
    'Install selected catalog tool…': 'Install the selected curated package. With routine tool management enabled, no repeated DeepThorT approval dialog is needed; Windows UAC can still appear.',
    'Automatically manage routine project tools': 'When enabled, approved BUILD jobs can install missing, locally curated WinGet tools without per-tool prompts. Existing source/command protections remain. Disable at any time.',
    'Allow tool upgrades': 'Allow version upgrades for recognised tools needed by approved projects, throttled to one attempt per 14 days. Windows elevation requests still appear normally.',
    'Review & approve install…': 'Legacy installation review for a selected fixed WinGet package.',
    'Review & run…': 'Review the exact project test or CLI command before JANUS runs it.',
    'Attach documents / pictures…': 'Choose local files or images for analysis. No automatic upload.',
    'Clear selection': 'Clear the selected media references without deleting the files.',
    'Read selected image': 'Use the optional installed local vision model to describe a selected image.',
    'Install PDF reader…': 'Install optional PDF-reading dependencies with approval.',
    'Install Vision Model…': 'Install a separate local image-reading model with approval; download may be substantial.',
    'Install Image Generator…': 'Install the optional offline image generator with approval; it can use substantial disk/RAM.',
    'Generate image from prompt': 'Queue local image generation from the prompt; choose a project for saved output.',
    'Ask local coding model to refine image description before generation': 'Let local Triad rewrite the prompt before the offline image generator receives it.',
}

TABS = {
    'Settings & Integrations': 'Inspect saved policy values and navigate to existing local configuration and explicitly reviewed integrations.',
    'Studio': 'Navigate production categories and inspect bounded workspace artifact metadata without running files.',
    'Knowledge & Memory': 'Inspect independent recall records and open the existing project knowledge library.',
    'Approvals & PC Activity': 'Read outstanding workspace review states and recent recorded PC actions; no approval or execution occurs here.',
    'Command Centre': 'Review project priorities, recorded job states and live operative observations. Navigate to existing controls without granting new authority.',
    'Chats': 'Manage saved conversations, submit instructions, draft a plan and request a file revision.',
    'Work queue': 'Inspect approved task dependencies, real tests/repairs, source revisions and blockers. Explicit rollback quarantines new files and invalidates old approvals.',
    'File review': 'Inspect proposed file contents and differences before accepting a write.',
    'Tasks': 'Keep durable manual project tasks; do not confuse task checkmarks with test evidence.',
    'Processes': 'See actual events, output and process cancellation controls.',
    'JANUS & Sentinel': 'Review JANUS coordination, Sentinel supervision, recommendations and approved process states.',
    'Computer & Tools': 'Inspect tools; configure standing routine installs/upgrades and Windows UAC handling; review unknown third-party software separately.',
    'Files & Images': 'Attach local documents/images and use optional offline vision and generation tools.',
}

AREA_TIPS = {
    'workspace_navigator': 'Choose any primary workspace even when notebook tabs overflow; Ctrl+F6 focuses navigation.',
    'resource_table': 'Measured tracked PIDs; CPU, resident and private commit are distinct measurements.',
    'operative_table': 'Observed neural-worker and creative-lane states, not inferred task assignments.',
    'inventory_table': 'Detected software and version evidence; detection does not grant permission.',
    'files': 'Project file tree. Select a file to preview or include it in the next request.',
    'chat_history': 'Saved chat transcript and replies. A model answer is not an approved file edit.',
    'input': 'Type project requirements here. Ctrl+Enter sends; Ctrl+Shift+O imports a large TXT/MD specification.',
    'job_tree': 'Select a saved job to inspect actual cycle state, test/repair budgets, latest diagnostic evidence and cancel/revoke controls.',
    'task_tree': 'Persistent task list for this workspace.',
    'activity': 'Timestamped operational events and tool activity; consult this when a task stalls.',
    'janus_action_tree': 'Real JANUS actions, approval states and tool/verification results.',
    'janus_events_text': 'JANUS cycles and Sentinel findings; proposals are advisory until approved.',
    'machine_text': 'Read-only tool inventory, resources and current project prerequisites.',
    'x4_source_info': 'X4 source inspection details and blockers; read-only evidence, not gameplay validation.',
    'image_preview': 'Selected image preview; does not imply the vision model has analyzed its contents.',
    'image_info': 'Local media analysis/generation status and descriptive output.',
    'install_menu': 'Select a known curated WinGet application. The routine tool policy governs repeat installation confirmation.',
    'check_menu': 'Choose a supported local project check; approval is required before it runs.',
    'model_status': 'Current local Triad worker availability, not a measure of completed work.',
}

class HoverTip:
    def __init__(self, widget, message, delay_ms=650):
        self.widget, self.message, self.delay_ms = widget, message, delay_ms
        self._after = None
        self._window = None
        widget.bind('<Enter>', self._schedule, add='+')
        widget.bind('<Motion>', self._motion, add='+')
        widget.bind('<Leave>', self._hide, add='+')
        widget.bind('<ButtonPress>', self._hide, add='+')
        widget.bind('<Destroy>', self._hide, add='+')
        widget.bind('<Escape>', self._hide, add='+')

    def _message(self, event=None):
        try:
            if callable(self.message):
                return str(self.message(event) or '')
            return str(self.message or '')
        except (tk.TclError, ValueError):
            return ''

    def _schedule(self, event=None):
        self._cancel()
        if self._message(event):
            self._after = self.widget.after(self.delay_ms, self._show)

    def _motion(self, event=None):
        # On notebooks another tab may be under the cursor, so restart its timer.
        if isinstance(self.widget, ttk.Notebook):
            self._hide()
            self._schedule(event)

    def _cancel(self):
        if self._after is not None:
            try: self.widget.after_cancel(self._after)
            except tk.TclError: pass
            self._after = None

    def _show(self):
        self._after = None
        try:
            if not self.widget.winfo_exists() or not self.widget.winfo_ismapped():
                return
            x = self.widget.winfo_pointerx()
            y = self.widget.winfo_pointery()
            local_x = x - self.widget.winfo_rootx()
            local_y = y - self.widget.winfo_rooty()
            if local_x < 0 or local_y < 0 or local_x >= self.widget.winfo_width() or local_y >= self.widget.winfo_height():
                return
            event = type('HoverPosition', (), {'x': local_x, 'y': local_y})()
            msg = self._message(event)
            if not msg:
                return
            self._window = tk.Toplevel(self.widget)
            self._window.withdraw()
            self._window.overrideredirect(True)
            label = tk.Label(self._window, text=msg, justify='left', wraplength=365,
                             bg='#fff5d5', fg='#20252b', relief='solid', borderwidth=1,
                             padx=10, pady=7, font=('Segoe UI', 9))
            label.pack()
            self._window.update_idletasks()
            screen_w = self.widget.winfo_screenwidth()
            screen_h = self.widget.winfo_screenheight()
            px = max(0, min(x + 14, screen_w - self._window.winfo_reqwidth() - 4))
            py = max(0, min(y + 20, screen_h - self._window.winfo_reqheight() - 4))
            self._window.geometry(f'+{px}+{py}')
            self._window.deiconify()
        except tk.TclError:
            self._window = None

    def _hide(self, event=None):
        self._cancel()
        if self._window:
            try: self._window.destroy()
            except tk.TclError: pass
            self._window = None


def _tab_description(widget, event):
    if event is None:
        return ''
    try:
        idx = widget.index(f'@{event.x},{event.y}')
        name = widget.tab(idx, 'text')
    except (tk.TclError, ValueError):
        return ''
    return TABS.get(name, 'Saved conversation tab. Click to open it; right-click for chat-specific actions.')


def install_tooltips(app):
    """Attach help to existing widgets; return handles for lifetime retention.

    Call after the main UI is built. Notebook tab texts are resolved dynamically.
    """
    tips = []
    visited = set()

    def attach(widget, message):
        if widget in visited or not message:
            return
        visited.add(widget)
        tips.append(HoverTip(widget, message))

    named = {getattr(app, name): help_text
             for name, help_text in AREA_TIPS.items()
             if isinstance(getattr(app, name, None), tk.Widget)}

    def walk(parent):
        for widget in parent.winfo_children():
            try:
                kind = widget.winfo_class()
                if widget in named:
                    attach(widget, named[widget])
                elif kind in ('TButton', 'Button', 'Checkbutton', 'TCheckbutton', 'TMenubutton'):
                    attach(widget, TOOLTIPS.get(widget.cget('text'),
                        f'{widget.cget("text")}: review this control before taking action.'))
                elif isinstance(widget, ttk.Notebook):
                    attach(widget, lambda event, w=widget: _tab_description(w, event))
                elif isinstance(widget, ttk.Treeview):
                    attach(widget, 'Select an item to inspect its details; selecting alone does not execute work.')
                elif isinstance(widget, tk.Text):
                    attach(widget, 'Scrollable project or activity text. Check adjacent controls for actions and approvals.')
                elif isinstance(widget, ttk.Combobox):
                    attach(widget, 'Select an option here; workspace and filter selectors change the visible view. Review the associated operation before running it.')
                elif kind in ('TEntry','Entry'):
                    attach(widget, 'Enter or edit a value for the current operation; review before submitting.')
                elif kind in ('TLabel', 'Label'):
                    if str(widget.cget('textvariable')) == str(getattr(app, 'model_status', None)):
                        attach(widget, AREA_TIPS['model_status'])
                walk(widget)
            except tk.TclError:
                continue
    walk(app)
    return tips
