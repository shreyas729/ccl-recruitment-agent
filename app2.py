from typing import Dict
import os
import json
import PyPDF2
import tempfile
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st
from agno.agent import Agent
from agno.models.groq import Groq
from streamlit_pdf_viewer import pdf_viewer

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Recruitment Scanner",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

* { font-family: 'Inter', sans-serif; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0f0f13;
    color: #e2e2e8;
}

h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 600; }

.hero-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #e2e2e8;
    margin: 0;
    letter-spacing: -0.02em;
}
.hero-sub {
    color: #4b5563;
    font-size: 0.78rem;
    margin-top: 0.3rem;
    font-weight: 400;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.steps-container {
    display: flex;
    align-items: center;
    gap: 0;
    margin: 1.5rem 0;
    padding: 1rem 1.5rem;
    background: #16161d;
    border-radius: 12px;
    border: 1px solid #2a2a35;
}
.step { display: flex; align-items: center; gap: 10px; flex: 1; }
.step-num {
    width: 28px; height: 28px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 600;
    font-size: 0.78rem;
    flex-shrink: 0;
}
.step-num.done { background: #14532d; color: #4ade80; }
.step-num.active { background: #e2e2e8; color: #0f0f13; }
.step-num.pending { background: #1e1e26; color: #4b5563; }
.step-label { font-size: 0.78rem; color: #4b5563; font-weight: 500; }
.step-label.active { color: #e2e2e8; font-weight: 600; }
.step-divider { flex: 1; height: 1px; background: #2a2a35; margin: 0 10px; max-width: 40px; }

.card {
    background: #16161d;
    border: 1px solid #2a2a35;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.card-winner {
    background: #0d1f15;
    border: 1px solid #166534;
    border-top: 3px solid #4ade80;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.card-title {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4b5563;
    margin-bottom: 1rem;
}

.score-row { margin-bottom: 0.8rem; }
.score-label {
    font-size: 0.82rem;
    color: #9ca3af;
    margin-bottom: 4px;
    display: flex;
    justify-content: space-between;
}
.score-track { background: #1e1e26; border-radius: 999px; height: 5px; width: 100%; }
.score-fill { height: 5px; border-radius: 999px; }

.decision-hire {
    background: #0d1f15;
    border: 1px solid #166534;
    border-left: 4px solid #4ade80;
    border-radius: 12px;
    padding: 1.5rem 2rem;
}
.decision-nohire {
    background: #1a0d0d;
    border: 1px solid #7f1d1d;
    border-left: 4px solid #f87171;
    border-radius: 12px;
    padding: 1.5rem 2rem;
}
.decision-title {
    font-size: 1.3rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.01em;
}

.agent-log {
    background: #0d0d12;
    border: 1px solid #2a2a35;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-size: 0.8rem;
    color: #6b7280;
    line-height: 1.7;
    white-space: pre-wrap;
    font-family: 'IBM Plex Mono', monospace;
}

.candidate-card {
    background: #16161d;
    border: 1px solid #2a2a35;
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 0.5rem;
    position: relative;
}
.candidate-card.winner {
    border-color: #166534;
    border-top: 3px solid #4ade80;
    background: #0d1f15;
}
.winner-badge {
    display: inline-block;
    background: #14532d;
    color: #4ade80;
    border: 1px solid #166534;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.7rem;
    font-weight: 600;
    margin-left: 8px;
    vertical-align: middle;
}

.tag-green {
    display: inline-block;
    background: #0d1f15;
    color: #4ade80;
    border: 1px solid #166534;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.74rem;
    margin: 3px;
}
.tag-red {
    display: inline-block;
    background: #1a0d0d;
    color: #f87171;
    border: 1px solid #7f1d1d;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.74rem;
    margin: 3px;
}

[data-testid="stTextInput"] input {
    background: #16161d !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 8px !important;
    color: #e2e2e8 !important;
    font-size: 0.9rem !important;
}
[data-testid="stTextInput"] input::placeholder { color: #4b5563 !important; }
[data-testid="stSelectbox"] > div {
    background: #16161d !important;
    border: 1px solid #2a2a35 !important;
    border-radius: 8px !important;
    color: #e2e2e8 !important;
}

.stButton > button {
    background: #e2e2e8 !important;
    color: #0f0f13 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.5rem 1.4rem !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.8 !important; }

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
ROLE_REQUIREMENTS: Dict[str, dict] = {
    "ai_ml_engineer": {
        "label": "AI / ML Engineer",
        "skills": ["Python", "PyTorch/TensorFlow", "Machine Learning", "Deep Learning", "MLOps", "LLM/RAG/Finetuning"],
    },
    "frontend_engineer": {
        "label": "Frontend Engineer",
        "skills": ["React/Vue/Angular", "HTML5/CSS3", "JavaScript/TypeScript", "Responsive Design", "State Management", "Frontend Testing"],
    },
    "backend_engineer": {
        "label": "Backend Engineer",
        "skills": ["Python/Java/Node.js", "REST APIs", "Database Design", "System Architecture", "Cloud (AWS/GCP)", "Docker/Kubernetes"],
    }
}

# ── SESSION STATE ─────────────────────────────────────────────────────────────
def init_session_state():
    defaults = {
        'groq_api_key': "", 'email_sender': "", 'email_password': "",
        'company_name': "TalentAI", 'analysis_complete': False,
        'agent3_outputs': [], 'skill_scores_list': [],
        'agent1_outputs': [], 'agent2_outputs': [],
        'candidate_emails': ["", "", ""],
        'candidate_names': ["Candidate 1", "Candidate 2", "Candidate 3"],
        'step': 1, 'active_skills': [], 'last_role': "",
        'resume_texts': [], 'num_candidates': 1,
        'comparison_result': {}, 'winner_index': -1
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ── HELPERS ───────────────────────────────────────────────────────────────────
def extract_text_from_pdf(pdf_file) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        return "".join(page.extract_text() for page in pdf_reader.pages)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.session_state.email_sender
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(st.session_state.email_sender, st.session_state.email_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email error: {e}")
        return False

def make_agent(system: str, instructions: list) -> Agent:
    return Agent(
        model=Groq(id="llama-3.3-70b-versatile", api_key=st.session_state.groq_api_key),
        description=system, instructions=instructions, markdown=False
    )

def get_reply(agent: Agent, prompt: str) -> str:
    response = agent.run(prompt)
    return next((m.content for m in response.messages if m.role == "assistant"), "")

def get_active_requirements() -> str:
    skills = st.session_state.get('active_skills', [])
    if not skills:
        return "No specific requirements set."
    return "\n".join(f"- {s}" for s in skills)

def parse_json(raw: str) -> dict:
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    try:
        return json.loads(clean.strip())
    except:
        return {}

# ── AGENTS ────────────────────────────────────────────────────────────────────
def run_screener(resume_text: str, role: str) -> str:
    agent = make_agent(
        "You are a resume parser. Extract structured information only.",
        ["Extract skills, tools, technologies", "Extract years of experience",
         "Extract education", "Extract notable projects", "Facts only, no opinions"]
    )
    return get_reply(agent, f"""Extract information from this resume for a {ROLE_REQUIREMENTS[role]['label']} role.
Required skills to look for: {get_active_requirements()}
Resume: {resume_text}
Return sections: 1. Technical Skills  2. Experience Level  3. Education  4. Projects""")

def run_evaluator(screener_output: str, role: str) -> tuple[str, dict]:
    active_skills = st.session_state.get('active_skills', ROLE_REQUIREMENTS[role]["skills"])
    agent = make_agent(
        "You are a technical skills evaluator. Score objectively.",
        ["Score each required skill area 0-10", "List matching and missing skills",
         "Give overall match percentage", "Return plain text then a JSON scores block"]
    )
    prompt = f"""Evaluate this candidate for {ROLE_REQUIREMENTS[role]['label']}.
Required skills: {get_active_requirements()}
Candidate profile: {screener_output}

First write a plain text evaluation. Then at the very end output:
SCORES_JSON:
{{"scores": {{{", ".join([f'"{s}": 7' for s in active_skills])}}},"overall": 70, "level": "mid"}}

Replace numbers with actual scores. Return ONLY valid JSON after SCORES_JSON:"""

    raw = get_reply(agent, prompt)
    scores = {}
    text_part = raw
    if "SCORES_JSON:" in raw:
        parts = raw.split("SCORES_JSON:")
        text_part = parts[0].strip()
        try:
            scores = json.loads(parts[1].strip())
        except:
            scores = {}
    return text_part, scores

def run_hiring_manager(a1: str, a2: str, role: str) -> dict:
    agent = make_agent(
        "You are a senior hiring manager. Make final hire/no-hire decisions.",
        ["Review candidate profile and evaluation", "Make definitive decision",
         "Consider potential not just current skills", "Return ONLY valid JSON no markdown no backticks"]
    )
    raw = get_reply(agent, f"""Final hiring decision for {ROLE_REQUIREMENTS[role]['label']}.
Firm required skills: {get_active_requirements()}
Agent 1 (Screener): {a1}
Agent 2 (Evaluator): {a2}

Return ONLY this JSON with no backticks no markdown:
{{
  "selected": true,
  "decision_reason": "2-3 sentence reason",
  "strengths": ["s1", "s2", "s3"],
  "gaps": ["g1", "g2"],
  "recommendation": "Hire / No Hire / Hold",
  "overall_score": 75
}}""")
    result = parse_json(raw)
    if not result:
        return {"selected": False, "decision_reason": raw,
                "strengths": [], "gaps": [], "recommendation": "Parse error", "overall_score": 0}
    return result

def run_comparator(candidates: list, role: str) -> dict:
    """Agent 4 — takes all candidate summaries and picks the best one."""
    agent = make_agent(
        "You are a chief hiring officer comparing multiple candidates for a single position.",
        ["Compare all candidates objectively", "Pick exactly one best candidate",
         "Justify why they are better than the others",
         "Return ONLY valid JSON no backticks no markdown"]
    )

    summaries = ""
    for i, c in enumerate(candidates):
        summaries += f"""
Candidate {i+1} ({c['name']}):
- Overall Score: {c['score']}%
- Recommendation: {c['recommendation']}
- Strengths: {', '.join(c['strengths'])}
- Gaps: {', '.join(c['gaps'])}
- Reason: {c['decision_reason']}
"""

    raw = get_reply(agent, f"""Compare these candidates for {ROLE_REQUIREMENTS[role]['label']}.
Required skills: {get_active_requirements()}

{summaries}

Return ONLY this JSON with no backticks:
{{
  "winner_index": 0,
  "winner_name": "Candidate 1",
  "comparison_reason": "2-3 sentences on why this candidate is best",
  "ranking": [
    {{"index": 0, "name": "Candidate 1", "rank": 1, "reason": "brief reason"}},
    {{"index": 1, "name": "Candidate 2", "rank": 2, "reason": "brief reason"}}
  ]
}}

winner_index must be 0-based integer matching the candidate number minus 1.""")

    result = parse_json(raw)
    if not result:
        return {"winner_index": 0, "winner_name": candidates[0]['name'],
                "comparison_reason": raw, "ranking": []}
    return result

# ── STEP INDICATOR ────────────────────────────────────────────────────────────
def render_steps(current: int):
    steps = ["Configure", "Upload Resumes", "Analysis", "Results"]
    html = '<div class="steps-container">'
    for i, label in enumerate(steps, 1):
        cls = "done" if i < current else ("active" if i == current else "pending")
        label_cls = "active" if i == current else ""
        icon = "✓" if i < current else str(i)
        html += f'<div class="step"><div class="step-num {cls}">{icon}</div><span class="step-label {label_cls}">{label}</span></div>'
        if i < len(steps):
            html += '<div class="step-divider"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ── SCORE BARS ────────────────────────────────────────────────────────────────
def render_score_bars(scores: dict):
    skill_scores = scores.get("scores", {})
    overall = scores.get("overall", 0)
    level = scores.get("level", "unknown")
    if not skill_scores:
        return

    def get_color(score):
        score = int(score)
        if score < 4: return "#f87171"
        if score < 7: return "#fbbf24"
        return "#4ade80"

    html = ''
    for skill, score in skill_scores.items():
        pct = int(score) * 10
        color = get_color(score)
        html += f'''<div class="score-row">
            <div class="score-label"><span>{skill}</span><span style="color:{color};font-weight:600">{score}/10</span></div>
            <div class="score-track"><div class="score-fill" style="width:{pct}%;background:{color}"></div></div>
        </div>'''

    overall_color = get_color(overall / 10)
    html += f'''<div style="margin-top:1rem;padding-top:1rem;border-top:1px solid #2a2a35;display:flex;justify-content:space-between;align-items:center">
        <span style="font-weight:700;font-size:0.95rem;color:#e2e2e8">Overall Match</span>
        <span style="font-size:1.5rem;font-weight:800;color:{overall_color}">{overall}%</span>
    </div>
    <div style="text-align:right;color:#4b5563;font-size:0.78rem;margin-top:2px">Level: <span style="color:#9ca3af;font-weight:600">{level}</span></div>'''
    st.markdown(html, unsafe_allow_html=True)

# ── MAIN ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 1.2rem 0 0.8rem 0; border-bottom: 1px solid #2a2a35; margin-bottom: 0.5rem;">
    <p class="hero-title">Resume Screener</p>
    <p class="hero-sub">4-Agent Pipeline · Llama 3.3 · AI Recruitment</p>
</div>
""", unsafe_allow_html=True)

render_steps(st.session_state.step)

# ── STEP 1: CONFIGURE ─────────────────────────────────────────────────────────
if st.session_state.step == 1:
    st.markdown("### ⚙️ Configuration")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card"><div class="card-title">AI Settings</div>', unsafe_allow_html=True)
        groq_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...", value=st.session_state.groq_api_key)
        if groq_key: st.session_state.groq_api_key = groq_key
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card"><div class="card-title">Email Settings (Optional)</div>', unsafe_allow_html=True)
        email_sender = st.text_input("Gmail Address", placeholder="recruiter@gmail.com", value=st.session_state.email_sender)
        email_password = st.text_input("Gmail App Password", type="password", placeholder="xxxx xxxx xxxx xxxx", value=st.session_state.email_password)
        company_name = st.text_input("Company Name", value=st.session_state.company_name)
        if email_sender: st.session_state.email_sender = email_sender
        if email_password: st.session_state.email_password = email_password
        if company_name: st.session_state.company_name = company_name
        st.markdown('</div>', unsafe_allow_html=True)

    st.caption("Email is optional — analysis works without it.")
    if st.button("Continue →"):
        if not st.session_state.groq_api_key:
            st.error("Groq API key is required.")
        else:
            st.session_state.step = 2
            st.rerun()

# ── STEP 2: UPLOAD ────────────────────────────────────────────────────────────
elif st.session_state.step == 2:
    st.markdown("### 📄 Job Requirements & Resumes")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="card"><div class="card-title">Role & Skills</div>', unsafe_allow_html=True)
        role_key = st.selectbox("Position", list(ROLE_REQUIREMENTS.keys()),
                                format_func=lambda x: ROLE_REQUIREMENTS[x]["label"])

        if st.session_state.last_role != role_key:
            st.session_state[f"skills_{role_key}"] = ROLE_REQUIREMENTS[role_key]["skills"].copy()
            st.session_state.last_role = role_key

        skill_key = f"skills_{role_key}"
        if skill_key not in st.session_state:
            st.session_state[skill_key] = ROLE_REQUIREMENTS[role_key]["skills"].copy()

        st.session_state.selected_role = role_key
        st.markdown("<small style='color:#4b5563'>Select required skills:</small>", unsafe_allow_html=True)

        selected_skills = []
        for skill in st.session_state[skill_key]:
            if st.checkbox(skill, value=True, key=f"cb_{role_key}_{skill}"):
                selected_skills.append(skill)

        st.markdown("---")
        nc1, nc2 = st.columns([3, 1])
        with nc1:
            new_skill = st.text_input("Add skill", placeholder="e.g. Kafka, Rust...", label_visibility="collapsed")
        with nc2:
            if st.button("＋ Add"):
                if new_skill and new_skill not in st.session_state[skill_key]:
                    st.session_state[skill_key].append(new_skill)
                    st.rerun()

        st.session_state.active_skills = selected_skills
        st.markdown('</div>', unsafe_allow_html=True)

        # Number of candidates
        st.markdown('<div class="card"><div class="card-title">Candidates</div>', unsafe_allow_html=True)
        num = st.radio("How many resumes to compare?", [1, 2, 3], horizontal=True,
                       index=st.session_state.num_candidates - 1)
        st.session_state.num_candidates = num
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        resume_files = []
        resume_texts = []

        for i in range(st.session_state.num_candidates):
            st.markdown(f"**Candidate {i+1}**")

            # Name input
            name = st.text_input(f"Name", value=st.session_state.candidate_names[i],
                                  key=f"name_{i}", placeholder=f"Candidate {i+1}")
            st.session_state.candidate_names[i] = name

            # Email input
            email = st.text_input(f"Email (optional)", value=st.session_state.candidate_emails[i],
                                   key=f"email_{i}", placeholder="candidate@email.com")
            st.session_state.candidate_emails[i] = email

            # File upload
            pdf = st.file_uploader(f"Upload Resume PDF", type=["pdf"], key=f"pdf_{i}")
            if pdf:
                resume_files.append(pdf)
                text = extract_text_from_pdf(pdf)
                resume_texts.append(text)
                st.success(f"✓ {pdf.name} loaded")
            else:
                resume_texts.append("")

            if i < st.session_state.num_candidates - 1:
                st.markdown("---")

        st.session_state.resume_texts = resume_texts

    bcol1, bcol2 = st.columns([1, 5])
    with bcol1:
        if st.button("← Back"):
            st.session_state.step = 1
            st.rerun()
    with bcol2:
        if st.button("Analyze Resumes 🔍"):
            filled = [t for t in st.session_state.resume_texts if t.strip()]
            if not filled:
                st.error("Please upload at least one resume.")
            elif not st.session_state.active_skills:
                st.error("Please select at least one skill.")
            else:
                st.session_state.step = 3
                st.rerun()

# ── STEP 3: ANALYSIS ──────────────────────────────────────────────────────────
elif st.session_state.step == 3:
    role = st.session_state.get('selected_role', 'ai_ml_engineer')
    resume_texts = st.session_state.resume_texts
    num = st.session_state.num_candidates

    st.markdown(f"### 🤖 Running {num * 3 + (1 if num > 1 else 0)}-Agent Pipeline...")

    all_a1, all_a2, all_a3, all_scores = [], [], [], []

    for i in range(num):
        text = resume_texts[i] if i < len(resume_texts) else ""
        if not text.strip():
            continue

        name = st.session_state.candidate_names[i]
        st.markdown(f"#### 👤 {name}")

        with st.status(f"🔎 Agent 1 — Screening {name}...", expanded=False) as s:
            a1 = run_screener(text, role)
            all_a1.append(a1)
            st.markdown(f'<div class="agent-log">{a1}</div>', unsafe_allow_html=True)
            s.update(label=f"✅ Screener done — {name}", state="complete")

        with st.status(f"📊 Agent 2 — Evaluating {name}...", expanded=False) as s:
            a2_text, a2_scores = run_evaluator(a1, role)
            all_a2.append(a2_text)
            all_scores.append(a2_scores)
            st.markdown(f'<div class="agent-log">{a2_text}</div>', unsafe_allow_html=True)
            s.update(label=f"✅ Evaluator done — {name}", state="complete")

        with st.status(f"👔 Agent 3 — Hiring decision for {name}...", expanded=False) as s:
            a3 = run_hiring_manager(a1, a2_text, role)
            all_a3.append(a3)
            s.update(label=f"✅ Decision made — {name}", state="complete")

    # Save results
    st.session_state.agent1_outputs = all_a1
    st.session_state.agent2_outputs = all_a2
    st.session_state.agent3_outputs = all_a3
    st.session_state.skill_scores_list = all_scores

    # Agent 4 — Comparator (only if multiple candidates)
    winner_index = 0
    comparison_result = {}

    if num > 1 and len(all_a3) > 1:
        with st.status("🏆 Agent 4 — Comparator picking the best candidate...", expanded=True) as s:
            candidates_summary = []
            for i, a3 in enumerate(all_a3):
                candidates_summary.append({
                    "name": st.session_state.candidate_names[i],
                    "score": a3.get("overall_score", all_scores[i].get("overall", 0) if i < len(all_scores) else 0),
                    "recommendation": a3.get("recommendation", ""),
                    "strengths": a3.get("strengths", []),
                    "gaps": a3.get("gaps", []),
                    "decision_reason": a3.get("decision_reason", "")
                })

            comparison_result = run_comparator(candidates_summary, role)
            winner_index = comparison_result.get("winner_index", 0)
            st.markdown(f"**🏆 Best candidate: {comparison_result.get('winner_name', '')}**")
            st.write(comparison_result.get("comparison_reason", ""))
            s.update(label="✅ Comparison complete", state="complete")

    st.session_state.comparison_result = comparison_result
    st.session_state.winner_index = winner_index
    st.session_state.analysis_complete = True

    # Send emails
    if st.session_state.email_sender and st.session_state.email_password:
        role_label = ROLE_REQUIREMENTS[role]["label"]
        for i, a3 in enumerate(all_a3):
            email = st.session_state.candidate_emails[i] if i < len(st.session_state.candidate_emails) else ""
            if not email:
                continue
            is_winner = (i == winner_index and num > 1) or (num == 1 and a3.get("selected", False))
            if is_winner:
                subject = f"Application Update — {role_label} at {st.session_state.company_name}"
                body = f"""Hi {st.session_state.candidate_names[i]},

We're pleased to inform you that after reviewing all applications for the {role_label} position at {st.session_state.company_name}, you have been selected as our top candidate!

Decision: {a3.get('recommendation', 'Hire')}
Reason: {a3.get('decision_reason', '')}

We will be in touch shortly with next steps.

Best regards,
{st.session_state.company_name} Recruiting Team"""
            else:
                subject = f"Application Update — {role_label} at {st.session_state.company_name}"
                body = f"""Hi {st.session_state.candidate_names[i]},

Thank you for applying for the {role_label} position at {st.session_state.company_name}.

After carefully reviewing all applications, we have decided to move forward with another candidate at this time.

Feedback: {a3.get('decision_reason', '')}
Areas to strengthen: {', '.join(a3.get('gaps', []))}

We encourage you to keep building your skills and apply again in the future.

Best regards,
{st.session_state.company_name} Recruiting Team"""

            with st.spinner(f"📧 Emailing {st.session_state.candidate_names[i]}..."):
                if send_email(email, subject, body):
                    st.success(f"📧 Email sent to {email}")

    st.session_state.step = 4
    st.rerun()

# ── STEP 4: RESULTS ───────────────────────────────────────────────────────────
elif st.session_state.step == 4:
    render_steps(4)
    role = st.session_state.get('selected_role', 'ai_ml_engineer')
    num = st.session_state.num_candidates
    all_a3 = st.session_state.agent3_outputs
    all_scores = st.session_state.skill_scores_list
    winner_index = st.session_state.winner_index
    comparison = st.session_state.comparison_result

    # ── Winner banner (multi-candidate only)
    if num > 1 and comparison:
        st.markdown(f"""<div class="decision-hire">
            <p class="decision-title" style="color:#4ade80">🏆 Best Candidate: {comparison.get('winner_name', '')}</p>
            <p style="color:#86efac;margin-top:0.5rem">{comparison.get('comparison_reason', '')}</p>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Ranking
        ranking = comparison.get("ranking", [])
        if ranking:
            st.markdown("#### 📊 Candidate Ranking")
            for r in sorted(ranking, key=lambda x: x.get("rank", 99)):
                medal = ["🥇", "🥈", "🥉"][r.get("rank", 1) - 1] if r.get("rank", 1) <= 3 else f"#{r.get('rank')}"
                st.markdown(f"**{medal} {r.get('name', '')}** — {r.get('reason', '')}")

        st.markdown("<br>", unsafe_allow_html=True)

    # ── Per-candidate cards
    st.markdown("#### 👥 Individual Results")
    cols = st.columns(min(num, 3))

    for i in range(min(num, len(all_a3))):
        a3 = all_a3[i]
        scores = all_scores[i] if i < len(all_scores) else {}
        is_winner = (i == winner_index and num > 1)
        name = st.session_state.candidate_names[i]

        with cols[i]:
            card_class = "candidate-card winner" if is_winner else "candidate-card"
            winner_html = '<span class="winner-badge">⭐ TOP PICK</span>' if is_winner else ""
            rec = a3.get("recommendation", "—")
            rec_color = "#4ade80" if "hire" in rec.lower() else "#f87171"

            st.markdown(f"""<div class="{card_class}">
                <div style="font-weight:700;font-size:1rem;color:#e2e2e8">{name}{winner_html}</div>
                <div style="color:{rec_color};font-size:0.82rem;margin-top:4px;font-weight:600">{rec}</div>
                <div style="color:#6b7280;font-size:0.78rem;margin-top:8px">{a3.get('decision_reason','')}</div>
            </div>""", unsafe_allow_html=True)

            # Score bars
            render_score_bars(scores)

            # Strengths & gaps
            if a3.get("strengths"):
                st.markdown('<div style="margin-top:0.5rem">', unsafe_allow_html=True)
                for s in a3.get("strengths", []):
                    st.markdown(f'<span class="tag-green">✓ {s}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            if a3.get("gaps"):
                st.markdown('<div style="margin-top:0.5rem">', unsafe_allow_html=True)
                for g in a3.get("gaps", []):
                    st.markdown(f'<span class="tag-red">✗ {g}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # ── Agent logs
    with st.expander("🔍 View full agent reasoning"):
        for i in range(min(num, len(all_a3))):
            name = st.session_state.candidate_names[i]
            tab1, tab2 = st.tabs([f"Agent 1 — {name}", f"Agent 2 — {name}"])
            with tab1:
                a1_out = st.session_state.agent1_outputs[i] if i < len(st.session_state.agent1_outputs) else ""
                st.markdown(f'<div class="agent-log">{a1_out}</div>', unsafe_allow_html=True)
            with tab2:
                a2_out = st.session_state.agent2_outputs[i] if i < len(st.session_state.agent2_outputs) else ""
                st.markdown(f'<div class="agent-log">{a2_out}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 New Analysis"):
        for key in ['resume_texts', 'analysis_complete', 'agent1_outputs', 'agent2_outputs',
                    'agent3_outputs', 'skill_scores_list', 'comparison_result', 'winner_index']:
            st.session_state[key] = [] if isinstance(st.session_state[key], list) else (
                {} if isinstance(st.session_state[key], dict) else False)
        st.session_state.candidate_emails = ["", "", ""]
        st.session_state.candidate_names = ["Candidate 1", "Candidate 2", "Candidate 3"]
        st.session_state.step = 2
        st.rerun()