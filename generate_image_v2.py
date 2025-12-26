import os
import datetime
from google.cloud import aiplatform
from google.cloud.aiplatform_v1beta1.services.prediction_service import PredictionServiceClient

def generate_image_to_gcs(
    project_id: str,
    location: str,
    prompt: str,
    bucket_name: str,
    model_name: str = "imagegeneration@006",
    num_images: int = 1
):
    try:
        aiplatform.init(project=project_id, location=location)

        client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        client = PredictionServiceClient(client_options=client_options)

        instances_json = [{"prompt": prompt}]
        
        # Génération du nom de fichier avec timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        gcs_uri = f"gs://{bucket_name}/insta_post_{timestamp}.png"

        # Paramètres corrigés pour éviter l'erreur 400
        parameters_json = {
            "sampleCount": num_images,
            "aspect_ratio": "4:5", # Essayez avec l'underscore si le camelCase échoue
            "storageUri": gcs_uri
        }

        endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_name}"

        print(f"--- GÉNÉRATION IMAGEN 3 VERS GCS ---")
        print(f"Destination : {gcs_uri}")

        response = client.predict(
            endpoint=endpoint,
            instances=instances_json,
            parameters=parameters_json,
            timeout=120.0
        )

        # En mode GCS, on vérifie simplement s'il n'y a pas d'erreur
        if response:
            print(f"✅ SUCCÈS : Image en cours d'écriture dans le bucket.")
            print(f"🔗 URL Publique probable : https://storage.googleapis.com/{bucket_name}/insta_post_{timestamp}.png")
        else:
            print("❌ Erreur : Aucune réponse de l'API.")

    except Exception as e:
        print(f"❌ ERREUR CRITIQUE : {e}")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    BUCKET_NAME = "media-auto-instagram" # Nom de votre bucket
    
    my_prompt = """Photorealistic portrait of a woman leaning against a dark wooden bedpost, 
    right arm raised holding the post. She is wearing a black lace loungewear set with a crop top, 
    matching shorts and an open sheer floral robe. Environment is a bright bedroom with cream 
    louvered wardrobe doors and a white bed. Soft natural lighting, 85mm lens, f/2.8, 
    elegant lifestyle mood, 8k resolution, sharp focus."""

    generate_image_to_gcs(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt,
        bucket_name=BUCKET_NAME
    )
