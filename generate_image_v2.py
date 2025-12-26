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
        # Initialisation sans import de types complexes
        aiplatform.init(project=project_id, location=location)

        client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        client = PredictionServiceClient(client_options=client_options)

        instances = [{"prompt": prompt}]
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Imagen 3 attend un dossier ou un préfixe URI pour storageUri
        gcs_uri_prefix = f"gs://{bucket_name}/insta_post_{timestamp}"

        # Paramètres avec dimensions explicites pour le format 4:5
        parameters = {
            "sampleCount": num_images,
            "width": 896,
            "height": 1120,
            "storageUri": gcs_uri_prefix 
        }

        endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_name}"

        print(f"--- GÉNÉRATION IMAGEN 3 VERS GCS ---")
        print(f"Destination : {gcs_uri_prefix}")

        # Appel de l'API
        response = client.predict(
            endpoint=endpoint,
            instances=instances,
            parameters=parameters,
            timeout=150.0 # Un peu plus de temps pour l'écriture sur GCS
        )

        # Une réponse réussie sur Vertex AI n'est pas None
        if response:
            print(f"✅ APPEL TERMINÉ")
            print(f"Vérifiez les fichiers commençant par : insta_post_{timestamp}")
            print(f"Lien GCS : https://console.cloud.google.com/storage/browser/{bucket_name}")
        else:
            print("❌ L'API a renvoyé une réponse vide.")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    # Configuration
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    BUCKET_NAME = "media-auto-instagram"
    
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
