import os
from moviepy import ImageClip, concatenate_videoclips

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_session.mp4"
DURATION_PER_IMAGE = 2.0  # Durée en secondes
FPS = 30
# ======================================================

def create_video_from_folder(folder_path, output_name):
    print(f"--- [LOG] Lecture du dossier : {folder_path} ---")
    
    # Vérification si le dossier existe
    if not os.path.exists(folder_path):
        print(f"--- [ERREUR] Le dossier {folder_path} n'existe pas. ---")
        return

    # Lister et filtrer les images (png, jpg, jpeg)
    valid_extensions = ('.png', '.jpg', '.jpeg')
    image_files = [
        os.path.join(folder_path, f) for f in sorted(os.listdir(folder_path))
        if f.lower().endswith(valid_extensions)
    ]

    if not image_files:
        print("--- [ERREUR] Aucune image trouvée dans le dossier. ---")
        return

    print(f"--- [LOG] {len(image_files)} images trouvées. Création des clips... ---")

    try:
        clips = []
        for path in image_files:
            # Création du clip pour chaque image
            clip = ImageClip(path).with_duration(DURATION_PER_IMAGE)
            
            # Optionnel : Ajout d'un zoom progressif (Ken Burns effect)
            # clip = clip.with_effects([lambda c: c.resize(lambda t: 1 + 0.04 * t)])
            
            clips.append(clip)

        # Assemblage des clips
        print("--- [LOG] Assemblage de la vidéo finale... ---")
        video = concatenate_videoclips(clips, method="compose")
        
        # Chemin de sortie final
        video_path = os.path.join(folder_path, output_name)

        # Exportation
        video.write_videofile(
            video_path,
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="medium",
            threads=4,
            logger="bar", # Affiche une barre de progression
            ffmpeg_params=["-crf", "23", "-pix_fmt", "yuv420p"]
        )

        print(f"\n=== SUCCÈS ===")
        print(f"✓ Vidéo générée avec succès : {video_path}")
        print(f"====================\n")

    except Exception as e:
        print(f"--- [ERREUR] Lors de la création vidéo : {e} ---")

if __name__ == "__main__":
    create_video_from_folder(SOURCE_DIR, OUTPUT_FILENAME)
