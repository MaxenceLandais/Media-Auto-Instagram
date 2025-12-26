import base64
import os
import datetime
from google.cloud import aiplatform

# --- IMPORTS POUR L'API DE PRÉDICTION ---
from google.cloud.aiplatform_v1beta1.services.prediction_service import PredictionServiceClient
from google.cloud.aiplatform_v1beta1.types import Value 

def generate_image_for_instagram(
    project_id: str,
    location: str,
    prompt: str,
    model_name: str = "imagegeneration@006", # Utilisation d'Imagen 3 Fast
    output_dir: str = "instagram_posts",
    num_images: int = 1,
    # Dimensions optimisées pour le format Portrait Instagram (4:5)
    image_width: int = 896, 
    image_height: int = 1120,
    mime_type: str = "image/png"
):
    """
    Génère une image optimisée pour Instagram en utilisant Imagen 3.
    """
    try:
        aiplatform.init(project=project_id, location=location)

        client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        client = PredictionServiceClient(client_options=client_options)

        # Structure de l'instance pour Imagen 3
        instances_json = [{"prompt": prompt}]
        
        # Paramètres de génération
        parameters_json = {
            "sampleCount": num_images,
            "aspectRatio": "4:5", # Précise explicitement le ratio pour Imagen 3
            "storageUri": "" # Laisser vide pour recevoir les bytes directement
        }

        endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_name}"

        print(f"--- GÉNÉRATION IMAGEN 3 ---")
        print(f"Prompt: {prompt[:50]}...")
        print(f"Format: Instagram Portrait ({image_width}x{image_height})")

        response = client.predict(
            endpoint=endpoint,
            instances=instances_json,
            parameters=parameters_json,
            timeout=120.0 # Augmentation du timeout pour Imagen 3
        )

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if response and response.predictions:
            for i, prediction_value_object in enumerate(response.predictions):
                # Extraction des données via le dictionnaire de prédiction
                # Le format de réponse de Vertex AI peut varier selon le SDK, on sécurise l'accès
                prediction_dict = dict(prediction_value_object)
                
                if "bytesBase64Encoded" in prediction_dict:
                    image_bytes = base64.b64decode(prediction_dict["bytesBase64Encoded"])
                    
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(output_dir, f"insta_post_{timestamp}_{i+1}.png")

                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    print(f"✅ SUCCÈS: Image sauvegardée dans {filename}")
                else:
                    print(f"⚠️ Erreur: Pas de données base64 dans la prédiction {i+1}")
        else:
            print("❌ Erreur: Aucune réponse de l'API.")

    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    
    # Prompt optimisé (le JSON est passé en texte brut, Imagen 3 le comprendra très bien)
    my_prompt = """Photorealistic portrait of a woman leaning against a dark wooden bedpost, 
    right arm raised holding the post. She is wearing a black lace loungewear set with a crop top, 
    matching shorts and an open sheer floral robe. Environment is a bright bedroom with cream 
    louvered wardrobe doors and a white bed. Soft natural lighting, 85mm lens, f/2.8, 
    elegant lifestyle mood, 8k resolution, sharp focus."""

    generate_image_for_instagram(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt
    )
