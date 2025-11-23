import base64
import os
import datetime
from google.cloud import aiplatform

# --- NOUVEAUX IMPORTS POUR L'API DE PRÉDICTION ---
# C'est la manière générique et stable d'interagir avec les modèles de fondation
# en utilisant les clients GAPIC (Google API Client Libraries).
from google.cloud.aiplatform_v1beta1.services.prediction_service import PredictionServiceClient
from google.cloud.aiplatform_v1beta1.types import PredictRequest, Value
# --- FIN NOUVEAUX IMPORTS ---


def generate_image_with_vertex_ai(
    project_id: str,
    location: str,
    prompt: str,
    model_name: str = "imagegeneration", # Nom du modèle de Google Publisher
    output_dir: str = "generated_images",
    num_images: int = 1,
    image_width: int = 1024,
    image_height: int = 1024,
    mime_type: str = "image/png"
):
    """
    Génère une ou plusieurs images en utilisant l'API Vertex AI via PredictionServiceClient.
    """
    try:
        # Initialisation du client aiplatform pour la configuration globale (projet, région)
        aiplatform.init(project=project_id, location=location)

        # Configuration du client de prédiction pour interagir avec le modèle spécifique
        client_options = {"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        client = PredictionServiceClient(client_options=client_options)

        # Préparation des instances (le prompt pour la génération d'images)
        # Chaque instance est un dictionnaire avec la clé "prompt".
        instances_proto = [
            Value(struct_value={"prompt": prompt})._pb
        ]
        
        # Préparation des paramètres de génération (nombre d'images, taille, etc.)
        parameters_proto = Value(struct_value={
            "sample_count": num_images,
            "width": image_width,
            "height": image_height,
            # "seed": 42 # Optionnel: pour la reproductibilité (décommenter si vous voulez un seed fixe)
        })._pb

        # Définition de l'endpoint du modèle de fondation (Publisher Model)
        # publishers/google/models/imagegeneration est le chemin standard.
        endpoint = f"projects/{project_id}/locations/{location}/publishers/google/models/{model_name}"

        print(f"Tentative de génération de {num_images} image(s) avec le prompt: '{prompt}' via l'endpoint '{endpoint}'...")

        # Appel à l'API de prédiction
        response = client.predict(
            endpoint=endpoint,
            instances=instances_proto,
            parameters=parameters_proto
        )

        # Création du répertoire de sortie si nécessaire
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Répertoire '{output_dir}' créé.")

        # Traitement de la réponse et sauvegarde des images
        if response and response.predictions:
            for i, prediction_value in enumerate(response.predictions):
                # Chaque prédiction est un objet Value contenant un dictionnaire struct_value
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
        print("1. **Permissions:** Le compte de service ('media-upload-key') doit avoir le rôle 'Utilisateur Vertex AI' (ou 'Generative AI User').")
        print("2. **Authentification:** La variable d'environnement GOOGLE_APPLICATION_CREDENTIALS doit pointer vers la clé JSON encodée en base64.")
        print("3. **Nom du Modèle:** 'imagegeneration' est le nom correct pour le modèle de Google Publisher.")
        print("4. **Région:** 'us-central1' est la région recommandée et où le modèle est le plus souvent disponible.")
        print("5. **Quotas:** Vérifiez les quotas pour l'API de génération d'images dans votre projet GCP.")

if __name__ == "__main__":
    # --- CONFIGURATION PRINCIPALE ---
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1" 
    my_prompt = "Un portrait d'un robot détective dans un style cyberpunk, éclairage néon, haute résolution."

    # --- APPEL DE LA FONCTION ---
    generate_image_with_vertex_ai(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt,
        model_name="imagegeneration", # Utilisez bien "imagegeneration" ici
        num_images=1,
        image_width=1024,
        image_height=1024,
        mime_type="image/png"
    )
