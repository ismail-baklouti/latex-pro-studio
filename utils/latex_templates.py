"""
Latex Pro Studio - Document Templates Library
Provides professional boilerplate for various LaTeX document classes.
GitHub: https://github.com/ismail-baklouti/latex-pro-studio
"""

from datetime import datetime

class LatexTemplates:
    """
    A collection of optimized LaTeX templates for quick document creation.
    Used by the UI to populate new files with standard boilerplate.
    """

    @staticmethod
    def get_template_names():
        """Returns a list of available template keys for UI menus."""
        return ["Basic Document", "Academic Article", "Technical Report", "Beamer Presentation", "Professional CV"]

    @staticmethod
    def get_template(name, author="Author Name", title="Document Title"):
        """
        Returns the LaTeX source string for a given template name.
        Injects the author name and title automatically.
        """
        templates = {
            "Basic Document": LatexTemplates._basic_template(),
            "Academic Article": LatexTemplates._article_template(),
            "Technical Report": LatexTemplates._report_template(),
            "Beamer Presentation": LatexTemplates._beamer_template(),
            "Professional CV": LatexTemplates._cv_template()
        }
        
        content = templates.get(name, LatexTemplates._basic_template())
        
        # Replace Placeholders
        content = content.replace("{{TITLE}}", title)
        content = content.replace("{{AUTHOR}}", author)
        content = content.replace("{{DATE}}", datetime.now().strftime("%B %d, %Y"))
        
        return content

    @staticmethod
    def _basic_template():
        return r"""\documentclass{article}
\usepackage[utf8]{inputenc}

\title{{{TITLE}}}
\author{{{AUTHOR}}}
\date{{{DATE}}}

\begin{document}

\maketitle

\section{Introduction}
Start typing your document here...

\end{document}
"""

    @staticmethod
    def _article_template():
        return r"""\documentclass[11pt,a4paper]{article}

% --- Essential Packages ---
\usepackage[utf8]{inputenc}
\usepackage[margin=1in]{geometry}
\usepackage{graphicx}
\usepackage{amsmath, amssymb}
\usepackage{hyperref}
\usepackage[backend=bibtex,style=numeric]{biblatex}

\title{{{TITLE}}}
\author{{{AUTHOR}}}
\date{{{DATE}}}

\begin{document}

\maketitle

\begin{abstract}
This is a standard academic abstract. Replace this text with a summary of your research, methods, and key findings.
\end{abstract}

\section{Introduction}
Provide background information and the motivation for your study here. 

\section{Literature Review}
Discuss related works and how they connect to your research \cite{example_key}.

\section{Methodology}
Explain your experimental setup or theoretical framework.

\section{Results}
Present your findings using figures and tables.

\section{Conclusion}
Summarize your contributions and future work.

\printbibliography

\end{document}
"""

    @staticmethod
    def _report_template():
        return r"""\documentclass[12pt,oneside]{report}

\usepackage[utf8]{inputenc}
\usepackage{geometry}
\usepackage{titlesec}

\title{{{TITLE}}}
\author{{{AUTHOR}}}
\date{{{DATE}}}

\begin{document}

\maketitle
\tableofcontents

\chapter{Executive Summary}
Summarize the entire report here.

\chapter{Project Background}
Detailed background info...

\chapter{Analysis}
Technical data and analysis...

\end{document}
"""

    @staticmethod
    def _beamer_template():
        return r"""\documentclass{beamer}

% --- Theme Selection ---
\usetheme{Madrid}
\usecolortheme{default}

\title{{{TITLE}}}
\author{{{AUTHOR}}}
\institute{Your University / Company}
\date{{{DATE}}}

\begin{document}

\frame{\titlepage}

\begin{frame}
\setbeamertemplate{section in toc}[sections numbered]
\tableofcontents
\end{frame}

\section{Introduction}
\begin{frame}{Motivation}
    \begin{itemize}
        \item Key point 1
        \item Key point 2
        \item Supporting evidence
    \end{itemize}
\end{frame}

\section{Methods}
\begin{frame}{Experimental Setup}
    Describe your methodology here.
\end{frame}

\end{document}
"""

    @staticmethod
    def _cv_template():
        return r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.75in]{geometry}

\begin{document}

\begin{center}
    {\huge \textbf{{{AUTHOR}}}} \\
    \vspace{2mm}
    Email: yourname@email.com | GitHub: github.com/username | Phone: +123 456 789
\end{center}

\section*{Education}
\textbf{University Name} \hfill Location \\
Degree Name \hfill Graduation Date

\section*{Experience}
\textbf{Company Name} \hfill Location \\
\textit{Job Title} \hfill Start Date -- End Date
\begin{itemize}
    \item Achievement 1: Quantified results if possible.
    \item Achievement 2: Tech stack used and problems solved.
\end{itemize}

\section*{Skills}
\textbf{Languages:} Python, C++, Java, LaTeX \\
\textbf{Tools:} Git, Docker, Linux, AI Prompt Engineering

\end{document}
"""