import json

import requests
import streamlit as st

from api_client import APIClient


API_BASE_URL = "http://127.0.0.1:8000"
MANAGER_ROLES = {"ADMIN", "SUPPORT_MANAGER"}


def get_api_client() -> APIClient:
    """Return the authenticated API client stored in session state."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient(API_BASE_URL)
    return st.session_state.api_client


def current_role() -> str:
    """Return the active user's normalized role."""
    return st.session_state.user["role"].upper()


def show_login() -> None:
    """Render customer-support login."""
    st.title("Customer Complaint Management")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            try:
                client = get_api_client()
                client.login(email, password)
                st.session_state.user = client.get_me()
                st.rerun()
            except Exception as exc:
                st.error(f"Login failed: {exc}")


def render_complaint_summary(complaint: dict) -> None:
    """Render common complaint details."""
    st.write(complaint["description"])
    st.caption(
        " | ".join(
            [
                f"Customer: {complaint['customer_id']}",
                f"Product: {complaint['product_id']}",
                f"Assigned agent: {complaint.get('assigned_agent_email') or 'Unassigned'}",
                f"Priority: {complaint['priority']}",
                f"SLA: {complaint['sla_state']}",
            ]
        )
    )


def show_customer_workflow(client: APIClient) -> None:
    """Render complaint submission and customer-owned complaint actions."""
    st.header("My Complaints")
    with st.form("new_complaint"):
        product_id = st.text_input("Product", value="product-1")
        category = st.text_input("Category", value="Billing")
        subject = st.text_input("Subject")
        description = st.text_area("Description")
        priority = st.selectbox("Priority", ["MEDIUM", "LOW", "HIGH", "CRITICAL"])
        if st.form_submit_button("Submit complaint"):
            try:
                client.create_complaint(
                    {
                        "product_id": product_id,
                        "category": category,
                        "channel": "web",
                        "subject": subject,
                        "description": description,
                        "priority": priority,
                    }
                )
                st.success("Complaint submitted")
                st.rerun()
            except Exception as exc:
                st.error(f"Submission failed: {exc}")

    try:
        complaints = client.get_complaints()
    except Exception as exc:
        st.error(f"Unable to load complaints: {exc}")
        return

    for complaint in complaints:
        with st.expander(f"#{complaint['id']} {complaint['subject']} [{complaint['status']}]"):
            render_complaint_summary(complaint)
            if complaint["status"] == "RESOLVED" and st.button("Close", key=f"close_{complaint['id']}"):
                client.update_complaint_status(complaint["id"], "CLOSED")
                st.rerun()
            if complaint["status"] == "CLOSED" and st.button("Reopen", key=f"reopen_{complaint['id']}"):
                client.update_complaint_status(complaint["id"], "REOPENED")
                st.rerun()


def show_agent_workflow(client: APIClient) -> None:
    """Render assigned support-agent queue and allowed work actions."""
    st.header("Assigned Queue")
    status_filter = st.selectbox(
        "Status",
        ["", "NEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REOPENED", "CLOSED"],
    )
    filters = {"status": status_filter} if status_filter else {}

    try:
        complaints = client.get_complaints(**filters)
    except Exception as exc:
        st.error(f"Unable to load assigned complaints: {exc}")
        return

    for complaint in complaints:
        with st.expander(f"#{complaint['id']} {complaint['subject']} [{complaint['status']}]"):
            render_complaint_summary(complaint)
            next_status = st.selectbox(
                "Next status",
                ["IN_PROGRESS", "RESOLVED"],
                key=f"agent_status_{complaint['id']}",
            )
            note = st.text_area("Work note", key=f"agent_note_{complaint['id']}")
            visibility = st.radio(
                "Note visibility",
                ["customer", "internal"],
                horizontal=True,
                key=f"agent_visibility_{complaint['id']}",
            )
            first, second = st.columns(2)
            if first.button("Update status", key=f"agent_update_{complaint['id']}"):
                try:
                    client.update_complaint_status(complaint["id"], next_status, note or None)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Status update failed: {exc}")
            if second.button("Add note", key=f"agent_note_button_{complaint['id']}"):
                try:
                    client.add_note(complaint["id"], note, visibility)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Note failed: {exc}")


