"""
Latex Pro Studio - Citation Manager UI
Supports real-time synchronization with Mendeley and Zotero.
GitHub: https://github.com/ismail-baklouti/latex-pro-studio
"""

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from citations.mendeley_api import MendeleyAPI
from citations.zotero_api import ZoteroAPI
import threading
import os

class CitationManagerDialog(ttk.Toplevel):
    def __init__(self, master, editor, project_path, config):
        super().__init__(master)
        self.title("Academic Reference Manager")
        self.geometry("1000x700")
        
        self.editor = editor
        self.project_path = project_path
        self.config = config
        self.library_items = []

        # Initialize API clients with keys from Config
        keys = self.config.get_api_keys()
        self.mendeley = MendeleyAPI(keys['mendeley_id'], keys['mendeley_secret'])
        self.zotero = ZoteroAPI(keys['zotero_id'], keys['zotero_key'])

        self._build_ui()

    def _build_ui(self):
        # 1. Sidebar for Sources
        self.sidebar = ttk.Frame(self, width=150, bootstyle=LIGHT)
        self.sidebar.pack(side=LEFT, fill=Y)
        
        ttk.Label(self.sidebar, text="SOURCES", font=("Helvetica", 8, "bold")).pack(pady=10)
        ttk.Button(self.sidebar, text="Mendeley", command=self._sync_mendeley, bootstyle=LINK).pack(fill=X)
        ttk.Button(self.sidebar, text="Zotero", command=self._sync_zotero, bootstyle=LINK).pack(fill=X)

        # 2. Main Content Area
        self.content = ttk.Frame(self, padding=10)
        self.content.pack(side=LEFT, fill=BOTH, expand=YES)

        # Search
        search_frame = ttk.Frame(self.content)
        search_frame.pack(fill=X, pady=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter)
        ttk.Entry(search_frame, textvariable=self.search_var, placeholder="Search library...").pack(fill=X)

        # Table
        self.tree = ttk.Treeview(self.content, columns=("Key", "Author", "Title", "Year"), show="headings", bootstyle=PRIMARY)
        for col in ("Key", "Author", "Title", "Year"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100 if col != "Title" else 400)
        self.tree.pack(fill=BOTH, expand=YES)

        # Preview Area (So user sees the BibTeX before inserting)
        self.preview = ttk.LabelFrame(self.content, text="BibTeX Preview", padding=10)
        self.preview.pack(fill=X, pady=10)
        self.preview_text = tk.Text(self.preview, height=5, font=("Consolas", 9), bg="#f8f9fa")
        self.preview_text.pack(fill=X)

        self.tree.bind("<<TreeviewSelect>>", self._update_preview)

        # Actions
        btn_frame = ttk.Frame(self.content)
        btn_frame.pack(fill=X)
        ttk.Button(btn_frame, text="Add to Document", command=self._insert_citation, bootstyle=SUCCESS).pack(side=RIGHT)

    def _sync_mendeley(self):
        auth_url = self.mendeley.get_auth_url()
        import webbrowser
        webbrowser.open(auth_url)
        # This would normally trigger the OAuthHandler server we wrote earlier
        # Once authenticated:
        self._load_data(self.mendeley.fetch_all_documents)

    def _sync_zotero(self):
        if not self.zotero.is_configured():
            messagebox.showwarning("Config", "Zotero ID/Key not found in settings.")
            return
        self._load_data(self.zotero.fetch_all_items)

    def _load_data(self, fetch_func):
        def task():
            items = fetch_func()
            self.library_items = items
            self.after(0, self._refresh_table)
        threading.Thread(target=task, daemon=True).start()

    def _refresh_table(self, data=None):
        self.tree.delete(*self.tree.get_children())
        items = data if data is not None else self.library_items
        for item in items:
            self.tree.insert("", "end", values=(item['key'], item['author'], item['title'], item['year']))

    def _update_preview(self, event):
        selected = self.tree.selection()
        if not selected: return
        item = next(i for i in self.library_items if i['key'] == self.tree.item(selected[0])['values'][0])
        
        bib = f"@article{{{item['key']},\n  author = {{{item['author']}}},\n  title = {{{item['title']}}},\n  year = {{{item['year']}}}\n}}"
        self.preview_text.delete("1.0", END)
        self.preview_text.insert(END, bib)

    def _insert_citation(self):
        selected = self.tree.selection()
        if not selected: return
        key = self.tree.item(selected[0])['values'][0]
        
        # 1. Insert \cite{key} into LaTeX Editor
        self.editor.insert_at_cursor(f"\\cite{{{key}}}")
        
        # 2. Update references.bib automatically
        bib_content = self.preview_text.get("1.0", END)
        bib_path = os.path.join(self.project_path, "references.bib")
        with open(bib_path, "a") as f:
            f.write(f"\n{bib_content}\n")
        
        self.destroy()

    def _filter(self, *args):
        q = self.search_var.get().lower()
        res = [i for i in self.library_items if q in i['title'].lower() or q in i['author'].lower()]
        self._refresh_table(res)