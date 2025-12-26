import os
import datetime
from google.cloud import aiplatform
from google.cloud.aiplatform_v1beta1.services.prediction_service import PredictionServiceClient
from google.cloud.aiplatform_v1beta1.types import PredictionServiceResponse

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
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Note : Imagen 3 gère souvent le storageUri comme un dossier ou un préfixe
        gcs_uri_prefix = f"gs://{bucket_name}/insta_post_{timestamp}"

        # Utilisation de width/height pour éviter l'erreur "Invalid aspect ratio"
        parameters_json = {
            "sampleCount": num_images,
            "width": 896,
            "height": 1120,
            "storageUri": gcs_uri_prefix 
        }

        endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_name}"

        print(f"--- GÉNÉRATION IMAGEN 3 VERS GCS ---")
        print(f"Destination préfixe : {gcs_uri_prefix}")

        response = client.predict(
            endpoint=endpoint,
            instances=instances_json,
            parameters=parameters_json,
            timeout=120.0
        )

        # Correction de la vérification de réponse
        if response:
            print(f"✅ APPEL RÉUSSI : Le processus de génération est terminé.")
            # En mode GCS, l'API peut renvoyer un objet vide mais un code 200 OK.
            print(f"Vérifiez votre bucket ici : https://console.cloud.google.com/storage/browser/{bucket_name}")
            print(f"URL publique estimée : https://storage.googleapis.com/{bucket_name}/insta_post_{timestamp}_1.png")
        else:
            print("❌ Erreur : L'API a renvoyé une réponse vide.")

    except Exception as e:
        print(f"❌ ERREUR CRITIQUE : {e}")

if __name__ == "__main__":
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
