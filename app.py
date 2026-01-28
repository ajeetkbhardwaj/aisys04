import gradio as gr
import os
import sys
import shutil
import uuid

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import graph

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

def get_status_output(config, thread_id):
    """Helper to format the output based on graph state."""
    snapshot = graph.get_state(config)
    
    if not snapshot.values:
        return (
            "No active claim.", 
            "", 
            thread_id, 
            gr.update(visible=False), 
            gr.update(visible=False)
        )
    
    order_value = snapshot.values.get('order_value', 0)
    customer_tier = snapshot.values.get('customer_tier', 'Unknown')
    refund_status = snapshot.values.get('refund_status', 'Pending')
    
    status_md = f"""
    ### Claim Status
    * **Order Value:** ${order_value}
    * **Customer Tier:** {customer_tier}
    * **Refund Status:** {refund_status}
    """
    
    # Check for human review
    show_buttons = False
    msg = ""
    
    # Check if we are paused for Human Review
    if snapshot.next and "human_review" in snapshot.next:
        show_buttons = True
        msg = "⚠️ **Action Required:** High Value Claim Detected (> ). Please Approve or Reject."
    elif refund_status in ["Approved", "Manager Approved"]:
        msg = "🎉 Claim has been finalized and refund processed!"
    elif refund_status == "Rejected":
        msg = "❌ Claim rejected."

    return (
        status_md, 
        msg, 
        thread_id, 
        gr.update(visible=show_buttons), 
        gr.update(visible=show_buttons)
    )

def process_claim(order_id, files, thread_id):
    if not order_id or not files:
        return "Please provide an Order ID and at least one Image/Video.", "", thread_id, gr.update(visible=False), gr.update(visible=False)

    # Generate new thread ID for new claims to ensure clean state
    thread_id = str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": thread_id}}
    
    saved_paths = []
    for file_path in files:
        filename = os.path.basename(file_path)
        dest_path = os.path.join("uploads", filename)
        # Copy from temp location to our uploads folder
        shutil.copy(file_path, dest_path)
        saved_paths.append(dest_path)
    
    initial_state = {
        "claim_id": order_id,
        "image_paths": saved_paths,
        "messages": [],
        "refund_status": "Pending"
    }
    
    # Run the Graph
    try:
        for event in graph.stream(initial_state, config=config):
            pass 
    except Exception as e:
        return f"Error processing claim: {e}", "", thread_id, gr.update(visible=False), gr.update(visible=False)

    return get_status_output(config, thread_id)

def approve_claim(thread_id):
    if not thread_id:
        return "Error: No active session.", "", None, gr.update(visible=False), gr.update(visible=False)
        
    config = {"configurable": {"thread_id": thread_id}}
    graph.update_state(config, {"refund_status": "Manager Approved"})
    
    for event in graph.stream(None, config=config): 
        pass
        
    return get_status_output(config, thread_id)

def reject_claim(thread_id):
    if not thread_id:
        return "Error: No active session.", "", None, gr.update(visible=False), gr.update(visible=False)

    config = {"configurable": {"thread_id": thread_id}}
    graph.update_state(config, {"refund_status": "Rejected"})
    
    for event in graph.stream(None, config=config): 
        pass
        
    return get_status_output(config, thread_id)

# --- Gradio UI Layout ---
with gr.Blocks(title="Logistics Damage Claim Agent") as demo:
    # State to hold the thread_id
    thread_state = gr.State()
    
    gr.Markdown("# 📦 Logistics Damage Claim Agent")
    gr.Markdown("Upload evidence of damage to initiate an automated refund claim.")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📝 New Claim")
            order_input = gr.Textbox(label="Order ID", value="ORD-123", placeholder="e.g., ORD-123")
            # type="filepath" ensures we get the path to the temp file
            file_input = gr.File(label="Upload Evidence", file_count="multiple", type="filepath")
            submit_btn = gr.Button("🚀 Submit Claim", variant="primary")
        
        with gr.Column(scale=1):
            gr.Markdown("### Status")
            status_output = gr.Markdown("No active claim.")
            message_output = gr.Markdown("")
            
            with gr.Row():
                approve_btn = gr.Button("✅ Approve Refund", visible=False, variant="primary")
                reject_btn = gr.Button("❌ Reject Claim", visible=False, variant="stop")

    # Event Listeners
    submit_btn.click(
        fn=process_claim,
        inputs=[order_input, file_input, thread_state],
        outputs=[status_output, message_output, thread_state, approve_btn, reject_btn]
    )
    
    approve_btn.click(
        fn=approve_claim,
        inputs=[thread_state],
        outputs=[status_output, message_output, thread_state, approve_btn, reject_btn]
    )
    
    reject_btn.click(
        fn=reject_claim,
        inputs=[thread_state],
        outputs=[status_output, message_output, thread_state, approve_btn, reject_btn]
    )

if __name__ == "__main__":
    demo.launch()