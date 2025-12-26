import os
import datetime
import json
import requests

# Configuration
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
OUTPUT_DIR = "generated_images"

def query_huggingface_api(payload, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content

def generate_image_sdxl(prompt_json_str):
    # 1. Extraction du prompt depuis votre JSON complexe
    try:
        data = json.loads(prompt_json_str)
        actual_prompt = data["generation_parameters"]["prompt"]
        negative_prompt = data["generation_parameters"]["negative_prompt"]
        print(f"📝 Prompt extrait : {actual_prompt[:50]}...")
    except Exception as e:
        print(f"⚠️ Erreur lecture JSON : {e}. Utilisation brute.")
        actual_prompt = prompt_json_str
        negative_prompt = "Blurry, low quality"

    # 2. Préparation de la requête API
    payload = {
        "inputs": actual_prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "width": 768,   # Format portrait
            "height": 1344, # Format portrait (compatible SDXL)
            "num_inference_steps": 35,
            "guidance_scale": 7.5
        }
    }

    # 3. Appel API (Nécessite le token HF_TOKEN dans les secrets GitHub)
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise ValueError("❌ La variable d'environnement HF_TOKEN est manquante !")

    print("🚀 Envoi de la demande à l'API SDXL...")
    image_bytes = query_huggingface_api(payload, token)

    # 4. Sauvegarde
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"insta_sdxl_{timestamp}.png")

    with open(filename, "wb") as f:
        f.write(image_bytes)
    
    print(f"✅ SUCCÈS : Image sauvegardée sous {filename}")

if __name__ == "__main__":
    # Votre Prompt JSON (identique à avant)
    my_prompt = """{
      "generation_parameters": {
        "prompt": "A candid photograph of a young woman with tousled dark hair, wearing a white tank top and red string bikini bottoms, leaning against the railing on the deck of a luxury yacht. She is looking over her shoulder towards a rocky island across the blue sea under a clear sky. The sunlight is bright and direct, casting defined shadows. The shot is medium-long and slightly low-angle.",
        "negative_prompt": "Blurry, grainy, artificial lighting, studio setting, text, watermark, painting, illustration, low resolution, overcast."
      }
    }"""
    
    generate_image_sdxl(my_prompt)
