import os
import datetime
import requests
import fal_client

# Configuration du dossier de sortie
OUTPUT_DIR = "generated_images"

def generate_pro_image():
    # RÉCUPÉRATION DE LA CLÉ : Très important pour GitHub Actions
    # Le script va chercher la variable d'environnement FAL_KEY définie dans le YAML
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("❌ Erreur : FAL_KEY manquante. Vérifiez vos Secrets GitHub.")
        return

    print(f"🚀 Connexion à Fal.ai (Modèle Flux.1 Dev)...")
    
    # Prompt optimisé pour le style "Maria Rubtsova"
    prompt = """
    High-end fashion photography, young woman with dark hair, 
    wearing a white tank top and red bikini, 
    standing on a luxury yacht deck, ocean background. 
    Sunset lighting, ultra-realistic skin texture, 8k resolution, 
    sharp focus, cinematic composition, professional color grading.
    """

    try:
        # Envoi de la requête à Fal.ai
        result = fal_client.subscribe(
            "fal-ai/flux/dev",
            arguments={
                "prompt": prompt,
                "image_size": "portrait_4_5",
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "enable_safety_checker": True
            },
        )

        image_url = result['images'][0]['url']
        print(f"🔗 Image générée avec succès. Téléchargement...")

        # Téléchargement et sauvegarde
        response = requests.get(image_url)
        if response.status_code == 200:
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(OUTPUT_DIR, f"flux_pro_{timestamp}.png")

            with open(filename, "wb") as f:
                f.write(response.content)
            
            print(f"✅ IMAGE SAUVEGARDÉE : {filename}")
        else:
            print(f"⚠️ Échec du téléchargement (Code: {response.status_code})")

    except Exception as e:
        print(f"❌ Erreur lors de la génération : {e}")

if __name__ == "__main__":
    generate_pro_image()
