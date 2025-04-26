pipeline {
    agent any

    environment {
        IMAGE_NAME = 'medical_chatbot'
        BASE_TAG = 'v1'
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
                echo "🔄 Cloning repository..."
            }
        }

        stage('Generate Dynamic Tag') {
            steps {
                script {
                    def date = new Date().format("yyyyMMdd-HHmm")
                    env.DYNAMIC_TAG = "${BASE_TAG}-${date}"
                    echo "🆕 Dynamic Tag Generated: ${DYNAMIC_TAG}"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "🐳 Building Docker image: ${IMAGE_NAME}:${DYNAMIC_TAG}"
                script {
                    sh """
                    docker build \\
                        --build-arg HF_TOKEN=${HF_TOKEN} \\
                        --build-arg PINECONE_API_KEY=${PINECONE_API_KEY} \\
                        -t ${IMAGE_NAME}:${DYNAMIC_TAG} .
                    """
                }
            }
        }

        stage('Stop & Remove Old Container') {
            steps {
                echo "🧹 Cleaning up old container if exists."
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
                echo "🛠️ Checking if port ${EXTERNAL_PORT} is free..."
                script {
                    sh """
                    if lsof -i :${EXTERNAL_PORT}; then
                        echo "⚡ Port ${EXTERNAL_PORT} is occupied. Killing..."
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
                echo "🚀 Running Docker container from image: ${IMAGE_NAME}:${DYNAMIC_TAG}"
                script {
                    sh """
                    docker run -d \\
                        --name ${CONTAINER_NAME} \\
                        -p ${EXTERNAL_PORT}:${INTERNAL_PORT} \\
                        -e HF_TOKEN=${HF_TOKEN} \\
                        -e PINECONE_API_KEY=${PINECONE_API_KEY} \\
                        -e PINECONE_API_ENV=${PINECONE_API_ENV} \\
                        ${IMAGE_NAME}:${DYNAMIC_TAG}
                    """
                }
            }
        }

        stage('Health Check') {
            steps {
                echo "🔍 Checking if FastAPI app is live"
                script {
                    sleep 10
                    sh """
                    if curl -f http://localhost:${EXTERNAL_PORT}/docs; then
                        echo '✅ FastAPI app running!'
                    else
                        echo '⚠️ App might not be ready yet.'
                    fi
                    """
                }
            }
        }
    }

    post {
        always {
            echo "📋 Fetching Docker container logs before cleanup."
            script {
                sh "docker logs ${CONTAINER_NAME} || echo '⚠️ Could not fetch logs (container may have exited)'"
            }

            echo "🎯 Stopping and cleaning container."
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
            echo "❌ Build failed. Check logs carefully."
        }
    }
}
