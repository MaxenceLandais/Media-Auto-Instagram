import os
import datetime
import json
import torch
from diffusers import DiffusionPipeline

def generate_image_sdxl(
    prompt_json: str,
    output_dir: str = "generated_images"
):
    print(f"--- DÉMARRAGE GÉNÉRATION SDXL (Local) ---")

    # 1. Extraction intelligente du prompt depuis votre JSON
    # SDXL a besoin du texte pur, pas de tout le bloc JSON technique
    try:
        data = json.loads(prompt_json)
        # On va chercher précisément le texte dans votre structure
        actual_prompt = data["generation_parameters"]["prompt"]
        negative_prompt = data["generation_parameters"]["negative_prompt"]
        print("✅ JSON analysé avec succès.")
        print(f"📝 Prompt extrait : {actual_prompt[:100]}...")
    except Exception as e:
        print(f"⚠️ Erreur de lecture JSON : {e}. Utilisation du texte brut.")
        actual_prompt = prompt_json
        negative_prompt = "Blurry, low quality, distortion"

    # 2. Configuration du Matériel (GPU vs CPU)
    # Vérifie si une carte graphique NVIDIA est disponible
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    if device == "cpu":
        print("⚠️ ATTENTION : Pas de GPU détecté. La génération sera lente sur CPU.")
        dtype = torch.float32
    else:
        print(f"🚀 GPU Détecté : Utilisation de CUDA ({torch.cuda.get_device_name(0)})")
        dtype = torch.float16

    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 3. Chargement du modèle SDXL
        # Le modèle est téléchargé automatiquement la première fois (~6 Go)
        pipe = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0", 
            torch_dtype=dtype, 
            use_safetensors=True, 
            variant="fp16" if device == "cuda" else None
        )
        pipe.to(device)

        # Optimisation pour moins de mémoire (optionnel)
        # pipe.enable_model_cpu_offload() 

        # 4. Génération de l'image
        # Pour un ratio 9:16 (Story Instagram), on utilise 768x1344 pixels
        image = pipe(
            prompt=actual_prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=40,    # 40 étapes = bonne qualité
            guidance_scale=7.5,        # À quel point l'IA suit le prompt
            height=1344, 
            width=768
        ).images[0]

        # 5. Sauvegarde
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"insta_sdxl_{timestamp}.png")
        image.save(filename)
        
        print(f"✅ SUCCÈS : Image sauvegardée sous {filename}")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    # Votre prompt complet (Format JSON conservé tel quel)
    my_prompt = """{
  "lighting": {
    "source": "Direct, bright sunlight",
    "shadows": "Defined shadows are cast on the deck, the subject's body, and the yacht structure.",
    "direction": "From the upper right, creating strong highlights and deep shadows",
    "intensity": "High contrast, hard light"
  },
  "background": {
    "depth": "Considerable depth of field, with the background elements clearly distinguishable.",
    "setting": "The deck of a luxury yacht on a sunny day.",
    "elements": [
      "White fiberglass yacht structure",
      "Stainless steel railing",
      "Teak wood deck planks",
      "A white staircase on the left leading to an upper deck",
      "Vast blue sea with small waves",
      "A rocky, rugged island or coastline in the distance on the right",
      "Clear blue sky",
      "Another small boat visible on the horizon"
    ]
  },
  "typography": {
    "placement": "None",
    "font_color": "None",
    "font_style": "None",
    "text_content": "None"
  },
  "composition": {
    "focus": "Sharp focus on the subject, with a slight blur in the distant background elements.",
    "framing": "The subject is positioned on the left side of the frame, with the yacht's deck and railing leading into the distance on the right. The horizon line is visible in the upper third.",
    "shot_type": "Medium-long shot",
    "camera_angle": "Slightly low-angle, looking up at the subject"
  },
  "color_profile": {
    "mood": "Bright, sunny, and summery.",
    "accent_colors": {
      "tan": "#D2B48C",
      "gold": "#FFD700"
    },
    "color_palette": "A high-contrast palette dominated by the cool blues of the water and sky, contrasted with the stark white of the yacht and tank top, and the warm red of the bikini.",
    "dominant_colors": {
      "red": "#DC143C",
      "blue": "#0047AB",
      "brown": "#A52A2A",
      "white": "#FFFFFF"
    }
  },
  "technical_specs": {
    "medium": "Photograph",
    "resolution": "High, with sharp detail",
    "camera_type": "Digital camera",
    "aspect_ratio": "2:3 (portrait orientation)"
  },
  "subject_analysis": {
    "hair": "Dark, shoulder-length, tousled hair with sun-kissed highlights, partially covering her face.",
    "pose": "Standing, leaning slightly against the yacht railing with her right hand on her hip and left hand holding the edge of her white tank top. Her body is angled towards the left, head turned to look over her left shoulder.",
    "clothing": {
      "top": "A white, slightly sheer ribbed tank top, partially pulled up.",
      "bottom": "A red string bikini bottom with side ties.",
      "swimsuit_under": "A red bikini top is visible underneath the tank top."
    },
    "skin_tone": "Fair",
    "expression": "Thoughtful or contemplative, looking towards the distance.",
    "accessories": "A thin gold bracelet on her left wrist.",
    "main_subject": "A young woman"
  },
  "artistic_elements": {
    "style": "Candid, naturalistic photography",
    "texture": "Smooth fiberglass, ribbed tank top fabric, wet-look bikini, wooden deck, rippled water",
    "contrast": "High tonal contrast between the brightly lit areas and the shadowed sections."
  },
  "generation_parameters": {
    "prompt": "A candid photograph of a young woman with tousled dark hair, wearing a white tank top and red string bikini bottoms, leaning against the railing on the deck of a luxury yacht. She is looking over her shoulder towards a rocky island across the blue sea under a clear sky. The sunlight is bright and direct, casting defined shadows. The shot is medium-long and slightly low-angle.",
    "negative_prompt": "Blurry, grainy, artificial lighting, studio setting, text, watermark, painting, illustration, low resolution, overcast."
  }
}"""

    # Appel de la nouvelle fonction SDXL
    generate_image_sdxl(prompt_json=my_prompt)
