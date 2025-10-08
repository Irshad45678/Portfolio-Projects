import os
import json
from pathlib import Path

import streamlit as st
import pandas as pd

try:
    import openai  # deprecated: will be removed
except Exception:
    openai = None
try:
    import groq  # deprecated: will be removed
except Exception:
    groq = None
try:
    import google.generativeai as genai
except Exception:
    genai = None
try:
    import requests
except Exception:
    requests = None


BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR.parent / "prompts"


def load_template(template_filename: str) -> dict:
    template_path = PROMPTS_DIR / template_filename
    with open(template_path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_prompt(template: dict, audience_role: str, data_text: str, timeframe: str | None = None, extra_vars: dict | None = None) -> tuple[str, str]:
    system_prompt = template.get("prompt", {}).get("system", "")
    user_prompt = template.get("prompt", {}).get("user", "")

    variables = {"audience_role": audience_role}
    # Map data key by template type
    if "sales_data" in user_prompt:
        variables["sales_data"] = data_text
    if "hr_data" in user_prompt:
        variables["hr_data"] = data_text
    if "finance_data" in user_prompt:
        variables["finance_data"] = data_text
    if "support_data" in user_prompt:
        variables["support_data"] = data_text

    # Populate timeframe if provided, else leave for defaulting
    if timeframe:
        variables["timeframe"] = timeframe
    # Optional variables like currency, etc.
    if extra_vars:
        variables.update(extra_vars)

    # Apply template defaults for missing variables (e.g., timeframe, currency)
    var_specs = template.get("variables", {})
    for key, spec in var_specs.items():
        if key not in variables and isinstance(spec, dict):
            default_val = spec.get("default")
            if default_val is not None:
                variables[key] = default_val

    # Safe formatting: missing keys default to ""
    try:
        from collections import defaultdict
        rendered_user = user_prompt.format_map(defaultdict(str, variables))
    except Exception:
        # Fallback to best-effort format
        rendered_user = user_prompt
    return system_prompt, rendered_user


def file_to_text(uploaded_file, input_type: str, sample_rows: int | None = None) -> str:
    if input_type == "CSV":
        df = pd.read_csv(uploaded_file)
        if sample_rows and sample_rows > 0:
            df = df.head(sample_rows)
        return df.to_csv(index=False)
    if input_type == "JSON":
        data = json.load(uploaded_file)
        return json.dumps(data, ensure_ascii=False, indent=2)
    # Text
    return uploaded_file.read().decode("utf-8", errors="ignore")


def estimate_tokens(*texts: str) -> int:
    # Very rough heuristic: ~4 chars per token
    total_chars = sum(len(t) for t in texts if isinstance(t, str))
    return max(1, total_chars // 4)


def summarize_input_text(raw_text: str, input_type: str, max_chars: int = 1500) -> str:
    if input_type == "CSV":
        try:
            from io import StringIO
            df = pd.read_csv(StringIO(raw_text))
            lines = []
            lines.append("[CSV Summary]")
            lines.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
            lines.append("Columns: " + ", ".join(map(str, df.columns.tolist())))
            # Basic numeric overview
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if numeric_cols:
                desc = df[numeric_cols].describe().loc[["mean", "min", "max"]]
                lines.append("Numeric overview (mean/min/max):")
                lines.append(desc.to_csv())
            # Include a tiny head sample for context
            head_csv = df.head(3).to_csv(index=False)
            lines.append("Sample (first 3 rows):")
            lines.append(head_csv)
            text = "\n".join(lines)
            return text[:max_chars]
        except Exception:
            return raw_text[:max_chars]
    elif input_type == "JSON":
        try:
            obj = json.loads(raw_text)
            compact = json.dumps(obj, ensure_ascii=False)  # no spaces
            return compact[:max_chars]
        except Exception:
            return raw_text[:max_chars]
    # Text
    return raw_text[:max_chars]


def build_kpi_table_markdown(
    csv_text: str,
    report_type: str,
    currency_symbol: str | None = None,
    use_indian_grouping: bool = False,
) -> str:
    try:
        from io import StringIO
        df = pd.read_csv(StringIO(csv_text))
    except Exception:
        return ""

    def format_indian_commas(value: float | int) -> str:
        try:
            n = int(round(float(value)))
        except Exception:
            return str(value)
        s = str(abs(n))
        if len(s) <= 3:
            out = s
        else:
            # last 3 digits
            last3 = s[-3:]
            rest = s[:-3]
            # group rest in 2s
            parts = []
            while len(rest) > 2:
                parts.insert(0, rest[-2:])
                rest = rest[:-2]
            if rest:
                parts.insert(0, rest)
            out = ",".join(parts + [last3])
        if n < 0:
            out = "-" + out
        return out

    def fmt_num(x):
        try:
            val = float(x)
            if use_indian_grouping:
                formatted = format_indian_commas(val)
            else:
                formatted = f"{val:,.0f}"
            if currency_symbol:
                return f"{currency_symbol}{formatted}"
            return formatted
        except Exception:
            return str(x)

    lines: list[str] = []
    if report_type == "Sales Performance Report":
        cols = {c.lower(): c for c in df.columns}
        need = ["revenue", "leads", "closeddeals"]
        if all(k in cols for k in need):
            rev, leads, deals = cols["revenue"], cols["leads"], cols["closeddeals"]
            total_rev = df[rev].sum()
            avg_conv = None
            try:
                avg_conv = (df[deals].sum() / df[leads].sum()) * 100 if df[leads].sum() else None
            except Exception:
                avg_conv = None
            lines.append("| KPI | Value |")
            lines.append("|---|---|")
            lines.append(f"| Total Revenue | {fmt_num(total_rev)} |")
            if avg_conv is not None:
                lines.append(f"| Lead→Deal Conversion % | {avg_conv:.1f}% |")
            lines.append(f"| Total Leads | {fmt_num(df[leads].sum())} |")
            lines.append(f"| Total Closed Deals | {fmt_num(df[deals].sum())} |")
    elif report_type == "HR Hiring Summary":
        cols = {c.lower(): c for c in df.columns}
        need = ["hires", "attrition"]
        if all(k in cols for k in need):
            hires, attr = cols["hires"], cols["attrition"]
            total_hires = df[hires].sum()
            total_attr = df[attr].sum()
            attr_rate = (total_attr / total_hires * 100) if total_hires else None
            lines.append("| KPI | Value |")
            lines.append("|---|---|")
            lines.append(f"| Total Hires | {fmt_num(total_hires)} |")
            lines.append(f"| Total Attrition | {fmt_num(total_attr)} |")
            if attr_rate is not None:
                lines.append(f"| Attrition Rate % | {attr_rate:.1f}% |")
    elif report_type == "Financial KPI Snapshot":
        cols = {c.lower(): c for c in df.columns}
        need = ["revenue", "costs", "profit"]
        if all(k in cols for k in need):
            rev, costs, profit = cols["revenue"], cols["costs"], cols["profit"]
            total_rev = df[rev].sum()
            total_costs = df[costs].sum()
            total_profit = df[profit].sum()
            margin = (total_profit / total_rev * 100) if total_rev else None
            lines.append("| KPI | Value |")
            lines.append("|---|---|")
            lines.append(f"| Total Revenue | {fmt_num(total_rev)} |")
            lines.append(f"| Total Costs | {fmt_num(total_costs)} |")
            lines.append(f"| Total Profit | {fmt_num(total_profit)} |")
            if margin is not None:
                lines.append(f"| Profit Margin % | {margin:.1f}% |")
    elif report_type == "Customer Support Report":
        cols = {c.lower(): c for c in df.columns}
        need = ["ticketsraised", "ticketsresolved"]
        if all(k in cols for k in need):
            raised, resolved = cols["ticketsraised"], cols["ticketsresolved"]
            total_raised = df[raised].sum()
            total_resolved = df[resolved].sum()
            res_rate = (total_resolved / total_raised * 100) if total_raised else None
            avg_rt = None
            for cand in ["avgresponsetime(min)", "avgresponsetime", "response_time", "avgresponsetime(min)"]:
                if cand in cols:
                    try:
                        avg_rt = float(df[cols[cand]].mean())
                    except Exception:
                        avg_rt = None
                    break
            lines.append("| KPI | Value |")
            lines.append("|---|---|")
            lines.append(f"| Tickets Raised | {fmt_num(total_raised)} |")
            lines.append(f"| Tickets Resolved | {fmt_num(total_resolved)} |")
            if res_rate is not None:
                lines.append(f"| Resolution Rate % | {res_rate:.1f}% |")
            if avg_rt is not None:
                lines.append(f"| Avg Response Time (min) | {avg_rt:.0f} |")

    # Fallback: ensure a minimal KPI table exists even if we couldn't compute domain KPIs
    if not lines:
        lines.append("| KPI | Value |")
        lines.append("|---|---|")
        try:
            lines.append(f"| Rows | {len(df)} |")
            lines.append(f"| Columns | {len(df.columns)} |")
        except Exception:
            lines.append("| Rows | N/A |")
            lines.append("| Columns | N/A |")
    return "\n".join(lines)


st.set_page_config(page_title="AI Executive Report Generator", page_icon="📑", layout="centered")
st.title("AI Executive Report Generator")
st.caption("Generate executive-style reports from CSV/JSON/Text using prompt templates.")

with st.sidebar:
    st.header("Settings")
    provider = st.selectbox("Provider", [
        "Preview only (no API)",
        "Gemini",
        "OpenRouter",
    ], index=0)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.1)
    max_tokens = st.slider("Max tokens", 128, 1024, 400, 32)
    sample_rows = st.number_input("CSV: sample first N rows", min_value=1, max_value=1000, value=5, step=1)
    debug_mode = st.checkbox("Debug mode (show raw API payload/response)", value=False)
    summarize_toggle = st.checkbox("Summarize input before generation (local)", value=True)
    summarize_chars = st.slider("Summarize to ~N characters", 300, 3000, 1200, 100)
    # India preferences (always on)
    st.subheader("India Preferences")
    west_state = st.text_input("West → State", value="Maharashtra")
    east_state = st.text_input("East → State", value="West Bengal")
    north_state = st.text_input("North → State", value="Delhi")
    south_state = st.text_input("South → State", value="Karnataka")

    # API keys (OpenAI/Groq removed)
    gemini_key = st.text_input("GEMINI_API_KEY", value=os.getenv("GEMINI_API_KEY", ""), type="password")
    openrouter_key = st.text_input("OPENROUTER_API_KEY", value=os.getenv("OPENROUTER_API_KEY", ""), type="password")

    # Model per provider
    if provider == "Gemini":
        model = st.text_input("Model", value="gemini-1.5-flash")
    elif provider == "OpenRouter":
        model = st.selectbox(
            "Model",
            [
                "google/gemma-2-9b-it:free",
                "meta-llama/llama-3.1-8b-instruct:free",
                "nousresearch/hermes-2-pro-llama-3-8b:free",
                "neversleep/noromaid-mixtral-8x7b-instruct:free",
            ],
            index=0,
        )
    else:
        model = "preview"


TEMPLATES = {
    "Sales Performance Report": "sales_report.json",
    "HR Hiring Summary": "hr_hiring_summary.json",
    "Financial KPI Snapshot": "finance_kpi_snapshot.json",
    "Customer Support Report": "support_report.json",
}


col1, col2 = st.columns(2)
with col1:
    report_type = st.selectbox("Report Type", list(TEMPLATES.keys()))
with col2:
    audience_role = st.selectbox("Audience Role", ["CEO", "Manager", "Analyst", "CFO", "CHRO", "Support Manager"]) 

input_type = st.radio("Input Type", ["CSV", "JSON", "Text"], horizontal=True)
uploaded = st.file_uploader("Upload your data", type=["csv", "json", "txt"]) 
timeframe = st.text_input("Timeframe (optional)", value="")

extra_vars: dict = {}
if report_type == "Financial KPI Snapshot":
    extra_vars["currency"] = st.text_input("Currency symbol/code", value="₹")

template = load_template(TEMPLATES[report_type])

if uploaded:
    data_text = file_to_text(uploaded, input_type, sample_rows if input_type == "CSV" else None)
    # Always localize Sales regions to Indian states; values customizable in sidebar
    if input_type == "CSV" and report_type == "Sales Performance Report":
        try:
            import io
            df_loc = pd.read_csv(io.StringIO(data_text))
            # Normalize Region names to Indian states
            if "Region" in df_loc.columns:
                mapping = {
                    "West": west_state,
                    "East": east_state,
                    "North": north_state,
                    "South": south_state,
                }
                df_loc["Region"] = df_loc["Region"].map(mapping).fillna(df_loc["Region"])
            data_text = df_loc.to_csv(index=False)
        except Exception:
            pass
    summarized_text = summarize_input_text(data_text, input_type, summarize_chars) if summarize_toggle else data_text
    # If CSV, compute KPI table and append for grounding
    # Determine currency preferences for KPI table
    currency_symbol = None
    indian_grouping = False
    if input_type == "CSV" and report_type == "Financial KPI Snapshot":
        currency_symbol = extra_vars.get("currency", None)
    if input_type == "CSV" and report_type == "Sales Performance Report":
        currency_symbol = "₹"
        indian_grouping = True
    kpi_md = build_kpi_table_markdown(
        data_text,
        report_type,
        currency_symbol=currency_symbol,
        use_indian_grouping=indian_grouping,
    ) if input_type == "CSV" else ""
    if input_type == "CSV":
        summarized_text = f"{summarized_text}\n\n[KPI Table]\n{kpi_md}"
    st.subheader("Input Preview")
    if input_type == "CSV":
        try:
            df_preview = pd.read_csv(pd.io.common.StringIO(data_text))
            st.dataframe(df_preview.head())
        except Exception:
            st.code(data_text)
    else:
        st.code(data_text)

    # Always hint INR for Sales
    if input_type == "CSV" and report_type == "Sales Performance Report":
        summarized_text = f"Currency: INR (₹)\n\n{summarized_text}"
    sys_prompt, user_prompt = render_prompt(template, audience_role, summarized_text, timeframe or None, extra_vars)

    with st.expander("Rendered Prompt (preview)"):
        st.markdown("**System**")
        st.code(sys_prompt)
        st.markdown("**User**")
        st.code(user_prompt)
        est_tokens = estimate_tokens(sys_prompt, user_prompt)
        st.caption(f"Estimated prompt tokens: ~{est_tokens} | Max response tokens: {int(max_tokens)}")

    generate = st.button("Generate Report")
    if generate:
        content = None
        try:
            if provider == "Gemini":
                if not (genai and gemini_key):
                    raise RuntimeError("Gemini not configured")
                genai.configure(api_key=gemini_key)
                model_obj = genai.GenerativeModel(model)
                gemini_prompt = f"System:\n{sys_prompt}\n\nUser:\n{user_prompt}"
                resp = model_obj.generate_content(
                    gemini_prompt,
                    generation_config={
                        "temperature": float(temperature),
                        "max_output_tokens": int(max_tokens),
                    },
                )
                content = resp.text
            elif provider == "OpenRouter":
                if not (requests and openrouter_key):
                    raise RuntimeError("OpenRouter not configured")
                headers = {
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8501",
                    "X-Title": "Exec Report Generator",
                }
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": float(temperature),
                    "max_tokens": int(max_tokens),
                }
                if debug_mode:
                    with st.expander("OpenRouter request payload"):
                        st.json(payload)
                try:
                    r = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=60,
                    )
                    r.raise_for_status()
                    data = r.json()
                except requests.HTTPError as http_err:
                    # Show server response body for easier debugging
                    err_text = getattr(http_err.response, "text", "") if hasattr(http_err, "response") else ""
                    raise RuntimeError(f"OpenRouter HTTP error {getattr(http_err.response, 'status_code', '')}: {err_text}")
                if debug_mode:
                    with st.expander("OpenRouter raw response"):
                        st.json(data)
                content = data["choices"][0]["message"]["content"]
            else:
                raise RuntimeError("Preview only: no API calls")
        except Exception as e:
            st.error(f"Generation failed: {e}")
            content = None

        if content:
            st.markdown("## 📑 Generated Report")
            st.markdown(content)
            st.download_button("Download .md", data=content, file_name="report.md", mime="text/markdown")
        else:
            st.info("Copy the rendered prompt above into your chosen web UI (e.g., ChatGPT/Gemini).")

else:
    st.info("Upload a CSV/JSON/Text file to begin.")

