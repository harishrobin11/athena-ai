import streamlit as st
import requests
import pandas as pd

def render_org_settings_panel():
    st.markdown("# :material/settings: Organization Management")
    st.caption("Sprint 26: Tenant Administration & RBAC")

    if "token" not in st.session_state or "user_profile" not in st.session_state:
        st.error("Unauthorized access.", icon=":material/lock:")
        return

    token = st.session_state["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # We need to know which organization to manage
    # Fetch user orgs if not already fetched
    orgs_url = "http://127.0.0.1:8000/orgs"
    try:
        res = requests.get(orgs_url, headers=headers)
        if res.status_code == 200:
            orgs = res.json()
            if not orgs:
                st.warning("You are not part of any organization.")
                return
            
            # Filter to organizations where the user is an admin
            admin_orgs = [o for o in orgs if o.get("role") == "admin"]
            
            if not admin_orgs:
                st.warning("You must be an Organization Admin to view this page.", icon=":material/security:")
                return
                
            org_options = {o["name"]: o["id"] for o in admin_orgs}
            selected_org_name = st.selectbox("Select Organization to Manage:", options=list(org_options.keys()))
            selected_org_id = org_options[selected_org_name]
            
            # Tabs for management
            tab_members, tab_invite = st.tabs([":material/group: Members", ":material/person_add: Invite User"])
            
            with tab_members:
                st.subheader(f"Members of {selected_org_name}")
                members_url = f"http://127.0.0.1:8000/orgs/{selected_org_id}/members"
                m_res = requests.get(members_url, headers=headers)
                
                if m_res.status_code == 200:
                    members = m_res.json().get("members", [])
                    if members:
                        df = pd.DataFrame(members)
                        st.dataframe(df, use_container_width=True)
                        
                        st.markdown("### Update Member")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            target_user_id = st.selectbox("Select User ID", options=[m["user_id"] for m in members])
                        with col2:
                            new_role = st.selectbox("New Role", options=["member", "admin", "analyst"])
                        with col3:
                            new_dept = st.selectbox("New Department", options=["GENERAL", "FINANCE", "PROCUREMENT", "HR"])
                            
                        if st.button("Update Role/Department", type="primary"):
                            update_url = f"http://127.0.0.1:8000/orgs/{selected_org_id}/members/{target_user_id}"
                            u_res = requests.put(update_url, json={"role": new_role, "department": new_dept}, headers=headers)
                            if u_res.status_code == 200:
                                st.success("Member updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to update: {u_res.text}")
                                
                        if st.button("Remove Member", type="primary"):
                            remove_url = f"http://127.0.0.1:8000/orgs/{selected_org_id}/members/{target_user_id}"
                            r_res = requests.delete(remove_url, headers=headers)
                            if r_res.status_code == 200:
                                st.success("Member removed.")
                                st.rerun()
                            else:
                                st.error(f"Failed to remove: {r_res.text}")
                    else:
                        st.info("No members found.")
                else:
                    st.error(f"Failed to fetch members: {m_res.text}")
            
            with tab_invite:
                st.subheader("Invite Existing User")
                invite_email = st.text_input("User Email")
                invite_role = st.selectbox("Role", options=["member", "admin", "analyst"])
                invite_dept = st.selectbox("Department", options=["GENERAL", "FINANCE", "PROCUREMENT", "HR"])
                
                if st.button("Send Invitation", type="primary"):
                    invite_url = f"http://127.0.0.1:8000/orgs/{selected_org_id}/invites"
                    i_res = requests.post(invite_url, json={"email": invite_email, "role": invite_role, "department": invite_dept}, headers=headers)
                    
                    if i_res.status_code == 200:
                        st.success(f"Successfully added {invite_email} to {selected_org_name}!")
                    else:
                        st.error(f"Failed to invite: {i_res.text}")
        else:
            st.error("Failed to load organizations.")
    except Exception as e:
        st.error(f"Connection error: {e}")
