# 🚀 Latex Pro Studio v1.0

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Profile](https://img.shields.io/badge/Developer-Ismail_Baklouti-orange.svg)](https://github.com/ismail-baklouti)

**Latex Pro Studio** is a sophisticated, modular LaTeX editor designed for researchers and engineers. It integrates professional document compilation with **Google Gemini, OpenAI (ChatGPT), and Anthropic** AI and real-time **Mendeley/Zotero** citation management.

---

## 🌟 Key Features

- **🤖 AI Document Assistant:** Generate, refactor, and debug LaTeX environments using Gemini 1.5, OpenAI (ChatGPT), or Anthropic (Claude).
- **📚 Reference Synchronization:** Seamlessly connect to Mendeley and Zotero. Auto-insert `\cite{}` keys and sync `.bib` files.
- **⚡ Live PDF Preview:** High-speed previewer with zoom, scroll, and multi-page rendering.
- **📂 Modular Architecture:** Clean code separation (UI, Core, API, Utils) for easy extension.
- **🎨 Modern Dark/Light Themes:** Built with `ttkbootstrap` for a premium user experience.
- **🔍 Syntax Highlighting:** Intelligent highlighting for commands, environments, and comments.

---

## 🛠️ Installation
1. **Clone the Project**

```bash
git clone https://github.com/ismail-baklouti/latex-pro-studio.git
cd latex-pro-studio
```

2. **Setup a Python virtual environment**

```bash
python -m venv venv
# Activate (Windows)
venv\Scripts\activate
# Activate (macOS / Linux)
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configuration** — create a `.env` file in the project root with your credentials:

```env
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
MENDELEY_APP_ID=your_id
MENDELEY_APP_SECRET=your_secret
```

## ⚡ Quick Start

After installation and adding your keys to `.env`, launch the application from the project root:

```bash
python main.py
```

Open the app, click the toolbar button labelled "🤖 Ask AI" to open the AI Assistant. In the assistant you can:
- Select a provider (`gemini`, `openai`, or `anthropic`).
- Paste or enter an API key in the `API Key` field and check the `Save` box to persist it to settings.
- Add attachments, write a prompt, and press `Run` to send the request.

The assistant shows output in the dialog and offers `Insert Into Editor` for generated LaTeX.

## 🧪 Testing the AI Assistant

- If you don't want to store keys in `.env`, you can paste a provider key directly into the AI Assistant and check `Save`.
- If a provider package is missing, the assistant will report which package to install (for example `pip install openai` or `pip install anthropic`).

## 🌍 Project Site

This repository can be published as a GitHub Pages site at:

- https://ismail-baklouti.github.io/latex-pro-studio (project page)

## 📂 Repository Structure

## core/: Logic for LaTeX compilation and AI communication.
## ui/: All Tkinter layout and custom widget classes.
## citations/: Mendeley OAuth and Zotero API logic.
## utils/: Configuration management and document templates.
## assets/: UI icons and branding images.

## 🤝 Contributing

## Contributions make the open-source community an amazing place to learn and create.
## Fork the Project.
## Create your Feature Branch.
## Commit your Changes.
## Open a Pull Request.

## 👨‍💻 Authors

## Ismail Baklouti & Muhammad Abdul Mujeebu
## GitHub: [@ismail-baklouti](https://github.com/ismail-baklouti)
## GitHub: [@mamujeebu](https://github.com/mamujeebu)
## Professional Focus: AI Engineering, Document Automation, Python UI Development.

## 📜 License

## Distributed under the MIT License. See LICENSE for more information.

### Next Steps for the modular build:
1. **Create the folder structure** on your computer.
2. **Move logic into files**: I will provide the content for `ui/main_window.py` and `core/ai_engine.py` next.

**Which file should I write for you now?**

