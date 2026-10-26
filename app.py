
# app.py

import streamlit as st
import pandas as pd

from database import (
    init_db,
    save_request,
    get_all_requests,
    update_request_status,
    get_dashboard_stats,
)
from ai_engine import analyze_request

st.set_page_config(
    page_title="AI Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ---------- CUSTOM STYLING ----------


st.markdown("""
<style>
.stApp {
    background-color: #f4f7fb;
    color: #1e293b;
}

[data-testid="stSidebar"] {
    background-color: #eaf0fa;
}

[data-testid="stSidebar"] * {
    color: #1e293b !important;
}

.main-title {
    font-size: 2.2rem;
    font-weight: 750;
    color: #163a70 !important;
}

.subtitle {
    color: #61728b !important;
    font-size: 1rem;
}

h1, h2, h3, h4, p, label,
[data-testid="stMarkdownContainer"] {
    color: #1e293b;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #dce5f1;
    padding: 18px;
    border-radius: 12px;
}

div[data-testid="stForm"] {
    background: #ffffff !important;
    color: #1e293b !important;
    padding: 20px;
    border-radius: 12px;
}

/* Make typed text and placeholders readable in light and dark themes */
.stTextArea textarea,
.stTextInput input,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    background-color: #ffffff !important;
    color: #1e293b !important;
    -webkit-text-fill-color: #1e293b !important;
    caret-color: #1e293b !important;
    border-color: #94a3b8 !important;
}

.stTextArea textarea::placeholder,
.stTextInput input::placeholder,
[data-baseweb="textarea"] textarea::placeholder,
[data-baseweb="input"] input::placeholder {
    color: #64748b !important;
    -webkit-text-fill-color: #64748b !important;
    opacity: 1 !important;
}

/* Improve button readability */
.stButton button,
.stFormSubmitButton button {
    color: #ffffff !important;
}

/* Keep alerts and normal page text readable */
[data-testid="stAlert"] *,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: #1e293b;
}
</style>
""", unsafe_allow_html=True)


# ---------- SIDEBAR ----------

with st.sidebar:
    st.title("🛡️ AI Sentinel")
    st.caption("Intelligent Workflow Automation")
    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "New Request",
            "Request History",
            "About Project",
        ],
    )

    st.divider()
    st.caption("Powered by")
    st.write("Python • Streamlit")
    st.write("LangChain • LLM • SQLite")


# ---------- DASHBOARD ----------

if page == "Dashboard":
    st.markdown(
        '<div class="main-title">AI Sentinel Dashboard</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">'
        'Monitor support requests and streamline workflows with AI.'
        '</div>',
        unsafe_allow_html=True,
    )

    stats = get_dashboard_stats()

    st.write("")
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Requests", stats["total"])
    c2.metric("High Priority", stats["high"])
    c3.metric("Pending", stats["pending"])
    c4.metric("Resolved", stats["resolved"])

    st.divider()
    st.subheader("Recent Requests")

    requests = get_all_requests()

    if not requests:
        st.info(
            "No requests yet. Select 'New Request' from the sidebar "
            "to analyze your first request."
        )
    else:
        for request in requests[:5]:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(
                        f"**#{request['id']} — "
                        f"{request['category']}**"
                    )
                    st.write(request["summary"])
                    st.caption(request["created_at"])

                with col2:
                    st.write(f"**Priority:** {request['priority']}")
                    st.write(f"**Status:** {request['status']}")


# ---------- NEW REQUEST ----------

