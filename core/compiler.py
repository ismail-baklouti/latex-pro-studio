"""
Latex Pro Studio - Compiler Engine
Handles pdflatex and bibtex execution.
GitHub: https://github.com/ismail-baklouti/latex-pro-studio
"""

import subprocess
import os
import re
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class LatexCompiler:
    def __init__(self):
        self.process = None
        self.last_log = ""

    def is_available(self):
        """Check if pdflatex is installed on the system."""
        return shutil.which("pdflatex") is not None

    def compile(self, tex_path, run_bibtex=False):
        """
        Executes the compilation sequence.
        Returns: (bool success, str log, list errors)
        """
        tex_path = Path(tex_path)
        working_dir = tex_path.parent
        file_name = tex_path.name
        base_name = tex_path.stem

        try:
            # 1. First Pass (Generate AUX)
            success, log = self._run_command(['pdflatex', '-interaction=nonstopmode', file_name], working_dir)
            if not success:
                return False, log, self._parse_errors(log)

            # 2. BibTeX (Optional)
            if run_bibtex:
                self._run_command(['bibtex', base_name], working_dir)
                # Second Pass (Incorporate citations)
                self._run_command(['pdflatex', '-interaction=nonstopmode', file_name], working_dir)

            # 3. Final Pass (Resolve references)
            success, log = self._run_command(['pdflatex', '-interaction=nonstopmode', file_name], working_dir)
            
            return success, log, self._parse_errors(log)

        except Exception as e:
            logger.error(f"Compilation crash: {e}")
            return False, str(e), []

    def _run_command(self, cmd, cwd):
        """Internal helper to run subprocess."""
        try:
            # Use 'startupinfo' on Windows to hide the console window
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore',
                startupinfo=startupinfo,
                timeout=30 # Prevent infinite loops
            )
            
            # Check for LaTeX specific errors in stdout even if returncode is 0
            if "! LaTeX Error" in result.stdout or "Fatal error" in result.stdout:
                return False, result.stdout
                
            return result.returncode == 0, result.stdout

        except subprocess.TimeoutExpired:
            return False, "Error: Compilation timed out (30s)."
        except Exception as e:
            return False, f"System Error: {str(e)}"

    def _parse_errors(self, log_content):
        """
        Parses the LaTeX log to find line numbers and error messages.
        Returns a list of dicts: [{'line': 10, 'msg': 'Undefined control sequence'}]
        """
        errors = []
        # Pattern for standard LaTeX errors
        # Example: ! Undefined control sequence. \nl.15 \badcommand
        pattern = re.compile(r"^\!\s+(.*?)\n.*?\s+l\.(\d+)", re.MULTILINE | re.DOTALL)
        
        for match in pattern.finditer(log_content):
            msg = match.group(1).replace('\n', ' ').strip()
            line = int(match.group(2))
            errors.append({'line': line, 'msg': msg})
            
        return errors

    def cleanup_auxiliary(self, project_path):
        """Removes .aux, .log, .out etc. to keep project clean."""
        extensions = ['.aux', '.log', '.out', '.toc', '.blg', '.bbl', '.synctex.gz']
        path = Path(project_path)
        for ext in extensions:
            for file in path.glob(f"*{ext}"):
                try:
                    os.remove(file)
                except:
                    pass