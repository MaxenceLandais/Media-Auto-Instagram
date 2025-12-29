import base64
import os
import datetime
from google.cloud import aiplatform
from google.cloud.aiplatform_v1beta1.services.prediction_service import PredictionServiceClient
from google.cloud.aiplatform_v1beta1.types import Value 

def generate_image_with_vertex_ai(
    project_id: str,
    location: str,
    prompt: str,
    model_name: str = "imagegeneration@006", # Utilisation de la version la plus récente (Imagen 3)
    output_dir: str = "generated_images",
    num_images: int = 1,
    mime_type: str = "image/png"
):
    try:
        aiplatform.init(project=project_id, location=location)
        client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        client = PredictionServiceClient(client_options=client_options)

        # 1. Nettoyage du prompt (on retire les tags Midjourney pour éviter de confondre Imagen)
        clean_prompt = prompt.replace("--ar 9:16", "").replace("--v 5", "").strip()

        instances_json = [{"prompt": clean_prompt}]
        
        # 2. Paramétrage du format 9:16 pour Instagram
        # Note : Pour Imagen sur Vertex AI, on utilise "aspectRatio": "9:16"
        parameters_json = {
            "sampleCount": num_images,
            "aspectRatio": "9:16", 
            "personGeneration": "allow_all" # Important pour voir le couple
        }

        endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_name}"

        print(f"Génération au format 9:16 avec le prompt: '{clean_prompt}'...")

        response = client.predict(
            endpoint=endpoint,
            instances=instances_json,
            parameters=parameters_json,
            timeout=60.0
        )

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if response and response.predictions:
            for i, prediction_value_object in enumerate(response.predictions):
                # Extraction des données base64
                # Selon la version de l'API, la structure peut varier légèrement
                pred = dict(prediction_value_object)
                
                if "bytesBase64Encoded" in pred:
                    image_bytes = base64.b64decode(pred["bytesBase64Encoded"])
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(output_dir, f"insta_916_{timestamp}_{i+1}.png")

                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    print(f"✅ Image Instagram sauvegardée : {filename}")
        else:
            print("Aucune image générée.")

    except Exception as e:
        print(f"ERREUR: {e}")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    
    # Prompt optimisé pour Google Imagen
    my_prompt = "Rear view of a young couple driving in a classic black 1960s Ford Thunderbird convertible along a coastal road at sunset, ocean on the left, clear sky, woman in passenger seat with long blonde hair raising both arms in joy and freedom, man driving wearing sunglasses, cinematic aesthetic, high detail, photorealistic, soft lighting"

    generate_image_with_vertex_ai(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt,
        model_name="imagegeneration@006" # Version supportant mieux les différents ratios
    )