elif page == "New Request":
    st.title("➕ New Support Request")
    st.write(
        "Describe a problem or task. AI Sentinel will analyze it "
        "and recommend the next step."
    )

    with st.form("new_request_form"):
        description = st.text_area(
            "Request description",
            placeholder=(
                "Example: Our website is down and customers "
                "cannot access their accounts."
            ),
            height=150,
            max_chars=5000,
        )

        submitted = st.form_submit_button(
            "Analyze Request",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not description.strip():
            st.error("Please enter a request description.")
        else:
            with st.spinner("Analyzing request..."):
                result = analyze_request(description.strip())

            # Store the analysis between Streamlit reruns.
            st.session_state["pending_analysis"] = {
                "description": description.strip(),
                "result": result,
            }

    pending = st.session_state.get("pending_analysis")

    if pending:
        result = pending["result"]

        st.divider()
        st.subheader("AI Analysis Results")

        if result["source"] == "Demo rules":
            st.warning(
                "Demo mode: these results were generated using "
                "basic rules, not an LLM. Configure an API key "
                "for AI-powered analysis."
            )
        else:
            st.success("Analysis completed using an AI language model.")

        c1, c2, c3 = st.columns(3)
        c1.metric("Category", result["category"])
        c2.metric("Priority", result["priority"])
        c3.metric("Analysis Mode", result["source"])

        st.markdown("#### Request Summary")
        st.write(result["summary"])

        st.markdown("#### Recommended Next Action")
        st.info(result["action"])

        st.caption(
            "Recommendations are not executed automatically. "
            "Review them before taking action."
        )

        col_save, col_discard = st.columns(2)

        with col_save:
            if st.button(
                "Approve & Save Request",
                type="primary",
                use_container_width=True,
            ):
                save_request(
                    pending["description"],
                    result,
                )
                st.session_state.pop("pending_analysis", None)
                st.session_state["request_saved"] = True
                st.rerun()

        with col_discard:
            if st.button(
                "Discard Analysis",
                use_container_width=True,
            ):
                st.session_state.pop("pending_analysis", None)
                st.rerun()

    if st.session_state.pop("request_saved", False):
        st.success("Approved request saved successfully!")


# ---------- REQUEST HISTORY ----------

elif page == "Request History":
    st.title("📋 Request History")
    st.write(
        "Review previous analyses and manage request status."
    )

    requests = get_all_requests()

    if not requests:
        st.info("No saved requests found.")
    else:
        search_text = st.text_input(
            "Search requests",
            placeholder="Search by description or category...",
        )

        filtered = [
            r for r in requests
            if search_text.lower() in (
                r["description"] + " " + r["category"]
            ).lower()
        ]

        if filtered:
            table_data = [
                {
                    "ID": r["id"],
                    "Category": r["category"],
                    "Priority": r["priority"],
                    "Status": r["status"],
                    "Summary": r["summary"],
                    "Created": r["created_at"],
                }
                for r in filtered
            ]

            st.dataframe(
                pd.DataFrame(table_data),
                use_container_width=True,
                hide_index=True,
            )

            st.divider()
            st.subheader("Manage a Request")

            selected_id = st.selectbox(
                "Select request ID",
                options=[r["id"] for r in filtered],
            )

            selected = next(
                r for r in filtered if r["id"] == selected_id
            )

            with st.container(border=True):
                st.write("**Description:**", selected["description"])
                st.write("**Category:**", selected["category"])
                st.write("**Priority:**", selected["priority"])
                st.write("**Summary:**", selected["summary"])
                st.write(
                    "**Recommended action:**",
                    selected["action"],
                )

                statuses = ["Pending", "In Progress", "Resolved"]

                new_status = st.selectbox(
                    "Workflow status",
                    statuses,
                    index=statuses.index(selected["status"]),
                    key=f"status_{selected_id}",
                )

                if st.button("Update Status", type="primary"):
                    update_request_status(selected_id, new_status)
                    st.success("Request status updated.")
                    st.rerun()
        else:
            st.info("No requests match your search.")


# ---------- ABOUT PROJECT ----------

elif page == "About Project":
    st.title("ℹ️ About AI Sentinel")

    st.markdown("""
    **AI Sentinel** is an AI-powered workflow automation prototype
    designed to reduce the manual effort involved in handling
    support requests.

    ### Main capabilities
    - AI classification of incoming requests.
    - Priority detection and concise summaries.
    - Recommended next steps.
    - Human approval before saving analyzed requests.
    - Persistent SQLite storage and workflow tracking.
    - Dashboard metrics and searchable history.

    ### Technology stack
    - Python
    - Streamlit
    - LangChain and an OpenAI-compatible LLM API
    - SQLite
    - Pandas

    ### Security
    - API keys are read from environment variables.
    - SQL statements use parameterized queries.
    - AI recommendations are not executed automatically.
    - Invalid model responses use a safe fallback.

    ### Limitations
    The demo fallback uses basic rules, not artificial intelligence.
    LLM output can be incorrect, so users must review recommendations.
    This prototype does not connect to a real ticketing platform.
    """)

st.divider()
st.caption(
    "AI Sentinel | Student Project | "
    "Human review is required before consequential actions."
)
