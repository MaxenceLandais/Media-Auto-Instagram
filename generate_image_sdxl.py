import os
import datetime
import json
import requests
import time

# NOUVELLE URL AVEC LE ROUTER HUGGING FACE
API_URL = "https://router.huggingface.co/hf-inference/models/SG161222/RealVisXL_V4.0"
OUTPUT_DIR = "generated_images"

def query_huggingface_api(payload, token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Appel vers le nouveau point de terminaison
    response = requests.post(API_URL, headers=headers, json=payload)
    
    # Gestion de l'attente si le modèle est en train de s'initialiser
    if response.status_code == 503:
        print("⏳ Modèle RealVisXL en cours de chargement sur Hugging Face... attente de 30s...")
        time.sleep(30)
        return query_huggingface_api(payload, token)
    elif response.status_code != 200:
        print(f"❌ Erreur API ({response.status_code}) : {response.text}")
        return None
        
    return response.content

def generate_image_sdxl(prompt_json_str):
    try:
        data = json.loads(prompt_json_str)
        base_prompt = data["generation_parameters"]["prompt"]
        
        # Amélioration du prompt pour la précision anatomique
        actual_prompt = f"(masterpiece, ultra-realistic photography, 8k, highly detailed anatomy, perfect legs, sharp focus), {base_prompt}"
        
        # Negative prompt renforcé contre les déformations
        negative_prompt = "extra legs, malformed limbs, fused fingers, bad anatomy, distorted body, extra limbs, poor proportions, blurry, grainy, watermark, bad hands"
    except Exception:
        actual_prompt = prompt_json_str
        negative_prompt = "deformed, low quality, bad anatomy"

    payload = {
        "inputs": actual_prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "width": 768,
            "height": 1344,
            "num_inference_steps": 50, # Qualité supérieure
            "guidance_scale": 7.0,
        }
    }

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("❌ Erreur : HF_TOKEN manquant dans les secrets GitHub.")
        return

    print(f"🚀 Génération avec RealVisXL V4.0 via le nouveau Router...")
    image_bytes = query_huggingface_api(payload, token)

    if image_bytes:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"insta_post_v4_{timestamp}.png")

        with open(filename, "wb") as f:
            f.write(image_bytes)
        print(f"✅ SUCCÈS : Image sauvegardée dans {filename}")

if __name__ == "__main__":
    my_prompt = """{
      "generation_parameters": {
        "prompt": "A candid photograph of a young woman with tousled dark hair, wearing a white tank top and red string bikini bottoms, leaning against the railing on the deck of a luxury yacht. She is looking over her shoulder towards a rocky island across the blue sea under a clear sky. The sunlight is bright and direct, casting defined shadows. The shot is medium-long and slightly low-angle.",
        "negative_prompt": "Blurry, grainy, artificial lighting, studio setting, text, watermark, painting, illustration, low resolution, overcast."
      }
    }"""
    
    generate_image_sdxl(my_prompt)
