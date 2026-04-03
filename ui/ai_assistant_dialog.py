"""Interactive AI Assistant dialog: provider selection, API key, attachments, prompt, run and insert."""
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class AIAssistantDialog(tk.Toplevel):
    def __init__(self, parent, ai_engine, config_mgr, editor):
        super().__init__(parent)
        self.title("AI Assistant")
        self.geometry("800x600")
        self.ai = ai_engine
        self.config = config_mgr
        self.editor = editor

        self._build_ui()
        self._load_defaults()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(frm)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Provider:").pack(side=tk.LEFT)
        self.provider_var = tk.StringVar(value='gemini')
        self.provider = ttk.Combobox(top, textvariable=self.provider_var, values=['gemini', 'openai', 'anthropic'], width=12)
        self.provider.pack(side=tk.LEFT, padx=6)

        ttk.Label(top, text="API Key:").pack(side=tk.LEFT, padx=(8,0))
        self.key_entry = ttk.Entry(top, width=50)
        self.key_entry.pack(side=tk.LEFT, padx=6)
        self.save_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text='Save', variable=self.save_key_var).pack(side=tk.LEFT)

        # Attachments
        a_frame = ttk.LabelFrame(frm, text='Attachments', padding=6)
        a_frame.pack(fill=tk.BOTH, expand=False, pady=8)
        self.attach_list = tk.Listbox(a_frame, height=4)
        self.attach_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ab = ttk.Frame(a_frame)
        ab.pack(side=tk.LEFT, padx=6)
        ttk.Button(ab, text='Add Files', command=self._add_files).pack(fill=tk.X, pady=2)
        ttk.Button(ab, text='Remove', command=self._remove_selected).pack(fill=tk.X, pady=2)
        ttk.Button(ab, text='Clear', command=self._clear_all).pack(fill=tk.X, pady=2)

        # Prompt area
        p_frame = ttk.LabelFrame(frm, text='Prompt / Instructions', padding=6)
        p_frame.pack(fill=tk.BOTH, expand=True)
        self.prompt_text = tk.Text(p_frame, height=10)
        self.prompt_text.pack(fill=tk.BOTH, expand=True)

        # Bottom area: run and output
        bottom = ttk.Frame(frm)
        bottom.pack(fill=tk.BOTH, expand=True, pady=(8,0))

        action_bar = ttk.Frame(bottom)
        action_bar.pack(fill=tk.X)
        ttk.Button(action_bar, text='Run', command=self._run).pack(side=tk.LEFT)
        ttk.Button(action_bar, text='Insert Into Editor', command=self._insert_result).pack(side=tk.LEFT, padx=6)
        ttk.Button(action_bar, text='Close', command=self.destroy).pack(side=tk.RIGHT)

        self.output = tk.Text(bottom, height=12, bg='#f7f7f7')
        self.output.pack(fill=tk.BOTH, expand=True, pady=(6,0))

    def _load_defaults(self):
        # Pre-fill key if saved in config for selected provider
        try:
            try:
                keys = {}
                if hasattr(self.config, 'load_api_keys'):
                    keys = self.config.load_api_keys() or {}
                # prefer explicit saved key for provider
                provider = self.provider_var.get().strip().lower()
                k = keys.get(provider) or self.config.get(provider) or self.config.get(provider + '_api_key')
                if k:
                    self.key_entry.delete(0, tk.END)
                    self.key_entry.insert(0, k)
            except Exception:
                pass
        except Exception:
            pass

    def _add_files(self):
        paths = filedialog.askopenfilenames(title='Select files')
        for p in paths:
            ok = self.ai.add_attachment(p)
            if ok:
                self.attach_list.insert(tk.END, p)

    def _remove_selected(self):
        sel = self.attach_list.curselection()
        if not sel: return
        idx = sel[0]
        path = self.attach_list.get(idx)
        if self.ai.remove_attachment(path):
            self.attach_list.delete(idx)

    def _clear_all(self):
        for p in list(self.ai.list_attachments()):
            self.ai.remove_attachment(p)
        self.attach_list.delete(0, tk.END)

    def _run(self):
        provider = self.provider_var.get().strip().lower()
        key = self.key_entry.get().strip()
        if key:
            self.ai.set_api_key(provider, key)
            if self.save_key_var.get():
                try:
                    self.config.set(provider, key)
                except Exception:
                    pass

        prompt = self.prompt_text.get('1.0', tk.END).strip()
        if not prompt:
            messagebox.showwarning('Empty', 'Write a prompt or instructions for the AI.')
            return

        context = self.editor.get_text()

        def cb(result):
            try:
                self.after(0, lambda: self.output.insert(tk.END, result + '\n'))
            except Exception:
                pass

        self.output.delete('1.0', tk.END)
        self.output.insert(tk.END, '⏳ Running...\n')
        self.ai.get_response(provider, prompt, context_code=context, callback=cb)

    def _insert_result(self):
        txt = self.output.get('1.0', tk.END).strip()
        if not txt:
            return
        try:
            self.editor.insert_at_cursor(txt)
        except Exception:
            messagebox.showerror('Insert', 'Failed to insert into editor.')
