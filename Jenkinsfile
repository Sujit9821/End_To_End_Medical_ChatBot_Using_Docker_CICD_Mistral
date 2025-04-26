pipeline {
    agent any

    environment {
        IMAGE_NAME = 'medical_chatbot'
        TAG = 'v1'
        HF_TOKEN = credentials('HF_TOKEN')  // Fetch HuggingFace Token from Jenkins credentials
        PINECONE_API_KEY = credentials('PINECONE_API_KEY')  // Fetch Pinecone API key from Jenkins credentials
        PINECONE_API_ENV = credentials('PINECONE_API_ENV') 
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
                        docker stop medical_chatbot:v_1.0.0 || true
                        docker rm medical_chatbot:v_1.0.0 || true
                        docker run -d --name medical_chatbot:v_1.0.0 -p 5000:8080 -e HF_TOKEN=${HF_TOKEN} -e PINECONE_API_KEY=${PINECONE_API_KEY} ${IMAGE_NAME}:${TAG}
                    """
                }
            }
        }
    }
}
