"""Citation management dialog: connect to Zotero/Mendeley and import/insert citations."""
import tkinter as tk
from tkinter import simpledialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from citations.zotero_client import ZoteroClient
from citations.bib_manager import add_entry
from pathlib import Path
from citations.mendeley_client import MendeleyClient


def _mendeley_to_bibtex(doc: dict) -> str:
    """Create a minimal BibTeX entry from Mendeley document metadata."""
    # Use id as key fallback
    doc_id = doc.get('id') or doc.get('document_id') or 'mendeley1'
    key = f"mendeley-{doc_id}"
    title = doc.get('title', 'No Title').replace('"', "'")
    year = ''
    if 'year' in doc:
        year = str(doc.get('year'))
    elif 'published' in doc and isinstance(doc.get('published'), dict):
        year = str(doc.get('published', {}).get('year', ''))

    authors = ''
    if 'authors' in doc and isinstance(doc.get('authors'), list):
        parts = []
        for a in doc['authors']:
            fn = a.get('first_name') or a.get('forename') or ''
            ln = a.get('last_name') or a.get('surname') or ''
            name = (f"{ln}, {fn}" if ln else fn).strip()
            if name:
                parts.append(name)
        authors = ' and '.join(parts)

    bib = f"@article{{{key},\n  title = {{{title}}},\n"
    if authors:
        bib += f"  author = {{{authors}}},\n"
    if year:
        bib += f"  year = {{{year}}},\n"
    bib += "}"
    return bib


