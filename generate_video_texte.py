import os
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
import moviepy.video.fx as fx

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_texte.mp4"
DISPLAY_DURATION = 2.0     
TRANSITION_DURATION = 0.5  
FPS = 60
TEXT_TO_DISPLAY = "REMIGRATION"
# ======================================================

def create_video_with_text(folder_path, output_name):
    print(f"--- [LOG] Création vidéo avec texte : {TEXT_TO_DISPLAY} ---")
    
    if not os.path.exists(folder_path):
        print(f"--- [ERREUR] Dossier introuvable ---")
        return

    valid_extensions = ('.png', '.jpg', '.jpeg')
    image_files = [
        os.path.join(folder_path, f) for f in sorted(os.listdir(folder_path))
        if f.lower().endswith(valid_extensions)
    ]

    if not image_files:
        return

    try:
        clips = []
        total_clip_duration = DISPLAY_DURATION + TRANSITION_DURATION

        for i, path in enumerate(image_files):
            # 1. Créer le clip image
            img_clip = ImageClip(path).with_duration(total_clip_duration)
            
            # 2. Créer le clip texte
            # Note: Si cette partie échoue sur GitHub à cause d'ImageMagick, 
            # il existe une alternative via PIL, mais testons d'abord celle-ci.
            txt_clip = TextClip(
                text=TEXT_TO_DISPLAY,
                font_size=120,
                color='white',
                font='Arial-Bold', # Police standard
                stroke_color='black',
                stroke_width=2
            ).with_duration(total_clip_duration).with_position('center')

            # 3. Superposer le texte sur l'image
            composite = CompositeVideoClip([img_clip, txt_clip])
            
            # 4. Appliquer le fondu
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
            logger="bar"
        )

        print(f"--- [SUCCÈS] Vidéo avec texte générée ---")

    except Exception as e:
        print(f"--- [ERREUR] : {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_video_with_text(SOURCE_DIR, OUTPUT_FILENAME)
