import os
import datetime
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.preview.vision_models import ImageGenerationModel
from moviepy.editor import ImageClip, concatenate_videoclips

# ==================== CONFIGURATION ====================
PROJECT_ID = "media-auto-instagram"   # À changer si besoin
LOCATION = "us-central1"
MODEL_NAME = "imagen-4.0-ultra-generate-001"  # ou imagen-3.0-generate-001 selon ton accès
NUM_SCENES = 5
DURATION_PER_IMAGE = 2.0  # secondes
# ======================================================

def get_creative_scenes(project_id, location, num_scenes=NUM_SCENES):
    """Demande à Gemini de générer des prompts créatifs 'Old Money'."""
    print(f"--- [LOG] Initialisation de Gemini ({location}) ---")
    vertexai.init(project=project_id, location=location)
    
    model = GenerativeModel("gemini-2.5-flash")  # Rapide et créatif
    
    prompt_instruction = (
        f"Generate {num_scenes} ultra-detailed image prompts for a high-end Instagram account. "
        "Style: 'Old Money', timeless luxury, cinematic, grand landscapes. "
        "Subjects: Young elegant European man and/or woman, impeccably dressed. "
        "Variety: Different locations (Swiss Alps, Monaco Riviera, Tuscany countryside, Lake Como, Scottish Highlands), "
        "different lightings (golden hour, misty morning, dramatic sunset), and subtle activities. "
        "Keep any mention of children extremely subtle or avoid it to pass safety filters. "
        "Return ONLY the list of prompts, one per line, no numbers, no quotes, no extra text."
    )
    
    print(f"--- [LOG] Envoi de la requête à Gemini ---")
    try:
        response = model.generate_content(prompt_instruction)
        prompts = [p.strip() for p in response.text.split('\n') if len(p.strip()) > 20]
        print(f"--- [LOG] Gemini a généré {len(prompts)} prompts ---")
        for i, p in enumerate(prompts):
            print(f"    Prompt {i+1}: {p[:100]}...")
        return prompts[:num_scenes]
    except Exception as e:
        print(f"--- [ERREUR] Gemini a échoué : {e} ---")
        return []

def generate_images_and_video(project_id=PROJECT_ID, location=LOCATION, model_name=MODEL_NAME):
    print(f"\n=== DÉBUT DE LA SESSION COMPLÈTE - {datetime.datetime.now()} ===\n")
    
    # Initialisation Vertex AI
    vertexai.init(project=project_id, location=location)
    image_model = ImageGenerationModel.from_pretrained(model_name)
    
    # Création du dossier de session
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_folder = f"session_{timestamp}"
    output_dir = os.path.join("generated_images", session_folder)
    os.makedirs(output_dir, exist_ok=True)
    print(f"--- [LOG] Dossier de sortie : {output_dir} ---")
    
    # Étape 1 : Obtenir les prompts
    scenes = get_creative_scenes(project_id, location)
    if not scenes:
        print("--- [ERREUR] Aucun prompt généré. Arrêt.")
        return
    
    # Étape 2 : Générer les images
    image_paths = []
    success_count = 0
    
    for i, scene_prompt in enumerate(scenes):
        index = i + 1
        print(f"\n--- [IMAGE {index}/{NUM_SCENES}] Génération en cours... ---")
        
        try:
            final_prompt = (
                f"{scene_prompt}, cinematic lighting, shot on 35mm film, shallow depth of field f/1.8, "
                "elegant and sophisticated atmosphere, ultra detailed textures, timeless luxury aesthetic"
            )
            
            response = image_model.generate_images(
                prompt=final_prompt,
                number_of_images=1,
                aspect_ratio="9:16",
                safety_filter_level="block_only_high",
                person_generation="allow_adult"
            )
            
            if response and response.images:
                filename = os.path.join(output_dir, f"scene_{index}.png")
                response.images[0].save(location=filename, include_generation_parameters=False)
                print(f"--- [SUCCÈS] Image {index} sauvegardée : {filename}")
                image_paths.append(filename)
                success_count += 1
            else:
                print(f"--- [WARNING] Aucune image retournée pour la scène {index} (filtre de sécurité ?)")
                
        except Exception as e:
            print(f"--- [ERREUR] Image {index} : {e} ---")
    
    print(f"\n--- Génération terminée : {success_count}/{NUM_SCENES} images réussies ---\n")
    
    if not image_paths:
        print("Aucune image à assembler en vidéo.")
        return
    
    # Étape 3 : Créer la vidéo de 10 secondes
    print("--- [VIDÉO] Assemblage de la vidéo en cours... ---")
    
    clips = []
    for img_path in image_paths:
        clip = ImageClip(img_path).set_duration(DURATION_PER_IMAGE)
        # Optionnel : zoom lent pour un effet plus cinématique
        clip = clip.resize(lambda t: 1 + 0.03*t)  # zoom progressif de 3%
        clips.append(clip)
    
    final_video = concatenate_videoclips(clips, method="compose")
    
    video_path = os.path.join(output_dir, "old_money_slideshow_10s.mp4")
    
    final_video.write_videofile(
        video_path,
        fps=30,
        codec="libx264",
        audio=False,
        preset="medium",
        threads=4,
        logger=None  # moins de logs verbeux
    )
    
    total_duration = len(image_paths) * DURATION_PER_IMAGE
    print(f"\n=== VIDÉO CRÉÉE AVEC SUCCÈS ===")
    print(f"→ Fichier : {video_path}")
    print(f"→ Durée  : {total_duration} secondes ({len(image_paths)} images × {DURATION_PER_IMAGE}s)")
    print(f"→ Dossier complet : {output_dir}")
    print(f"=================================\n")

if __name__ == "__main__":
    # Prérequis : pip install moviepy vertexai
    generate_images_and_video()
