pipeline {
    agent any

    environment {
        IMAGE_NAME = "sit753-app:latest"
        STAGING_CONTAINER = "sit753-staging"
        PROD_CONTAINER = "sit753-prod"
        APP_PORT = "8000"
        GIT_BRANCH = "master"
    }

    stages {

        stage('Checkout') {
            steps {
                echo '=== Checking out master branch ==='
                checkout([$class: 'GitSCM',
                    branches: [[name: "*/${GIT_BRANCH}"]],
                    userRemoteConfigs: [[url: 'https://github.com/ohwenyi/SIT753_Task7.3HD.git']]
                ])
            }
        }

        stage('Build') {
            steps {
                echo '=== Build Stage ==='
                bat 'docker build -t %IMAGE_NAME% .'
                echo 'Docker image built.'
            }
        }

        stage('Test') {
            steps {
                echo '=== Test Stage ==='
                bat 'docker run --rm %IMAGE_NAME% pytest --junitxml=test-results.xml'
                echo 'Tests executed.'
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Code Quality') {
            steps {
                echo '=== Code Quality Stage ==='
                bat 'docker run --rm %IMAGE_NAME% flake8 . --output-file=flake8-report.txt'
                bat 'docker run --rm %IMAGE_NAME% pylint main.py > pylint-report.txt'
                bat 'docker run --rm %IMAGE_NAME% black . > black-report.txt'
                echo 'Code quality checks complete.'
            }
        }

        stage('Security') {
            steps {
                echo '=== Security Stage ==='
                bat 'docker run --rm %IMAGE_NAME% bandit -r . > bandit-report.txt'
                echo 'Security scan complete.'
            }
        }

        stage('Deploy') {
            steps {
                echo '=== Deploy Stage (Staging) ==='
                bat 'docker rm -f %STAGING_CONTAINER% || exit 0'
                bat 'docker run -d --name %STAGING_CONTAINER% -p %APP_PORT%:8000 %IMAGE_NAME%'
                echo 'App deployed to staging.'
            }
        }

        stage('Release') {
            steps {
                echo '=== Release Stage (Production) ==='
                bat 'docker rm -f %PROD_CONTAINER% || exit 0'
                bat 'docker run -d --name %PROD_CONTAINER% -p 80:8000 %IMAGE_NAME%'
                echo 'App promoted to production.'
            }
        }

        stage('Monitoring') {
            steps {
                echo '=== Monitoring Stage ==='
                bat '''
                curl http://localhost:%APP_PORT%/health > health-check.log
                echo Monitoring complete.
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '**/*-report.txt, health-check.log', fingerprint: true
        }
        cleanup {
            cleanWs()
        }
    }
}
