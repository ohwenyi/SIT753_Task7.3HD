pipeline {
    agent any

    environment {
        PYTHON = 'C:\\Python310\\python.exe' // Adjust to your Python path
        VENV_DIR = 'venv'
        APP_PORT = '8000'
    }

    stages {

        stage('Build') {
            steps {
                bat '''
                python -m venv %VENV_DIR%
                call %VENV_DIR%\\Scripts\\activate
                pip install --upgrade pip
                pip install setuptools
                pip install -r requirements.txt
                pip install flake8 pylint black bandit
                echo Build complete.
                '''
            }
        }
        
        stage('Test') {
            steps {
                bat '''
                call %VENV_DIR%\\Scripts\\activate
                pytest --junitxml=test-results.xml
                echo Testing complete.
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Code Quality') {
          steps {
              bat '''
              call venv\\Scripts\\activate
              flake8 . --output-file=flake8-report.txt
              pylint main.py > pylint-report.txt
              black . --check > black-report.txt
              echo Code quality checks complete.
              '''
          }
      }

        stage('Security') {
            steps {
                bat '''
                call %VENV_DIR%\\Scripts\\activate
                bandit -r . > bandit-report.txt
                echo Security scan complete.
                '''
            }
        }

        stage('Deploy') {
            steps {
                bat '''
                call %VENV_DIR%\\Scripts\\activate
                start /B uvicorn main:app --host 0.0.0.0 --port %APP_PORT%
                echo App deployed to test environment.
                '''
            }
        }

        stage('Release') {
            steps {
                bat '''
                git tag -a "v1.0.%BUILD_NUMBER%" -m "Release v1.0.%BUILD_NUMBER%"
                git push origin --tags
                echo Release tagged and pushed.
                '''
            }
        }

        stage('Monitoring') {
            steps {
                bat '''
                curl http://localhost:%APP_PORT%/health > health-check.log
                echo Monitoring complete.
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '**/*-report.txt', fingerprint: true
        }
    }
}
