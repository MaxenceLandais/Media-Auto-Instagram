import os
import random
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
import moviepy.video.fx as fx

# ==================== CONFIGURATION ====================
SOURCE_DIR = "generated_images/session_20251230_000707"
OUTPUT_FILENAME = "recap_video_final.mp4"
DISPLAY_DURATION = 2.0     
TRANSITION_DURATION = 0.5  
FPS = 60

PHRASES = [
    "remigration", "send them back", "life after remigration", 
    "this and remigration", "remigration vibes", "remigration is beautiful", 
    "remigrate them", "stop the boats", "ask for mass deportation", 
    "mass deportation", "this vibe and remigration"
]

# Positions sécurisées
POSITIONS = [
    ('left', 'top'), ('right', 'top'), 
    ('left', 'bottom'), ('right', 'bottom'),
    ('center', 'bottom'), ('center', 'top')
]

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
# ======================================================

def create_dynamic_video_fixed(folder_path, output_name):
    print(f"--- [LOG] Rendu vidéo avec corrections marges ---")
    
    if not os.path.exists(folder_path):
        print(f"--- [ERREUR] Dossier introuvable ---")
        return

    image_files = [
        os.path.join(folder_path, f) for f in sorted(os.listdir(folder_path))
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

    try:
        clips = []
        total_clip_duration = DISPLAY_DURATION + TRANSITION_DURATION

        for i, path in enumerate(image_files):
            current_text = random.choice(PHRASES)
            current_pos = random.choice(POSITIONS)
            
            # 1. Clip Image
            img_clip = ImageClip(path).with_duration(total_clip_duration)
            
            # 2. Clip Texte
            txt_clip = TextClip(
                text=current_text,
                font_size=28,
                color='white',
                font=FONT_PATH,
                stroke_color='black',
                stroke_width=1
            ).with_duration(total_clip_duration).with_opacity(0.45)
            
            # Correction de la marge : On applique l'effet de marge AVANT la position
            # On ajoute 30 pixels de marge sur tous les côtés
            txt_clip = txt_clip.with_effects([fx.Margin(all=30)])
            txt_clip = txt_clip.with_position(current_pos)

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

        print(f"--- [SUCCÈS] Vidéo générée avec marges de sécurité ---")

    except Exception as e:
        print(f"--- [ERREUR] : {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_dynamic_video_fixed(SOURCE_DIR, OUTPUT_FILENAME)
