import os
import datetime
import requests
import time

OUTPUT_DIR = "generated_images"

def generate_image_pollinations(prompt_text):
    print(f"🚀 Génération via Pollinations (Mode Robuste)...")
    
    # On utilise un prompt plus court pour accélérer le traitement initial
    clean_prompt = prompt_text.replace("\n", " ").strip()
    
    # URL simplifiée (modèle par défaut pour plus de rapidité)
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(clean_prompt)}?width=768&height=1344&nologo=true&seed={int(time.time())}"

    # Tentatives multiples (3 essais)
    for i in range(3):
        try:
            print(f"🔄 Tentative {i+1}/3 (Délai d'attente : 120s)...")
            # timeout=120 permet de laisser plus de temps au serveur pour répondre
            response = requests.get(url, timeout=120)
            
            if response.status_code == 200:
                if not os.path.exists(OUTPUT_DIR):
                    os.makedirs(OUTPUT_DIR)
                    
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(OUTPUT_DIR, f"insta_post_{timestamp}.png")
                
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"✅ SUCCÈS : Image générée dans {filename}")
                return # On sort de la fonction si ça a marché
            else:
                print(f"⚠️ Erreur serveur {response.status_code}, nouvelle tentative dans 10s...")
                time.sleep(10)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur réseau lors de la tentative {i+1} : {e}")
            if i < 2:
                print("⏳ Attente de 15s avant le prochain essai...")
                time.sleep(15)
            else:
                print("💀 Échec définitif après 3 tentatives.")

if __name__ == "__main__":
    # Prompt optimisé (plus direct pour éviter les erreurs d'encodage)
    my_prompt = "High-end fashion photography, young woman with dark hair, white tank top, red bikini, on luxury yacht deck, bright sunlight, cinematic lighting, 8k"
    
    generate_image_pollinations(my_prompt)
