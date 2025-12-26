import os
import datetime
import requests
import time
import urllib.parse

OUTPUT_DIR = "generated_images"

def generate_stable_image(prompt_text):
    print(f"🚀 Génération en mode Haute Stabilité...")
    
    # On garde un prompt très qualitatif
    full_prompt = f"professional 8k portrait, highly detailed, sharp focus, {prompt_text}"
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # URL simplifiée au maximum pour éviter la 404
    # On retire "model=flux" qui cause l'erreur 404 actuellement
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=1344&nologo=true&seed={int(time.time())}"

    for i in range(3):
        try:
            print(f"🔄 Tentative {i+1}/3...")
            response = requests.get(url, timeout=120)
            
            if response.status_code == 200:
                if not os.path.exists(OUTPUT_DIR):
                    os.makedirs(OUTPUT_DIR)
                    
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(OUTPUT_DIR, f"insta_final_{timestamp}.png")
                
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"✅ SUCCÈS : Image sauvegardée dans {filename}")
                return
            else:
                print(f"⚠️ Erreur {response.status_code}. Le serveur est peut-être saturé.")
                time.sleep(10)
        except Exception as e:
            print(f"❌ Erreur réseau : {e}")
            time.sleep(10)

if __name__ == "__main__":
    my_prompt = "young woman, dark hair, white tank top, red bikini, luxury yacht, sunset, cinematic"
    generate_stable_image(my_prompt)
