pipeline {
    agent any

    environment {
        IMAGE_NAME = 'chatbot_medical'
        TAG = 'v1'
        HF_TOKEN = credentials('HF_TOKEN')  // Fetch HuggingFace Token from Jenkins credentials
        PINECONE_API_KEY = credentials('pinecone_api_key')  // Fetch Pinecone API key from Jenkins credentials
        PINECONE_API_ENV = credentials('pinecone_api_env') 
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo "Code will be cloned automatically via GitHub webhook or Jenkins SCM config."
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build Docker image and pass HuggingFace token and Pinecone API key as build args
                    sh "docker build --build-arg HF_TOKEN=${HF_TOKEN} --build-arg PINECONE_API_KEY=${PINECONE_API_KEY} -t ${IMAGE_NAME}:${TAG} ."
                }
            }
        }

        stage('Run Docker Container') {
            steps {
                script {
                    // Stop and remove existing container if it exists, then run a new container with necessary environment variables
                    sh """
                        docker stop chatbot_app || true
                        docker rm chatbot_app || true
                        docker run -d --name chatbot_app -p 5000:8080 -e HF_TOKEN=${HF_TOKEN} -e PINECONE_API_KEY=${PINECONE_API_KEY} ${IMAGE_NAME}:${TAG}
                    """
                }
            }
        }
    }
}
