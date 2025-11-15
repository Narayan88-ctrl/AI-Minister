# AI Minister for Nepal — Starter Kit

A minimal, terminal-driven prototype you can run today. It loads example public-spending data, answers questions, and prints clean tables with sources.

## Quick Start

```bash
# 1) Create a project folder and venv
cd ~/ && mkdir -p ai-minister && cd ai-minister
python3 -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run a few demo commands
python3 cli.py budgets --sector roads --region Pokhara
python3 cli.py projects --region Pokhara --top 5
python3 cli.py report --region Pokhara
python3 cli.py ask "Where did the 2024 road budget go in Pokhara?"
```

> If you have an OpenAI API key, export it and `ask` will use GPT for natural-language answers:
```bash
export OPENAI_API_KEY="sk-..."
```
