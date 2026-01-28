import streamlit as st
import os
import sys

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import graph

st.set_page_config(page_title="Logistics Claims AI", page_icon="📦", layout="wide")

st.title("📦 Logistics Damage Claim Agent")
st.markdown("Upload evidence of damage to initiate an automated refund claim.")

# --- Session State Setup ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "web_session_001"

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# --- Sidebar: Input ---
with st.sidebar:
    st.header("📝 New Claim")
    claim_id = st.text_input("Order ID", value="ORD-123", help="Try ORD-123 for High Value, ORD-456 for Low Value")
    uploaded_files = st.file_uploader("Upload Evidence", type=["jpg", "png", "jpeg", "mp4", "mov"], accept_multiple_files=True)
    
    if st.button("🚀 Submit Claim", type="primary"):
        if uploaded_files and claim_id:
            # Save the file locally so the Vision Node can read it
            os.makedirs("uploads", exist_ok=True)
            saved_paths = []
            
            for uploaded_file in uploaded_files:
                file_path = os.path.join("uploads", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_paths.append(file_path)
            
            st.toast(f"Uploaded {len(saved_paths)} files.", icon="💾")
            
            # Initialize Graph State
            initial_state = {
                "claim_id": claim_id,
                "image_paths": saved_paths,
                "messages": [],
                "refund_status": "Pending"
            }
            
            # Run the Graph
            with st.spinner("🤖 AI Agent is processing your claim..."):
                for event in graph.stream(initial_state, config=config):
                    pass # Just run to the next breakpoint or end
            st.rerun()
        else:
            st.error("Please provide an Order ID and at least one Image/Video.")

# --- Main Area: Status & Human Loop ---

# Get current state of the graph
snapshot = graph.get_state(config)

if snapshot.values:
    # Display Current State
    col1, col2, col3 = st.columns(3)
    col1.metric("Order Value", f"${snapshot.values.get('order_value', 0)}")
    col2.metric("Customer Tier", snapshot.values.get('customer_tier', 'Unknown'))
    col3.metric("Refund Status", snapshot.values.get('refund_status', 'Pending'))

    st.divider()

    # Check if we are paused for Human Review
    if snapshot.next and "human_review" in snapshot.next:
        st.warning("⚠️ **Action Required:** High Value Claim Detected.")
        st.write("The AI has flagged this claim for manual approval because the value exceeds $1000.")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Approve Refund"):
                graph.update_state(config, {"refund_status": "Manager Approved"})
                for event in graph.stream(None, config=config): pass
                st.rerun()
        with col_b:
            if st.button("❌ Reject Claim"):
                graph.update_state(config, {"refund_status": "Rejected"})
                for event in graph.stream(None, config=config): pass
                st.rerun()
    
    elif snapshot.values.get("refund_status") in ["Approved", "Manager Approved"]:
        st.success("🎉 Claim has been finalized and refund processed!")