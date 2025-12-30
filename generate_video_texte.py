import os
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
import moviepy.video.fx as fx

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_subtile.mp4"
DISPLAY_DURATION = 2.0     
TRANSITION_DURATION = 0.5  
FPS = 60
TEXT_TO_DISPLAY = "remigration"

# Chemin de la police standard sur Ubuntu
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
# ======================================================

def create_subtle_video(folder_path, output_name):
    print(f"--- [LOG] Rendu vidéo avec texte subtil ---")
    
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
            # 1. Image de fond
            img_clip = ImageClip(path).with_duration(total_clip_duration)
            
            # 2. Texte subtil et "caché"
            txt_clip = TextClip(
                text=TEXT_TO_DISPLAY,
                font_size=24,             # Taille très réduite
                color='white',
                font=FONT_PATH,
                stroke_color='black',
                stroke_width=0.5          # Bordure presque invisible
            ).with_duration(total_clip_duration)
            
            # Réduction de l'opacité (50%) pour le rendre semi-transparent
            txt_clip = txt_clip.with_opacity(0.4)
            
            # Positionnement subtil : en bas à droite avec une marge (margin)
            # 'right', 'bottom' place le texte dans le coin
            txt_clip = txt_clip.with_position((0.8, 0.9), relative=True)

            # 3. Superposition
            composite = CompositeVideoClip([img_clip, txt_clip])
            
            # 4. Transition
            if i > 0:
                composite = composite.with_effects([fx.CrossFadeIn(TRANSITION_DURATION)])
            
            clips.append(composite)

        # Assemblage
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

        print(f"--- [SUCCÈS] Vidéo générée avec filigrane discret ---")

    except Exception as e:
        print(f"--- [ERREUR] : {e} ---")

if __name__ == "__main__":
    create_subtle_video(SOURCE_DIR, OUTPUT_FILENAME)
