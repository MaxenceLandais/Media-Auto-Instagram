import os
from moviepy import ImageClip, concatenate_videoclips
import moviepy.video.fx as fx

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_60fps.mp4"
DURATION_PER_IMAGE = 2.0
FPS = 60
# ======================================================

def create_video_60fps(folder_path, output_name):
    print(f"--- [LOG] Début du rendu à {FPS} FPS ---")
    
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
        for path in image_files:
            # Création du clip de base
            clip = ImageClip(path).with_duration(DURATION_PER_IMAGE)
            
            # Application de l'effet de zoom (Syntaxe MoviePy v2)
            # On utilise .resized qui accepte une fonction pour le facteur d'échelle
            clip = clip.resized(lambda t: 1 + 0.04 * (t / DURATION_PER_IMAGE))
            
            clips.append(clip)

        print(f"--- [LOG] Assemblage de {len(clips)} clips ---")
        # On utilise method="chain" pour des images fixes, c'est plus rapide
        video = concatenate_videoclips(clips, method="compose")
        
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

        print(f"\n=== SUCCÈS 60 FPS ===")
        print(f"✓ Vidéo : {video_path}")
        print(f"======================\n")

    except Exception as e:
        print(f"--- [ERREUR] : {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_video_60fps(SOURCE_DIR, OUTPUT_FILENAME)
