import os
import base64
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from state import ClaimState

# 1. Define the OpenRouter Model ID
#    This matches the HuggingFace ID exactly on OpenRouter
MODEL_ID = "meta-llama/llama-3.2-11b-vision-instruct"

def encode_image(image_path):
    """Helper to convert local image to Base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def vision_node(state: ClaimState):
    print(f"👁️  [Vision Node] Analyzing with Llama 3.2: {state['image_path']}")
    
    # 2. Initialize ChatOpenAI pointing to OpenRouter
    llm = ChatOpenAI(
        model=MODEL_ID,
        openai_api_key=os.environ["OPENROUTER_API_KEY"],
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.1,
        # Optional: Add headers if OpenRouter requires them for tracking
        default_headers={
            "HTTP-Referer": "https://localhost:3000", # Required by OpenRouter for some tiers
            "X-Title": "Logistics Agent"
        }
    )

    # 3. Handle Local vs Simulated Images
    if not os.path.exists(state['image_path']):
        print("   (Simulating Vision Analysis based on text description...)")
        # ... keep your simulation logic here ...
        return {"is_valid_damage": True, "damage_description": "Simulated damage report."}

    # 4. Prepare the Payload (Standard OpenAI Format)
    #    Llama 3.2 on OpenRouter accepts the same "image_url" structure
    base64_image = encode_image(state['image_path'])
    
    msg = HumanMessage(content=[
        {
            "type": "text", 
            "text": "Examine this image of a package. Is the item damaged? Answer strictly YES or NO, then provide a short description of the damage if any."
        },
        {
            "type": "image_url", 
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        }
    ])
    
    # 5. Invoke
    response = llm.invoke([msg])
    content = response.content
    
    print(f"   🤖 Llama says: {content}")
    
    is_damaged = "YES" in content.upper()
    
    return {
        "is_valid_damage": is_damaged,
        "damage_description": content
    }