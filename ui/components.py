"""
Latex Pro Studio - Custom UI Components
Vertical Navigation, Document Outline, and Status Bars.
GitHub: https://github.com/ismail-baklouti/latex-pro-studio
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import re

class SideNavigationBar(ttk.Frame):
    """A vertical icon-based navigation bar for switching between panels."""
    def __init__(self, master, on_switch_callback, **kwargs):
        super().__init__(master, bootstyle=SECONDARY, width=50, **kwargs)
        self.pack_propagate(False)
        self.on_switch = on_switch_callback
        self._build_buttons()

    def _build_buttons(self):
        # Using Emojis for simplicity; in a final build, use SVG/PNG icons
        buttons = [
            ("📁", "project", "Project Explorer"),
            ("🤖", "ai", "AI Assistant"),
            ("📚", "cite", "Citation Manager"),
            ("⚙️", "settings", "Settings")
        ]
        
        for icon, name, tooltip in buttons:
            btn = ttk.Button(
                self, 
                text=icon, 
                bootstyle=(LINK, INVERSE_SECONDARY),
                command=lambda n=name: self.on_switch(n)
            )
            btn.pack(side=TOP, pady=10, fill=X)
            # Add basic tooltip behavior (can be expanded)
            self._add_tooltip(btn, tooltip)

    def _add_tooltip(self, widget, text):
        # A simple tooltip logic could be added here
        pass

class DocumentOutline(ttk.Frame):
    """A treeview that automatically extracts \section and \subsection from LaTeX."""
    def __init__(self, master, on_select_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_select = on_select_callback
        
        ttk.Label(self, text="Document Outline", font=("Helvetica", 10, "bold")).pack(fill=X, pady=5)
        
        self.tree = ttk.Treeview(self, show="tree", bootstyle=INFO)
        self.tree.pack(fill=BOTH, expand=YES)
        self.tree.bind("<<TreeviewSelect>>", self._on_click)

    def update_outline(self, tex_content):
        """Regex-based extraction of LaTeX sections."""
        self.tree.delete(*self.tree.get_children())
        
        # Patterns for sections and subsections
        pattern = re.compile(r"\\(section|subsection|subsubsection)\*?\{(.*?)\}")
        
        last_section = ""
        for match in pattern.finditer(tex_content):
            level = match.group(1)
            title = match.group(2)
            
            if level == "section":
                last_section = self.tree.insert("", "end", text=title, open=True)
            elif level == "subsection" and last_section:
                self.tree.insert(last_section, "end", text=title)
            else:
                self.tree.insert("", "end", text=title)

    def _on_click(self, event):
        item = self.tree.selection()[0]
        title = self.tree.item(item, "text")
        self.on_select(title)

class EditorStatusBar(ttk.Frame):
    """Bottom bar for showing line numbers, compilation status, and encoding."""
    def __init__(self, master, **kwargs):
        super().__init__(master, bootstyle=SECONDARY, **kwargs)
        
        self.status_label = ttk.Label(self, text="Ready", bootstyle=(INVERSE, SECONDARY))
        self.status_label.pack(side=LEFT, padx=10)
        
        self.line_col_label = ttk.Label(self, text="Ln 1, Col 1", bootstyle=(INVERSE, SECONDARY))
        self.line_col_label.pack(side=RIGHT, padx=10)
        
        ttk.Label(self, text="UTF-8", bootstyle=(INVERSE, SECONDARY)).pack(side=RIGHT, padx=20)

    def set_status(self, text, color=SECONDARY):
        self.status_label.config(text=text, bootstyle=(INVERSE, color))

    def update_position(self, line, col):
        self.line_col_label.config(text=f"Ln {line}, Col {col}")

class ErrorMarker(tk.Canvas):
    """A thin canvas strip next to the editor that shows visual blocks for errors."""
    def __init__(self, master, **kwargs):
        super().__init__(master, width=12, bg="#f0f0f0", highlightthickness=0, **kwargs)

    def mark_error(self, line_number, total_lines):
        """Draw a red block proportional to the document length."""
        # Note: This requires mapping the line number to the canvas Y coordinate
        # This is a 'Pro' feature for larger documents.
        pass