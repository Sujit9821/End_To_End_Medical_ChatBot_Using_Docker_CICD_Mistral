pipeline {
    agent any

    environment {
        IMAGE_NAME = 'chatbot_medical'
        TAG = 'v1'
        HF_TOKEN = credentials('huggingface_token')
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
                    sh 'docker build --build-arg HF_TOKEN=$HF_TOKEN -t chatbot_medical:v1 .'
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
                    sh 'docker run -d --name chatbot_app -p 5000:8080 -e HF_TOKEN=$HF_TOKEN chatbot_medical:v1'
                    '''
                }
            }
        }
    }
}
