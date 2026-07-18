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
            
            # Filter to organizations where the user is an owner or admin
            admin_orgs = [o for o in orgs if o.get("role") in ["owner", "admin"]]
            
            if not admin_orgs:
                st.warning("You must be an Organization Admin to view this page.", icon=":material/security:")
                return
                
            org_options = {o["name"]: o["id"] for o in admin_orgs}
            selected_org_name = st.selectbox("Select Organization to Manage:", options=list(org_options.keys()))
            selected_org_id = org_options[selected_org_name]
            
            # Tabs for management
            tab_members, tab_invite, tab_billing = st.tabs([":material/group: Members", ":material/person_add: Invite User", ":material/credit_card: Billing"])
            
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
                        
            with tab_billing:
                st.subheader("Billing & Subscriptions")
                st.caption("Manage your organization's subscription plan and payment methods.")
                
                sub_url = f"http://127.0.0.1:8000/billing/{selected_org_id}/subscription"
                s_res = requests.get(sub_url, headers=headers)
                
                if s_res.status_code == 200:
                    sub_data = s_res.json().get("data", {})
                    current_plan = sub_data.get("billing_plan", "free").upper()
                    st.info(f"**Current Plan**: {current_plan} | **Status**: {sub_data.get('status', 'active').capitalize()}")
                    
                    usage_url = f"http://127.0.0.1:8000/billing/{selected_org_id}/usage"
                    u_res = requests.get(usage_url, headers=headers)
                    if u_res.status_code == 200:
                        usage_data = u_res.json().get("data", {})
                        st.markdown("### Current Usage")
                        col_w, col_d, col_t = st.columns(3)
                        
                        def format_limit(limit):
                            return str(limit) if limit != -1 else "Unlimited"
                            
                        with col_w:
                            current_w = usage_data['workspaces']['current']
                            limit_w = usage_data['workspaces']['limit']
                            st.metric("Workspaces", f"{current_w} / {format_limit(limit_w)}")
                            if limit_w != -1:
                                st.progress(min(1.0, current_w / max(1, limit_w)))
                                
                        with col_d:
                            current_d = usage_data['documents']['current']
                            limit_d = usage_data['documents']['limit']
                            st.metric("Documents", f"{current_d} / {format_limit(limit_d)}")
                            if limit_d != -1:
                                st.progress(min(1.0, current_d / max(1, limit_d)))
                                
                        with col_t:
                            current_t = usage_data['tokens']['current']
                            limit_t = usage_data['tokens']['limit']
                            st.metric("Tokens (Month)", f"{current_t} / {format_limit(limit_t)}")
                            if limit_t != -1:
                                st.progress(min(1.0, current_t / max(1, limit_t)))
                    st.divider()
                    
                    plans_url = "http://127.0.0.1:8000/billing/plans"
                    p_res = requests.get(plans_url, headers=headers)
                    if p_res.status_code == 200:
                        plans = p_res.json().get("data", [])
                        st.markdown("### Available Plans")
                        cols = st.columns(len(plans))
                        for i, plan in enumerate(plans):
                            with cols[i]:
                                with st.container(border=True):
                                    st.markdown(f"#### {plan['name'].upper()}")
                                    st.markdown(f"**${plan['price']}/mo**")
                                    for feature in plan['features']:
                                        st.markdown(f"- {feature}")
                                        
                                    is_current = plan['name'].lower() == current_plan.lower()
                                    if is_current:
                                        st.button("Current Plan", disabled=True, key=f"btn_{plan['name']}", use_container_width=True)
                                    else:
                                        if st.button("Upgrade", key=f"btn_{plan['name']}", use_container_width=True, type="primary"):
                                            checkout_url = f"http://127.0.0.1:8000/billing/{selected_org_id}/checkout"
                                            c_res = requests.post(checkout_url, json={"plan": plan['name']}, headers=headers)
                                            if c_res.status_code == 200:
                                                st.success(c_res.json().get("message"))
                                                # Simulate redirect
                                                st.markdown(f"[Proceed to Checkout]({c_res.json().get('checkout_url')})")
                                                st.rerun()
                                            else:
                                                st.error(f"Failed to create checkout session: {c_res.text}")
                    else:
                        st.error("Failed to load plans.")
                else:
                    st.error(f"Failed to load subscription data: {s_res.text}")
        else:
            st.error("Failed to load organizations.")
    except Exception as e:
        st.error(f"Connection error: {e}")
