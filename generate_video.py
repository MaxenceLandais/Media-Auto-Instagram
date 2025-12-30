import os
from moviepy import ImageClip, concatenate_videoclips
import moviepy.video.fx as fx

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_2s_fixed.mp4"
DISPLAY_DURATION = 2.0     # Temps d'affichage fixe
TRANSITION_DURATION = 0.5  # Temps de fondu
FPS = 60
# ======================================================

def create_perfect_timing_video(folder_path, output_name):
    print(f"--- [LOG] Rendu 2s par image + transitions ---")
    
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
        # La durée totale d'un clip doit être le temps d'affichage + le fondu
        total_clip_duration = DISPLAY_DURATION + TRANSITION_DURATION

        for i, path in enumerate(image_files):
            clip = ImageClip(path).with_duration(total_clip_duration)
            
            # On applique le fondu au début de chaque clip sauf le premier
            if i > 0:
                clip = clip.with_effects([fx.CrossFadeIn(TRANSITION_DURATION)])
            
            clips.append(clip)

        # On concatène en chevauchant exactement de la durée de la transition
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

        print(f"\n=== SUCCÈS : 2 SECONDES PAR IMAGE ===")
        print(f"✓ Vidéo générée : {video_path}")

    except Exception as e:
        print(f"--- [ERREUR] : {e} ---")

if __name__ == "__main__":
    create_perfect_timing_video(SOURCE_DIR, OUTPUT_FILENAME)
