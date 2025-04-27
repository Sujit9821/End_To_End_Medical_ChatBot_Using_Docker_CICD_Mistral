pipeline {
  agent any

  environment {
    BASE_IMAGE_NAME  = 'medbot-prod-app'
    BASE_TAG         = 'prod'
    INTERNAL_PORT    = '8000'
    EXTERNAL_PORT    = '8000'
    HF_TOKEN         = credentials('HF_TOKEN')
    PINECONE_API_KEY = credentials('PINECONE_API_KEY')
    PINECONE_API_ENV = credentials('PINECONE_API_ENV')
    AWS_ACCOUNT_ID   = credentials('AWS_ACCOUNT_ID')
    AWS_REGION       = 'eu-north-1'
  }

  stages {
    stage('Checkout Code') {
      steps {
        echo "🔄 Cloning source code..."
        checkout scm
      }
    }

    stage('Generate Dynamic Names') {
      steps {
        script {
          def randomStr = UUID.randomUUID().toString().substring(0, 6)
          env.RANDOM_SUFFIX = randomStr
          env.DYNAMIC_TAG = "${BASE_TAG}-${new Date().format('yyyyMMdd-HHmm')}"
          env.CONTAINER_NAME = "app_${randomStr}"
          env.IMAGE_NAME = BASE_IMAGE_NAME
          echo "🆕 Container Name: ${env.CONTAINER_NAME}"
          echo "🆕 Image Tag: ${env.DYNAMIC_TAG}"
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        withCredentials([string(credentialsId: 'HF_TOKEN', variable: 'HF_TOKEN')]) {
          sh """
            echo "🔍 Checking environment..."
            export DOCKER_CLI_PLUGIN_PATH=/home/ubuntu/.docker/cli-plugins
            echo "User: \$(whoami) | Groups: \$(groups) | Docker Version: \$(docker --version) | Buildx Version: \$(docker buildx version)" && docker info

            echo "🐳 Building using Buildx..."
            docker buildx build --load \
              --build-arg HF_TOKEN=\$HF_TOKEN \
              -t ${IMAGE_NAME}:${DYNAMIC_TAG} .
          """
        }
      }
    }

    stage('Push to AWS ECR') {
      steps {
        script {
          echo "🔐 Logging into AWS ECR..."
        }
        sh """
          aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

          echo "🏷️ Tagging Image..."
          docker tag ${IMAGE_NAME}:${DYNAMIC_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${DYNAMIC_TAG}

          echo "📤 Pushing Image to AWS ECR..."
          docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${DYNAMIC_TAG}
        """
      }
    }

    stage('Deploy to AWS EC2') {
      steps {
        echo "🚀 Deploying to EC2..."
        sshagent(['EC2_SSH_KEY']) {
          sh """
            ssh -o StrictHostKeyChecking=no ubuntu@13.51.174.211 << 'EOF'
              echo "🔄 Pulling new image..."
              docker pull ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${DYNAMIC_TAG}

              echo "🐳 Running new container..."
              docker run -d --name ${CONTAINER_NAME}_new -p ${EXTERNAL_PORT}:${INTERNAL_PORT} \
                -e HF_TOKEN=${HF_TOKEN} \
                -e PINECONE_API_KEY=${PINECONE_API_KEY} \
                -e PINECONE_API_ENV=${PINECONE_API_ENV} \
                ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${DYNAMIC_TAG}

              echo "🔍 Health check starting..."
              start_time=\$(date +%s)
              while true; do
                if curl -s http://localhost:${EXTERNAL_PORT}/health | grep "ok"; then
                  break
                fi
                sleep 5
              done
              end_time=\$(date +%s)
              total_time=\$(( (end_time - start_time) / 60 ))
              echo "✅ Healthcheck passed after \$total_time minutes."

              echo "🧹 Cleaning old containers..."
              docker stop \$(docker ps -q --filter "name=app_") || true
              docker rm \$(docker ps -a -q --filter "name=app_") || true

              echo "🔁 Renaming new container..."
              docker rename ${CONTAINER_NAME}_new ${CONTAINER_NAME}
            EOF
          """
        }
      }
    }
  }

  post {
    always {
      echo "📋 Checking containers after deployment:"
      sshagent(['EC2_SSH_KEY']) {
        sh """
          ssh -o StrictHostKeyChecking=no ubuntu@13.51.174.211 "docker ps -a || true; docker logs \$(docker ps -alq) || true"
        """
      }
    }
    success {
      echo "✅ Pipeline completed successfully!"
    }
    failure {
      echo "❌ Pipeline failed. Please check logs."
    }
  }
}
