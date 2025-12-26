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
    image_width: int = 512,
    image_height: int = 512,
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
        }

        endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_name}"

        print(f"Tentative de génération de {num_images} image(s) ({image_width}x{image_height}) avec le prompt: '{prompt}' via l'endpoint '{endpoint}'...")

        response = client.predict(
            endpoint=endpoint,
            instances=instances_json,
            parameters=parameters_json,
            timeout=60.0
        )

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Répertoire '{output_dir}' créé.")

        # --- CHANGEMENT CLÉ ICI : ACCÈS À LA PRÉDICTION ---
        if response and response.predictions:
            for i, prediction_value_object in enumerate(response.predictions):
                # Convertir l'objet Value ou MapComposite en dictionnaire Python
                # Cela garantit que nous pouvons accéder aux clés comme un dict normal.
                prediction_dict = {}
                if hasattr(prediction_value_object, 'struct_value'): # Cas typique de Value
                    prediction_dict = prediction_value_object.struct_value
                elif hasattr(prediction_value_object, 'fields'): # Autre structure possible pour MapComposite
                    # Il faut reconstruire le dict à partir des champs
                    prediction_dict = {key: getattr(value, 'string_value', None) or \
                                            getattr(value, 'number_value', None) or \
                                            getattr(value, 'bool_value', None) or \
                                            getattr(value, 'struct_value', None) or \
                                            getattr(value, 'list_value', None) \
                                            for key, value in prediction_value_object.fields.items()}
                else: # Cas le plus simple si l'objet est déjà un dict-like ou directement le contenu
                    # Tenter de convertir directement si ce n'est pas un proto object
                    try:
                        prediction_dict = dict(prediction_value_object) 
                    except TypeError:
                        print(f"Avertissement: Impossible de convertir l'objet de prédiction {i+1} en dictionnaire.")
                        continue # Passer à la prédiction suivante
                
                # Maintenant, nous pouvons accéder à 'bytesBase64Encoded'
                if "bytesBase64Encoded" in prediction_dict:
                    image_bytes = base64.b64decode(prediction_dict["bytesBase64Encoded"])
                    
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(output_dir, f"generated_image_{timestamp}_{i+1}.{mime_type.split('/')[-1]}")

                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    print(f"Image {i+1} générée et sauvegardée sous {filename}")
                else:
                    print(f"Avertissement: La prédiction {i+1} ne contient pas de données d'image valides. Contenu: {prediction_dict}")
        else:
            print("Aucune prédiction d'image reçue de l'API Vertex AI.")

    except Exception as e:
        print(f"ERREUR: Une erreur est survenue lors de la génération d'images: {e}")
        print("\nPoints à vérifier impérativement:")
        print("1. **Permissions:** Le compte de service a les rôles nécessaires (Administrateur Vertex AI). (Confirmé)")
        print("2. **Authentification:** La variable GOOGLE_APPLICATION_CREDENTIALS est correctement définie. (Confirmé)")
        print("3. **Nom du Modèle:** 'imagegeneration' est le nom correct.")
        print("4. **Région:** 'us-central1' est utilisée. (Confirmé)")
        print("5. **Quotas:** Le quota est bon. (Confirmé)")
        print("6. **Logs Vertex AI:** Consultez l'explorateur de journaux pour plus de détails sur la réponse API.")

if __name__ == "__main__":
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1"
    my_prompt = "{
  "image_generation_prompt": {
    "subject_details": {
      "main_subject": "Woman",
      "reference_adherence": "Reference face and body 100% match",
      "pose": "Leaning against dark wooden bedpost, right arm raised holding the post"
    },
    "apparel": {
      "type": "Black lace loungewear set",
      "components": [
        "Solid black crop top",
        "Matching shorts",
        "Open sheer floral robe"
      ],
      "accessories": "Minimal jewelry"
    },
    "environment": {
      "location": "Bright bedroom",
      "furniture_and_decor": [
        "Dark wooden bedpost",
        "Cream louvered wardrobe doors",
        "White bed",
        "Wood floor"
      ]
    },
    "technical_specs": {
      "resolution": "8K",
      "style": "Photorealistic portrait",
      "lighting": "Soft natural lighting",
      "camera_settings": "85mm lens, f/2.8 aperture",
      "focus": "Sharp focus"
    },
    "artistic_direction": {
      "mood": "Elegant lifestyle"
    },
    "parameters": {
      "aspect_ratio": "--ar 3:4"
    }
  }
}"

    generate_image_with_vertex_ai(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt,
        model_name="imagegeneration",
        num_images=1,
        image_width=512,
        image_height=512,
        mime_type="image/png"
    )
