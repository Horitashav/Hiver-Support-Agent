"""
Interactive Support Agent Dashboard.
Streamlit application demonstrating real-time Intent Classification,
RAG-grounded Response Generation, and Escalation Guardrails.
"""

import streamlit as st
from src.agent import SupportAgent

st.set_page_config(
    page_title="AppleSupport AI Agent",
    page_icon="🍏",
    layout="wide"
)

# Cache the agent instance so embeddings & models load only once
@st.cache_resource
def load_support_agent():
    return SupportAgent()

agent = load_support_agent()

# Header & Introduction
st.title("🍏 AppleSupport Autonomous AI Agent")
st.markdown(
    "Production-grade support pipeline featuring **3-Tier Intent Classification**, "
    "**FAISS Semantic Retrieval (RAG)**, and **Hybrid Escalation Routing**."
)

st.divider()

# Sidebar: Preset Scenarios & System Stats
with st.sidebar:
    st.header("🎯 Test Presets")
    preset_choice = st.selectbox(
        "Choose a test scenario to auto-fill:",
        [
            "Custom Input",
            "Routine How-To: Apple Pay setup",
            "Technical Issue: Frozen black screen",
            "Account Access: Locked Apple ID",
            "Urgent Hazard: Battery expanding & smoking",
            "High Risk: Threat of legal action",
            "Edge Case: Sarcasm / Frustration"
        ]
    )
    
    preset_map = {
        "Routine How-To: Apple Pay setup": "How do I set up Apple Pay on my new Apple Watch?",
        "Technical Issue: Frozen black screen": "My iPhone screen is totally black and won't respond to touch or charging.",
        "Account Access: Locked Apple ID": "I forgot my Apple ID password and my recovery phone number is disconnected.",
        "Urgent Hazard: Battery expanding & smoking": "My iPhone battery is swelling and started emitting smoke, this is a dangerous fire hazard!",
        "High Risk: Threat of legal action": "If my account isn't unbanned today I will have my attorney file a formal lawsuit.",
        "Edge Case: Sarcasm / Frustration": "Oh fantastic, another iOS update that completely bricked my phone. Truly stellar work /s"
    }
    
    default_text = preset_map.get(preset_choice, "")
    
    st.divider()
    st.markdown("### ⚙️ System Architecture")
    st.markdown("- **Model:** Groq (`openai/gpt-oss-20b`)")
    st.markdown("- **Embeddings:** `all-MiniLM-L6-v2` (384-dim)")
    st.markdown("- **Vector Store:** FAISS Flat Inner Product (5,063 vectors)")
    st.markdown("- **Escalation:** Word-boundary Regex + LLM Guardrails")

# Input Section
col1, col2 = st.columns([4, 1])
with col1:
    user_query = st.text_input(
        "Enter customer tweet / message:",
        value=default_text,
        placeholder="Type a customer message..."
    )
with col2:
    st.write("")
    st.write("")
    run_button = st.button("Run Pipeline", type="primary", use_container_width=True)

# Processing & Results
if run_button and user_query.strip():
    with st.spinner("Processing through Intent Classifier, FAISS, and Escalation Decider..."):
        output = agent.process(user_query)

    intent_res = output['intent']
    reply_res = output['reply']
    esc_res = output['escalation']

    st.subheader("🔍 Execution Telemetry")
    
    # Telemetry Badges
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        st.metric(
            label="Classified Intent",
            value=intent_res.get('intent', 'other'),
            delta=f"Conf: {intent_res.get('confidence', 0.0):.2f}"
        )
        st.caption(f"Reason: {intent_res.get('reasoning', 'N/A')}")
        
    with metric_col2:
        if output['auto_handled']:
            st.success("✅ **Status: AUTO-HANDLED**")
        else:
            st.error("🚨 **Status: ESCALATED TO HUMAN**")
        st.caption(f"Decision Basis: {esc_res.get('reason', 'N/A')}")

    with metric_col3:
        retrieval_conf = reply_res.get('confidence', 0.0)
        st.metric(
            label="Top Vector Similarity",
            value=f"{retrieval_conf:.3f}",
            delta="Cosine Sim" if retrieval_conf > 0.6 else "Low Relevance"
        )
        st.caption("Similarity against 5,063 reference cases")

    st.divider()

    # Response Section
    st.subheader("💬 Agent Decision & Response")
    if output['auto_handled']:
        st.success(f"**Delivered Customer Reply:**\n\n{reply_res['reply']}")
    else:
        st.warning(f"**Automated Reply Suppressed:**\n\n{reply_res['reply']}")
        with st.expander("Inspect Internal Generated Draft (Held for Human Review)"):
            st.info(reply_res['generated_draft'])

    # RAG Context Drawer
    with st.expander("📚 Retrieved Historical Evidence (FAISS Matches)"):
        examples = reply_res.get('retrieved_examples', [])
        if examples:
            for i, ex in enumerate(examples, 1):
                st.markdown(f"**Reference #{i}** (Similarity: `{ex.get('similarity', 0.0):.3f}`)")
                st.markdown(f"- *Past Customer:* \"{ex.get('customer', '')}\"")
                st.markdown(f"- *Official Agent:* \"{ex.get('brand', '')}\"")
                st.write("---")
        else:
            st.write("No historical references retrieved.")