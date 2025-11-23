import base64
import os
import datetime
from google.cloud import aiplatform

# --- IMPORTS POUR L'API DE PRÉDICTION ---
from google.cloud.aiplatform_v1beta1.services.prediction_service import PredictionServiceClient
from google.cloud.aiplatform_v1beta1.types import Value 


def generate_image_with_vertex_ai(
    project_id: str,
    location: str,
    prompt: str,
    model_name: str = "imagegeneration",
    output_dir: str = "generated_images",
    num_images: int = 1,
    image_width: int = 512,  # CHANGEMENT: Taille réduite
    image_height: int = 512, # CHANGEMENT: Taille réduite
    mime_type: str = "image/png"
):
    """
    Génère une ou plusieurs images en utilisant l'API Vertex AI via PredictionServiceClient.
    """
    try:
        aiplatform.init(project=project_id, location=location)

        client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        client = PredictionServiceClient(client_options=client_options)

        instances_json = [{"prompt": prompt}]
        
        parameters_json = {
            "sample_count": num_images,
            "width": image_width,
            "height": image_height,
            # "seed": 42 # Optionnel: pour la reproductibilité
        }

        endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_name}"

        print(f"Tentative de génération de {num_images} image(s) ({image_width}x{image_height}) avec le prompt: '{prompt}' via l'endpoint '{endpoint}'...")

        response = client.predict(
            endpoint=endpoint,
            instances=instances_json,
            parameters=parameters_json
        )

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Répertoire '{output_dir}' créé.")

        if response and response.predictions:
            for i, prediction_value in enumerate(response.predictions):
                prediction_dict = prediction_value.struct_value
                if "bytesBase64Encoded" in prediction_dict:
                    image_bytes = base64.b64decode(prediction_dict["bytesBase64Encoded"])
                    
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(output_dir, f"generated_image_{timestamp}_{i+1}.{mime_type.split('/')[-1]}")

                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    print(f"Image {i+1} générée et sauvegardée sous {filename}")
                else:
                    print(f"Avertissement: La prédiction {i+1} ne contient pas de données d'image valides.")
                    if "error" in prediction_dict:
                        print(f"Détails de l'erreur pour la prédiction {i+1}: {prediction_dict['error']}")
        else:
            print("Aucune prédiction d'image reçue de l'API Vertex AI.")

    except Exception as e:
        print(f"ERREUR: Une erreur est survenue lors de la génération d'images: {e}")
        print("\nPoints à vérifier impérativement:")
        print("1. **Permissions:** Le compte de service ('media-upload-key') doit avoir le rôle 'Utilisateur Vertex AI' (ou 'Generative AI User'). (Vous avez déjà confirmé cela)")
        print("2. **Authentification:** La variable d'environnement GOOGLE_APPLICATION_CREDENTIALS doit être correctement définie et pointer vers la clé JSON.")
        print("3. **Nom du Modèle:** 'imagegeneration' est le nom correct pour le modèle de Google Publisher.")
        print("4. **Région:** 'us-central1' est la région recommandée et où le modèle est le plus souvent disponible.")
        print("5. **Quotas:** Vérifiez les quotas pour l'API de génération d'images dans votre projet GCP. Un '504 Deadline Exceeded' peut masquer un problème de quota ou de capacité temporaire.")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1" 
    # CHANGEMENT: Prompt plus simple
    my_prompt = "Un petit chaton joueur sur une pelouse ensoleillée, style dessin animé."

    generate_image_with_vertex_ai(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt,
        model_name="imagegeneration",
        num_images=1,
        image_width=512,  # CHANGEMENT
        image_height=512, # CHANGEMENT
        mime_type="image/png"
    )
