import os
import datetime
import json
import requests
import time

# Utilisation de SDXL Turbo (Beaucoup plus rapide, évite les timeouts)
API_URL = "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo"
OUTPUT_DIR = "generated_images"

def query_huggingface_api(payload, token):
    headers = {"Authorization": f"Bearer {token}"}
    # On tente 3 fois en cas de non-réponse
    for i in range(3):
        try:
            print(f"🔄 Tentative {i+1}/3...")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                return response
            elif response.status_code == 503:
                print("⏳ Modèle en cours de réveil, attente de 20s...")
                time.sleep(20)
            else:
                print(f"⚠️ Erreur {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion : {e}")
            time.sleep(5)
    return None

def generate_image_sdxl(prompt_json_str):
    try:
        data = json.loads(prompt_json_str)
        actual_prompt = data["generation_parameters"]["prompt"]
    except Exception:
        actual_prompt = prompt_json_str

    payload = {
        "inputs": actual_prompt,
        "parameters": {
            "width": 512, # Turbo est optimisé pour 512x512 ou 768x768
            "height": 768, 
            "num_inference_steps": 4 # SDXL Turbo n'a besoin que de 4 étapes
        },
        "options": {"wait_for_model": True}
    }

    token = os.environ.get("HF_TOKEN")
    print(f"🚀 Génération avec SDXL Turbo...")
    response = query_huggingface_api(payload, token)

    if response and response.status_code == 200:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"insta_post_turbo_{timestamp}.png")
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ SUCCÈS : Image générée dans {filename}")
    else:
        print("❌ Échec définitif : Le serveur Hugging Face ne répond pas.")

if __name__ == "__main__":
    my_prompt = "A candid photograph of a young woman on a luxury yacht, high detail, sunny day."
    generate_image_sdxl(my_prompt)
