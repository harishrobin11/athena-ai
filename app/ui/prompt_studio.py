import streamlit as st
import time
from langchain_core.messages import SystemMessage, HumanMessage
from app.services.agent_framework.supervisor import azure_llm

def render_prompt_studio():
    with st.container(border=True):
        st.markdown("""
            <h3 style="margin-top: 0;">Visual Prompt Studio</h3>
            <p style="color: #94A3B8;">A/B test system prompts side-by-side using the Azure OpenAI engine.</p>
        """, unsafe_allow_html=True)
        
    st.markdown("### User Query")
    query = st.text_input("Enter the user query to test:", value="What is the company policy on remote work?")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Prompt A (Base)")
        prompt_a = st.text_area("System Prompt A", value="You are a helpful, factual corporate assistant.", height=150)
        
    with col2:
        st.markdown("#### Prompt B (Variant)")
        prompt_b = st.text_area("System Prompt B", value="You are a highly strictly structured bot. Reply ONLY with YES or NO if possible. Otherwise, summarize briefly.", height=150)
        
    if st.button("Execute A/B Test", type="primary", use_container_width=True):
        if not query.strip():
            st.error("Please enter a query.")
            return
            
        with st.spinner("Executing models..."):
            res_col1, res_col2 = st.columns(2)
            
            # Execute Prompt A
            start_a = time.time()
            try:
                response_a = azure_llm.invoke([SystemMessage(content=prompt_a), HumanMessage(content=query)])
                latency_a = time.time() - start_a
                with res_col1:
                    with st.container(border=True):
                        st.success(f"**Latency:** {latency_a:.2f}s | **Tokens:** {response_a.response_metadata.get('token_usage', {}).get('total_tokens', 'N/A')}")
                        st.markdown(response_a.content)
            except Exception as e:
                with res_col1:
                    st.error(f"Error executing Prompt A: {e}")
                    
            # Execute Prompt B
            start_b = time.time()
            try:
                response_b = azure_llm.invoke([SystemMessage(content=prompt_b), HumanMessage(content=query)])
                latency_b = time.time() - start_b
                with res_col2:
                    with st.container(border=True):
                        st.success(f"**Latency:** {latency_b:.2f}s | **Tokens:** {response_b.response_metadata.get('token_usage', {}).get('total_tokens', 'N/A')}")
                        st.markdown(response_b.content)
            except Exception as e:
                with res_col2:
                    st.error(f"Error executing Prompt B: {e}")
