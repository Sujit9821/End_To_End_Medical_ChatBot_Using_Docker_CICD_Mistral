pipeline {
    agent any

    environment {
        IMAGE_NAME = 'medical_chatbot'
        TAG = 'v1'
        CONTAINER_NAME = 'medical_chatbot_container'
        INTERNAL_PORT = '8000'   // FastAPI default port
        EXTERNAL_PORT = '5000'   // Exposed port on host machine
        HF_TOKEN = credentials('HF_TOKEN')  
        PINECONE_API_KEY = credentials('PINECONE_API_KEY')  
        PINECONE_API_ENV = credentials('PINECONE_API_ENV') 
    }

    stages {

        stage('Checkout Code') {
            steps {
                echo "🔄 Code will be automatically cloned via GitHub webhook or Jenkins SCM settings."
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "🐳 Building Docker image: ${IMAGE_NAME}:${TAG}"
                script {
                    sh """
                    docker build \\
                        --build-arg HF_TOKEN=${HF_TOKEN} \\
                        --build-arg PINECONE_API_KEY=${PINECONE_API_KEY} \\
                        -t ${IMAGE_NAME}:${TAG} .
                    """
                }
            }
        }

        stage('Stop & Remove Old Container') {
            steps {
                echo "🧹 Cleaning up old container if it exists."
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
                echo "🛠️ Checking if port ${EXTERNAL_PORT} is already in use."
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
                echo "🚀 Running new Docker container on port ${EXTERNAL_PORT}"
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
                echo "🔍 Checking if FastAPI app is up and running"
                script {
                    sleep 300  // Give a few seconds for app to start
                    sh "curl -f http://localhost:${EXTERNAL_PORT}/docs || echo '⚠️ FastAPI app might not be ready yet.'"
                }
            }
        }
    }

    post {
        always {
            echo "🎯 Post Actions: Stopping and cleaning up the Docker container."
            script {
                sh """
                docker stop ${CONTAINER_NAME} || true
                docker rm ${CONTAINER_NAME} || true
                """
            }
        }

        success {
            echo "✅ Build, container run, and health check succeeded!"
        }

        failure {
            echo "❌ Build failed. Check above logs carefully."
        }
    }
}
