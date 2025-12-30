import os
import random
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
import moviepy.video.fx as fx

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_random_subtile.mp4"
DISPLAY_DURATION = 2.0     
TRANSITION_DURATION = 0.5  
FPS = 60

# Liste des phrases à piocher aléatoirement
PHRASES = [
    "remigration", "send them back", "life after remigration", 
    "this and remigration", "remigration vibes", "remigration is beautiful", 
    "remigrate them", "stop the boats", "ask for mass deportation", 
    "mass deportation", "this vibe and remigration"
]

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
# ======================================================

def create_random_text_video(folder_path, output_name):
    print(f"--- [LOG] Rendu vidéo avec textes aléatoires ---")
    
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
            # 1. Sélection aléatoire de la phrase pour cette image précise
            current_text = random.choice(PHRASES)
            print(f"   > Image {i+1}: Texte choisi -> '{current_text}'")

            # 2. Image de fond
            img_clip = ImageClip(path).with_duration(total_clip_duration)
            
            # 3. Texte subtil
            txt_clip = TextClip(
                text=current_text,
                font_size=22,             # Très petit
                color='white',
                font=FONT_PATH,
                stroke_color='black',
                stroke_width=0.5
            ).with_duration(total_clip_duration)
            
            # Opacité réduite (très discret)
            txt_clip = txt_clip.with_opacity(0.35)
            
            # Positionnement aléatoire dans les coins (optionnel) ou fixe en bas
            # Ici, on le garde fixe en bas à droite pour la cohérence
            txt_clip = txt_clip.with_position((0.75, 0.92), relative=True)

            # 4. Superposition
            composite = CompositeVideoClip([img_clip, txt_clip])
            
            # 5. Transition
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

        print(f"--- [SUCCÈS] Vidéo générée avec messages variables ---")

    except Exception as e:
        print(f"--- [ERREUR] : {e} ---")

if __name__ == "__main__":
    create_random_text_video(SOURCE_DIR, OUTPUT_FILENAME)
