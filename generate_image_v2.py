import base64
import os
import datetime
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

def generate_image_locally(
    project_id: str,
    location: str,
    prompt: str,
    model_name: str = "imagegeneration@006",
    output_dir: str = "generated_images"
):
    """
    Génère une image avec Imagen 3 et la sauvegarde localement.
    """
    try:
        # Initialisation du SDK
        vertexai.init(project=project_id, location=location)
        model = ImageGenerationModel.from_pretrained(model_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Dossier '{output_dir}' créé.")

        print(f"--- GÉNÉRATION IMAGEN 3 (Local) ---")
        
        # On ne précise PAS de storage_uri pour recevoir le Base64
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="4:5"
        )

        if response and response[0]:
            # Imagen 3 via le SDK vertexai permet d'accéder directement aux images
            img = response[0]
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_dir, f"insta_post_{timestamp}.png")

            # Sauvegarde directe via la méthode intégrée au SDK
            img.save(location=filename, include_generation_parameters=False)
            
            print(f"✅ SUCCÈS : Image sauvegardée sous {filename}")
        else:
            print("❌ Erreur : Aucune image générée.")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    
    # Prompt simplifié pour une meilleure compréhension par l'IA
    my_prompt = """Photorealistic portrait of a woman leaning against a dark wooden bedpost, 
    right arm raised holding the post. Black lace loungewear, bright bedroom, soft natural lighting, 
    85mm lens, elegant lifestyle mood, sharp focus."""

    generate_image_locally(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt
    )
