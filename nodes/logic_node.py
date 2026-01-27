from state import ClaimState
"""
The Supervisor/Brain. 
It defines where to go next, but strictly speaking, 
in LangGraph, the Conditional Edge function usually handles the "Next" logic.
 This node prepares the final judgment state.
"""
def logic_node(state: ClaimState):
    """
    Acts as the Supervisor.
    """
    print("🧠 [Logic Node] Evaluating Policy rules...")
    
    if not state.get("is_valid_damage"):
        return {"refund_status": "Rejected"}
    
    value = state.get("order_value", 0)
    
    # Policy: refunds > $1000 require human review
    if value > 1000:
        print("   ⚠️ High Value Detected. Flagging for Human Review.")
        return {"refund_status": "Manual Review"}
    
    return {"refund_status": "Approved"}