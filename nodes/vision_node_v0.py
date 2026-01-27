from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from state import ClaimState
import base64
import os

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def vision_node(state: ClaimState):
    print(f"👁️  [Vision Node] Analyzing: {state['image_path']}")
    
    # SIMULATION MODE: If file doesn't exist, simulate GPT-4o based on text
    if not os.path.exists(state['image_path']):
        print("   (Simulating Vision Analysis based on text description...)")
        if "broken" in state['image_path'].lower():
            return {"is_valid_damage": True, "damage_description": "Screen is shattered."}
        else:
            return {"is_valid_damage": False, "damage_description": "Item looks pristine."}

    # REAL MODE: GPT-4o
    llm = ChatOpenAI(model="gpt-4o")
    base64_image = encode_image(state['image_path'])
    
    msg = HumanMessage(content=[
        {"type": "text", "text": "Is this item damaged? Answer strictly YES or NO, then describe it."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
    ])
    
    response = llm.invoke([msg])
    content = response.content
    
    is_damaged = "YES" in content.upper()
    return {
        "is_valid_damage": is_damaged,
        "damage_description": content
    }