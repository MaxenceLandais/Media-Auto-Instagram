import os
import datetime
import sys

# === Vérification précoce de ffmpeg ===
try:
    import imageio
    imageio.plugins.ffmpeg.download()  # Télécharge une version portable de ffmpeg si besoin
    print("--- [LOG] imageio-ffmpeg initialisé avec succès ---")
except Exception as e:
    print(f"--- [WARNING] Problème avec imageio-ffmpeg : {e} ---")

try:
    from moviepy.editor import ImageClip, concatenate_videoclips
    print("--- [LOG] moviepy importé avec succès ---")
except ImportError as e:
    print(f"--- [ERREUR FATALE] Impossible d'importer moviepy : {e} ---")
    sys.exit(1)

import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.preview.vision_models import ImageGenerationModel

# ==================== CONFIGURATION ====================
PROJECT_ID = "media-auto-instagram"          # À adapter si différent
LOCATION = "us-central1"
MODEL_NAME = "imagen-4.0-ultra-generate-001" # ou "imagen-3.0-generate-001" si tu n'as pas accès à la v4
NUM_SCENES = 5
DURATION_PER_IMAGE = 2.0  # secondes → 10s total
# ======================================================

def get_creative_scenes(project_id, location, num_scenes=NUM_SCENES):
    print(f"--- [LOG] Initialisation de Gemini ({location}) ---")
    vertexai.init(project=project_id, location=location)
    
    model = GenerativeModel("gemini-2.5-flash")
    
    prompt_instruction = (
        f"Generate {num_scenes} ultra-detailed image prompts for a high-end Instagram account. "
        "Style: 'Old Money', timeless luxury, cinematic, grand landscapes. "
        "Subjects: Young elegant European man and/or woman, impeccably dressed. "
        "Variety: Different locations (Swiss Alps, Monaco Riviera, Tuscany countryside, Lake Como, Scottish Highlands), "
        "different lightings (golden hour, misty morning, dramatic sunset), and subtle activities. "
        "Avoid any mention of children to pass safety filters. "
        "Return ONLY the list of prompts, one per line, no numbers, no quotes, no extra text."
    )
    
    print("--- [LOG] Envoi de la requête à Gemini ---")
    try:
        response = model.generate_content(prompt_instruction)
        prompts = [p.strip() for p in response.text.split('\n') if len(p.strip()) > 20]
        print(f"--- [LOG] {len(prompts)} prompts reçus de Gemini ---")
        for i, p in enumerate(prompts[:num_scenes]):
            print(f"    Prompt {i+1}: {p[:120]}...")
        return prompts[:num_scenes]
    except Exception as e:
        print(f"--- [ERREUR] Gemini a échoué : {e} ---")
        return []

def generate_images_and_video(project_id=PROJECT_ID, location=LOCATION, model_name=MODEL_NAME):
    print(f"\n=== DÉBUT DE LA GÉNÉRATION - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    
    vertexai.init(project=project_id, location=location)
    image_model = ImageGenerationModel.from_pretrained(model_name)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_folder = f"session_{timestamp}"
    output_dir = os.path.join("generated_images", session_folder)
    os.makedirs(output_dir, exist_ok=True)
    print(f"--- [LOG] Dossier de sortie : {output_dir} ---")
    
    scenes = get_creative_scenes(project_id, location)
    if not scenes:
        print("--- [ERREUR] Aucun prompt généré. Arrêt du script.")
        return
    
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
            
            if response and response.images and len(response.images) > 0:
                filename = os.path.join(output_dir, f"scene_{index}.png")
                response.images[0].save(location=filename, include_generation_parameters=False)
                print(f"--- [SUCCÈS] Image {index} sauvegardée : {filename}")
                image_paths.append(filename)
                success_count += 1
            else:
                print(f"--- [WARNING] Aucune image retournée pour la scène {index} (filtre de sécurité ?)")
                
        except Exception as e:
            print(f"--- [ERREUR] Échec génération image {index} : {e} ---")
    
    print(f"\n--- Génération d'images terminée : {success_count}/{NUM_SCENES} réussies ---\n")
    
    if not image_paths:
        print("Aucune image générée → pas de vidéo créée.")
        return
    
    # ==================== CRÉATION DE LA VIDÉO ====================
    print("--- [VIDÉO] Assemblage de la vidéo 10 secondes en cours... ---")
    
    try:
        clips = []
        for img_path in image_paths:
            clip = ImageClip(img_path).set_duration(DURATION_PER_IMAGE)
            # Zoom doux progressif pour un effet cinématique
            clip = clip.resize(lambda t: 1 + 0.04 * t)  # Zoom de 4% sur 2 secondes
            clips.append(clip)
        
        final_video = concatenate_videoclips(clips, method="compose")
        
        video_path = os.path.join(output_dir, "old_money_reel_10s.mp4")
        
        print(f"--- [VIDÉO] Encodage en cours → {video_path} ---")
        final_video.write_videofile(
            video_path,
            fps=30,
            codec="libx264",
            audio=False,
            preset="medium",
            threads=4,
            logger=None,  # Moins de logs verbeux dans la CI
            ffmpeg_params=["-crf", "23"]  # Bonne qualité / taille raisonnable
        )
        
        total_duration = len(image_paths) * DURATION_PER_IMAGE
        print(f"\n=== SUCCÈS TOTAL ===")
        print(f"→ {success_count} images générées")
        print(f"→ Vidéo créée : {video_path}")
        print(f"→ Durée : {total_duration} secondes")
        print(f"→ Dossier : {output_dir}")
        print(f"====================\n")
        
    except Exception as e:
        print(f"--- [ERREUR] Échec création vidéo : {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_images_and_video()
