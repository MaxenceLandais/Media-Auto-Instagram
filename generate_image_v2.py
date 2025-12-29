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
    try:
        vertexai.init(project=project_id, location=location)
        model = ImageGenerationModel.from_pretrained(model_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"--- GÉNÉRATION IMAGEN 3 (Local) ---")
        print(f"Ratio : 9:16 | Modèle : {model_name}")
        
        # Appel avec gestion de la sécurité pour éviter le blocage (Content Filtering)
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="9:16",
            safety_filter_level="block_only_high", # Autorise plus de flexibilité
            person_generation="allow_adult"       # Nécessaire pour des sujets adultes/mode
        )

        # Vérification robuste de la liste de réponse
        if response and len(response.images) > 0:
            img = response.images[0]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_dir, f"insta_post_{timestamp}.png")

            img.save(location=filename, include_generation_parameters=False)
            print(f"✅ SUCCÈS : Image sauvegardée sous {filename}")
        else:
            print("⚠️ L'IA n'a pas retourné d'image. Elle a probablement été filtrée par les règles de sécurité.")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    
    # Prompt légèrement ajusté pour être plus "Safe" tout en gardant l'esthétique
    my_prompt = """Rear view of a young couple driving in a classic black 1960s Ford Thunderbird convertible along a coastal road at sunset, ocean on the left, clear sky, woman in passenger seat with long blonde hair raising both arms in joy and freedom, man driving wearing sunglasses, cinematic aesthetic, high detail, photorealistic, soft lighting --ar 9:16 --v 5"""

    generate_image_locally(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt
    )
