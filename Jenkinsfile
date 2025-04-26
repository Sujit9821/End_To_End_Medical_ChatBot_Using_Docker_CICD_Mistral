pipeline {
  agent any

  environment {
    IMAGE_NAME      = 'medical_chatbot'
    BASE_TAG        = 'v1'
    CONTAINER_NAME  = 'medical_chatbot_container'
    INTERNAL_PORT   = '8000'
    EXTERNAL_PORT   = '8000'
    HF_TOKEN        = credentials('HF_TOKEN')
    PINECONE_API_KEY= credentials('PINECONE_API_KEY')
    PINECONE_API_ENV= credentials('PINECONE_API_ENV')
  }

  stages {
    stage('Checkout Code') {
      steps {
        echo "🔄 Cloning repository..."
        checkout scm
      }
    }

    stage('Generate Dynamic Tag') {
      steps {
        script {
          def date = new Date().format("yyyyMMdd-HHmm")
          env.DYNAMIC_TAG = "${BASE_TAG}-${date}"
          echo "🆕 Dynamic Tag: ${DYNAMIC_TAG}"
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        echo "🐳 Building Docker image..."
        sh """
          docker build \
            --build-arg HF_TOKEN=${HF_TOKEN} \
            --build-arg PINECONE_API_KEY=${PINECONE_API_KEY} \
            -t ${IMAGE_NAME}:${DYNAMIC_TAG} .
        """
      }
    }

    stage('Cleanup Old Container') {
      steps {
        echo "🧹 Removing old container..."
        sh """
          docker stop ${CONTAINER_NAME} || true
          docker rm   ${CONTAINER_NAME} || true
        """
      }
    }

    stage('Free Port if Occupied') {
      steps {
        echo "🛠️ Freeing port ${EXTERNAL_PORT} if needed..."
        sh """
          if lsof -i :${EXTERNAL_PORT}; then
            fuser -k ${EXTERNAL_PORT}/tcp || true
          fi
        """
      }
    }

    stage('Run Docker Container') {
      steps {
        echo "🚀 Launching container..."
        sh """
          docker run -d \
            --name ${CONTAINER_NAME} \
            -p ${EXTERNAL_PORT}:${INTERNAL_PORT} \
            -e HF_TOKEN=${HF_TOKEN} \
            -e PINECONE_API_KEY=${PINECONE_API_KEY} \
            -e PINECONE_API_ENV=${PINECONE_API_ENV} \
            ${IMAGE_NAME}:${DYNAMIC_TAG}
        """
      }
    }

    stage('Health Check') {
      steps {
        echo "🔍 Waiting for FastAPI to respond on /health"
        retry(5) {
          sleep time: 5, unit: 'SECONDS'
          sh "curl -f http://localhost:${EXTERNAL_PORT}/health"
        }
      }
    }
  }

  post {
    always {
      echo "📋 Container logs:"
      sh "docker logs ${CONTAINER_NAME} || true"

      echo "📂 Checking model folder inside container:"
      sh "docker exec ${CONTAINER_NAME} ls -lh /app/models || true"

      echo "🎯 Stopping & removing container..."
      sh """
        docker stop ${CONTAINER_NAME} || true
        docker rm   ${CONTAINER_NAME} || true
      """
    }

    success { echo "✅ All stages completed successfully!" }
    failure { echo "❌ Pipeline failed; check above logs." }
  }
}
