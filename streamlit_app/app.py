import streamlit as st
import requests

from api_client import APIClient


API_BASE_URL = "http://127.0.0.1:8000"


def get_api_client() -> APIClient:
    """Return the authenticated API client stored in session state."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient(API_BASE_URL)
    return st.session_state.api_client


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


def show_complaints(client: APIClient) -> None:
    """Render complaint submission and the authorized complaint queue."""
    st.header("Complaints")
    with st.form("new_complaint"):
        product_id = st.text_input("Product", value="product-1")
        category = st.text_input("Category", value="Billing")
        subject = st.text_input("Subject")
        description = st.text_area("Description")
        if st.form_submit_button("Submit complaint"):
            try:
                client.create_complaint({"product_id": product_id, "category": category, "channel": "web", "subject": subject, "description": description})
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
            st.write(complaint["description"])
            st.caption(f"Priority: {complaint['priority']} | SLA: {complaint['sla_state']}")
            if complaint["status"] == "RESOLVED" and st.button("Close", key=f"close_{complaint['id']}"):
                client.update_complaint_status(complaint["id"], "CLOSED")
                st.rerun()


def show_dashboard(client: APIClient) -> None:
    """Render live complaint metrics."""
    st.header("Support Dashboard")
    try:
        metrics = client.get_support_dashboard()
    except Exception as exc:
        st.error(f"Unable to load dashboard: {exc}")
        return
    first, second, third = st.columns(3)
    first.metric("Total complaints", metrics["total"])
    second.metric("Open complaints", metrics["open"])
    third.metric("SLA compliance", f"{metrics['sla_compliance_pct']}%")
    st.json(metrics)


def show_jobs(client: APIClient) -> None:
    """Render complaint import and export actions."""
    st.header("Complaint Import / Export")
    uploaded = st.file_uploader("Complaint CSV", type=["csv"])
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
    if st.button("Export complaints"):
        try:
            response = client.export_complaints()
            st.download_button("Download CSV", response.content, "complaints.csv", "text/csv")
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


def main() -> None:
    """Run the customer complaint Streamlit application."""
    st.set_page_config(page_title="Customer Complaint Management", page_icon="C", layout="wide")
    if "user" not in st.session_state:
        show_login()
        return
    client = get_api_client()
    user = st.session_state.user
    st.title("Customer Complaint Management")
    st.sidebar.write(user["email"])
    st.sidebar.write(user["role"])
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
    page = st.sidebar.radio("Navigation", ["Dashboard", "Complaints", "Import / Export", "Trend Summary"])
    if page == "Dashboard":
        show_dashboard(client)
    elif page == "Complaints":
        show_complaints(client)
    elif page == "Import / Export":
        show_jobs(client)
    else:
        show_trend_summary(client)


if __name__ == "__main__":
    main()
