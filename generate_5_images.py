import os
import datetime
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.preview.vision_models import ImageGenerationModel

def get_creative_scenes(project_id, location, num_scenes=5):
    """Demande à Gemini d'inventer 5 scènes Old Money uniques."""
    vertexai.init(project=project_id, location=location)
    model = GenerativeModel("gemini-2.5-flash") # Utilisation de Gemini pour la créativité
    
    instruction = (
        f"Generate {num_scenes} highly detailed image prompts for an 'Old Money' and 'Luxury' lifestyle. "
        "Themes: grand landscapes, European young man and/or woman, elegant, classy, sometimes with children. "
        "Locations to vary: Swiss Alps, Lake Como, French Riviera, Loire Valley chateau, or Scottish Highlands. "
        "Technical requirements: photorealistic, cinematic lighting, 8k, soft colors. "
        "Return ONLY a list of prompts, one per line, no numbers, starting each with 'A photorealistic...'"
    )
    
    response = model.generate_content(instruction)
    # On sépare les lignes et on nettoie les espaces vides
    prompts = [p.strip() for p in response.text.split('\n') if len(p.strip()) > 10]
    return prompts[:num_scenes]

def generate_old_money_session(project_id, location, model_name="imagen-4.0-ultra-generate-001"):
    try:
        vertexai.init(project=project_id, location=location)
        image_model = ImageGenerationModel.from_pretrained(model_name)

        # 1. Création du répertoire unique pour cette session
        timestamp_session = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("generated_images", f"session_{timestamp_session}")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 2. Récupération des 5 scènes via Gemini
        print(f"🤖 Gemini imagine 5 scènes exclusives...")
        scenes = get_creative_scenes(project_id, location)

        # 3. Boucle de génération des images
        for i, scene_prompt in enumerate(scenes):
            print(f"\n📸 Génération de l'image {i+1}/5...")
            print(f"Prompt : {scene_prompt[:100]}...")

            response = image_model.generate_images(
                prompt=scene_prompt,
                number_of_images=1,
                aspect_ratio="9:16",
                safety_filter_level="block_only_high",
                person_generation="allow_adult"
            )

            if response and len(response.images) > 0:
                img = response.images[0]
                filename = os.path.join(output_dir, f"scene_{i+1}.png")
                img.save(location=filename, include_generation_parameters=False)
                print(f"✅ Sauvegardée : {filename}")
            else:
                print(f"⚠️ Échec pour la scène {i+1}")

        print(f"\n✨ Session terminée. Retrouvez vos images dans : {output_dir}")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    
    generate_old_money_session(
        project_id=PROJECT_ID,
        location=LOCATION,
        model_name="imagen-4.0-ultra-generate-001"
    )
