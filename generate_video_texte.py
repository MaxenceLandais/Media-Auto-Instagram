import os
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
import moviepy.video.fx as fx

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_remigration.mp4"
DISPLAY_DURATION = 2.0     
TRANSITION_DURATION = 0.5  
FPS = 60
TEXT_TO_DISPLAY = "REMIGRATION"

# Chemin de la police standard sur Ubuntu (GitHub Actions)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
# ======================================================

def create_video_with_text(folder_path, output_name):
    print(f"--- [LOG] Démarrage du rendu avec texte : {TEXT_TO_DISPLAY} ---")
    
    if not os.path.exists(folder_path):
        print(f"--- [ERREUR] Dossier introuvable : {folder_path} ---")
        return

    valid_extensions = ('.png', '.jpg', '.jpeg')
    image_files = [
        os.path.join(folder_path, f) for f in sorted(os.listdir(folder_path))
        if f.lower().endswith(valid_extensions)
    ]

    if not image_files:
        print("--- [ERREUR] Aucune image trouvée ---")
        return

    try:
        clips = []
        total_clip_duration = DISPLAY_DURATION + TRANSITION_DURATION

        for i, path in enumerate(image_files):
            # 1. Clip Image
            img_clip = ImageClip(path).with_duration(total_clip_duration)
            
            # 2. Clip Texte (avec gestion d'erreur police)
            try:
                txt_clip = TextClip(
                    text=TEXT_TO_DISPLAY,
                    font_size=100,
                    color='white',
                    font=FONT_PATH,
                    stroke_color='black',
                    stroke_width=3
                ).with_duration(total_clip_duration).with_position(('center', 'center'))
            except Exception as font_err:
                print(f"--- [WARNING] Erreur police, utilisation police par défaut : {font_err} ---")
                txt_clip = TextClip(
                    text=TEXT_TO_DISPLAY,
                    font_size=100,
                    color='white'
                ).with_duration(total_clip_duration).with_position(('center', 'center'))

            # 3. Superposition
            composite = CompositeVideoClip([img_clip, txt_clip])
            
            # 4. Effet de transition
            if i > 0:
                composite = composite.with_effects([fx.CrossFadeIn(TRANSITION_DURATION)])
            
            clips.append(composite)

        # Assemblage final
        video = concatenate_videoclips(clips, method="compose", padding=-TRANSITION_DURATION)
        
        video_path = os.path.join(folder_path, output_name)
        video.write_videofile(
            video_path,
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="medium",
            ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"]
        )

        print(f"\n=== SUCCÈS : VIDÉO TEXTE GÉNÉRÉE ===\nPath: {video_path}")

    except Exception as e:
        print(f"--- [ERREUR GÉNÉRALE] : {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_video_with_text(SOURCE_DIR, OUTPUT_FILENAME)
