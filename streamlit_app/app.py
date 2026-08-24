import time

import streamlit as st

from api_client import APIClient


API_BASE_URL = "http://127.0.0.1:8000"


def get_api_client() -> APIClient:
    """Get the API client from Streamlit session state."""

    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient(
            API_BASE_URL
        )

    return st.session_state.api_client


def show_login() -> None:
    """Display the login screen."""

    st.title("Vendor Contract Management")

    st.subheader("Login")

    with st.form("login_form"):

        email = st.text_input(
            "Email",
            placeholder="admin@example.com",
        )

        password = st.text_input(
            "Password",
            type="password",
        )

        submitted = st.form_submit_button(
            "Login",
            use_container_width=True,
        )

        if submitted:

            if not email or not password:
                st.error(
                    "Email and password are required."
                )
                return

            client = get_api_client()

            try:
                client.login(
                    email,
                    password,
                )

                user = client.get_me()

                st.session_state.authenticated = True
                st.session_state.user = user

                st.rerun()

            except Exception as exc:
                st.error(
                    f"Login failed: {exc}"
                )


def show_dashboard() -> None:
    """Display the main dashboard."""

    client = get_api_client()
    user = st.session_state.user

    st.title("Vendor Contract Management")

    st.sidebar.success(
        f"Logged in as {user['email']}"
    )

    st.sidebar.write(
        f"Role: {user['role']}"
    )

    if st.sidebar.button(
        "Logout",
        use_container_width=True,
    ):
        st.session_state.clear()
        st.rerun()

    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Contracts",
            "Import / Export",
            "AI Analysis",
        ],
    )

    if page == "Dashboard":
        show_dashboard_home(client)

    elif page == "Contracts":
        show_contracts(client)

    elif page == "Import / Export":
        show_import_export(client)

    elif page == "AI Analysis":
        show_ai_analysis(client)


def show_dashboard_home(
    client: APIClient,
) -> None:
    """Display dashboard summary."""

    st.header("Dashboard")

    try:
        contracts = client.get_contracts()

    except Exception as exc:
        st.error(
            f"Unable to load contracts: {exc}"
        )
        return

    total_contracts = len(contracts)

    total_value = sum(
        float(contract["contract_value"])
        for contract in contracts
    )

    total_spend = sum(
        float(contract["spend"])
        for contract in contracts
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Contracts",
        total_contracts,
    )

    col2.metric(
        "Contract Value",
        f"${total_value:,.2f}",
    )

    col3.metric(
        "Current Spend",
        f"${total_spend:,.2f}",
    )

    if contracts:
        st.subheader("Contracts")

        st.dataframe(
            contracts,
            use_container_width=True,
        )
    else:
        st.info(
            "No contracts available."
        )


def show_contracts(
    client: APIClient,
) -> None:
    """Display contract management page."""

    st.header("Contracts")

    try:
        contracts = client.get_contracts()

    except Exception as exc:
        st.error(
            f"Unable to load contracts: {exc}"
        )
        return

    if not contracts:
        st.info(
            "No contracts found."
        )
        return

    for contract in contracts:

        with st.expander(
            f"{contract['id']} - "
            f"{contract['title']}"
        ):

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    f"**Vendor ID:** "
                    f"{contract['vendor_id']}"
                )

                st.write(
                    f"**Value:** "
                    f"${float(contract['contract_value']):,.2f}"
                )

                st.write(
                    f"**Spend:** "
                    f"${float(contract['spend']):,.2f}"
                )

            with col2:
                st.write(
                    f"**Status:** "
                    f"{contract['status']}"
                )

                st.write(
                    f"**Start:** "
                    f"{contract['start_date']}"
                )

                st.write(
                    f"**End:** "
                    f"{contract['end_date']}"
                )

            if st.button(
                "Delete",
                key=f"delete_{contract['id']}",
            ):
                try:
                    client.delete_contract(
                        contract["id"]
                    )

                    st.success(
                        "Contract deleted."
                    )

                    st.rerun()

                except Exception as exc:
                    st.error(
                        f"Delete failed: {exc}"
                    )


