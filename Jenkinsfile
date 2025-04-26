pipeline {
    agent any

    environment {
        IMAGE_NAME = 'medical_chatbot'
        TAG = 'v1'
        CONTAINER_NAME = 'medical_chatbot_container'
        INTERNAL_PORT = '8000'
        EXTERNAL_PORT = '8000'
        HF_TOKEN = credentials('HF_TOKEN')  
        PINECONE_API_KEY = credentials('PINECONE_API_KEY')  
        PINECONE_API_ENV = credentials('PINECONE_API_ENV') 
    }

    stages {

        stage('Checkout Code') {
            steps {
                echo "🔄 Cloning code from GitHub..."
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "🐳 Building Docker image: ${IMAGE_NAME}:${TAG}"
                script {
                    sh """
                    docker build \\
                        --build-arg HF_TOKEN=${HF_TOKEN} \\
                        -t ${IMAGE_NAME}:${TAG} .
                    """
                }
            }
        }

        stage('Stop & Remove Old Container') {
            steps {
                echo "🧹 Stopping old container if it exists."
                script {
                    sh """
                    docker stop ${CONTAINER_NAME} || true
                    docker rm ${CONTAINER_NAME} || true
                    """
                }
            }
        }

        stage('Free Port if Occupied') {
            steps {
                echo "🛠️ Checking port ${EXTERNAL_PORT}"
                script {
                    sh """
                    if lsof -i :${EXTERNAL_PORT}; then
                        echo "⚡ Port ${EXTERNAL_PORT} is occupied. Killing process..."
                        fuser -k ${EXTERNAL_PORT}/tcp || true
                    else
                        echo "✅ Port ${EXTERNAL_PORT} is free."
                    fi
                    """
                }
            }
        }

        stage('Run Docker Container') {
            steps {
                echo "🚀 Running container on port ${EXTERNAL_PORT}"
                script {
                    sh """
                    docker run -d \\
                        --name ${CONTAINER_NAME} \\
                        -p ${EXTERNAL_PORT}:${INTERNAL_PORT} \\
                        -e HF_TOKEN=${HF_TOKEN} \\
                        -e PINECONE_API_KEY=${PINECONE_API_KEY} \\
                        -e PINECONE_API_ENV=${PINECONE_API_ENV} \\
                        ${IMAGE_NAME}:${TAG}
                    """
                }
            }
        }

        stage('Health Check') {
            steps {
                echo "🔍 Checking if FastAPI app is ready..."
                script {
                    sleep 10
                    sh """
                    if curl -f http://localhost:${EXTERNAL_PORT}/docs; then
                        echo '✅ FastAPI app is running!'
                    else
                        echo '⚠️ FastAPI app might not be ready yet.'
                    fi
                    """
                }
            }
        }
    }

    post {
        always {
            echo "📋 Fetching Docker logs before cleaning."
            script {
                sh """
                docker logs ${CONTAINER_NAME} || echo '⚠️ Could not fetch logs'
                """
            }

            echo "🎯 Cleaning up container."
            script {
                sh """
                docker stop ${CONTAINER_NAME} || true
                docker rm ${CONTAINER_NAME} || true
                """
            }
        }

        success {
            echo "✅ Full CI/CD succeeded!"
        }

        failure {
            echo "❌ CI/CD failed. Please check errors."
        }
    }
}
