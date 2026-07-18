import streamlit as st
from app.services.automation.engine import workflow_engine
import uuid

def render_workflow_builder():
    with st.container(border=True):
        st.markdown("""
            <h3 style="margin-top: 0;">Workflow Builder</h3>
            <p style="color: #94A3B8;">Design, save, and execute automated event-driven sequences.</p>
        """, unsafe_allow_html=True)
        
    st.markdown("### Create New Workflow")
    
    workflow_name = st.text_input("Workflow Name", value="My Automation")
    trigger = st.selectbox("Select Trigger", ["Manual (Run Now)", "On Document Upload", "Scheduled (Cron)", "Webhook API"])
    
    st.markdown("#### Action Sequence")
    
    if "workflow_actions" not in st.session_state:
        st.session_state["workflow_actions"] = []
        
    col1, col2 = st.columns([3, 1])
    with col1:
        new_action = st.selectbox("Available Actions", [
            "Run OCR Extraction",
            "Analyze Sentiment", 
            "Send Slack Message",
            "Create Jira Ticket",
            "Fetch Salesforce Data"
        ], key="new_action_select")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add Action", use_container_width=True):
            st.session_state["workflow_actions"].append(new_action)
            st.rerun()
            
    if st.session_state["workflow_actions"]:
        for i, act in enumerate(st.session_state["workflow_actions"]):
            st.info(f"**Step {i+1}:** {act}")
            
        if st.button("Clear Actions"):
            st.session_state["workflow_actions"] = []
            st.rerun()
            
        st.markdown("---")
        if st.button("Save & Deploy Workflow", type="primary"):
            wf_id = f"wf_{uuid.uuid4().hex[:8]}"
            workflow_engine.save_workflow(wf_id, trigger, st.session_state["workflow_actions"].copy())
            st.success(f"Workflow '{workflow_name}' deployed successfully!")
            st.session_state["workflow_actions"] = []
            
    st.markdown("---")
    st.markdown("### Saved Workflows")
    
    workflows = workflow_engine.get_workflows()
    if not workflows:
        st.write("No active workflows.")
    else:
        for wf_id, wf_data in workflows.items():
            with st.expander(f"{wf_id} ({wf_data['trigger']}) - {len(wf_data['actions'])} steps"):
                for i, act in enumerate(wf_data["actions"]):
                    st.write(f"{i+1}. {act}")
                    
                if st.button(f"Run Now ##{wf_id}", key=f"run_{wf_id}"):
                    with st.spinner("Executing sequence..."):
                        results = workflow_engine.run_workflow(wf_id, {"message": "Hello from Workflow Builder!", "title": "Automated Ticket"})
                        for r in results:
                            st.code(r)
