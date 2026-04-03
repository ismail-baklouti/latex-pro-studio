"""
Latex Pro Studio - Main UI Window
GitHub: https://github.com/ismail-baklouti/latex-pro-studio
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from pathlib import Path
import threading
import fitz  # PyMuPDF
from PIL import Image, ImageTk

# Import internal components
from ui.editor import LatexEditor
from ui.citations_dialog import CitationsDialog
from core.compiler import LatexCompiler

class MainWindow:
    def __init__(self, root, project, ai, config):
        self.root = root
        self.project = project
        self.ai = ai
        self.config = config
        self.compiler = LatexCompiler()
        
        # State variables
        self.current_file_path = None
        self.pdf_images = [] # Store references to prevent garbage collection
        
        self._setup_ui()
        self._setup_bindings()

        # 1. Create a Context Menu (Right-click menu)
        self.explorer_menu = tk.Menu(self.root, tearoff=0)
        self.explorer_menu.add_command(label="Open Externally (Adobe/etc.)", command=self._open_selected_externally)
        self.explorer_menu.add_separator()
        self.explorer_menu.add_command(label="Delete File", command=self._delete_selected_file, foreground="red")

        # 2. Bind right-click to the explorer tree
        self.explorer_tree.bind("<Button-3>", self._show_explorer_context_menu)

    def _show_explorer_context_menu(self, event):
        """Displays the right-click menu at mouse position."""
        item = self.explorer_tree.identify_row(event.y)
        if item:
            self.explorer_tree.selection_set(item)
            self.explorer_menu.post(event.x_root, event.y_root)

    def _open_selected_externally(self):
        """Gets path from selected item and calls ProjectManager."""
        selected = self.explorer_tree.selection()
        if not selected: return
        
        file_path = self.explorer_tree.item(selected[0], "values")[0]
        success = self.project.open_in_system_viewer(file_path)
        
        if not success:
            messagebox.showerror("Error", "Could not open external viewer. Is a PDF viewer installed?")

    def _delete_selected_file(self):
        """Delete the selected file or folder after confirmation."""
        selected = self.explorer_tree.selection()
        if not selected:
            return

        file_path = self.explorer_tree.item(selected[0], "values")[0]
        name = Path(file_path).name
        if not messagebox.askyesno("Delete", f"Delete '{name}'? This action cannot be undone."):
            return

        success = self.project.delete_item(file_path)
        if success:
            # If the deleted file was open in the editor, clear it
            try:
                if self.current_file_path and Path(self.current_file_path) == Path(file_path):
                    self.current_file_path = None
                    self.editor.set_text("")
            except Exception:
                pass

            self._refresh_explorer()
        else:
            messagebox.showerror("Error", "Could not delete the selected item.")

    def _setup_ui(self):
        """Create the professional IDE-like layout."""
        # --- 1. Main Toolbar ---
        self.toolbar = ttk.Frame(self.root, bootstyle=SECONDARY)
        self.toolbar.pack(side=TOP, fill=X)
        self._build_toolbar()

        # --- 2. Main Paned Window (Horizontal) ---
        self.main_paned = ttk.PanedWindow(self.root, orient=HORIZONTAL)
        self.main_paned.pack(fill=BOTH, expand=YES)

        # --- 3. Left Panel (Project Explorer) ---
        self.explorer_frame = ttk.Frame(self.main_paned, width=250)
        self.explorer_tree = ttk.Treeview(self.explorer_frame, show="tree", bootstyle=PRIMARY)
        self.explorer_tree.pack(fill=BOTH, expand=YES, padx=2, pady=2)
        self.main_paned.add(self.explorer_frame)

        # --- 4. Center Panel (Editor) ---
        self.editor_frame = ttk.Frame(self.main_paned)
        self.editor = LatexEditor(self.editor_frame)
        self.editor.pack(fill=BOTH, expand=YES)
        self.main_paned.add(self.editor_frame)

        # --- 5. Right Panel (Preview & AI) ---
        self.right_paned = ttk.PanedWindow(self.main_paned, orient=VERTICAL)
        
        # PDF Preview Area
        self.preview_frame = ttk.Frame(self.right_paned)
        self.preview_canvas = tk.Canvas(self.preview_frame, background="#525659")
        self.preview_canvas.pack(fill=BOTH, expand=YES)
        self.right_paned.add(self.preview_frame)

        # AI Chat / Log Area
        self.bottom_frame = ttk.Frame(self.right_paned, height=200)
        self.log_area = ttk.ScrolledText(self.bottom_frame, height=10, font=("Consolas", 10))
        self.log_area.pack(fill=BOTH, expand=YES)
        self.right_paned.add(self.bottom_frame)

        self.main_paned.add(self.right_paned)

    def _build_toolbar(self):
        """Add action buttons with icons (emojis used for simplicity)."""
        btn_config = {"padding": 5, "bootstyle": LINK}
        
        ttk.Button(self.toolbar, text="📁 Open", command=self._open_project, **btn_config).pack(side=LEFT)
        ttk.Button(self.toolbar, text="💾 Save", command=self._save_file, **btn_config).pack(side=LEFT)
        ttk.Separator(self.toolbar, orient=VERTICAL).pack(side=LEFT, padx=5, fill=Y)
        
        self.compile_btn = ttk.Button(self.toolbar, text="⚡ Compile", command=self._start_compilation, bootstyle=SUCCESS)
        self.compile_btn.pack(side=LEFT, padx=5)
        
        ttk.Separator(self.toolbar, orient=VERTICAL).pack(side=LEFT, padx=5, fill=Y)
        ttk.Button(self.toolbar, text="🤖 Ask AI", command=self._open_ai_assistant, **btn_config).pack(side=LEFT)
        ttk.Button(self.toolbar, text="📚 Citations", command=self._open_citations_dialog, **btn_config).pack(side=LEFT, padx=6)

    def _setup_bindings(self):
        """Key shortcuts and mouse events."""
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-Enter>", lambda e: self._start_compilation())
        self.explorer_tree.bind("<<TreeviewSelect>>", self._on_file_selected)
        # Wire citation trigger from editor to open picker
        try:
            self.editor.on_cite_trigger = self._open_citations_dialog
        except Exception:
            pass
        # AI settings removed; AI Assistant provides provider/key management


    # --- Logic Methods ---

    def _open_project(self):
        folder = filedialog.askdirectory()
        if folder:
            self.project.set_project_dir(folder)
            self._refresh_explorer()

    def _refresh_explorer(self):
        """Update the file tree."""
        for i in self.explorer_tree.get_children():
            self.explorer_tree.delete(i)
        
        structure = self.project.get_directory_structure()
        self._fill_tree("", structure)

    def _fill_tree(self, parent, items):
        for item in items:
            node = self.explorer_tree.insert(parent, "end", text=item["name"], values=(item["path"],))
            if item["is_dir"]:
                self._fill_tree(node, item["children"])

    def _on_file_selected(self, event):
        item_id = self.explorer_tree.selection()[0]
        file_path = self.explorer_tree.item(item_id, "values")[0]
        
        if Path(file_path).suffix in self.project.editable_extensions:
            content = self.project.load_file_content(file_path)
            if content is not None:
                self.current_file_path = file_path
                self.editor.set_text(content)

    def _save_file(self):
        if self.current_file_path:
            content = self.editor.get_text()
            self.project.save_file_content(self.current_file_path, content)
        else:
            path = filedialog.asksaveasfilename(defaultextension=".tex")
            if path:
                self.current_file_path = path
                self._save_file()
                self._refresh_explorer()

    def _start_compilation(self):
        """Run compilation in a thread to keep UI responsive."""
        if not self.current_file_path:
            messagebox.showwarning("Warning", "Save the file first!")
            return

        self.compile_btn.config(state=DISABLED, text="⌛ Compiling...")
        self.log_area.delete("1.0", END)
        self.log_area.insert(END, "Compilation started...\n")
        
        thread = threading.Thread(target=self._compile_task, daemon=True)
        thread.start()

    def _compile_task(self):
        success, log, errors = self.compiler.compile(self.current_file_path)
        
        # GUI updates must happen on main thread
        self.root.after(0, lambda: self._on_compilation_complete(success, log, errors))

    def _on_compilation_complete(self, success, log, errors):
        self.compile_btn.config(state=NORMAL, text="⚡ Compile")
        self.log_area.insert(END, log)
        self.log_area.see(END)
        
        if success:
            pdf_path = Path(self.current_file_path).with_suffix(".pdf")
            self._render_pdf(pdf_path)
        else:
            for err in errors:
                self.editor.mark_error(err['line'])
            messagebox.showerror("Error", "LaTeX Compilation Failed. Check Logs.")

    def _render_pdf(self, pdf_path):
        """Live render the PDF using PyMuPDF and PIL."""
        if not pdf_path.exists(): return
        
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(0) # Show first page
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) # 1.5x zoom
            
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            photo = ImageTk.PhotoImage(img)
            
            self.pdf_images = [photo] # Keep reference
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, anchor=NW, image=photo)
            self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))
            doc.close()
        except Exception as e:
            print(f"PDF Rendering failed: {e}")

    def _show_ai_dialog(self):
        """High-end AI Assistant Integration."""
        # We create a more advanced prompt
        query = ttk.dialogs.Querybox.get_string("Task (e.g. 'Fix my errors' or 'Add a table')", "AI Assistant")
        if not query: return

        context = self.editor.get_text()
        
        # Decide the action
        action = "generate"
        if "fix" in query.lower(): action = "fix"
        elif "explain" in query.lower(): action = "explain"

        self.log_area.insert(END, f"\n🤖 AI Status: Performing '{action}'...\n")
        
        self.ai.request_action(
            action=action,
            user_input=query,
            context=context,
            callback=self._handle_ai_result
        )

    def _handle_ai_result(self, result):
        """Intelligent handling of AI output."""
        def update():
            # If the action was a fix, we show a 'Diff' or offer to replace
            if "AI Error" in result:
                self.log_area.insert(END, f"❌ {result}\n", "error")
            else:
                self.log_area.insert(END, "✅ AI Task Complete.\n")
                # Add a specialized log entry for explanations
                self.log_area.insert(END, f"\n--- AI RESPONSE ---\n{result}\n")
                
                # If the result looks like pure LaTeX code (from the fix/generate actions)
                # We could offer to insert it directly
                if "\\documentclass" in result or "\\begin" in result:
                    if messagebox.askyesno("AI Suggestion", "The AI generated code. Insert it at the cursor?"):
                        self.editor.insert_at_cursor(result)
        
        self.root.after(0, update)

    def _on_ai_response(self, response):
        self.root.after(0, lambda: self._display_ai_response(response))

    def _display_ai_response(self, response):
        self.log_area.insert(END, f"\n🤖 AI Response:\n{response}\n")
        self.log_area.see(END)

    def _open_citations_dialog(self):
        """Opens the citations manager/picker dialog."""
        try:
            dlg = CitationsDialog(self.root, config=self.config, project=self.project, editor=self.editor)
            dlg.grab_set()
        except Exception as e:
            messagebox.showerror("Citations", f"Failed to open citations dialog: {e}")

    def _open_ai_assistant(self):
        try:
            from ui.ai_assistant_dialog import AIAssistantDialog
            dlg = AIAssistantDialog(self.root, ai_engine=self.ai, config_mgr=self.config, editor=self.editor)
            dlg.grab_set()
        except Exception as e:
            messagebox.showerror('AI Assistant', f'Failed to open AI assistant: {e}')
    # AI settings dialog removed — use AI Assistant to configure providers/keys