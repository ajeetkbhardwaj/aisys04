import operator
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
"""
state.py : defines the shared memory for all our agents will read and write to.
"""
class ClaimState(TypedDict):
    # Inputs
    claim_id: str
    image_path: str  # Path to image or text description for simulation
    
    # Vision Node Outputs
    is_valid_damage: Optional[bool]
    damage_description: Optional[str]
    
    # CRM Node Outputs
    order_value: Optional[float]
    customer_tier: Optional[str]
    
    # Logic/Human Outputs
    refund_status: str # "Pending", "Approved", "Rejected", "Manual Review"
    
    # Conversation History
    messages: Annotated[List[AnyMessage], add_messages]