import os
import datetime
import requests
import time
import urllib.parse

OUTPUT_DIR = "generated_images"

def generate_clean_image(prompt_text):
    print(f"🚀 Génération d'une image lisse et nette...")
    
    # Prompt de nettoyage : on insiste sur une peau lisse et une image propre
    clean_directives = "ultra-sharp focus, smooth skin, clean textures, high gloss, professional lighting, 8k resolution, no grain, no noise, high-quality digital rendering, "
    full_prompt = clean_directives + prompt_text
    
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # Paramètres techniques :
    # model=pro (souvent plus stable et propre sur Pollinations)
    # enhance=true (aide à lisser les détails)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=1344&nologo=true&model=pro&enhance=true&seed={int(time.time())}"

    try:
        response = requests.get(url, timeout=120)
        if response.status_code == 200:
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)
                
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(OUTPUT_DIR, f"insta_clean_{timestamp}.png")
            
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"✅ SUCCÈS : Image nette sauvegardée dans {filename}")
        else:
            print(f"⚠️ Erreur serveur {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    # On évite 'candid' ou 'tousled' qui peuvent amener du désordre visuel
    my_prompt = "Portrait of a beautiful woman, dark hair, white tank top, red bikini, luxury yacht background, sunset, realistic skin, hyper-detailed, clean sharp lines"
    
    generate_clean_image(my_prompt)
