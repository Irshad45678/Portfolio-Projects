# Automated Executive Report Prompt Pack

Generate business-ready executive reports (Sales, HR, Finance, Support) from CSV/JSON/Text using reusable AI prompt templates and a simple Streamlit app.

## What this project currently does
- Provides four ready-to-use prompt templates under `prompts/` with a consistent schema and guardrails.
- Includes sample input datasets under `examples/` and example report outputs for reference.
- Ships a minimal Streamlit app (`app/streamlit_app.py`) that:
  - Lets you upload CSV/JSON/Text
  - Selects a report type and audience
  - Renders the prompt (preview)
  - Optionally calls OpenAI (if API key provided) to generate the report
  - Allows downloading the generated report as Markdown

You can use the templates in any LLM, or run the Streamlit demo locally.

## Repo structure
```
.
├─ app/
│  ├─ requirements.txt        # Streamlit + dependencies
│  └─ streamlit_app.py        # Minimal UI to render prompts and call OpenAI
├─ prompts/                   # Prompt templates (JSON)
│  ├─ sales_report.json
│  ├─ hr_hiring_summary.json
│  ├─ finance_kpi_snapshot.json
│  └─ support_report.json
├─ examples/                  # Sample inputs and example outputs
│  ├─ input_sales.csv
│  ├─ output_sales_report.md
│  ├─ input_hr.csv
│  ├─ output_hr_report.md
│  ├─ input_finance.csv
│  ├─ output_finance_report.md
│  ├─ input_support.csv
│  └─ output_support_report.md
└─ README.md                  # You are here
```

## Quickstart (Windows PowerShell)
1) Navigate to the project directory
```
cd E:\Automated_Executive_Report_Prompt_Pack
```

2) Create and activate a virtual environment (optional but recommended)
```
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3) Install dependencies
```
pip install -r app\requirements.txt
```

4) (Optional) Set your OpenAI API key
```
$env:OPENAI_API_KEY = "sk-..."
```

5) Run the Streamlit app
```
streamlit run app\streamlit_app.py
```

6) Open your browser
- Streamlit will open automatically. If not, visit `http://localhost:8501`.

## Copy/paste setup (Python 3.11 venv)

PowerShell (recommended):
```
cd E:\Automated_Executive_Report_Prompt_Pack
deactivate 2>$null
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install -U pip
pip install -r app\requirements.txt
# Optional: set a provider key (example: Groq)
$env:GROQ_API_KEY="REPLACE_ME"
python -m streamlit run app\streamlit_app.py
```

CMD (alternative):
```
cd /d E:\Automated_Executive_Report_Prompt_Pack
deactivate 2>nul
rmdir /s /q .venv
py -3.11 -m venv .venv
\.venv\Scripts\activate.bat
python --version
python -m pip install -U pip
pip install -r app\requirements.txt
set GROQ_API_KEY=REPLACE_ME
python -m streamlit run app\streamlit_app.py
```

## Using the app
- Report Type: pick one of Sales, HR, Finance, Support.
- Audience Role: select CEO/Manager/Analyst (and CFO/CHRO/Support Manager where relevant).
- Input Type: choose CSV, JSON, or Text.
- Upload File: provide your dataset.
- Timeframe/Currency (optional): fill if relevant.
- Prompt Preview: expand to see system + user prompts.
- Generate Report: if an OpenAI key is set, the app will call the API and render the report; otherwise, you can copy the rendered prompt to your provider of choice.
- Download: save the generated report as `report.md`.

## Without the app (prompt-only usage)
Use any `prompts/*.json` file and substitute variables (e.g., `{audience_role}`, `{sales_data}`) with your data, then submit to your preferred LLM.

## Example datasets
See `examples/` for CSVs and example outputs that match each report type.

## Troubleshooting
- No output? Ensure you set `OPENAI_API_KEY` and your network allows API calls.
- CSV preview fails? The app still shows the raw CSV in code format; verify delimiter and encoding.
- Model errors? Try a different model name (e.g., `gpt-4o` or `gpt-3.5-turbo`) in the sidebar.

## Next steps (optional enhancements)
- Add charts for trends (Streamlit `st.line_chart`, `st.bar_chart`).
- Provider adapter to switch between OpenAI/Claude/Gemini.
- `.env.example` and `.gitignore` for cleaner setup.
- Screenshots and badges in this README.
- One-click deploy to Streamlit Community Cloud.

## License
Add your preferred license (MIT recommended) as `LICENSE` in the repo root.


## Full Forms
CEO: Chief Executive Officer
CFO: Chief Financial Officer
CHRO: Chief Human Resources Officer
ROI: Return on Investment
L&D: Learning and Development
SLA: Service Level Agreement
KPI: Key Performance Indicator
DAU: Daily Active Users
EMEA: Europe, Middle East, and Africa

## Audience Roles
CEO: Needs high-level outcomes, revenue/profit impact, and 1–2 decisions. Minimal detail; focus on direction, risks, and ROI.
Manager: Needs operational levers to act on (regions, funnel steps, staffing). Short, specific actions and owners.
Analyst: Needs concise metrics, deltas, and simple calculations. Clear assumptions, KPI table, and data-grounded insights.
CFO: Needs revenue, cost, margin trends, variance notes, and risk controls. Emphasis on cash/margin and efficiency levers.
CHRO: Needs hiring vs attrition, retention risks, pipeline health, and program-level actions (L&D, comp, policy).
Support Manager: Needs ticket volume, resolution SLA, response-time trends, backlog, and process/staffing fixes.
How this changes the report:
Tone: CEO/CFO more strategic; Manager/Support Manager action-focused; Analyst metric-focused.
Detail: Analyst > Manager > Execs.
Sections: All get Executive Summary + KPI Table; Analyst/Managers get more granular bullets and specific owners.