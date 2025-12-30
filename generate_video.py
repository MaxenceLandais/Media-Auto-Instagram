import os
from moviepy import ImageClip, concatenate_videoclips

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_final_fixe.mp4"
DURATION_PER_IMAGE = 2.0  # Temps total d'affichage
TRANSITION_DURATION = 0.5 # Durée du fondu entre deux images
FPS = 60
# ======================================================

def create_clean_video(folder_path, output_name):
    print(f"--- [LOG] Rendu Vidéo Fixe (Stabilité 100%) ---")
    
    if not os.path.exists(folder_path):
        print(f"--- [ERREUR] Dossier introuvable : {folder_path} ---")
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
        for i, path in enumerate(image_files):
            # Créer le clip image sans aucun effet de redimensionnement (zoom)
            clip = ImageClip(path).with_duration(DURATION_PER_IMAGE)
            
            # Ajouter un fondu enchaîné (crossfadein) 
            # Note : on ne le met pas sur le premier clip pour éviter un démarrage noir
            if i > 0:
                clip = clip.with_crossfadein(TRANSITION_DURATION)
            
            clips.append(clip)

        # Utilisation de method="compose" est obligatoire pour le crossfade
        # padding=-TRANSITION_DURATION permet de superposer les clips pour le fondu
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
        print(f"✓ Vidéo générée (sans zoom) : {video_path}")

    except Exception as e:
        print(f"--- [ERREUR] : {e} ---")

if __name__ == "__main__":
    create_clean_video(SOURCE_DIR, OUTPUT_FILENAME)
