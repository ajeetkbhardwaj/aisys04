from state import ClaimState

def refund_node(state: ClaimState):
    status = state["refund_status"]
    print(f"💰 [Refund Node] Finalizing Transaction. Status: {status}")
    # In a real app, this would call the Stripe API
    return {}