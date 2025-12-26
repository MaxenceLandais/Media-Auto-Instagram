import os
import datetime
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

def generate_image_locally(
    project_id: str,
    location: str,
    prompt: str,
    model_name: str = "imagegeneration@006",
    output_dir: str = "generated_images"
):
    try:
        vertexai.init(project=project_id, location=location)
        model = ImageGenerationModel.from_pretrained(model_name)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"--- GÉNÉRATION IMAGEN 3 (Local) ---")
        print(f"Ratio : 9:16 | Modèle : {model_name}")
        
        # Appel avec gestion de la sécurité pour éviter le blocage (Content Filtering)
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="9:16",
            safety_filter_level="block_only_high", # Autorise plus de flexibilité
            person_generation="allow_adult"       # Nécessaire pour des sujets adultes/mode
        )

        # Vérification robuste de la liste de réponse
        if response and len(response.images) > 0:
            img = response.images[0]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_dir, f"insta_post_{timestamp}.png")

            img.save(location=filename, include_generation_parameters=False)
            print(f"✅ SUCCÈS : Image sauvegardée sous {filename}")
        else:
            print("⚠️ L'IA n'a pas retourné d'image. Elle a probablement été filtrée par les règles de sécurité.")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    
    # Prompt légèrement ajusté pour être plus "Safe" tout en gardant l'esthétique
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

    generate_image_locally(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt
    )
