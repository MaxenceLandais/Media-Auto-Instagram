import os
import datetime
import fal_client # La nouvelle bibliothèque
import requests

OUTPUT_DIR = "generated_images"

def generate_flux_image(prompt_text):
    print(f"🚀 Génération Pro avec FLUX.1 [dev] via Fal.ai...")
    
    # On définit les paramètres de haute qualité
    # Plus besoin de '8k' ou 'masterpiece', le modèle est déjà entraîné pour ça
    arguments = {
        "prompt": prompt_text,
        "image_size": "portrait_4_5", # Format idéal pour Instagram
        "num_inference_steps": 28,     # Équilibre parfait entre vitesse et détail
        "guidance_scale": 3.5,
        "enable_safety_checker": True
    }

    try:
        # Appel à l'API Fal
        result = fal_client.subscribe("fal-ai/flux/dev", arguments=arguments)
        
        image_url = result['images'][0]['url']
        
        # Téléchargement de l'image finale
        response = requests.get(image_url)
        if response.status_code == 200:
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)
                
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(OUTPUT_DIR, f"insta_flux_{timestamp}.png")
            
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"✅ SUCCÈS : Image Pro sauvegardée dans {filename}")
        
    except Exception as e:
        print(f"❌ Erreur avec Fal.ai : {e}")

if __name__ == "__main__":
    # Prompt de haut niveau (style Maria Rubtsova)
    my_prompt = """
    Cinematic fashion photography of a young woman with dark hair, 
    wearing a high-quality white tank top and red bikini, 
    standing on a luxury yacht deck at sunset. 
    Golden hour lighting, soft shadows, realistic skin texture (pores visible), 
    sharp focus on eyes, 35mm lens, high-end commercial aesthetic.
    """
    
    generate_flux_image(my_prompt)
