import streamlit as st
import random

# Predefined interview questions, organized by category.
# Each category has questions for each difficulty level.
INTERVIEW_QUESTIONS = {
    "HR": {
        "Beginner": [
            "Tell me about yourself.",
            "Why do you want to work in a call center?",
            "What are your strengths and weaknesses?",
        ],
        "Intermediate": [
            "Describe a time you handled a conflict with a coworker.",
            "How do you handle stress during a busy shift?",
            "Why should we hire you over other candidates?",
        ],
        "Advanced": [
            "Tell me about a time you disagreed with your manager. How did you handle it?",
            "How would you handle being asked to work overtime with no notice?",
            "Describe a situation where you had to give difficult feedback to a peer.",
        ],
    },
    "Customer Service": {
        "Beginner": [
            "How would you greet a customer calling for the first time?",
            "What does good customer service mean to you?",
            "How do you stay polite when a customer is rude?",
        ],
        "Intermediate": [
            "A customer is unhappy with a delayed order. How do you respond?",
            "How would you handle a customer who keeps interrupting you?",
            "Describe how you would de-escalate an angry customer.",
        ],
        "Advanced": [
            "A customer threatens to cancel their service unless given a refund you can't approve. How do you handle it?",
            "How would you manage a customer who has been transferred multiple times and is frustrated?",
            "Describe a time you turned a negative customer experience into a positive one.",
        ],
    },
    "Sales": {
        "Beginner": [
            "How would you introduce a new product to a customer?",
            "What makes a good salesperson?",
            "How do you handle a customer who says 'I'm not interested'?",
        ],
        "Intermediate": [
            "How would you upsell a product without sounding pushy?",
            "Describe how you would handle a customer comparing you to a competitor.",
            "What would you do if a customer wanted a discount you couldn't give?",
        ],
        "Advanced": [
            "How would you close a sale with a customer who has been hesitant for weeks?",
            "Describe a time you lost a sale. What would you do differently now?",
            "How would you handle a high-value client threatening to switch to a competitor?",
        ],
    },
    "Technical Support": {
        "Beginner": [
            "How would you explain a technical issue to a non-technical customer?",
            "What steps would you take when a customer says their device won't turn on?",
            "How do you stay calm when you don't know the answer right away?",
        ],
        "Intermediate": [
            "A customer's internet keeps disconnecting. How would you troubleshoot this over the phone?",
            "How would you handle a customer who doesn't follow your instructions correctly?",
            "Describe how you would explain a software update to a frustrated user.",
        ],
        "Advanced": [
            "A customer's issue requires escalation, but they refuse to be transferred. How do you handle it?",
            "Describe how you would manage a technical outage affecting many customers at once.",
            "How would you handle a customer who claims your previous advice made the problem worse?",
        ],
    },
}

# Predefined customer scenarios, one per situation type.
# These are shown to the user after they pick an option and click "Generate Scenario".
CUSTOMER_SCENARIOS = {
    "Angry Customer": "A customer is shouting on the call because their issue hasn't been fixed after multiple attempts. They feel ignored and want to speak to a manager immediately.",
    "Refund Request": "A customer is requesting a full refund for a product they say did not meet their expectations. They are firm and want the refund processed today.",
    "Late Delivery": "A customer's package was supposed to arrive three days ago but still hasn't shown up. They have an important event coming up and are anxious about not receiving it in time.",
    "Wrong Product Received": "A customer received the wrong product and is very upset. They are demanding an immediate replacement and want compensation.",
    "Technical Support": "A customer's device stopped working after a recent software update. They have already tried restarting it and are frustrated that basic troubleshooting hasn't helped.",
}