def show_manager_queue(client: APIClient) -> None:
    """Render manager/admin queue management, assignment, and escalation."""
    st.header("Team Queue")
    try:
        agents = client.get_support_agents()
    except Exception as exc:
        st.error(f"Unable to load support agents: {exc}")
        return

    st.subheader("Agent workload")
    st.dataframe(
        [
            {
                "Agent": agent["email"],
                "Open complaints": agent["open_complaints"],
            }
            for agent in agents
        ],
        use_container_width=True,
        hide_index=True,
    )
    status_filter = st.selectbox(
        "Status",
        ["", "NEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REOPENED", "CLOSED"],
    )
    category = st.text_input("Category filter")
    filters: dict[str, str] = {}
    if status_filter:
        filters["status"] = status_filter
    if category:
        filters["category"] = category

    try:
        complaints = client.get_complaints(**filters)
    except Exception as exc:
        st.error(f"Unable to load queue: {exc}")
        return

    for complaint in complaints:
        with st.expander(f"#{complaint['id']} {complaint['subject']} [{complaint['status']}]"):
            render_complaint_summary(complaint)
            agent_options = {"No assignment": None}
            agent_options.update({
                f"{agent['email']} ({agent['open_complaints']} open)": agent["id"]
                for agent in agents
            })
            current_label = next(
                (label for label, agent_id in agent_options.items()
                 if agent_id == complaint["assigned_agent_id"]),
                "No assignment",
            )
            selected_agent = st.selectbox(
                "Assign to agent",
                list(agent_options),
                index=list(agent_options).index(current_label),
                key=f"assign_agent_{complaint['id']}",
            )
            if st.button("Assign", key=f"assign_button_{complaint['id']}"):
                try:
                    client.assign_complaint(
                        complaint["id"],
                        assigned_agent_id=agent_options[selected_agent],
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Assignment failed: {exc}")

            level = st.slider("Escalation level", 1, 3, 1, key=f"esc_level_{complaint['id']}")
            reason = st.text_input("Escalation reason", key=f"esc_reason_{complaint['id']}")
            if st.button("Escalate", key=f"escalate_button_{complaint['id']}"):
                try:
                    client.escalate_complaint(complaint["id"], level, reason)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Escalation failed: {exc}")


def show_dashboard(client: APIClient) -> None:
    """Render live complaint metrics."""
    st.header("Support Dashboard")
    try:
        metrics = client.get_support_dashboard()
    except Exception as exc:
        st.error(f"Unable to load dashboard: {exc}")
        return
    first, second, third, fourth = st.columns(4)
    first.metric("Total complaints", metrics["total"])
    second.metric("Open complaints", metrics["open"])
    third.metric("SLA compliance", f"{metrics['sla_compliance_pct']}%")
    fourth.metric("Cache", metrics["cache"])
    st.json(metrics)


def show_reports(client: APIClient) -> None:
    """Render manager/admin operational reports."""
    st.header("Reports")
    try:
        st.subheader("SLA Performance")
        st.dataframe(client.get_sla_performance(), use_container_width=True)
        st.subheader("Agent Ranking")
        st.dataframe(client.get_agent_ranking(), use_container_width=True)
    except Exception as exc:
        st.error(f"Unable to load reports: {exc}")


def show_jobs(client: APIClient) -> None:
    """Render complaint import and export actions."""
    st.header("Complaint Import / Export")
    uploaded = st.file_uploader("Complaint CSV or JSON", type=["csv", "json"])
    if uploaded is not None and st.button("Start import"):
        try:
            result = client.import_complaints(uploaded.getvalue(), uploaded.name)
            st.session_state.complaint_job_id = result["job_id"]
        except Exception as exc:
            st.error(f"Import failed: {exc}")
    job_id = st.session_state.get("complaint_job_id")
    if job_id:
        job = client.get_job(job_id)
        st.write(f"Job {job['id']}: {job['status']}")
        st.progress(job["progress"] / 100)
        st.write(f"Accepted: {job['accepted_count']} | Rejected: {job['rejected_count']}")
        if job.get("result"):
            st.json(json.loads(job["result"]))

    export_format = st.radio("Export format", ["csv", "json"], horizontal=True)
    if st.button("Export complaints"):
        try:
            response = client.export_complaints(export_format)
            media_type = "application/json" if export_format == "json" else "text/csv"
            st.download_button(
                f"Download {export_format.upper()}",
                response.content,
                f"complaints.{export_format}",
                media_type,
            )
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 401:
                st.session_state.clear()
                st.error("Your login session expired. Please log in again.")
                st.stop()
            st.error(f"Export failed: {exc}")


def show_trend_summary(client: APIClient) -> None:
    """Render the computed-metrics complaint trend narrative."""
    st.header("Complaint Trend Summary")
    instruction = st.text_area("Manager instruction")
    if st.button("Generate summary"):
        try:
            result = client.get_trend_summary(instruction)
            st.write(result["narrative"])
            st.json(result["metrics"])
            st.write(result["observations"])
        except Exception as exc:
            st.error(f"Summary unavailable: {exc}")


def navigation_for(role: str) -> list[str]:
    """Return role-specific Streamlit navigation."""
    if role == "CUSTOMER":
        return ["My Complaints"]
    if role == "SUPPORT_AGENT":
        return ["Assigned Queue", "Dashboard", "Trend Summary"]
    if role in MANAGER_ROLES:
        return ["Dashboard", "Team Queue", "Reports", "Import / Export", "Trend Summary"]
    return ["Dashboard"]


def main() -> None:
    """Run the customer complaint Streamlit application."""
    st.set_page_config(page_title="Customer Complaint Management", page_icon="C", layout="wide")
    if "user" not in st.session_state:
        show_login()
        return

    client = get_api_client()
    user = st.session_state.user
    role = current_role()
    st.title("Customer Complaint Management")
    st.sidebar.write(user["email"])
    st.sidebar.write(role)
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    page = st.sidebar.radio("Navigation", navigation_for(role))
    if page == "My Complaints":
        show_customer_workflow(client)
    elif page == "Assigned Queue":
        show_agent_workflow(client)
    elif page == "Team Queue":
        show_manager_queue(client)
    elif page == "Reports":
        show_reports(client)
    elif page == "Import / Export":
        show_jobs(client)
    elif page == "Trend Summary":
        show_trend_summary(client)
    else:
        show_dashboard(client)


if __name__ == "__main__":
    main()
