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
    stage('Checkout') {
      steps {
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
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        sh """
          DOCKER_BUILDKIT=1 docker build \
            --build-arg HF_TOKEN=${HF_TOKEN} \
            -t ${IMAGE_NAME}:${DYNAMIC_TAG} .
        """
      }
    }

    stage('Push to AWS ECR') {
      steps {
        sh """
          aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
          docker tag ${IMAGE_NAME}:${DYNAMIC_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${DYNAMIC_TAG}
          docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${DYNAMIC_TAG}
        """
      }
    }

    stage('Deploy on AWS EC2') {
      steps {
        sshagent(['EC2_SSH_KEY']) {
          sh """
            ssh -o StrictHostKeyChecking=no ubuntu@13.51.174.211 << 'EOF'
              docker pull ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${DYNAMIC_TAG}
              docker run -d --name ${CONTAINER_NAME}_new -p ${EXTERNAL_PORT}:${INTERNAL_PORT} \
                -e HF_TOKEN=${HF_TOKEN} \
                -e PINECONE_API_KEY=${PINECONE_API_KEY} \
                -e PINECONE_API_ENV=${PINECONE_API_ENV} \
                ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${DYNAMIC_TAG}

              echo "Waiting for container to be healthy..."
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

              docker stop \$(docker ps -q --filter "name=app_") || true
              docker rm \$(docker ps -a -q --filter "name=app_") || true
              docker rename ${CONTAINER_NAME}_new ${CONTAINER_NAME}
            EOF
          """
        }
      }
    }
  }
}