# Predefined professional email templates, one per email type.
# {customer_name} etc. are left as placeholders for the user to fill in when editing.
EMAIL_TEMPLATES = {
    "Apology Email": """Subject: Our Apologies for the Inconvenience

Dear [Customer Name],

I want to sincerely apologize for the inconvenience you experienced with [issue/order]. This is not the level of service we strive to provide, and I understand your frustration.

We have looked into what happened and are taking steps to make sure it does not happen again. [Add specific details about the resolution here.]

Thank you for your patience and for bringing this to our attention. Please let me know if there is anything else I can do to help.

Best regards,
[Your Name]
[Company Name]""",

    "Follow-up Email": """Subject: Following Up on Your Recent Request

Dear [Customer Name],

I hope you're doing well. I'm following up regarding [topic/request] from [date] to check if everything is resolved on your end.

If you still have questions or need further assistance, please don't hesitate to reach out. I'm happy to help in any way I can.

Looking forward to hearing from you.

Best regards,
[Your Name]
[Company Name]""",

    "Refund Approval": """Subject: Your Refund Has Been Approved

Dear [Customer Name],

Good news! Your refund request for [order/product] has been reviewed and approved.

You should see the amount of [refund amount] credited back to your original payment method within [X] business days.

We appreciate your patience throughout this process, and please let us know if you have any further questions.

Best regards,
[Your Name]
[Company Name]""",

    "Customer Reply": """Subject: Re: [Original Subject]

Dear [Customer Name],

Thank you for reaching out to us. I appreciate you taking the time to share your concerns about [issue/topic].

[Add your specific response or solution here.]

If you need any further assistance, feel free to reply to this email or contact us anytime.

Best regards,
[Your Name]
[Company Name]""",
}

# Basic page setup
st.set_page_config(
    page_title="AI Call Center Training Assistant",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — gives the app a premium SaaS-dashboard look (gradient
# background, glassmorphism cards, hover animations, styled widgets).
# This only changes appearance; it doesn't touch any app logic below.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #2563EB;
    --secondary: #0F172A;
    --accent: #38BDF8;
    --success: #10B981;
    --text-light: #E2E8F0;
    --text-muted: #94A3B8;
    --glass-bg: rgba(255, 255, 255, 0.06);
    --glass-border: rgba(255, 255, 255, 0.12);
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Gradient app background */
.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(37, 99, 235, 0.35), transparent 45%),
        radial-gradient(circle at 85% 0%, rgba(56, 189, 248, 0.25), transparent 40%),
        radial-gradient(circle at 50% 100%, rgba(16, 185, 129, 0.12), transparent 40%),
        linear-gradient(160deg, #0B1120 0%, #0F172A 45%, #111827 100%);
    background-attachment: fixed;
}

footer { visibility: hidden; }

h1, h2, h3, h4, h5, h6 { color: #F8FAFC !important; font-weight: 700 !important; }
p, li, label, span { color: var(--text-light); }

.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1120 0%, #111827 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] * { color: var(--text-light); }

.sidebar-brand {
    padding: 0.5rem 0.25rem 1.25rem 0.25rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1rem;
}
.sidebar-brand .brand-icon { font-size: 2rem; }
.sidebar-brand .brand-name { font-size: 1.05rem; font-weight: 700; color: #fff; margin-top: 4px; }
.sidebar-brand .brand-tag { font-size: 0.78rem; color: var(--text-muted); }

.sidebar-section-label {
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    font-weight: 700;
    margin: 0.25rem 0 0.5rem 0.1rem;
}

.sidebar-footer {
    margin-top: 1.5rem;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(255,255,255,0.08);
    font-size: 0.72rem;
    color: var(--text-muted);
    text-align: center;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 0.5rem 0.7rem;
    border-radius: 10px;
    transition: background 0.2s ease, transform 0.15s ease;
    width: 100%;
    margin-bottom: 2px;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(56, 189, 248, 0.12);
    transform: translateX(2px);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(37,99,235,0.4), rgba(56,189,248,0.15));
    border: 1px solid rgba(56,189,248,0.35);
}

/* ---------- Glass cards (st.container(border=True) sections) ---------- */
[data-testid="stMain"] [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"]),
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--glass-bg);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--glass-border);
    border-radius: 18px;
    padding: 1.25rem 1.25rem 0.5rem 1.25rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}
