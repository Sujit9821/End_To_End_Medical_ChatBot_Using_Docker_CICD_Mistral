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
        echo "🧹 Removing old container if exists..."
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

    stage('Wait for Health Check (with timer)') {
      steps {
        script {
          echo "⏳ Starting health check loop..."
          def startTime = sh(script: "date +%s", returnStdout: true).trim()
          def maxRetries = 800
          def sleepSeconds = 5
          def success = false

          for (int i = 0; i < maxRetries; i++) {
            try {
              sh "curl -f http://localhost:${EXTERNAL_PORT}/health"
              success = true
              break
            } catch (Exception e) {
              echo "🔄 Health check attempt ${i+1} failed, retrying in ${sleepSeconds} seconds..."
              sleep time: sleepSeconds, unit: 'SECONDS'
            }
          }

          if (!success) {
            error "❌ Health check failed after ${maxRetries} retries."
          } else {
            def endTime = sh(script: "date +%s", returnStdout: true).trim()
            def totalTime = (endTime.toInteger() - startTime.toInteger()) / 60.0
            echo "✅ App became healthy after ${totalTime} minutes."
          }
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

    success {
      echo "✅ All Jenkins stages completed successfully!"
    }

    failure {
      echo "❌ Jenkins pipeline failed; please check above logs."
    }
  }
}
