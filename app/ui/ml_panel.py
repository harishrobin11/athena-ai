import streamlit as st
import requests
from app.ui.utils import get_auth_headers

API_BASE_URL = ""
PREDICT_EXPENSE_API = f"{API_BASE_URL}/ml/predict-expense"

def render_ml_panel():
    st.markdown("## :material/model_training: Athena ML Classifier")
    st.caption("Interactive ML Quick Inference Utility")
    
    ws_param = {"workspace_id": st.session_state.get("active_workspace_id")} if st.session_state.get("active_workspace_id") else {}
    
    with st.container(border=True):
        raw_input = st.text_area(
            "Transaction Descriptions",
            placeholder="AWS EC2 Bill, Uber to airport, Staples paper",
            key="ml_main_input_area",
            help="Supply comma-separated transactions to evaluate baseline tokens instantly."
        )
        
        if st.button("Run Classifier Inference", use_container_width=True, key="ml_main_trigger_btn"):
            if raw_input.strip():
                descriptions = [item.strip() for item in raw_input.split(",") if item.strip()]
                try:
                    ml_response = requests.post(
                        PREDICT_EXPENSE_API,
                        json={"descriptions": descriptions, **ws_param},
                        headers=get_auth_headers(),
                        timeout=30,
                    )

                    if ml_response.status_code == 200:
                        predictions = ml_response.json().get("predictions", [])
                        st.success("Analysis Complete")
                        for desc, pred in zip(descriptions, predictions):
                            st.markdown(f"**{desc}**")
                            st.caption(f"↳ `{pred['category']}` ({pred['confidence']*100:.1f}%)")
                    elif ml_response.status_code == 503:
                        st.warning("Classifier model environment has not been seeded.")
                    else:
                        st.error(f"Inference error status configuration: {ml_response.status_code}")
                except Exception as ml_err:
                    st.error(f"Inference gateway connectivity failure: {ml_err}")
            else:
                st.warning("Please supply valid description tokens.")