[data-testid="stMain"] [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"]):hover,
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 14px 40px rgba(37, 99, 235, 0.25);
    border-color: rgba(56, 189, 248, 0.4);
}

/* ---------- Hero ---------- */
.hero-card {
    background: linear-gradient(120deg, rgba(37,99,235,0.25), rgba(56,189,248,0.12));
    border: 1px solid rgba(56,189,248,0.25);
    border-radius: 22px;
    padding: 2.5rem 2rem;
    text-align: center;
    margin-bottom: 1.75rem;
    backdrop-filter: blur(16px);
    box-shadow: 0 10px 40px rgba(37,99,235,0.2);
}
.hero-title {
    font-size: 2.3rem;
    font-weight: 800;
    background: linear-gradient(90deg, #38BDF8, #60A5FA, #818CF8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
}
.hero-subtitle { font-size: 1.02rem; color: var(--text-muted); max-width: 700px; margin: 0 auto; }

/* ---------- Page header (non-home pages) ---------- */
.page-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 18px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(14px);
}
.page-header-icon {
    font-size: 1.8rem;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    width: 56px; height: 56px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 14px;
    flex-shrink: 0;
}
.page-header-title { font-size: 1.4rem; font-weight: 700; color: #fff; }
.page-header-subtitle { font-size: 0.92rem; color: var(--text-muted); margin-top: 2px; }

/* ---------- Metric cards ---------- */
.metric-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 1.25rem 1rem;
    text-align: center;
    backdrop-filter: blur(12px);
    transition: transform 0.2s ease, border-color 0.2s ease;
    margin-bottom: 1rem;
}
.metric-card:hover { transform: translateY(-3px); border-color: rgba(56,189,248,0.4); }
.metric-icon { font-size: 1.6rem; margin-bottom: 0.35rem; }
.metric-value { font-size: 1.7rem; font-weight: 800; color: #fff; }
.metric-label { font-size: 0.8rem; color: var(--text-muted); margin-top: 2px; }

.section-label {
    font-size: 0.8rem;
    letter-spacing: 0.1em;
    color: var(--accent);
    font-weight: 700;
    margin: 1.5rem 0 0.75rem 0.2rem;
}

/* ---------- Feature cards (Home page) ---------- */
.feature-card-icon {
    font-size: 1.6rem;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    width: 52px; height: 52px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 13px;
    margin-bottom: 0.6rem;
}
.feature-card-title { font-size: 1.15rem; font-weight: 700; color: #fff; margin-bottom: 0.3rem; }
.feature-card-desc { font-size: 0.88rem; color: var(--text-muted); line-height: 1.4; margin-bottom: 0.5rem; }

/* ---------- Buttons ---------- */
.stButton > button {
    background: linear-gradient(135deg, var(--primary), var(--accent));
    color: #fff !important;
    border: none;
    border-radius: 10px;
    padding: 0.55rem 1.2rem;
    font-weight: 600;
    transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(37, 99, 235, 0.45);
    opacity: 0.95;
    color: #fff !important;
}
.stButton > button:active { transform: translateY(0); }
.stButton > button p { color: #fff !important; }

/* ---------- Selectbox / dropdown ---------- */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 10px !important;
    color: var(--text-light) !important;
    transition: border-color 0.2s ease;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover { border-color: var(--accent) !important; }
div[data-baseweb="popover"] ul {
    background: #111827 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
}
div[data-baseweb="popover"] li { color: var(--text-light) !important; }
div[data-baseweb="popover"] li:hover { background: rgba(56,189,248,0.15) !important; }

/* ---------- Text areas ---------- */
[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    color: var(--text-light) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.2) !important;
}
[data-testid="stTextArea"] textarea::placeholder { color: var(--text-muted) !important; }

/* ---------- Alerts ---------- */
[data-testid="stAlert"] { border-radius: 12px !important; }

/* ---------- Footer ---------- */
.app-footer {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.85rem;
    padding: 1.5rem 0 0.5rem 0;
    margin-top: 2rem;
    border-top: 1px solid rgba(255,255,255,0.08);
}
.app-footer span { color: var(--accent); font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Navigation setup. We keep the same five sections as before, just displayed
# with icons and made clickable from feature cards on the Home page too.
# ---------------------------------------------------------------------------
MENU_OPTIONS = ["Home", "Interview Practice", "Answer Evaluation", "Customer Scenarios", "Email Generator"]
MENU_ICONS = {
    "Home": "🏠",
    "Interview Practice": "🎤",
    "Answer Evaluation": "📝",
    "Customer Scenarios": "💬",
    "Email Generator": "✉️",
}

# Track the active section in session_state so the Home page's feature cards
# can jump straight to a section (in addition to the sidebar radio).
if "menu_choice" not in st.session_state:
    st.session_state.menu_choice = "Home"

# Premium sidebar: brand header + icon navigation
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="brand-icon">📞</div>
        <div class="brand-name">AI Call Center</div>
        <div class="brand-tag">Training Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">NAVIGATION</div>', unsafe_allow_html=True)
    menu = st.radio(
        "Menu",
        MENU_OPTIONS,
        format_func=lambda option: f"{MENU_ICONS[option]}  {option}",
        key="menu_choice",
        label_visibility="collapsed",
    )

    st.markdown('<div class="sidebar-footer">Portfolio Project • v1.0</div>', unsafe_allow_html=True)


def render_page_header(icon, title, subtitle):
    """Shows a consistent glass-card header at the top of a page section."""
    st.markdown(f"""
    <div class="page-header">
        <div class="page-header-icon">{icon}</div>
        <div>
            <div class="page-header-title">{title}</div>
            <div class="page-header-subtitle">{subtitle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Home page
if menu == "Home":
    st.markdown("""
    <div class="hero-card">
        <div class="hero-title">📞 AI Call Center Training Assistant</div>
        <div class="hero-subtitle">A modern, all-in-one training dashboard to practice interviews, evaluate your
        answers, master real customer scenarios, and craft professional emails.</div>
    </div>
    """, unsafe_allow_html=True)

    # Metric cards — real counts pulled from the data above, not fake numbers.
    metric_values = [
        ("🗂️", len(INTERVIEW_QUESTIONS), "Question Categories"),
        ("🎯", len(next(iter(INTERVIEW_QUESTIONS.values()))), "Difficulty Levels"),
        ("💬", len(CUSTOMER_SCENARIOS), "Customer Scenarios"),
        ("✉️", len(EMAIL_TEMPLATES), "Email Templates"),
    ]
    metric_cols = st.columns(4)
    for col, (icon, value, label) in zip(metric_cols, metric_values):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">EXPLORE FEATURES</div>', unsafe_allow_html=True)

    features = [
        ("🎤", "Interview Practice", "Practice with real HR, sales, and support questions across 3 difficulty levels."),
        ("📝", "Answer Evaluation", "Get instant feedback on communication, grammar, and confidence."),
        ("💬", "Customer Scenarios", "Handle realistic customer situations and sharpen your responses."),
        ("✉️", "Email Generator", "Generate professional email templates in seconds."),
    ]

    row1 = st.columns(2)
    row2 = st.columns(2)
    card_slots = [row1[0], row1[1], row2[0], row2[1]]

    for (icon, title, desc), col in zip(features, card_slots):
        with col:
            with st.container(border=True):
                st.markdown(f"""
                <div class="feature-card-icon">{icon}</div>
                <div class="feature-card-title">{title}</div>
                <div class="feature-card-desc">{desc}</div>
                """, unsafe_allow_html=True)
                if st.button(f"Open {title} →", key=f"open_{title}", use_container_width=True):
                    st.session_state.menu_choice = title
                    st.rerun()

# Interview Practice page
elif menu == "Interview Practice":
    render_page_header("🎤", "Interview Practice", "Pick a category and difficulty, then generate a random question to practice with.")

    with st.container(border=True):
        # Dropdown to choose the question category
        category = st.selectbox(
            "Category",
            ["HR", "Customer Service", "Sales", "Technical Support"]
        )

        # Dropdown to choose the difficulty level
        difficulty = st.selectbox(
            "Difficulty",
            ["Beginner", "Intermediate", "Advanced"]
        )

        # When the button is clicked, pick and show a random question
        if st.button("Generate Question", use_container_width=True):
            questions = INTERVIEW_QUESTIONS[category][difficulty]
            question = random.choice(questions)
            st.success(question)

# Answer Evaluation page
elif menu == "Answer Evaluation":
    render_page_header("📝", "Answer Evaluation", "Write an interview answer below and get a professional-style evaluation.")

    with st.container(border=True):
        # Text area for the user to type their answer
        answer = st.text_area("Your Answer", height=150, placeholder="Type your interview answer here...")

        # When the button is clicked, show a fixed sample evaluation
        # (No AI is used yet — these are placeholder scores for now.)
        if st.button("Evaluate Answer", use_container_width=True):
            if answer.strip() == "":
                st.warning("Please write an answer before evaluating.")
            else:
                st.markdown("### Evaluation Results")
                st.write("Communication: 8/10")
                st.write("Grammar: 7/10")
                st.write("Confidence: 9/10")
                st.write("Professionalism: 8/10")
                st.write("**Overall Score: 8/10**")

                st.markdown("### Improvement Suggestions")
                st.write("1. Use more specific examples to support your points.")
                st.write("2. Keep sentences shorter and clearer for easier understanding.")
                st.write("3. Practice a confident tone by speaking slower and pausing between ideas.")

# Customer Scenarios page
elif menu == "Customer Scenarios":
    render_page_header("💬", "Customer Scenarios", "Pick a situation, generate a scenario, then write and submit your response.")

    with st.container(border=True):
        # Dropdown to choose which customer situation to practice
        scenario_type = st.selectbox(
            "Scenario Type",
            ["Angry Customer", "Refund Request", "Late Delivery", "Wrong Product Received", "Technical Support"]
        )

        # When clicked, show the scenario text for the chosen situation
        if st.button("Generate Scenario", use_container_width=True):
            st.markdown("### Scenario")
            st.info(CUSTOMER_SCENARIOS[scenario_type])

        # Text area for the user to write how they would respond to the customer
        response = st.text_area("Write your response to the customer", height=150, placeholder="Type your response here...")

        # When the button is clicked, show a fixed sample evaluation
        # (No AI is used yet — these are placeholder scores for now.)
        if st.button("Submit Response", use_container_width=True):
            if response.strip() == "":
                st.warning("Please write a response before submitting.")
            else:
                st.markdown("### Evaluation Results")
                st.write("Customer Handling: 8/10")
                st.write("Professionalism: 9/10")
                st.write("Empathy: 8/10")
                st.write("Problem Solving: 8/10")
                st.write("**Overall Score: 8.5/10**")

                st.markdown("### Improvement Suggestions")
                st.write("1. Show more empathy.")
                st.write("2. Offer a clear solution.")
                st.write("3. End with reassurance.")

# Email Generator page
elif menu == "Email Generator":
    render_page_header("✉️", "Email Generator", "Pick an email type, generate a template, then copy and edit it as needed.")

    with st.container(border=True):
        # Dropdown to choose which type of email to generate
        email_type = st.selectbox(
            "Email Type",
            ["Apology Email", "Follow-up Email", "Refund Approval", "Customer Reply"]
        )

        # When clicked, show the template inside an editable text area
        if st.button("Generate Email", use_container_width=True):
            st.text_area("Generated Email", value=EMAIL_TEMPLATES[email_type], height=300)
            st.success("Copy Ready ✅")

# Footer — shown on every page
st.markdown("""
<div class="app-footer">Built with <span>Python</span> • <span>Streamlit</span> • <span>Claude Code</span></div>
""", unsafe_allow_html=True)
