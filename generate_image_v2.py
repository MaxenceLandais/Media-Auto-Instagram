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
        # Initialisation
        vertexai.init(project=project_id, location=location)
        model = ImageGenerationModel.from_pretrained(model_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"--- GÉNÉRATION IMAGEN 3 (Local) ---")
        print(f"Ratio choisi : 9:16 (Format Story/Vertical)")
        
        # On utilise le ratio 9:16 qui est supporté officiellement
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="9:16"
        )

        if response and response[0]:
            img = response[0]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_dir, f"insta_post_{timestamp}.png")

            # Sauvegarde
            img.save(location=filename, include_generation_parameters=False)
            print(f"✅ SUCCÈS : Image sauvegardée sous {filename}")
        else:
            print("❌ Erreur : L'API n'a pas retourné d'image.")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    
    my_prompt = """Photorealistic portrait of a woman leaning against a dark wooden bedpost, 
    right arm raised holding the post. Black lace loungewear, bright bedroom, soft natural lighting, 
    85mm lens, elegant lifestyle mood, sharp focus."""

    generate_image_locally(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt
    )
