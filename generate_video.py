import os
from moviepy import ImageClip, concatenate_videoclips
import moviepy.video.fx as fx

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_final_fixe.mp4"
DURATION_PER_IMAGE = 2.0  
TRANSITION_DURATION = 0.5 
FPS = 60
# ======================================================

def create_clean_video(folder_path, output_name):
    print(f"--- [LOG] Rendu Vidéo Fixe (Sans Zoom) ---")
    
    if not os.path.exists(folder_path):
        print(f"--- [ERREUR] Dossier introuvable : {folder_path} ---")
        return

    valid_extensions = ('.png', '.jpg', '.jpeg')
    image_files = [
        os.path.join(folder_path, f) for f in sorted(os.listdir(folder_path))
        if f.lower().endswith(valid_extensions)
    ]

    if not image_files:
        print("--- [ERREUR] Aucune image trouvée. ---")
        return

    try:
        clips = []
        for i, path in enumerate(image_files):
            clip = ImageClip(path).with_duration(DURATION_PER_IMAGE)
            
            # Application du fondu enchaîné via la nouvelle syntaxe v2
            if i > 0:
                # On applique l'effet de fondu au début de chaque clip (sauf le premier)
                clip = clip.with_effects([fx.CrossFadeIn(TRANSITION_DURATION)])
            
            clips.append(clip)

        # Assemblage avec superposition pour permettre le fondu
        video = concatenate_videoclips(clips, method="compose", padding=-TRANSITION_DURATION)
        
        video_path = os.path.join(folder_path, output_name)

        video.write_videofile(
            video_path,
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="medium",
            threads=4,
            logger="bar",
            ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"]
        )

        print(f"\n=== SUCCÈS VIDÉO STABLE ===")
        print(f"✓ Vidéo générée : {video_path}")

    except Exception as e:
        print(f"--- [ERREUR] : {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_clean_video(SOURCE_DIR, OUTPUT_FILENAME)
