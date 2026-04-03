"""
Latex Pro Studio - Project & File Manager
Handles file I/O, Treeview data generation, and ZIP archiving.
GitHub: https://github.com/ismail-baklouti/latex-pro-studio
"""

from asyncio import subprocess
import os
import shutil
import sys
import zipfile
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ProjectManager:
    def __init__(self):
        self.project_root = None
        self.active_file = None
        # Supported extensions for the editor
        self.editable_extensions = {'.tex', '.bib', '.txt', '.sty', '.cls', '.md', '.json'}

    def set_project_dir(self, directory_path):
        """Sets the current working project directory."""
        if os.path.isdir(directory_path):
            self.project_root = Path(directory_path)
            logger.info(f"Project root set to: {self.project_root}")
            return True
        return False

    def get_directory_structure(self, root_path=None):
        """
        Recursively scans the directory to build a data structure for the UI Treeview.
        Returns a list of dictionaries.
        """
        if root_path is None:
            root_path = self.project_root
        
        if not root_path:
            return []

        items = []
        try:
            # Sort: Folders first, then files alphabetically
            for entry in sorted(os.scandir(root_path), key=lambda e: (not e.is_dir(), e.name.lower())):
                # Skip hidden files (like .git or .vscode)
                if entry.name.startswith('.'):
                    continue

                item_data = {
                    "name": entry.name,
                    "path": entry.path,
                    "is_dir": entry.is_dir(),
                    "size": self._format_size(entry.stat().st_size) if entry.is_file() else "",
                    "modified": datetime.fromtimestamp(entry.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "children": []
                }

                if entry.is_dir():
                    item_data["children"] = self.get_directory_structure(entry.path)
                
                items.append(item_data)
        except Exception as e:
            logger.error(f"Error scanning directory {root_path}: {e}")
            
        return items

    def load_file_content(self, file_path):
        """Reads file content safely."""
        path = Path(file_path)
        if not path.is_file():
            return None
        
        try:
            # Attempt to read as UTF-8
            return path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Could not read file {file_path}: {e}")
            return None

    def save_file_content(self, file_path, content):
        """Writes content to a file."""
        try:
            Path(file_path).write_text(content, encoding='utf-8')
            self.active_file = file_path
            return True
        except Exception as e:
            logger.error(f"Save failed for {file_path}: {e}")
            return False

    def create_new_item(self, parent_dir, name, is_folder=False):
        """Creates a new file or directory."""
        new_path = Path(parent_dir) / name
        try:
            if is_folder:
                new_path.mkdir(parents=True, exist_ok=True)
            else:
                new_path.touch()
            return True
        except Exception as e:
            logger.error(f"Creation failed: {e}")
            return False

    def delete_item(self, path):
        """Deletes a file or folder (recursive)."""
        try:
            path = Path(path)
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            return True
        except Exception as e:
            logger.error(f"Deletion failed: {e}")
            return False

    def export_project_zip(self, output_zip_path):
        """Compresses the entire project into a ZIP file."""
        if not self.project_root:
            return False
        
        try:
            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(self.project_root):
                    for file in files:
                        file_path = Path(root) / file
                        # Create relative path for the zip structure
                        arc_name = file_path.relative_to(self.project_root)
                        zf.write(file_path, arc_name)
            return True
        except Exception as e:
            logger.error(f"Export ZIP failed: {e}")
            return False

    def import_project_zip(self, zip_path, extract_to):
        """Extracts a ZIP file into a new project directory."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_to)
            self.set_project_dir(extract_to)
            return True
        except Exception as e:
            logger.error(f"Import ZIP failed: {e}")
            return False

    def _format_size(self, size):
        """Converts bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def open_in_system_viewer(self, file_path):
        """Opens the file with the system's default application (Adobe, Foxit, etc.)"""
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return False

        try:
            if sys.platform == 'win32':
                # Windows standard
                os.startfile(str(path))
            elif sys.platform == 'darwin':
                # macOS standard
                subprocess.call(['open', str(path)])
            else:
                # Linux standard
                subprocess.call(['xdg-open', str(path)])
            return True
        except Exception as e:
            logger.error(f"Failed to open external viewer: {e}")
            return False
        
    def open_project_in_explorer(self):
        """Opens the project folder in the OS file explorer."""
        if self.project_root:
            return self.open_in_system_viewer(self.project_root)