import os
import datetime
import json
import requests
import time

# URL directe (Plus stable pour RealVisXL)
API_URL = "https://api-inference.huggingface.co/models/SG161222/RealVisXL_V4.0"
OUTPUT_DIR = "generated_images"

def query_huggingface_api(payload, token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Appel API
    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code == 503:
        print("⏳ Modèle en cours de chargement... attente de 20s...")
        time.sleep(20)
        return query_huggingface_api(payload, token)
    elif response.status_code == 404:
        print("❌ Erreur 404 : Le modèle est introuvable sur ce point d'accès. Tentative sur le modèle SDXL de base pour ne pas bloquer...")
        # Fallback de secours si RealVisXL est indisponible
        fallback_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        response = requests.post(fallback_url, headers=headers, json=payload)
        
    return response

def generate_image_sdxl(prompt_json_str):
    try:
        data = json.loads(prompt_json_str)
        base_prompt = data["generation_parameters"]["prompt"]
        
        # On force les détails anatomiques
        actual_prompt = f"photorealistic, masterpiece, 8k, highly detailed, beautiful anatomy, perfect legs, realistic skin, yacht background, {base_prompt}"
        negative_prompt = "deformed, extra legs, mutated, bad proportions, blurry, low resolution, malformed limbs"
    except Exception:
        actual_prompt = prompt_json_str
        negative_prompt = "low quality"

    payload = {
        "inputs": actual_prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "width": 768,
            "height": 1344,
            "num_inference_steps": 50,
            "guidance_scale": 7.5
        },
        "options": {"wait_for_model": True} # Option HF pour attendre que le modèle soit prêt
    }

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("❌ Erreur : HF_TOKEN manquant.")
        return

    print(f"🚀 Génération en cours...")
    response = query_huggingface_api(payload, token)

    if response and response.status_code == 200:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"insta_post_final_{timestamp}.png")

        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ SUCCÈS : Image générée dans {filename}")
    else:
        print(f"❌ Échec final : {response.status_code if response else 'No Response'} - {response.text if response else ''}")

if __name__ == "__main__":
    my_prompt = """{
      "generation_parameters": {
        "prompt": "A candid photograph of a young woman with tousled dark hair, wearing a white tank top and red string bikini bottoms, leaning against the railing on the deck of a luxury yacht. She is looking over her shoulder towards a rocky island across the blue sea under a clear sky.",
        "negative_prompt": "Blurry, grainy, artificial lighting, text, watermark, low resolution."
      }
    }"""
    generate_image_sdxl(my_prompt)
