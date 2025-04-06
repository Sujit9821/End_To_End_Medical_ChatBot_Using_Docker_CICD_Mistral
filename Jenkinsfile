pipeline {
    agent any

    environment {
        IMAGE_NAME = 'chatbot_medical'
        TAG = 'v1'
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
                    sh 'docker build -t ${IMAGE_NAME}:${TAG} .'
                }
            }
        }

        stage('Run Docker Container') {
            steps {
                script {
                    // Stop and remove previous container if exists
                    sh '''
                    docker stop chatbot_app || true
                    docker rm chatbot_app || true
                    docker run --env-file .env -d -p 5000:5000 --name chatbot_app ${IMAGE_NAME}:${TAG}
                    '''
                }
            }
        }
    }
}
