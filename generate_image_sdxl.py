import os
import datetime
import requests
import time
import urllib.parse

OUTPUT_DIR = "generated_images"

def generate_high_quality_image(prompt_text):
    print(f"🚀 Génération Haute Qualité (Modèle Flux)...")
    
    # On ajoute des directives techniques pour la qualité 8K et l'anatomie
    quality_header = "(photorealistic:1.3), (highly detailed skin texture:1.2), masterpiece, 8k uhd, sharp focus, perfect anatomy, "
    full_prompt = quality_header + prompt_text
    
    # Encodage du prompt
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # URL avec les paramètres : 
    # model=flux (Précision maximale)
    # enhance=true (Augmente le nombre de calculs pour les détails)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=1344&nologo=true&model=flux&enhance=true&seed={int(time.time())}"

    for i in range(3):
        try:
            print(f"🔄 Tentative {i+1}/3 - Calcul des détails en cours...")
            response = requests.get(url, timeout=120)
            
            if response.status_code == 200:
                if not os.path.exists(OUTPUT_DIR):
                    os.makedirs(OUTPUT_DIR)
                    
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(OUTPUT_DIR, f"insta_premium_{timestamp}.png")
                
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"✅ SUCCÈS : Image Haute Qualité sauvegardée dans {filename}")
                return
            else:
                print(f"⚠️ Erreur {response.status_code}, nouvelle tentative...")
                time.sleep(10)
        except Exception as e:
            print(f"❌ Erreur : {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Prompt ultra-détaillé pour éviter les membres déformés
    my_prompt = """
    Young woman with dark hair, white tank top, red bikini, 
    standing on a luxury yacht deck, leaning on railing, 
    full body shot, cinematic lighting, sunset glow, 
    detailed hands, straight legs, 35mm lens, f/1.8
    """
    
    generate_high_quality_image(my_prompt)
