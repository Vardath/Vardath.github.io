"""Offline contextual help for DeepThorT's Tk desktop.

Passive and UI-only: no model calls, file operations or external links.  Tooltips
never acquire focus and are removed on leave, click, destroy and Escape.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

TOOLTIPS = {
    'User guide': 'Open the illustrated offline user guide in your default browser (F1). No internet connection is needed.',
    'Cancel': 'Dismiss this review without authorizing a change or command.',
    'Approve WRITE ONLY': 'Save the exact reviewed script in the selected workspace with a backup. This does not run the script.',
    'Install AI': 'Install the optional local Qwen coding model and dependencies. Review the installation consent dialog first.',
    'Start AI': 'Start the local ONNX inference worker. Readiness is shown beside these controls; this does not start a project job.',
    'Stop AI': 'Stop the local language-model worker. Saved conversations, approved jobs and other state remain on disk.',
    'Self-diagnose': 'Check local model and required dependencies. This does not run your project or install software.',
    'Export diagnostics': 'Save a local support ZIP with bounded health/log evidence. Nothing is uploaded automatically.',
    'Choose folder…': 'Select the project directory DeepThorT may inspect and use for explicitly approved file work.',
    'Refresh project files': 'Update the project file tree from disk; no project files are modified.',
    'Propose new project file…': 'Stage a new project file proposal for review. Saving to the project requires specific approval.',
    '+ New chat': 'Start a separate persistent conversation; your other chats remain available.',
    'Rename chat': 'Change the name of the selected saved conversation.',
    'Close chat': 'Close the selected conversation; it does not erase your project files.',
    'Attach files…': 'Select local supporting documents or images for this conversation. Files are not automatically executed.',
    'Clear attachments': 'Remove the current attachment selection without deleting the original files.',
    'Include selected project file': 'Include the highlighted project file as local context for your next request.',
    'Send message': 'Send the editor text to the offline model. This alone does not authorize a plan or file changes. Ctrl+Enter also sends.',
    'Diagnose AI': 'Inspect the local inference setup and explain problems starting or using Qwen.',
    'Retry failed reply': 'Retry an unsuccessful conversation reply. Exact previously saved successful model passes may be reused.',
    'Stop reply': 'Stop the current model response; unrelated approved tasks are not automatically cancelled.',
    'Draft project plan': 'Ask Qwen to draft a staged implementation plan from your instructions; no work is approved yet.',
    'Approve plan & queue': 'Review the proposed plan and explicitly authorize the next milestone. Later milestones remain gated.',
    'Revise existing file': 'Propose a change to a selected project file. Review the diff before approving the write.',
    'Pause queue': 'Pause dispatch of new queue jobs. Already-running work may continue until separately stopped.',
    'Resume queue': 'Allow new queued jobs to start after the pause; resource and approval rules still apply.',
    'Refresh': 'Reload the saved work queue and its actual statuses.',
    'Cancel selected': 'Cancel the selected queued job; this does not remove source files already written.',
    'Resume selected': 'Retry or resume a selected paused/blocked job, subject to its current permissions.',
    'Review legacy plan': 'Review an older build plan with the same explicit-approval safeguards.',
    'Verify build': 'Run a specifically approved static check or project test; a pass is not automatically proof of gameplay.',
    'Load prompt into editor': 'Copy the selected queued job request back to the chat editor for editing.',
    'Apply approved change': 'After reviewing the proposed file, write the approved content with backup and workspace checks.',
    'Add task': 'Create a durable manual task for the selected project.',
    'Complete / reopen': 'Mark a selected task done or open; only verified work should be marked complete.',
    'Send to prompt': 'Place the selected task in the prompt editor without starting execution.',
    'Cancel running job': 'Request cancellation of the active build or inference job.',
    'Stop tool / install process': 'Request termination of a running supervised local tool or installer.',
    'Refresh status': 'Read the actual persisted JANUS, Sentinel and process states.',
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
    'Ask local coding model to refine image description before generation': 'Let local Qwen rewrite the prompt before the offline image generator receives it.',
}

TABS = {
    'Chats': 'Manage saved conversations, submit instructions, draft a plan and request a file revision.',
    'Work queue': 'Inspect real persisted jobs, pause/resume dispatch and run approved verification.',
    'File review': 'Inspect proposed file contents and differences before accepting a write.',
    'Tasks': 'Keep durable manual project tasks; do not confuse task checkmarks with test evidence.',
    'Processes': 'See actual events, output and process cancellation controls.',
    'JANUS & Sentinel': 'Review JANUS coordination, Sentinel supervision, recommendations and approved process states.',
    'Computer & Tools': 'Inspect tools; configure standing routine installs/upgrades and Windows UAC handling; review unknown third-party software separately.',
    'Files & Images': 'Attach local documents/images and use optional offline vision and generation tools.',
}

AREA_TIPS = {
    'files': 'Project file tree. Select a file to preview or include it in the next request.',
    'chat_history': 'Saved chat transcript and replies. A model answer is not an approved file edit.',
    'input': 'Type project requirements here. Ctrl+Enter sends; Ctrl+Shift+O imports a large TXT/MD specification.',
    'job_tree': 'Persisted work queue. Select a job before cancelling, resuming or verifying it.',
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
    'model_status': 'Current local Qwen worker availability, not a measure of completed work.',
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
                elif kind in ('TButton', 'Button', 'Checkbutton', 'TCheckbutton'):
                    attach(widget, TOOLTIPS.get(widget.cget('text'),
                        f'{widget.cget("text")}: review this control before taking action.'))
                elif isinstance(widget, ttk.Notebook):
                    attach(widget, lambda event, w=widget: _tab_description(w, event))
                elif isinstance(widget, ttk.Treeview):
                    attach(widget, 'Select an item to inspect its details; selecting alone does not execute work.')
                elif isinstance(widget, tk.Text):
                    attach(widget, 'Scrollable project or activity text. Check adjacent controls for actions and approvals.')
                elif isinstance(widget, ttk.Combobox):
                    attach(widget, 'Select an option here. Choosing a value alone does not execute or install software.')
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
