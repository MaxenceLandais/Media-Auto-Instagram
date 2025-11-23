import base64
import os
import datetime
from google.cloud import aiplatform

def generate_image_with_vertex_ai(
    project_id: str,
    location: str,
    prompt: str,
    model_name: str = "imagegeneration@latest",
    output_dir: str = "generated_images",
    num_images: int = 1,
    image_width: int = 1024,
    image_height: int = 1024,
    mime_type: str = "image/png"
):
    """
    Génère une ou plusieurs images en utilisant l'API Vertex AI.
    """
    try:
        # Initialisation du client Vertex AI
        # L'authentification se fait via la variable d'environnement 
        # GOOGLE_APPLICATION_CREDENTIALS que le workflow YAML a définie.
        aiplatform.init(project=project_id, location=location)

        # Chargement du modèle
        model = aiplatform.ImageGenerationModel.from_pretrained(model_name)

        # Préparation des instances pour la requête
        instances = [
            {
                "prompt": prompt,
                "sampleCount": num_images,
                "mimeType": mime_type,
                "width": image_width,
                "height": image_height
            },
        ]

        print(f"Tentative de génération de {num_images} image(s) avec le prompt: '{prompt}'...")

        # Envoi de la requête
        response = model.generate_images(instances=instances)

        # Création du répertoire de sortie
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Répertoire '{output_dir}' créé.")

        # Traitement de la réponse et sauvegarde des images
        if response and response.predictions:
            for i, prediction in enumerate(response.predictions):
                if "bytesBase64Encoded" in prediction:
                    image_bytes = base64.b64decode(prediction["bytesBase64Encoded"])
                    
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(output_dir, f"generated_image_{timestamp}_{i+1}.{mime_type.split('/')[-1]}")

                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    print(f"Image {i+1} générée et sauvegardée sous {filename}")
                else:
                    print(f"Avertissement: La prédiction {i+1} ne contient pas de données d'image valides.")

    except Exception as e:
        print(f"ERREUR: Une erreur est survenue lors de la génération d'images: {e}")

if __name__ == "__main__":
    # --- CONFIGURATION À PARTIR DE VOS INFOS ---
    PROJECT_ID = "media-auto-instagram" 
    LOCATION = "us-central1" # Région la plus stable pour l'IA générative

    # --- PROMPT À PERSONNALISER ---
    my_prompt = "Une photo réaliste et magnifique d'une Tour Eiffel illuminée, prise depuis les toits de Paris au lever du soleil."

    # --- APPEL DE LA FONCTION PRINCIPALE ---
    generate_image_with_vertex_ai(
        project_id=PROJECT_ID,
        location=LOCATION,
        prompt=my_prompt,
        num_images=1,
        image_width=1024,
        image_height=1024,
        mime_type="image/png"
    )
