import os
import base64
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from state import ClaimState

# 1. Define the OpenRouter Model ID
#    This matches the HuggingFace ID exactly on OpenRouter
MODEL_ID = "meta-llama/llama-3.2-11b-vision-instruct"

def extract_frame_from_video(video_path):
    """
    Attempts to extract the first frame from a video file.
    Falls back to the original path if opencv is not installed.
    """
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Save frame as a temporary image
            image_path = video_path + "_frame.jpg"
            cv2.imwrite(image_path, frame)
            print(f"   🎬 Extracted frame from video: {image_path}")
            return image_path
    except ImportError:
        print("   ⚠️ OpenCV not found. Cannot extract video frame. Treating as file.")
    except Exception as e:
        print(f"   ⚠️ Error processing video: {e}")
    return video_path

def encode_image(image_path):
    """Helper to convert local image to Base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def vision_node(state: ClaimState):
    image_paths = state.get('image_paths', [])
    print(f"👁️  [Vision Node] Analyzing {len(image_paths)} items with Llama 3.2...")
    
    # Process all paths (handle videos)
    processed_paths = []
    for path in image_paths:
        if path.lower().endswith(('.mp4', '.mov', '.avi')):
            path = extract_frame_from_video(path)
        processed_paths.append(path)
    
    # Check if we have valid files or if this is a simulation
    # We assume if the first file doesn't exist, it's a text simulation
    is_simulation = len(processed_paths) > 0 and not os.path.exists(processed_paths[0])

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
    if is_simulation or not processed_paths:
        print("   (Simulating Vision Analysis based on text description...)")
        # ... keep your simulation logic here ...
        return {"is_valid_damage": True, "damage_description": "Simulated damage report."}

    # 4. Prepare the Payload (Standard OpenAI Format)
    content_payload = [
        {
            "type": "text", 
            "text": "Examine these images/videos of a package. Is the item damaged? Answer strictly YES or NO, then provide a short description of the damage if any."
        }
    ]

    # Append all images to the message
    for path in processed_paths:
        if os.path.exists(path):
            base64_image = encode_image(path)
            content_payload.append({
                "type": "image_url", 
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
    
    msg = HumanMessage(content=content_payload)
    
    # 5. Invoke
    response = llm.invoke([msg])
    content = response.content
    
    print(f"   🤖 Llama says: {content}")
    
    is_damaged = "YES" in content.upper()
    
    return {
        "is_valid_damage": is_damaged,
        "damage_description": content
    }