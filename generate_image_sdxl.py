import os
import datetime
import json
import requests
import time

# NOUVELLE URL DE L'API HUGGING FACE
API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
OUTPUT_DIR = "generated_images"

def query_huggingface_api(payload, token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Tentative d'appel avec gestion d'attente si le modèle charge
    response = requests.post(API_URL, headers=headers, json=payload)
    
    # Si le modèle est en train de charger, on attend un peu
    if response.status_code == 503:
        print("⏳ Le modèle charge sur les serveurs Hugging Face, attente de 20s...")
        time.sleep(20)
        return query_huggingface_api(payload, token)
        
    return response.content

def generate_image_sdxl(prompt_json_str):
    try:
        data = json.loads(prompt_json_str)
        actual_prompt = data["generation_parameters"]["prompt"]
        negative_prompt = data["generation_parameters"]["negative_prompt"]
    except Exception:
        actual_prompt = prompt_json_str
        negative_prompt = "low quality, blurry, distorted"

    # Configuration pour SDXL (le format 9:16 est géré par width/height)
    payload = {
        "inputs": actual_prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "width": 768,   
            "height": 1344, 
            "target_size": {"width": 768, "height": 1344},
            "num_inference_steps": 30,
            "guidance_scale": 7.5
        }
    }

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("❌ ERREUR : Le token HF_TOKEN n'est pas configuré dans GitHub Secrets.")
        return

    print(f"🚀 Envoi à la nouvelle API Router...")
    image_bytes = query_huggingface_api(payload, token)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"insta_post_{timestamp}.png")

    with open(filename, "wb") as f:
        f.write(image_bytes)
    
    print(f"✅ SUCCÈS : Image générée dans {filename}")

if __name__ == "__main__":
    # On garde votre prompt JSON d'origine
    my_prompt = """{
      "generation_parameters": {
        "prompt": "A candid photograph of a young woman with tousled dark hair, wearing a white tank top and red string bikini bottoms, leaning against the railing on the deck of a luxury yacht. She is looking over her shoulder towards a rocky island across the blue sea under a clear sky. The sunlight is bright and direct, casting defined shadows. The shot is medium-long and slightly low-angle.",
        "negative_prompt": "Blurry, grainy, artificial lighting, studio setting, text, watermark, painting, illustration, low resolution, overcast."
      }
    }"""
    
    generate_image_sdxl(my_prompt)
