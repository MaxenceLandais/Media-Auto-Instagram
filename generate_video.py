import os
from moviepy import ImageClip, concatenate_videoclips

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_60fps_stable.mp4"
DURATION_PER_IMAGE = 2.0
FPS = 60
# ======================================================

def create_stable_video(folder_path, output_name):
    print(f"--- [LOG] Début du rendu STABLE à {FPS} FPS ---")
    
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
            # Charger l'image
            clip = ImageClip(path).with_duration(DURATION_PER_IMAGE)
            
            # ZOOM STABLE :
            # Au lieu d'un zoom linéaire pur, on peut utiliser un lissage 
            # Mais pour la stabilité, le plus important est l'interpolation.
            # On définit une fonction de zoom très légère (2%) pour éviter les distorsions
            clip = clip.resized(lambda t: 1 + 0.02 * (t / DURATION_PER_IMAGE))
            
            clips.append(clip)

        print(f"--- [LOG] Assemblage de {len(clips)} clips ---")
        video = concatenate_videoclips(clips, method="compose")
        
        video_path = os.path.join(folder_path, output_name)

        # Paramètres d'encodage pour la stabilité visuelle
        video.write_videofile(
            video_path,
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="slow",      # Plus lent = calcul plus précis des vecteurs de mouvement
            threads=4,
            logger="bar",
            ffmpeg_params=[
                "-crf", "17",           # Qualité quasi-parfaite
                "-pix_fmt", "yuv420p", 
                "-tune", "stillimage",  # Optimise l'encodage pour les images fixes avec mouvement
                "-flags", "+gray"       # Optionnel : réduit le bruit de couleur sur les textures
            ]
        )

        print(f"\n=== SUCCÈS 60 FPS STABLE ===")
        print(f"✓ Vidéo : {video_path}")
        print(f"============================\n")

    except Exception as e:
        print(f"--- [ERREUR] : {e} ---")

if __name__ == "__main__":
    create_stable_video(SOURCE_DIR, OUTPUT_FILENAME)
