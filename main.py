import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langfuse.langchain import CallbackHandler
import sys

# --- PATH HANDLER ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import components
from state import ClaimState
from tools.db_tools import setup_db
from nodes.vision_node import vision_node
from nodes.crm_node import crm_node
from nodes.logic_node import logic_node
from nodes.human_node import human_review_node
from nodes.refund_node import refund_node

# Load Environment
load_dotenv()
#setup_db() # Init the SQLite DB

# --- 1. Define Routing Logic ---
def route_decision(state: ClaimState):
    status = state["refund_status"]
    if status == "Rejected":
        return "END"
    elif status == "Manual Review":
        return "human_review"
    else:
        return "refund"

# --- 2. Build the Graph ---
builder = StateGraph(ClaimState)

# Add Nodes
builder.add_node("vision", vision_node)
builder.add_node("crm", crm_node)
builder.add_node("logic", logic_node)
builder.add_node("human_review", human_review_node)
builder.add_node("refund", refund_node)

# Add Edges
builder.add_edge(START, "vision")
builder.add_edge("vision", "crm")
builder.add_edge("crm", "logic")

# Conditional Edge from Logic
builder.add_conditional_edges(
    "logic",
    route_decision,
    {
        "END": END,
        "human_review": "human_review",
        "refund": "refund"
    }
)

# After human review, we try to refund (assuming human approved)
builder.add_edge("human_review", "refund")
builder.add_edge("refund", END)

# --- 3. Persistence & Compilation ---
# MemorySaver is crucial for "pausing" the graph and resuming later
checkpointer = MemorySaver()

# We interrupt BEFORE the human_review node runs
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review"]
)

# --- 4. Execution Simulation ---

def run_simulation():
    # Setup Observability
    langfuse_handler = CallbackHandler()
    config_settings = {"callbacks": [langfuse_handler], "configurable": {"thread_id": "ticket_888"}}

    print("\n--- 🏁 STARTING AUTOMATED CLAIM PROCESS (High Value: $1500) ---")
    
    # Initial State: A broken item claim
    initial_state = {
        "claim_id": "ORD-123", # This ID exists in DB with $1500 value
        "image_path": "broken_laptop_description_text", # Simulating vision
        "messages": []
    }

    # Run the graph until it hits the interrupt or finishes
    # We use stream to see steps happening
    for event in graph.stream(initial_state, config=config_settings):
        for key, value in event.items():
            pass # Creating side effects (prints) in nodes

    # Check the current state of the graph
    snapshot = graph.get_state(config_settings)
    
    if snapshot.next:
        print("\n--- 🛑 GRAPH PAUSED (Human-in-the-Loop Triggered) ---")
        print(f"Current Node Pending: {snapshot.next}")
        print(f"Current Logic Status: {snapshot.values['refund_status']}")
        
        # Simulate a Manager reviewing the data externally
        user_input = input("\n[MANAGER UI] High value claim detected. Approve refund? (y/n): ")
        
        if user_input.lower() == 'y':
            print("\n--- ▶️ MANAGER APPROVED. RESUMING GRAPH... ---")
            
            # Update state to act as the approval
            # note: We keep the status as 'Manual Review' or change to 'Approved'. 
            # In this flow, the graph simply proceeds to 'refund' node after human_review.
            # But let's explicitly update the status to clean up the record.
            graph.update_state(config_settings, {"refund_status": "Manager Approved"})
            
            # Resume execution (None input means 'continue')
            for event in graph.stream(None, config=config_settings):
                for key, value in event.items():
                    pass
        else:
            print("\n❌ Manager Rejected. Workflow stops.")
    else:
        print("\n--- ✅ PROCESS COMPLETED AUTOMATICALLY ---")

if __name__ == "__main__":
    run_simulation()