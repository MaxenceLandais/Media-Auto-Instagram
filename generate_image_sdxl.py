import os
import datetime
import requests
import time
import urllib.parse
from PIL import Image, ImageFilter

OUTPUT_DIR = "generated_images"

def apply_anti_grain(filename):
    """Applique un filtre de lissage léger pour supprimer le grain IA"""
    try:
        with Image.open(filename) as img:
            # Filtre de lissage pour enlever le bruit numérique
            img_smooth = img.filter(ImageFilter.SMOOTH_MORE)
            # On peut aussi ajuster la netteté pour garder les détails
            img_final = img_smooth.filter(ImageFilter.SHARPEN)
            img_final.save(filename, quality=95)
            print(f"✨ Post-traitement terminé : Grain supprimé sur {filename}")
    except Exception as e:
        print(f"⚠️ Impossible de traiter l'image : {e}")

def generate_fast_and_clean(prompt_text):
    print(f"🚀 Génération optimisée (Vitesse + Lissage local)...")
    
    # Prompt conçu pour être simple à générer pour le serveur
    full_prompt = f"digital photography, high resolution, smooth skin, clear lighting, {prompt_text}"
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # On utilise un modèle plus rapide pour éviter le Timeout
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=1344&nologo=true&seed={int(time.time())}"

    try:
        # Timeout réduit à 60s car on veut une réponse rapide
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)
                
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(OUTPUT_DIR, f"insta_smooth_{timestamp}.png")
            
            with open(filename, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Image téléchargée.")
            # Application du filtre anti-grain localement
            apply_anti_grain(filename)
            
        else:
            print(f"⚠️ Erreur serveur : {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur réseau ou Timeout : {e}. Le serveur est surchargé, réessayez dans 5 min.")

if __name__ == "__main__":
    my_prompt = "Woman with dark hair, white tank top, red bikini, luxury yacht, sunset background, cinematic"
    generate_fast_and_clean(my_prompt)
