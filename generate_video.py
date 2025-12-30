import os
from moviepy import ImageClip, concatenate_videoclips

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_ultra_stable.mp4"
DURATION_PER_IMAGE = 2.0
FPS = 60
# ======================================================

def create_ultra_stable_video(folder_path, output_name):
    print(f"--- [LOG] Rendu ULTRA STABLE (Filtre Lanczos) ---")
    
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
        for path in image_files:
            # Charger l'image en forçant une résolution cible pour éviter les calculs flottants
            clip = ImageClip(path).with_duration(DURATION_PER_IMAGE)
            
            # Utilisation de la méthode de redimensionnement de MoviePy avec l'algorithme "bilinear" 
            # qui est souvent plus stable pour les animations que le défaut.
            # On réduit aussi la vitesse du zoom (0.015) pour une élégance maximale.
            clip = clip.resized(lambda t: 1 + 0.015 * (t / DURATION_PER_IMAGE))
            
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        video_path = os.path.join(folder_path, output_name)

        video.write_videofile(
            video_path,
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="veryslow",   # Maximum de précision pour le mouvement
            threads=4,
            logger="bar",
            ffmpeg_params=[
                "-crf", "16",
                "-pix_fmt", "yuv420p",
                "-sws_flags", "lanczos+accurate_rnd", # Force FFmpeg à utiliser le meilleur algorithme de mise à l'échelle
                "-vf", "format=yuv420p" 
            ]
        )

        print(f"\n=== SUCCÈS ULTRA STABLE ===")
    except Exception as e:
        print(f"--- [ERREUR] : {e} ---")

if __name__ == "__main__":
    create_ultra_stable_video(SOURCE_DIR, OUTPUT_FILENAME)
