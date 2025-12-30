import os
from moviepy import ImageClip, concatenate_videoclips

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_60fps.mp4"
DURATION_PER_IMAGE = 2.0  # Chaque image reste 2 secondes
FPS = 60                  # Fluidité maximale pour les réseaux sociaux
# ======================================================

def create_video_60fps(folder_path, output_name):
    print(f"--- [LOG] Début du rendu à {FPS} FPS ---")
    
    if not os.path.exists(folder_path):
        print(f"--- [ERREUR] Dossier introuvable : {folder_path} ---")
        return

    # Sélection des images
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
            # Création du clip
            clip = ImageClip(path).with_duration(DURATION_PER_IMAGE)
            
            # Effet de zoom progressif (Ken Burns)
            # 1.04 signifie un zoom de 4% sur la durée du clip
            # À 60 FPS, ce mouvement sera parfaitement lisse
            clip = clip.with_effects([lambda c: c.resize(lambda t: 1 + 0.04 * (t / DURATION_PER_IMAGE))])
            
            clips.append(clip)

        # Assemblage
        print(f"--- [LOG] Assemblage de {len(clips)} clips ---")
        video = concatenate_videoclips(clips, method="compose")
        
        video_path = os.path.join(folder_path, output_name)

        # Exportation haute fluidité
        video.write_videofile(
            video_path,
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="slow",      # 'slow' permet une meilleure compression à 60 FPS
            threads=4,
            logger="bar",
            ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"] 
            # -crf 18 offre une qualité visuellement sans perte
        )

        print(f"\n=== SUCCÈS 60 FPS ===")
        print(f"✓ Vidéo : {video_path}")
        print(f"======================\n")

    except Exception as e:
        print(f"--- [ERREUR] : {e} ---")

if __name__ == "__main__":
    create_video_60fps(SOURCE_DIR, OUTPUT_FILENAME)
