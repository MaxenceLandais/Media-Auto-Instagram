import os
import datetime
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.preview.vision_models import ImageGenerationModel

def get_creative_scenes(project_id, location, num_scenes=5):
    """Demande à Gemini d'imaginer des scènes. Log chaque étape."""
    print(f"--- [LOG] Initialisation de Gemini ({location}) ---")
    vertexai.init(project=project_id, location=location)
    
    # Utilisation de Gemini 1.5 Flash pour la rapidité et l'inventivité
    model = GenerativeModel("gemini-2.5-flash")
    
    prompt_instruction = (
        f"Generate {num_scenes} ultra-detailed image prompts for a high-end Instagram account. "
        "Style: 'Old Money', luxury, cinematic, grand landscapes. "
        "Subjects: Young European man and/or woman, impeccably dressed, elegant. "
        "Variety: Change locations (Alps, Monaco, Tuscany), lightings (golden hour, misty morning), and activities. "
        "Important: Keep descriptions of children subtle to avoid safety filters. "
        "Return ONLY the list of prompts, one per line, no numbers, no quotes."
    )
    
    print(f"--- [LOG] Envoi de la requête créative à Gemini ---")
    try:
        response = model.generate_content(prompt_instruction)
        prompts = [p.strip() for p in response.text.split('\n') if len(p.strip()) > 20]
        
        print(f"--- [LOG] Gemini a généré {len(prompts)} prompts avec succès ---")
        for i, p in enumerate(prompts):
            print(f"    Détail Prompt {i+1}: {p[:80]}...")
            
        return prompts[:num_scenes]
    except Exception as e:
        print(f"--- [ERREUR] Échec de Gemini : {e} ---")
        return []

def generate_session(project_id, location, model_name="imagen-4.0-ultra-generate-001"):
    print(f"\n=== DÉBUT DE LA SESSION DE GÉNÉRATION ===")
    print(f"Heure : {datetime.datetime.now()}")
    
    try:
        vertexai.init(project=project_id, location=location)
        image_model = ImageGenerationModel.from_pretrained(model_name)

        # Création du dossier de session
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_folder = f"session_{timestamp}"
        output_dir = os.path.join("generated_images", session_folder)
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"--- [LOG] Dossier créé : {output_dir} ---")

        # Récupération des idées
        scenes = get_creative_scenes(project_id, location)
        if not scenes:
            print("--- [ERREUR] Aucune scène à générer. Arrêt. ---")
            return

        success_count = 0
        
        # Boucle de génération
        for i, scene_prompt in enumerate(scenes):
            index = i + 1
            print(f"\n--- [IMAGE {index}/5] Lancement ---")
            
            try:
                # Ajout de contraintes esthétiques fixes pour la cohérence
                final_prompt = f"{scene_prompt}, cinematic lighting, shot on 35mm lens, f/1.8, elegant atmosphere, highly detailed textures."
                
                response = image_model.generate_images(
                    prompt=final_prompt,
                    number_of_images=1,
                    aspect_ratio="9:16",
                    safety_filter_level="block_only_high",
                    person_generation="allow_adult"
                )

                if response and response.images and len(response.images) > 0:
                    filename = os.path.join(output_dir, f"scene_{index}.png")
                    response.images[0].save(location=filename, include_generation_parameters=False)
                    print(f"--- [SUCCÈS] Image {index} sauvegardée sous {filename} ---")
                    success_count += 1
                else:
                    print(f"--- [WARNING] L'API n'a retourné aucune image pour la scène {index} (Filtre de sécurité probable) ---")
            
            except Exception as e:
                print(f"--- [ERREUR] Erreur technique sur l'image {index} : {e} ---")
                continue

        print(f"\n=== RÉSUMÉ DE SESSION ===")
        print(f"Images réussies : {success_count}/{len(scenes)}")
        print(f"Dossier final : {output_dir}")
        print(f"===========================\n")

    except Exception as e:
        print(f"--- [ERREUR CRITIQUE] La session a échoué : {e} ---")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram"
    LOCATION = "us-central1"
    generate_session(PROJECT_ID, LOCATION)
