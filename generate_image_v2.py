import os
import datetime
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

def generate_image_locally(
    project_id: str,
    location: str,
    prompt: str,
    model_name: str = "imagen-4.0-ultra-generate-001", # Mise à jour vers Imagen 4
    output_dir: str = "generated_images"
):
    try:
        vertexai.init(project=project_id, location=location)
        
        # Chargement du modèle Imagen (3.0 ou 4.0 selon model_name)
        model = ImageGenerationModel.from_pretrained(model_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"--- GÉNÉRATION {model_name.upper()} ---")
        print(f"Format : 9:16 | Destination : {output_dir}")
        
        # Nettoyage du prompt pour enlever les résidus Midjourney (--ar, --v)
        clean_prompt = prompt.split("--")[0].strip()

        # Appel de l'API avec les paramètres optimisés pour Imagen 4
        response = model.generate_images(
            prompt=clean_prompt,
            number_of_images=1,
            aspect_ratio="9:16",
            # Imagen 4 améliore la flexibilité des filtres
            safety_filter_level="block_only_high", 
            person_generation="allow_adult"
        )

        if response and len(response.images) > 0:
            img = response.images[0]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # On indique le modèle dans le nom du fichier pour comparer
            model_tag = "img4" if "4.0" in model_name else "img3"
            filename = os.path.join(output_dir, f"insta_{model_tag}_{timestamp}.png")

            img.save(location=filename, include_generation_parameters=False)
            print(f"✅ SUCCÈS : Image sauvegardée sous {filename}")
        else:
            print("⚠️ ÉCHEC : Aucune image retournée (blocage de sécurité ou erreur API).")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    
    # Prompt optimisé (sans les tags Midjourney qui ne sont pas compris par Google)
    my_prompt = (
        "Rear view of a young couple driving in a classic black 1960s Ford Thunderbird convertible "
        "along a coastal road at sunset, ocean on the left, clear sky, woman in passenger seat "
        "with long blonde hair raising both arms in joy and freedom, man driving wearing sunglasses, "
        "cinematic aesthetic, high detail, photorealistic, soft lighting"
    )

    # Note : Si Imagen 4 n'est pas encore déployé sur votre zone, 
    # utilisez "imagen-3.0-generate-002"
    generate_image_locally(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt,
        model_name="imagen-4.0-ultra-generate-001" 
    )
