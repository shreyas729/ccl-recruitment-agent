from typing import Dict, List
import os
import json
import random
import string
import PyPDF2
import tempfile
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import boto3
from botocore.exceptions import NoCredentialsError
import streamlit as st
from agno.agent import Agent
from agno.models.groq import Groq
from streamlit_pdf_viewer import pdf_viewer

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Recruitment Platform",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

* { font-family: 'Inter', sans-serif; }
html, body, [data-testid="stAppViewContainer"] { background-color: #0f0f13; color: #e2e2e8; }
h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 600; }

.hero-title { font-size: 1.5rem; font-weight: 700; color: #e2e2e8; margin: 0; letter-spacing: -0.02em; }
.hero-sub { color: #4b5563; font-size: 0.78rem; margin-top: 0.3rem; font-weight: 400; letter-spacing: 0.08em; text-transform: uppercase; }

.landing-card {
    background: #16161d; border: 1px solid #2a2a35; border-radius: 16px;
    padding: 2.5rem; text-align: center; margin: 1rem;
}
.landing-icon { font-size: 2rem; margin-bottom: 1rem; }
.landing-title { font-size: 1.2rem; font-weight: 700; color: #e2e2e8; margin-bottom: 0.5rem; }
.landing-desc { font-size: 0.82rem; color: #4b5563; line-height: 1.6; }

.card { background: #16161d; border: 1px solid #2a2a35; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }
.card-title { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #4b5563; margin-bottom: 1rem; }

.job-card {
    background: #16161d; border: 1px solid #2a2a35; border-radius: 12px;
    padding: 1.5rem; margin-bottom: 0.8rem;
}
.job-card-title { font-size: 1rem; font-weight: 700; color: #e2e2e8; }
.job-card-meta { font-size: 0.78rem; color: #4b5563; margin-top: 0.3rem; }
.job-card-count { font-size: 0.78rem; color: #4ade80; font-weight: 600; margin-top: 0.5rem; }

.job-id-box {
    background: #0d0d12; border: 2px dashed #2a2a35;
    border-radius: 12px; padding: 1.5rem; text-align: center; margin: 1rem 0;
}
.job-id-code { font-family: 'IBM Plex Mono', monospace; font-size: 2.5rem; font-weight: 700; color: #4ade80; letter-spacing: 0.2em; }
.job-id-label { font-size: 0.75rem; color: #4b5563; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.5rem; }

.candidate-job-card {
    background: #16161d; border: 1px solid #2a2a35; border-radius: 16px; padding: 2rem; margin-bottom: 1.5rem;
}
.candidate-job-title { font-size: 1.4rem; font-weight: 700; color: #e2e2e8; }
.candidate-job-company { font-size: 0.88rem; color: #4b5563; margin-top: 0.3rem; }
.candidate-job-desc { font-size: 0.85rem; color: #9ca3af; margin-top: 1rem; line-height: 1.6; }

.weight-critical { color: #f87171; font-weight: 600; font-size: 0.78rem; }
.weight-important { color: #fbbf24; font-weight: 600; font-size: 0.78rem; }
.weight-nice { color: #60a5fa; font-weight: 600; font-size: 0.78rem; }

.score-row { margin-bottom: 0.8rem; }
.score-label { font-size: 0.82rem; color: #9ca3af; margin-bottom: 4px; display: flex; justify-content: space-between; }
.score-track { background: #1e1e26; border-radius: 999px; height: 5px; width: 100%; }
.score-fill { height: 5px; border-radius: 999px; }

.decision-hire { background: #0d1f15; border: 1px solid #166534; border-left: 4px solid #4ade80; border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1rem; }
.decision-nohire { background: #1a0d0d; border: 1px solid #7f1d1d; border-left: 4px solid #f87171; border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1rem; }
.decision-title { font-size: 1.1rem; font-weight: 700; margin: 0; }

.redflag-box { background: #1a0d0d; border: 1px solid #7f1d1d; border-radius: 8px; padding: 1rem 1.2rem; margin-top: 0.5rem; }
.redflag-title { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #f87171; margin-bottom: 0.5rem; }

.agent-log { background: #0d0d12; border: 1px solid #2a2a35; border-radius: 8px; padding: 1rem 1.2rem; font-size: 0.8rem; color: #6b7280; line-height: 1.7; white-space: pre-wrap; font-family: 'IBM Plex Mono', monospace; }

.rank-card { background: #16161d; border: 1px solid #2a2a35; border-radius: 12px; padding: 1.2rem; margin-bottom: 0.8rem; }
.rank-card.winner { border-color: #166534; border-left: 4px solid #4ade80; background: #0d1f15; }
.winner-badge { display: inline-block; background: #14532d; color: #4ade80; border: 1px solid #166534; border-radius: 999px; padding: 2px 10px; font-size: 0.7rem; font-weight: 600; margin-left: 8px; }

.tag-green { display: inline-block; background: #0d1f15; color: #4ade80; border: 1px solid #166534; border-radius: 6px; padding: 3px 10px; font-size: 0.74rem; margin: 3px; }
.tag-red { display: inline-block; background: #1a0d0d; color: #f87171; border: 1px solid #7f1d1d; border-radius: 6px; padding: 3px 10px; font-size: 0.74rem; margin: 3px; }
.tag-yellow { display: inline-block; background: #1a1400; color: #fbbf24; border: 1px solid #92400e; border-radius: 6px; padding: 3px 10px; font-size: 0.74rem; margin: 3px; }
.tag-blue { display: inline-block; background: #0c1a2e; color: #60a5fa; border: 1px solid #1e3a5f; border-radius: 6px; padding: 3px 10px; font-size: 0.74rem; margin: 3px; }

[data-testid="stTextInput"] input { background: #16161d !important; border: 1px solid #2a2a35 !important; border-radius: 8px !important; color: #e2e2e8 !important; font-size: 0.9rem !important; }
[data-testid="stTextInput"] input::placeholder { color: #4b5563 !important; }
[data-testid="stSelectbox"] > div { background: #16161d !important; border: 1px solid #2a2a35 !important; border-radius: 8px !important; color: #e2e2e8 !important; }
[data-testid="stTextArea"] textarea { background: #16161d !important; border: 1px solid #2a2a35 !important; border-radius: 8px !important; color: #e2e2e8 !important; }

.stButton > button { background: #e2e2e8 !important; color: #0f0f13 !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 0.88rem !important; padding: 0.5rem 1.4rem !important; transition: opacity 0.2s !important; }
.stButton > button:hover { opacity: 0.8 !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
WEIGHT_MAP = {"Critical": 3, "Important": 2, "Nice to have": 1}
WEIGHT_COLORS = {"Critical": "weight-critical", "Important": "weight-important", "Nice to have": "weight-nice"}

DEFAULT_SKILLS = {
    "ai_ml_engineer": ["Python", "PyTorch/TensorFlow", "Machine Learning", "Deep Learning", "MLOps", "LLM/RAG/Finetuning"],
    "frontend_engineer": ["React/Vue/Angular", "HTML5/CSS3", "JavaScript/TypeScript", "Responsive Design", "State Management", "Frontend Testing"],
    "backend_engineer": ["Python/Java/Node.js", "REST APIs", "Database Design", "System Architecture", "Cloud (AWS/GCP)", "Docker/Kubernetes"],
}

ROLE_LABELS = {
    "ai_ml_engineer": "AI / ML Engineer",
    "frontend_engineer": "Frontend Engineer",
    "backend_engineer": "Backend Engineer",
    "custom": "Custom Role"
}

# ── SESSION STATE ─────────────────────────────────────────────────────────────
def init_session_state():
    defaults = {
        'groq_api_key': "",
        'email_sender': "", 'email_password': "", 'company_name': "HireAI",
        'mode': None,
        'aws_access_key': "",
        'aws_secret_key': "",
        'job_postings': {},
        'applications': {},
        'analyses': {},
        'r_screen': 'dashboard',
        'r_selected_job': None,
        'r_skills': [],
        'c_screen': 'enter_id',
        'c_job_id': "",
        'c_name': "",
        'c_email': "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ── HELPERS ───────────────────────────────────────────────────────────────────
def generate_job_id() -> str:
    return "J" + "".join(random.choices(string.digits, k=4))

def extract_text_from_pdf(pdf_file) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        return "".join(page.extract_text() for page in pdf_reader.pages)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""
    
def upload_to_s3(file_bytes: bytes, filename: str) -> str:
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=st.session_state.get('aws_access_key', ''),
            aws_secret_access_key=st.session_state.get('aws_secret_key', ''),
            region_name='us-east-1'
        )
        s3.put_object(
            Bucket='ccl-resume-bucket-2024',
            Key=f"resumes/{filename}",
            Body=file_bytes,
            ContentType='application/pdf'
        )
        return f"s3://ccl-resume-bucket-2024/resumes/{filename}"
    except Exception as e:
        st.warning(f"S3 upload skipped: {e}")
        return ""

def send_email(to_email: str, subject: str, body: str) -> bool:
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

def format_skills_with_weights(skills_weights: dict) -> str:
    return "\n".join(f"- {s} [{w}] ({WEIGHT_MAP[w]}x)" for s, w in skills_weights.items())

def calculate_weighted_score(skill_scores: dict, skills_weights: dict) -> float:
    total_weighted = sum(skill_scores.get(s, 0) * WEIGHT_MAP.get(w, 1) for s, w in skills_weights.items())
    total_max = sum(10 * WEIGHT_MAP.get(w, 1) for w in skills_weights.values())
    return round((total_weighted / total_max) * 100, 1) if total_max > 0 else 0

# ── AGENTS ────────────────────────────────────────────────────────────────────
def run_screener(resume_text: str, job: dict) -> str:
    agent = make_agent(
        "You are a resume parser. Extract structured factual information only.",
        ["Extract all skills and technologies with proficiency level",
         "Extract years and depth of experience per domain",
         "Extract education background",
         "Extract projects briefly",
         "Note employment gaps or short tenures",
         "Facts only, no opinions"]
    )
    return get_reply(agent, f"""Parse this resume for a {job['title']} role.
Skills to look for: {', '.join(job['skills_weights'].keys())}
Resume: {resume_text}
Return: 1. Technical Skills  2. Experience Depth  3. Education  4. Projects  5. Employment Timeline""")

def run_context_evaluator(screener_output: str, job: dict) -> tuple[str, dict]:
    skills = job['skills_weights']
    agent = make_agent(
        "You are a technical evaluator scoring candidates based on job context.",
        ["Score based on demonstrated depth, not just keyword presence",
         "Production experience = 8-10, project experience = 5-7, coursework only = 2-4",
         "Consider full job description context",
         "Return plain text then SCORES_JSON block"]
    )
    template = ", ".join([f'"{s}": 7' for s in skills])
    raw = get_reply(agent, f"""Evaluate for: {job['title']}
Context: {job['description']}
Required skills: {format_skills_with_weights(skills)}
Candidate: {screener_output}

Write evaluation, then end with:
SCORES_JSON:
{{"scores": {{{template}}}, "overall": 70, "level": "junior/mid/senior"}}""")

    text_part, scores = raw, {}
    if "SCORES_JSON:" in raw:
        parts = raw.split("SCORES_JSON:")
        text_part = parts[0].strip()
        try:
            scores = json.loads(parts[1].strip())
        except:
            scores = {}
    return text_part, scores

def run_red_flag_detector(resume_text: str, screener_output: str) -> dict:
    agent = make_agent(
        "You are a recruitment risk analyst.",
        ["Flag AI buzzword-heavy language with no substance",
         "Identify employment gaps over 6 months",
         "Flag vague claims without measurable outcomes",
         "Note frequent job changes under 1 year",
         "Return ONLY valid JSON no backticks"]
    )
    raw = get_reply(agent, f"""Analyze for red flags:
Resume: {resume_text}
Summary: {screener_output}
Return ONLY:
{{"red_flags": [], "employment_gaps": [], "vague_claims": [], "risk_level": "Low/Medium/High", "risk_summary": "..."}}""")
    result = parse_json(raw)
    return result if result else {"red_flags": [], "employment_gaps": [], "vague_claims": [], "risk_level": "Low", "risk_summary": "No significant red flags."}

def run_hiring_manager(screener: str, evaluator: str, red_flags: dict, weighted_score: float, job: dict) -> dict:
    agent = make_agent(
        "You are a senior hiring manager.",
        ["Consider all inputs holistically",
         "Weight skill priorities defined by recruiter",
         "High risk red flags are strong negative signals",
         "Return ONLY valid JSON no backticks"]
    )
    raw = get_reply(agent, f"""Decision for: {job['title']}
Context: {job['description']}
Skills: {format_skills_with_weights(job['skills_weights'])}
Screener: {screener}
Evaluator: {evaluator}
Red Flags: Risk={red_flags.get('risk_level')}, Flags={red_flags.get('red_flags',[])}
Weighted Score: {weighted_score}%

Return ONLY:
{{"selected": true, "decision_reason": "2-3 sentences", "strengths": [], "gaps": [], "recommendation": "Strong Hire/Hire/Hold/No Hire", "overall_score": {weighted_score}}}""")
    result = parse_json(raw)
    return result if result else {"selected": False, "decision_reason": raw, "strengths": [], "gaps": [], "recommendation": "Parse error", "overall_score": weighted_score}

def run_comparator(candidates: list, job: dict) -> dict:
    agent = make_agent(
        "You are a chief hiring officer comparing candidates.",
        ["Use weighted scores and risk levels to rank",
         "Pick exactly one winner",
         "Return ONLY valid JSON no backticks"]
    )
    summaries = "\n".join([f"Candidate {i+1} ({c['name']}): Score={c['score']}%, Risk={c.get('risk_level','Low')}, Rec={c['recommendation']}, Strengths={c['strengths']}, Gaps={c['gaps']}" for i, c in enumerate(candidates)])
    raw = get_reply(agent, f"""Compare for {job['title']}:
{summaries}
Return ONLY:
{{"winner_index": 0, "winner_name": "name", "comparison_reason": "2-3 sentences", "ranking": [{{"index": 0, "name": "name", "rank": 1, "reason": "brief"}}]}}""")
    result = parse_json(raw)
    return result if result else {"winner_index": 0, "winner_name": candidates[0]['name'], "comparison_reason": "", "ranking": []}

# ── UI HELPERS ────────────────────────────────────────────────────────────────
def render_score_bars(scores: dict, skills_weights: dict = {}):
    skill_scores = scores.get("scores", {})
    overall = scores.get("overall", 0)
    level = scores.get("level", "—")
    if not skill_scores:
        return

    def get_color(s):
        s = int(s)
        return "#f87171" if s < 4 else ("#fbbf24" if s < 7 else "#4ade80")

    html = ""
    for skill, score in skill_scores.items():
        color = get_color(score)
        weight = skills_weights.get(skill, "")
        weight_html = f'<span class="{WEIGHT_COLORS.get(weight,"")}" style="margin-left:6px">({weight})</span>' if weight else ""
        html += f'''<div class="score-row">
            <div class="score-label"><span>{skill}{weight_html}</span><span style="color:{color};font-weight:600">{score}/10</span></div>
            <div class="score-track"><div class="score-fill" style="width:{int(score)*10}%;background:{color}"></div></div>
        </div>'''

    oc = get_color(overall / 10)
    html += f'''<div style="margin-top:1rem;padding-top:1rem;border-top:1px solid #2a2a35;display:flex;justify-content:space-between;align-items:center">
        <span style="font-weight:700;color:#e2e2e8">Weighted Score</span>
        <span style="font-size:1.5rem;font-weight:800;color:{oc}">{overall}%</span>
    </div>
    <div style="text-align:right;color:#4b5563;font-size:0.78rem">Level: <span style="color:#9ca3af;font-weight:600">{level}</span></div>'''
    st.markdown(html, unsafe_allow_html=True)

def render_red_flags(rf: dict):
    if not rf or (rf.get('risk_level') == 'Low' and not rf.get('red_flags')):
        st.markdown('<span class="tag-green">✓ No red flags</span>', unsafe_allow_html=True)
        return
    risk = rf.get('risk_level', 'Low')
    rc = {"Low": "#4ade80", "Medium": "#fbbf24", "High": "#f87171"}.get(risk, "#9ca3af")
    st.markdown(f'<div class="redflag-box"><div class="redflag-title">Risk Level: <span style="color:{rc}">{risk}</span></div><div style="color:#9ca3af;font-size:0.8rem">{rf.get("risk_summary","")}</div></div>', unsafe_allow_html=True)
    for f in rf.get('red_flags', []):
        st.markdown(f'<span class="tag-red">⚑ {f}</span>', unsafe_allow_html=True)
    for g in rf.get('employment_gaps', []):
        st.markdown(f'<span class="tag-yellow">⏱ {g}</span>', unsafe_allow_html=True)

def run_full_analysis(job_id: str):
    job = st.session_state.job_postings[job_id]
    candidates = st.session_state.applications.get(job_id, [])

    all_results = []
    for cand in candidates:
        st.markdown(f"**{cand['name']}**")

        with st.status(f"Screening {cand['name']}...", expanded=False) as s:
            a1 = run_screener(cand['resume_text'], job)
            s.update(label=f"Screener complete — {cand['name']}", state="complete")

        with st.status(f"Evaluating skills — {cand['name']}...", expanded=False) as s:
            a2_text, a2_scores = run_context_evaluator(a1, job)
            s.update(label=f"Evaluation complete — {cand['name']}", state="complete")

        with st.status(f"Checking profile — {cand['name']}...", expanded=False) as s:
            red_flags = run_red_flag_detector(cand['resume_text'], a1)
            s.update(label=f"Profile check complete — {cand['name']}", state="complete")

        weighted_score = calculate_weighted_score(a2_scores.get("scores", {}), job['skills_weights'])

        with st.status(f"Making decision — {cand['name']}...", expanded=False) as s:
            decision = run_hiring_manager(a1, a2_text, red_flags, weighted_score, job)
            s.update(label=f"Decision complete — {cand['name']}", state="complete")

        all_results.append({
            "name": cand['name'], "email": cand.get('email', ''),
            "a1": a1, "a2": a2_text, "scores": a2_scores,
            "red_flags": red_flags, "weighted_score": weighted_score, "decision": decision
        })

    winner_index = 0
    comparison = {}
    if len(all_results) > 1:
        with st.status("Comparing candidates...", expanded=True) as s:
            summaries = [{"name": r['name'], "score": r['weighted_score'],
                          "recommendation": r['decision'].get('recommendation', ''),
                          "risk_level": r['red_flags'].get('risk_level', 'Low'),
                          "strengths": r['decision'].get('strengths', []),
                          "gaps": r['decision'].get('gaps', [])} for r in all_results]
            comparison = run_comparator(summaries, job)
            winner_index = comparison.get("winner_index", 0)
            s.update(label="Comparison complete", state="complete")

    st.session_state.analyses[job_id] = {
        "done": True,
        "results": all_results,
        "comparison": comparison,
        "winner_index": winner_index,
        "decision_made": False
    }

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:1.2rem 0 0.8rem 0;border-bottom:1px solid #2a2a35;margin-bottom:1rem;">
    <p class="hero-title">Recruitment Platform</p>
    <p class="hero-sub">AI-Powered Recruitment · Weighted Skill Matching · Llama 3.3</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LANDING
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.mode is None:
    st.markdown("### Who are you?")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""<div class="landing-card">
            <div class="landing-icon">👔</div>
            <div class="landing-title">I'm a Recruiter</div>
            <div class="landing-desc">Post jobs, define skill priorities, and run AI-powered candidate analysis</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Enter as Recruiter", use_container_width=True):
            st.session_state.mode = 'recruiter'
            st.rerun()
    with col2:
        st.markdown("""<div class="landing-card">
            <div class="landing-icon">👤</div>
            <div class="landing-title">I'm a Candidate</div>
            <div class="landing-desc">Enter a Job ID, view the posting, and submit your resume</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Enter as Candidate", use_container_width=True):
            st.session_state.mode = 'candidate'
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RECRUITER
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.mode == 'recruiter':

    tcol1, tcol2, tcol3 = st.columns([2, 6, 2])
    with tcol1:
        if st.button("← Landing"):
            st.session_state.mode = None
            st.rerun()
    with tcol3:
        if not st.session_state.groq_api_key:
            if st.button("Setup"):
                st.session_state.r_screen = 'setup'
                st.rerun()

    # ── SETUP ─────────────────────────────────────────────────────────────────
    if st.session_state.r_screen == 'setup' or not st.session_state.groq_api_key:
        st.markdown("### Setup")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="card"><div class="card-title">AI Settings</div>', unsafe_allow_html=True)
            groq_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...", value=st.session_state.groq_api_key)
            if groq_key: st.session_state.groq_api_key = groq_key
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="card"><div class="card-title">AWS Settings</div>', unsafe_allow_html=True)
            aws_key = st.text_input("AWS Access Key ID", type="password", value=st.session_state.aws_access_key)
            aws_secret = st.text_input("AWS Secret Access Key", type="password", value=st.session_state.aws_secret_key)
            if aws_key: st.session_state.aws_access_key = aws_key
            if aws_secret: st.session_state.aws_secret_key = aws_secret
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="card"><div class="card-title">Company & Email</div>', unsafe_allow_html=True)
            company = st.text_input("Company Name", value=st.session_state.company_name)
            esender = st.text_input("Gmail (optional)", value=st.session_state.email_sender)
            epass = st.text_input("App Password (optional)", type="password", value=st.session_state.email_password)
            if company: st.session_state.company_name = company
            if esender: st.session_state.email_sender = esender
            if epass: st.session_state.email_password = epass
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Save & Continue"):
            if not st.session_state.groq_api_key:
                st.error("Groq API key required.")
            else:
                st.session_state.r_screen = 'dashboard'
                st.rerun()

    # ── DASHBOARD ─────────────────────────────────────────────────────────────
    elif st.session_state.r_screen == 'dashboard':
        st.markdown(f"### {st.session_state.company_name} — Dashboard")

        dcol1, dcol2 = st.columns(2)
        with dcol1:
            st.markdown('<div class="card" style="text-align:center;padding:2rem">', unsafe_allow_html=True)
            st.markdown("**Post a New Job**")
            st.markdown("<p style='color:#4b5563;font-size:0.82rem'>Create a job posting with skill requirements and priority weights</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("Post New Job", use_container_width=True):
                st.session_state.r_screen = 'post_job'
                st.session_state.r_skills = []
                st.rerun()

        with dcol2:
            st.markdown('<div class="card" style="text-align:center;padding:2rem">', unsafe_allow_html=True)
            st.markdown("**View Applications**")
            total_apps = sum(len(v) for v in st.session_state.applications.values())
            st.markdown(f"<p style='color:#4b5563;font-size:0.82rem'>{len(st.session_state.job_postings)} jobs posted · {total_apps} applications received</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("View Applications", use_container_width=True):
                st.session_state.r_screen = 'view_applications'
                st.rerun()

    # ── POST JOB ──────────────────────────────────────────────────────────────
    elif st.session_state.r_screen == 'post_job':
        st.markdown("### New Job Posting")
        if st.button("← Dashboard"):
            st.session_state.r_screen = 'dashboard'
            st.rerun()

        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown('<div class="card"><div class="card-title">Job Details</div>', unsafe_allow_html=True)
            job_title = st.text_input("Job Title", placeholder="e.g. Senior ML Engineer")
            job_desc = st.text_area("Job Description", placeholder="Describe the role, team, expectations...", height=120)
            role_key = st.selectbox("Base Skill Template",
                                    ["custom"] + list(DEFAULT_SKILLS.keys()),
                                    format_func=lambda x: ROLE_LABELS.get(x, x))
            if role_key != "custom" and not st.session_state.r_skills:
                st.session_state.r_skills = DEFAULT_SKILLS[role_key].copy()
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="card"><div class="card-title">Skills & Priority Weights</div>', unsafe_allow_html=True)
            st.markdown("<small style='color:#4b5563'>Critical = 3x weight · Important = 2x · Nice to have = 1x</small><br><br>", unsafe_allow_html=True)

            skills_weights = {}
            for skill in st.session_state.r_skills:
                sc1, sc2 = st.columns([3, 2])
                with sc1:
                    st.markdown(f"<small style='color:#9ca3af;line-height:2.5'>{skill}</small>", unsafe_allow_html=True)
                with sc2:
                    w = st.selectbox("", ["Critical", "Important", "Nice to have"], key=f"w_{skill}", label_visibility="collapsed")
                    skills_weights[skill] = w

            st.markdown("---")
            nc1, nc2 = st.columns([3, 1])
            with nc1:
                new_skill = st.text_input("", placeholder="Add skill...", label_visibility="collapsed", key="r_new_skill")
            with nc2:
                if st.button("Add"):
                    if new_skill and new_skill not in st.session_state.r_skills:
                        st.session_state.r_skills.append(new_skill)
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Post Job & Generate ID", use_container_width=True):
            if not job_title:
                st.error("Please enter a job title.")
            elif not skills_weights:
                st.error("Please add at least one skill.")
            else:
                job_id = generate_job_id()
                st.session_state.job_postings[job_id] = {
                    "title": job_title,
                    "description": job_desc or f"We are looking for a {job_title}.",
                    "role": role_key,
                    "skills_weights": skills_weights,
                    "company": st.session_state.company_name
                }
                st.session_state.applications[job_id] = []
                st.session_state.r_selected_job = job_id
                st.session_state.r_screen = 'job_posted'
                st.rerun()

    # ── JOB POSTED ────────────────────────────────────────────────────────────
    elif st.session_state.r_screen == 'job_posted':
        job_id = st.session_state.r_selected_job
        job = st.session_state.job_postings[job_id]

        st.markdown("### Job Posted")
        st.markdown(f"""<div class="job-id-box">
            <div class="job-id-label">Share this ID with candidates</div>
            <div class="job-id-code">{job_id}</div>
            <div class="job-id-label" style="margin-top:0.5rem">{job['title']} · {job['company']}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="card-title">Required Skills</div>', unsafe_allow_html=True)
        for skill, weight in job['skills_weights'].items():
            st.markdown(f'<span class="{WEIGHT_COLORS[weight]}" style="margin-right:14px">● {skill} ({weight})</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Post Another Job"):
                st.session_state.r_screen = 'post_job'
                st.session_state.r_skills = []
                st.rerun()
        with col2:
            if st.button("View Applications →"):
                st.session_state.r_screen = 'view_applications'
                st.rerun()

    # ── VIEW APPLICATIONS ─────────────────────────────────────────────────────
    elif st.session_state.r_screen == 'view_applications':
        st.markdown("### Applications")
        if st.button("← Dashboard"):
            st.session_state.r_screen = 'dashboard'
            st.rerun()

        if not st.session_state.job_postings:
            st.markdown('<div class="card"><div style="color:#4b5563;text-align:center;padding:1rem">No jobs posted yet.</div></div>', unsafe_allow_html=True)
        else:
            for job_id, job in st.session_state.job_postings.items():
                apps = st.session_state.applications.get(job_id, [])
                analysis = st.session_state.analyses.get(job_id, {})
                is_analyzed = analysis.get("done", False)
                decision_made = analysis.get("decision_made", False)

                if decision_made:
                    status_badge = "<span style='color:#4ade80;font-size:0.75rem;font-weight:600'>● Decision Made</span>"
                elif is_analyzed:
                    status_badge = "<span style='color:#fbbf24;font-size:0.75rem;font-weight:600'>● Analysed</span>"
                elif apps:
                    status_badge = "<span style='color:#60a5fa;font-size:0.75rem;font-weight:600'>● Applications Received</span>"
                else:
                    status_badge = "<span style='color:#4b5563;font-size:0.75rem;font-weight:600'>● Waiting for applicants</span>"

                st.markdown(f"""<div class="job-card">
                    <div class="job-card-title">{job['title']} <span style="font-family:monospace;font-size:0.78rem;color:#4b5563">#{job_id}</span></div>
                    <div class="job-card-meta">{job['company']}</div>
                    <div style="margin-top:0.5rem">{status_badge}</div>
                    <div class="job-card-count">{len(apps)} applicant(s)</div>
                </div>""", unsafe_allow_html=True)

                bcol1, bcol2, bcol3 = st.columns([2, 2, 4])
                with bcol1:
                    if st.button("View / Analyze", key=f"analyze_{job_id}"):
                        st.session_state.r_selected_job = job_id
                        st.session_state.r_screen = 'job_detail'
                        st.rerun()
                with bcol2:
                    if is_analyzed and not decision_made:
                        if st.button("See Results", key=f"results_{job_id}"):
                            st.session_state.r_selected_job = job_id
                            st.session_state.r_screen = 'results'
                            st.rerun()
                st.markdown("---")

    # ── JOB DETAIL ────────────────────────────────────────────────────────────
    elif st.session_state.r_screen == 'job_detail':
        job_id = st.session_state.r_selected_job
        job = st.session_state.job_postings[job_id]
        apps = st.session_state.applications.get(job_id, [])
        analysis = st.session_state.analyses.get(job_id, {})

        if st.button("← Back to Applications"):
            st.session_state.r_screen = 'view_applications'
            st.rerun()

        st.markdown(f"### {job['title']}")
        st.markdown(f"""<div class="job-id-box" style="padding:1rem">
            <div class="job-id-code" style="font-size:1.5rem">{job_id}</div>
            <div class="job-id-label">Job ID</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"#### Applicants ({len(apps)})")
        if not apps:
            st.markdown('<div style="color:#4b5563;padding:1rem">No applications yet. Share the Job ID with candidates.</div>', unsafe_allow_html=True)
        else:
            for i, a in enumerate(apps):
                st.markdown(f"**{i+1}. {a['name']}** — {a.get('email') or 'No email provided'}")

        st.markdown("---")
        if apps and not analysis.get("done"):
            if st.button(f"Run Analysis on {len(apps)} Candidate(s)", use_container_width=True):
                st.markdown("### Analyzing Candidates...")
                run_full_analysis(job_id)
                st.session_state.r_screen = 'results'
                st.rerun()
        elif analysis.get("done"):
            if st.button("View Results", use_container_width=True):
                st.session_state.r_screen = 'results'
                st.rerun()

    # ── RESULTS ───────────────────────────────────────────────────────────────
    elif st.session_state.r_screen == 'results':
        job_id = st.session_state.r_selected_job
        job = st.session_state.job_postings[job_id]
        analysis = st.session_state.analyses.get(job_id, {})

        if not analysis.get("done"):
            st.markdown("### Analyzing Candidates...")
            run_full_analysis(job_id)
            st.rerun()

        if st.button("← Back to Applications"):
            st.session_state.r_screen = 'view_applications'
            st.rerun()

        all_results = analysis.get("results", [])
        comparison = analysis.get("comparison", {})
        winner_index = analysis.get("winner_index", 0)
        decision_made = analysis.get("decision_made", False)

        st.markdown(f"### Results — {job['title']}")

        if len(all_results) > 1 and comparison:
            st.markdown(f"""<div class="decision-hire">
                <p class="decision-title" style="color:#4ade80">Recommended Candidate: {comparison.get('winner_name','')}</p>
                <p style="color:#86efac;margin-top:0.5rem">{comparison.get('comparison_reason','')}</p>
            </div>""", unsafe_allow_html=True)

            ranking = comparison.get("ranking", [])
            if ranking:
                st.markdown("#### Ranking")
                for r in sorted(ranking, key=lambda x: x.get("rank", 99)):
                    medal = ["🥇", "🥈", "🥉"][r.get("rank", 1) - 1] if r.get("rank", 1) <= 3 else f"#{r.get('rank')}"
                    candidate_result = all_results[r.get("index", 0)] if r.get("index", 0) < len(all_results) else {}
                    ws = candidate_result.get("weighted_score", 0)
                    st.markdown(f"**{medal} {r.get('name','')}** — {ws}% weighted score — {r.get('reason','')}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Individual Analysis")
        cols = st.columns(min(len(all_results), 3))
        for i, r in enumerate(all_results):
            decision = r['decision']
            is_winner = (i == winner_index and len(all_results) > 1)
            with cols[i % len(cols)]:
                card_cls = "rank-card winner" if is_winner else "rank-card"
                winner_html = '<span class="winner-badge">Top Pick</span>' if is_winner else ""
                rec = decision.get("recommendation", "—")
                rec_color = "#4ade80" if "hire" in rec.lower() else "#f87171"

                st.markdown(f"""<div class="{card_cls}">
                    <div style="font-weight:700;font-size:1rem;color:#e2e2e8">{r['name']}{winner_html}</div>
                    <div style="color:{rec_color};font-size:0.82rem;margin-top:4px;font-weight:600">{rec}</div>
                    <div style="color:#4ade80;font-size:1.1rem;font-weight:800;margin-top:4px">{r['weighted_score']}%</div>
                    <div style="color:#6b7280;font-size:0.78rem;margin-top:6px">{decision.get('decision_reason','')}</div>
                </div>""", unsafe_allow_html=True)

                render_score_bars(r['scores'], job.get('skills_weights', {}))
                render_red_flags(r['red_flags'])

                for s in decision.get("strengths", []):
                    st.markdown(f'<span class="tag-green">✓ {s}</span>', unsafe_allow_html=True)
                for g in decision.get("gaps", []):
                    st.markdown(f'<span class="tag-red">✗ {g}</span>', unsafe_allow_html=True)

        with st.expander("View Full Analysis"):
            for r in all_results:
                st.markdown(f"**{r['name']} — Resume Extraction**")
                st.markdown(f'<div class="agent-log">{r["a1"]}</div>', unsafe_allow_html=True)
                st.markdown(f"**{r['name']} — Skills Evaluation**")
                st.markdown(f'<div class="agent-log">{r["a2"]}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if not decision_made:
            st.markdown("---")
            st.markdown("#### Final Decision")
            st.markdown("<p style='color:#9ca3af;font-size:0.85rem'>This will notify all candidates of the outcome.</p>", unsafe_allow_html=True)

            if st.button("Confirm Decision & Notify Candidates", use_container_width=True):
                if not st.session_state.email_sender or not st.session_state.email_password:
                    st.session_state.analyses[job_id]["decision_made"] = True
                    st.success("Decision recorded. No email configured.")
                    st.rerun()
                else:
                    with st.spinner("Sending notifications..."):
                        for i, r in enumerate(all_results):
                            if not r['email']:
                                continue
                            is_winner = (i == winner_index)
                            if is_winner:
                                send_email(r['email'],
                                    f"You've been selected — {job['title']} at {job['company']}",
                                    f"""Hi {r['name']},

Congratulations! After reviewing all applications for the {job['title']} position at {job['company']}, we are pleased to offer you the role.

Your profile stood out with a match score of {r['weighted_score']}%.

We will be in touch shortly with next steps.

Best regards,
{job['company']} Recruiting Team""")
                            else:
                                send_email(r['email'],
                                    f"Application Update — {job['title']} at {job['company']}",
                                    f"""Hi {r['name']},

Thank you for applying for the {job['title']} position at {job['company']}.

After reviewing all applications, we have decided to move forward with another candidate at this time.

Feedback: {r['decision'].get('decision_reason', '')}
Areas to strengthen: {', '.join(r['decision'].get('gaps', []))}

We encourage you to apply again in the future.

Best regards,
{job['company']} Recruiting Team""")

                    st.session_state.analyses[job_id]["decision_made"] = True
                    st.success("Notifications sent to all candidates.")
                    st.rerun()
        else:
            st.success("Decision has been made for this posting.")

# ══════════════════════════════════════════════════════════════════════════════
# CANDIDATE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.mode == 'candidate':

    if st.button("← Landing"):
        st.session_state.mode = None
        st.rerun()

    # ── ENTER JOB ID ─────────────────────────────────────────────────────────
    if st.session_state.c_screen == 'enter_id':
        st.markdown("### Find a Job")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        c_name = st.text_input("Your Name", value=st.session_state.c_name, placeholder="Full name")
        c_email = st.text_input("Your Email", value=st.session_state.c_email, placeholder="your@email.com")
        c_job_id = st.text_input("Job ID", value=st.session_state.c_job_id, placeholder="e.g. J4829 — provided by the recruiter")
        if c_name: st.session_state.c_name = c_name
        if c_email: st.session_state.c_email = c_email
        if c_job_id: st.session_state.c_job_id = c_job_id.upper().strip()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Find Job"):
            if not c_name:
                st.error("Please enter your name.")
            elif not st.session_state.c_job_id:
                st.error("Please enter a Job ID.")
            elif st.session_state.c_job_id not in st.session_state.job_postings:
                st.error(f"Job ID '{st.session_state.c_job_id}' not found. Please check with your recruiter.")
            else:
                st.session_state.c_screen = 'job_card'
                st.rerun()

    # ── JOB CARD ─────────────────────────────────────────────────────────────
    elif st.session_state.c_screen == 'job_card':
        job_id = st.session_state.c_job_id
        job = st.session_state.job_postings[job_id]

        if st.button("← Back"):
            st.session_state.c_screen = 'enter_id'
            st.rerun()

        st.markdown(f"""<div class="candidate-job-card">
            <div class="candidate-job-title">{job['title']}</div>
            <div class="candidate-job-company">{job['company']} · Job ID: {job_id}</div>
            <div class="candidate-job-desc">{job['description']}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="card-title">Required Skills</div>', unsafe_allow_html=True)
        for skill, weight in job['skills_weights'].items():
            st.markdown(f'<span class="{WEIGHT_COLORS[weight]}" style="margin-right:14px;font-size:0.85rem">● {skill}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("#### Upload Resume")
        pdf = st.file_uploader("PDF only", type=["pdf"])

        if pdf:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(pdf.read())
                tmp_path = tmp.name
            pdf.seek(0)
            try:
                pdf_viewer(tmp_path)
            finally:
                os.unlink(tmp_path)

        if st.button("Submit Application", use_container_width=True):
            if not pdf:
                st.error("Please upload your resume first.")
            else:
                resume_text = extract_text_from_pdf(pdf)
                if resume_text:
                    pdf.seek(0)
                    s3_url = upload_to_s3(
                        pdf.read(),
                        f"{st.session_state.c_name.replace(' ','_')}_{job_id}.pdf"
                    )
                    st.session_state.applications[job_id].append({
                        "name": st.session_state.c_name,
                        "email": st.session_state.c_email,
                        "resume_text": resume_text,
                        "s3_url": s3_url
                    })
                    st.session_state.c_screen = 'submitted'
                    st.rerun()


    # ── SUBMITTED ─────────────────────────────────────────────────────────────
    elif st.session_state.c_screen == 'submitted':
        job_id = st.session_state.c_job_id
        job = st.session_state.job_postings.get(job_id, {})

        st.markdown(f"""<div style="text-align:center;padding:3rem 1rem">
            <div style="font-size:2rem;color:#4ade80">✓</div>
            <h2 style="color:#e2e2e8;margin-top:1rem">Application Received</h2>
            <p style="color:#9ca3af;font-size:0.95rem;margin-top:0.5rem">
                Thanks {st.session_state.c_name}, your application for
                <strong style="color:#e2e2e8">{job.get('title','')}</strong>
                at <strong style="color:#e2e2e8">{job.get('company','')}</strong> has been submitted.
            </p>
            <p style="color:#4b5563;font-size:0.85rem;margin-top:1rem">We'll be in touch.</p>
        </div>""", unsafe_allow_html=True)

        if st.button("Apply to Another Job", use_container_width=True):
            st.session_state.c_screen = 'enter_id'
            st.session_state.c_job_id = ""
            st.session_state.c_name = ""
            st.session_state.c_email = ""
            st.rerun()