def show_import_export(
    client: APIClient,
) -> None:
    """Display import/export page."""

    st.header("Import / Export")

    st.subheader("Import Contracts")

    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"],
    )

    if uploaded_file is not None:

        if st.button(
            "Import Contracts",
            use_container_width=True,
        ):

            try:
                result = client.import_contracts(
                    uploaded_file.getvalue(),
                    uploaded_file.name,
                )

                job_id = result["job_id"]

                st.success(
                    f"Import started. "
                    f"Job ID: {job_id}"
                )

                st.session_state.import_job_id = job_id

            except Exception as exc:
                st.error(
                    f"Import failed: {exc}"
                )

    job_id = st.session_state.get(
        "import_job_id"
    )

    if job_id:

        st.subheader(
            f"Import Job #{job_id}"
        )

        try:
            job = client.get_job(job_id)

            st.progress(
                job["progress"] / 100
            )

            st.write(
                f"Status: **{job['status']}**"
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "Accepted",
                job["accepted_count"],
            )

            col2.metric(
                "Rejected",
                job["rejected_count"],
            )

            if job["status"] == "processing":
                time.sleep(1)
                st.rerun()

        except Exception as exc:
            st.error(
                f"Unable to get job status: {exc}"
            )

    st.divider()

    st.subheader("Export Contracts")

    export_format = st.selectbox(
        "Format",
        ["csv", "json"],
    )

    if st.button(
        "Export",
        use_container_width=True,
    ):

        try:
            response = client.export_contracts(
                export_format
            )

            extension = export_format

            st.download_button(
                "Download File",
                data=response.content,
                file_name=f"contracts.{extension}",
                mime=response.headers.get(
                    "content-type",
                    "application/octet-stream",
                ),
            )

        except Exception as exc:
            st.error(
                f"Export failed: {exc}"
            )


def show_ai_analysis(
    client: APIClient,
) -> None:
    """Display AI contract analysis."""

    st.header("AI Contract Analysis")

    try:
        contracts = client.get_contracts()

    except Exception as exc:
        st.error(
            f"Unable to load contracts: {exc}"
        )
        return

    if not contracts:
        st.info(
            "No contracts available."
        )
        return

    contract_options = {
        f"{contract['id']} - {contract['title']}":
        contract["id"]
        for contract in contracts
    }

    selected = st.selectbox(
        "Select Contract",
        list(contract_options.keys()),
    )

    contract_id = contract_options[selected]

    if st.button(
        "Analyze Contract",
        use_container_width=True,
    ):

        with st.spinner(
            "Analyzing contract..."
        ):

            try:
                analysis = client.analyze_contract(
                    contract_id
                )

                st.subheader("Summary")

                st.write(
                    analysis["summary"]
                )

                st.subheader("Risk Level")

                risk = analysis["risk_level"]

                if risk == "high":
                    st.error("HIGH")

                elif risk == "medium":
                    st.warning("MEDIUM")

                else:
                    st.success("LOW")

                st.subheader("Key Risks")

                for risk in analysis["key_risks"]:
                    st.write(
                        f"- {risk}"
                    )

                st.subheader(
                    "Recommendations"
                )

                for recommendation in analysis[
                    "recommendations"
                ]:
                    st.write(
                        f"- {recommendation}"
                    )

            except Exception as exc:
                st.error(
                    f"Analysis failed: {exc}"
                )


def main() -> None:
    """Run the Streamlit application."""

    st.set_page_config(
        page_title="Vendor Contract Management",
        page_icon="📄",
        layout="wide",
    )

    if not st.session_state.get(
        "authenticated",
        False,
    ):
        show_login()
        return

    show_dashboard()


if __name__ == "__main__":
    main()