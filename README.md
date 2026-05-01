# ProContracts

ProContracts is a Streamlit-based contract intelligence and management system.

## Features

- Upload and parse PDF/DOCX/TXT contracts
- Hybrid clause segmentation (regex first, AI fallback)
- Party detection and definition extraction
- Clause classification, criticality, and red-flag detection
- Favorability and risk analysis by party
- Clause rewrite workshop (Balanced / FavorParty / Aggressive)
- Report exports (XLSX + DOCX)
- Offline-first AI provider routing (Ollama / LM Studio, optional Gemini)
- SQLite persistence + basic login

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Run Web App

```powershell
streamlit run streamlit_app.py
```

## Run CLI

```powershell
python main.py phase1 --file sample_contracts/sample_contract.txt --output output/phase1_contract.json
python main.py classify --contract-json output/phase1_contract.json --output output/classified_contract.json
python main.py favorability --contract-json output/classified_contract.json --output output/favorability_contract.json
python main.py modify --contract-json output/favorability_contract.json --mode Balanced --target-party Party1 --output output/modified_contract_state.json
python main.py report --contract-json output/modified_contract_state.json --output-dir output
```
