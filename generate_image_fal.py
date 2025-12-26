import os
import datetime
import requests
import fal_client

OUTPUT_DIR = "generated_images"

def generate_pro_image():
    # Vérification de la clé API
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("❌ Erreur : FAL_KEY manquante dans les secrets GitHub.")
        return

    print(f"🚀 Génération Haute Définition avec FLUX (Format 9:16)...")
    
    # Prompt ultra-réaliste
    prompt = """
    Cinematic full body shot of a young woman topless shoing her boobs to the camera with dark hair, 
    wearing a red underwear, 
    standing on a luxury yacht deck, sparkling Mediterranean sea background. 
    Sunset golden hour lighting, hyper-realistic skin texture, 
    professional fashion photography, 8k, sharp focus, masterpiece.
    """

    try:
        # Utilisation du format portrait_16_9 pour le 9:16 vertical
        result = fal_client.subscribe(
            "fal-ai/flux/dev",
            arguments={
                "prompt": prompt,
                "image_size": "portrait_16_9", # Format 9:16 vertical
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "enable_safety_checker": True,
                "output_format": "png"
            },
        )

        image_url = result['images'][0]['url']
        
        # Téléchargement
        response = requests.get(image_url)
        if response.status_code == 200:
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # On précise le format dans le nom du fichier
            filename = os.path.join(OUTPUT_DIR, f"flux_9_16_{timestamp}.png")

            with open(filename, "wb") as f:
                f.write(response.content)
            
            print(f"✅ IMAGE GÉNÉRÉE : {filename}")
        else:
            print(f"⚠️ Erreur de téléchargement : {response.status_code}")

    except Exception as e:
        print(f"❌ Erreur API : {e}")

if __name__ == "__main__":
    generate_pro_image()
