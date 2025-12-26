import os
import datetime
import json
import requests
import time

# Utilisation du modèle SDXL de base (le plus fiable sur l'API gratuite)
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
OUTPUT_DIR = "generated_images"

def query_huggingface_api(payload, token):
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # On augmente le timeout à 120 secondes pour laisser le temps au modèle de charger
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion : {e}")
        return None

def generate_image_sdxl(prompt_json_str):
    try:
        data = json.loads(prompt_json_str)
        base_prompt = data["generation_parameters"]["prompt"]
        
        # On injecte les instructions de qualité directement dans le prompt
        actual_prompt = f"professional fashion photography, highly detailed, sharp focus, 8k, perfect anatomy, {base_prompt}"
        negative_prompt = "deformed, distorted, extra limbs, bad anatomy, low quality, blurry"
    except Exception:
        actual_prompt = prompt_json_str
        negative_prompt = "low quality"

    payload = {
        "inputs": actual_prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "width": 768,
            "height": 1344,
            "num_inference_steps": 40,
            "guidance_scale": 7.5
        },
        "options": {
            "wait_for_model": True, # Indispensable pour éviter le 'No Response'
            "use_cache": False
        }
    }

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("❌ Token HF_TOKEN manquant.")
        return

    print(f"🚀 Génération en cours sur SDXL (Attente du serveur)...")
    response = query_huggingface_api(payload, token)

    if response and response.status_code == 200:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"insta_post_v5_{timestamp}.png")

        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ SUCCÈS : Image générée dans {filename}")
    elif response:
        print(f"❌ Échec ({response.status_code}) : {response.text}")
    else:
        print("❌ Échec : Pas de réponse du serveur.")

if __name__ == "__main__":
    my_prompt = """{
      "generation_parameters": {
        "prompt": "A candid photograph of a young woman with tousled dark hair, wearing a white tank top and red string bikini bottoms, leaning against the railing on the deck of a luxury yacht. Sunlight casting defined shadows.",
        "negative_prompt": "blurry, grainy, low resolution"
      }
    }"""
    generate_image_sdxl(my_prompt)