class CitationsDialog(tk.Toplevel):
    def __init__(self, parent, config, project, editor):
        super().__init__(parent)
        self.title("Citations")
        self.geometry("700x450")
        self.config_mgr = config
        self.project = project
        self.editor = editor

        self.zclient = None

        self._build_ui()
        self._load_saved_credentials()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        # Zotero connection area
        conn_frame = ttk.LabelFrame(frm, text="Zotero", padding=10)
        conn_frame.pack(fill=tk.X)

        ttk.Label(conn_frame, text="User ID:").grid(row=0, column=0, sticky=tk.W)
        self.z_user = ttk.Entry(conn_frame, width=30)
        self.z_user.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(conn_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W)
        self.z_key = ttk.Entry(conn_frame, width=50, show='*')
        self.z_key.grid(row=1, column=1, padx=5, pady=2)

        ttk.Button(conn_frame, text="Connect", command=self._connect_zotero).grid(row=0, column=2, rowspan=2, padx=8)
        ttk.Button(conn_frame, text="Autodetect from Key", command=self._autodetect_zotero_from_key).grid(row=0, column=3, rowspan=2, padx=6)

        # Mendeley connection area
        mframe = ttk.LabelFrame(frm, text="Mendeley", padding=10)
        mframe.pack(fill=tk.X, pady=(6,0))

        ttk.Label(mframe, text="Client ID:").grid(row=0, column=0, sticky=tk.W)
        self.m_client_id = ttk.Entry(mframe, width=30)
        self.m_client_id.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(mframe, text="Client Secret:").grid(row=1, column=0, sticky=tk.W)
        self.m_client_secret = ttk.Entry(mframe, width=50, show='*')
        self.m_client_secret.grid(row=1, column=1, padx=5, pady=2)

        ttk.Button(mframe, text="Authenticate", command=self._authenticate_mendeley).grid(row=0, column=2, rowspan=2, padx=8)

        # Items list and actions
        list_frame = ttk.Frame(frm)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        # Zotero list
        z_frame = ttk.LabelFrame(list_frame, text="Zotero Items", padding=6)
        z_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.items_list = tk.Listbox(z_frame)
        self.items_list.pack(fill=tk.BOTH, expand=True)
        self.items_list.bind('<Double-Button-1>', self._insert_selected_citation)

        # Mendeley list
        m_frame = ttk.LabelFrame(list_frame, text="Mendeley Items", padding=6)
        m_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6)
        self.m_items_list = tk.Listbox(m_frame)
        self.m_items_list.pack(fill=tk.BOTH, expand=True)
        self.m_items_list.bind('<Double-Button-1>', self._insert_selected_mendeley)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=6)

        ttk.Button(btn_frame, text="Refresh Zotero", command=self._refresh_list).pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text="Insert Zotero", command=self._insert_selected_citation).pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text="Import Zotero → .bib", command=self._import_selected_to_bib).pack(fill=tk.X, pady=4)
        ttk.Separator(btn_frame, orient=VERTICAL).pack(fill=tk.X, pady=6)
        ttk.Button(btn_frame, text="Refresh Mendeley", command=self._refresh_mendeley_list).pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text="Insert Mendeley", command=self._insert_selected_mendeley).pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text="Import Mendeley → .bib", command=self._import_selected_mendeley).pack(fill=tk.X, pady=4)
        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.BOTTOM, fill=tk.X, pady=4)

    def _load_saved_credentials(self):
        user = self.config_mgr.get('zotero_user_id', '')
        key = self.config_mgr.get('zotero_api_key', '')
        if user:
            self.z_user.insert(0, user)
        if key:
            self.z_key.insert(0, key)
        # Load saved Mendeley client id/secret if present
        mid = self.config_mgr.get('mendeley_client_id', '')
        msec = self.config_mgr.get('mendeley_client_secret', '')
        if mid:
            self.m_client_id.insert(0, mid)
        if msec:
            self.m_client_secret.insert(0, msec)

    def _connect_zotero(self):
        uid = self.z_user.get().strip()
        api = self.z_key.get().strip()
        if not uid or not api:
            messagebox.showwarning("Missing", "Please provide both Zotero User ID and API Key.")
            return

        self.zclient = ZoteroClient(user_id=uid, api_key=api)
        # Save to settings for future runs
        try:
            self.config_mgr.set('zotero_user_id', uid)
            self.config_mgr.set('zotero_api_key', api)
        except Exception:
            pass

        self._refresh_list()

    def _autodetect_zotero_from_key(self):
        api = self.z_key.get().strip()
        if not api:
            messagebox.showwarning("Missing", "Please paste your Zotero API Key first.")
            return

        zc = ZoteroClient(api_key=api)
        ok = zc.configure_with_key(api)
        if ok and zc.user_id:
            self.zclient = zc
            # Save detected values
            try:
                self.config_mgr.set('zotero_api_key', api)
                self.config_mgr.set('zotero_user_id', zc.user_id)
            except Exception:
                pass
            self.z_user.delete(0, tk.END)
            self.z_user.insert(0, zc.user_id)
            messagebox.showinfo("Detected", f"Zotero user id detected: {zc.user_id}")
            self._refresh_list()
            return

        # If autodetect failed, prompt the user to open the Zotero Keys page
        if messagebox.askyesno("Autodetect Failed", "Could not auto-detect user id. Open Zotero keys page to create a personal API key? "):
            import webbrowser
            webbrowser.open('https://www.zotero.org/settings/keys')

    # --- Mendeley Integration ---
    def _connect_mendeley(self, token: str):
        self.mclient = MendeleyClient(access_token=token)
        try:
            self.config_mgr.set('mendeley_access_token', token)
        except Exception:
            pass
        self._refresh_mendeley_list()

    def _refresh_mendeley_list(self):
        # Load saved token if not configured
        token = getattr(self, 'mendeley_token', None) or self.config_mgr.get('mendeley_access_token', '')
        if not getattr(self, 'mclient', None) or not self.mclient.is_configured():
            if not token:
                # Prompt for token (simple approach)
                token = simpledialog.askstring("Mendeley Token", "Paste your Mendeley access token:")
                if not token:
                    return
                self.mendeley_token = token
            self._connect_mendeley(token)

        self.m_items_list.delete(0, tk.END)
        items = self.mclient.list_documents(limit=50)
        self._m_items_cache = []
        for doc in items:
            title = doc.get('title') or doc.get('id')
            display = f"{title} [{doc.get('id')}]"
            self.m_items_list.insert(tk.END, display)
            self._m_items_cache.append(doc)

    def _get_selected_mendeley(self):
        sel = self.m_items_list.curselection()
        if not sel:
            messagebox.showinfo("Select", "Please select a Mendeley item first.")
            return None
        idx = sel[0]
        return self._m_items_cache[idx]

    def _insert_selected_mendeley(self, event=None):
        doc = self._get_selected_mendeley()
        if not doc:
            return
        key = f"mendeley-{doc.get('id')}"
        try:
            self.editor.insert_at_cursor(key)
            self.editor.insert_at_cursor('}')
        except Exception:
            pass

    def _import_selected_mendeley(self):
        doc = self._get_selected_mendeley()
        if not doc:
            return
        bib = _mendeley_to_bibtex(doc)
        if not bib:
            messagebox.showerror("Error", "Could not generate BibTeX for this item.")
            return

        bib_path = None
        try:
            if getattr(self.project, 'project_root', None):
                bib_path = Path(self.project.project_root) / 'references.bib'
            else:
                bib_path = Path.cwd() / 'references.bib'
        except Exception:
            bib_path = Path.cwd() / 'references.bib'

        ok = add_entry(bib_path, bib)
        if ok:
            messagebox.showinfo("Imported", f"Imported into {bib_path}")
        else:
            messagebox.showwarning("Skipped", "Entry already exists or import failed.")

    def _refresh_list(self):
        self.items_list.delete(0, tk.END)
        if not self.zclient or not self.zclient.is_configured():
            messagebox.showinfo("Not connected", "Connect to Zotero first.")
            return

        items = self.zclient.list_items(limit=50)
        self._items_cache = []
        for it in items:
            key = it.get('key')
            data = it.get('data', {})
            title = data.get('title') or data.get('publicationTitle') or key
            display = f"{title} [{key}]"
            self.items_list.insert(tk.END, display)
            self._items_cache.append({'key': key, 'title': title})

    def _authenticate_mendeley(self):
        # Use fields or saved config
        client_id = self.m_client_id.get().strip() or self.config_mgr.get('mendeley_client_id', '')
        client_secret = self.m_client_secret.get().strip() or self.config_mgr.get('mendeley_client_secret', '')
        if not client_id or not client_secret:
            messagebox.showwarning("Missing", "Provide Mendeley Client ID and Client Secret (from developer console).")
            return

        # Save to settings
        try:
            self.config_mgr.set('mendeley_client_id', client_id)
            self.config_mgr.set('mendeley_client_secret', client_secret)
        except Exception:
            pass

        # Perform interactive OAuth
        try:
            from citations.mendeley_client import MendeleyClient
            mc = MendeleyClient()
            ok = mc.authenticate_interactive(client_id, client_secret, scope='all', port=8086, timeout=180)
            if not ok:
                messagebox.showerror("Auth Failed", "Mendeley authentication failed or timed out.")
                return

            # Save access token
            self.mclient = mc
            try:
                self.config_mgr.set('mendeley_access_token', mc.access_token)
            except Exception:
                pass

            messagebox.showinfo("Authenticated", "Mendeley authentication completed.")
            self._refresh_mendeley_list()
        except Exception as e:
            messagebox.showerror("Error", f"Mendeley auth error: {e}")

    def _get_selected(self):
        sel = self.items_list.curselection()
        if not sel:
            messagebox.showinfo("Select", "Please select an item first.")
            return None
        idx = sel[0]
        return self._items_cache[idx]

    def _insert_selected_citation(self, event=None):
        sel = self._get_selected()
        if not sel:
            return
        key = sel['key']
        # Insert citation at cursor in editor
        try:
            self.editor.insert_at_cursor(key)
            # If the user typed \cite{ just before, we should insert key and close brace
            # Try to detect if preceding text endswith \cite{
            # Insert pattern: key}
            # Simpler approach: insert key + '}'
            self.editor.insert_at_cursor('}')
        except Exception:
            pass

    def _import_selected_to_bib(self):
        sel = self._get_selected()
        if not sel:
            return
        key = sel['key']
        bib = self.zclient.get_bibtex_for_item(key)
        if not bib:
            messagebox.showerror("Error", "Could not fetch BibTeX for this item.")
            return

        # Determine project bib path
        bib_path = None
        try:
            if getattr(self.project, 'project_root', None):
                bib_path = Path(self.project.project_root) / 'references.bib'
            else:
                bib_path = Path.cwd() / 'references.bib'
        except Exception:
            bib_path = Path.cwd() / 'references.bib'

        ok = add_entry(bib_path, bib)
        if ok:
            messagebox.showinfo("Imported", f"Imported {key} into {bib_path}")
        else:
            messagebox.showwarning("Skipped", "Entry already exists or import failed.")
