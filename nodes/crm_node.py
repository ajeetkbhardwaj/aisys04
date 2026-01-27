from state import ClaimState
from tools.db_tools import get_order_details

def crm_node(state: ClaimState):
    print(f"🗄️  [CRM Node] Looking up Order ID: {state['claim_id']}")
    order_data = get_order_details(state['claim_id'])
    
    if order_data:
        print(f"   Found: Value=${order_data['amount']}, Tier={order_data['tier']}")
        return {
            "order_value": order_data['amount'],
            "customer_tier": order_data['tier']
        }
    else:
        print("   ❌ Order not found!")
        return {
            "order_value": 0,
            "customer_tier": "Unknown"
        }