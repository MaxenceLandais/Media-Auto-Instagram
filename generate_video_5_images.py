import os
import datetime

# Import corrigé pour MoviePy v2+ (plus de .editor)
from moviepy import ImageClip, concatenate_videoclips

import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.preview.vision_models import ImageGenerationModel

# ==================== CONFIGURATION ====================
PROJECT_ID = "media-auto-instagram"
LOCATION = "us-central1"
MODEL_NAME = "imagen-4.0-ultra-generate-001"  # ou imagen-3 si besoin
NUM_SCENES = 5
DURATION_PER_IMAGE = 2.0  # 10 secondes total
# ======================================================

def get_creative_scenes(project_id, location, num_scenes=NUM_SCENES):
    print("--- [LOG] Initialisation Gemini ---")
    vertexai.init(project=project_id, location=location)
    model = GenerativeModel("gemini-1.5-flash")

    prompt_instruction = (
        f"Generate {num_scenes} ultra-detailed image prompts for a luxury 'Old Money' aesthetic Instagram reel. "
        "Subjects: young elegant European man and/or woman, impeccably dressed in timeless fashion. "
        "Locations: Swiss Alps, Monaco, Tuscany hills, Lake Como, Scottish Highlands, French Riviera. "
        "Lighting: golden hour, misty morning, dramatic sunset, soft natural light. "
        "Atmosphere: sophisticated, serene, cinematic, grand landscapes. "
        "Return ONLY the prompts, one per line, no numbering, no quotes, no extra text."
    )

    try:
        response = model.generate_content(prompt_instruction)
        prompts = [line.strip() for line in response.text.split('\n') if len(line.strip()) > 20]
        print(f"--- [LOG] {len(prompts)} prompts générés ---")
        return prompts[:num_scenes]
    except Exception as e:
        print(f"--- [ERREUR] Gemini : {e} ---")
        return []

def generate_images_and_video():
    print(f"\n=== DÉBUT SESSION - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    image_model = ImageGenerationModel.from_pretrained(MODEL_NAME)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_folder = f"session_{timestamp}"
    output_dir = os.path.join("generated_images", session_folder)
    os.makedirs(output_dir, exist_ok=True)
    print(f"--- Dossier de sortie : {output_dir} ---")

    scenes = get_creative_scenes(PROJECT_ID, LOCATION)
    if not scenes:
        print("Aucun prompt → arrêt.")
        return

    image_paths = []
    for i, prompt in enumerate(scenes):
        print(f"\n--- Génération image {i+1}/{NUM_SCENES} ---")
        try:
            final_prompt = f"{prompt}, cinematic 35mm film look, f/1.8, ultra detailed, luxury old money aesthetic"
            response = image_model.generate_images(
                prompt=final_prompt,
                number_of_images=1,
                aspect_ratio="9:16",
                safety_filter_level="block_only_high",
                person_generation="allow_adult"
            )
            if response.images:
                path = os.path.join(output_dir, f"scene_{i+1}.png")
                response.images[0].save(location=path)
                print(f"✓ Image {i+1} sauvegardée")
                image_paths.append(path)
            else:
                print(f"✗ Image {i+1} bloquée")
        except Exception as e:
            print(f"✗ Erreur image {i+1} : {e}")

    if not image_paths:
        print("Aucune image → pas de vidéo.")
        return

    print("\n--- Création vidéo Reel 10s ---")
    try:
        clips = []
        for path in image_paths:
            clip = ImageClip(path).set_duration(DURATION_PER_IMAGE)
            clip = clip.resize(lambda t: 1 + 0.04 * t)  # Zoom doux
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        video_path = os.path.join(output_dir, "old_money_reel_10s.mp4")

        video.write_videofile(
            video_path,
            fps=30,
            codec="libx264",
            audio=False,
            preset="medium",
            threads=4,
            logger=None,
            ffmpeg_params=["-crf", "23", "-pix_fmt", "yuv420p"]
        )

        print(f"\n=== SUCCÈS ===")
        print(f"✓ {len(image_paths)} images + vidéo créée : {video_path}")
        print(f"====================\n")

    except Exception as e:
        print(f"--- [ERREUR VIDÉO] : {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_images_and_video()
