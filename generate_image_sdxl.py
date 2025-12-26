import os
import datetime
import requests
import urllib.parse

OUTPUT_DIR = "generated_images"

def generate_image_pollinations(prompt_text):
    print(f"🚀 Génération via Pollinations (SDXL)...")
    
    # Nettoyage et encodage du prompt pour l'URL
    encoded_prompt = urllib.parse.quote(prompt_text)
    
    # Paramètres : Largeur 768, Hauteur 1344 (Format 9:16), Modèle flux (très réaliste)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=1344&nologo=true&model=flux"

    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)
                
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(OUTPUT_DIR, f"insta_pollination_{timestamp}.png")
            
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"✅ SUCCÈS : Image générée dans {filename}")
        else:
            print(f"❌ Échec : Code erreur {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur réseau : {e}")

if __name__ == "__main__":
    # Ton prompt de mode luxe
    my_prompt = "A candid high-end fashion photograph of a young woman with tousled dark hair, wearing a white tank top and red bikini, leaning against the railing on the deck of a luxury yacht, bright sunlight, cinematic lighting, 8k resolution"
    
    generate_image_pollinations(my_prompt)
