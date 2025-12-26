import os
import datetime
import json
import requests
import time

# NOUVELLE URL OBLIGATOIRE (Router)
API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/sdxl-turbo"
OUTPUT_DIR = "generated_images"

def query_huggingface_api(payload, token):
    headers = {"Authorization": f"Bearer {token}"}
    
    for i in range(3):
        try:
            print(f"🔄 Tentative {i+1}/3 via Router...")
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                return response
            elif response.status_code == 503:
                print("⏳ Le modèle se réveille, attente de 25s...")
                time.sleep(25)
            elif response.status_code == 429:
                print("⚠️ Limite de débit atteinte, pause de 10s...")
                time.sleep(10)
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
            "width": 512,
            "height": 768,
            "num_inference_steps": 4 # Très rapide pour éviter les coupures
        }
    }

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("❌ Erreur : HF_TOKEN manquant dans les secrets GitHub.")
        return

    print(f"🚀 Génération en cours sur SDXL Turbo...")
    response = query_huggingface_api(payload, token)

    if response and response.status_code == 200:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"insta_turbo_{timestamp}.png")
        
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ SUCCÈS : Image générée dans {filename}")
    else:
        print("❌ Échec : Impossible d'obtenir une image du Router.")

if __name__ == "__main__":
    my_prompt = "A high-quality photograph of a young woman on a luxury yacht, bright sunlight, blue sea."
    generate_image_sdxl(my_prompt)
