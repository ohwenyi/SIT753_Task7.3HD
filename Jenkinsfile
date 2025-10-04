pipeline {
    agent any

    environment {
        PYTHON = 'C:\\Python310\\python.exe'
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
                pip install redis
                pip install pytest
                pip install pytest_asyncio
                pip install httpx
                pip install fastapi
                pip install uvicorn
                pip install pydantic-settings
                pip install loguru
                pip install asyncpg
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
                call %VENV_DIR%\\Scripts\\activate
                flake8 . --output-file=flake8-report.txt
                pylint main.py > pylint-report.txt
                black . > black-report.txt
                echo Code quality checks complete.
                '''
            }
        }

        stage('Security') {
            steps {
                bat '''
                call %VENV_DIR%\\Scripts\\activate
                chcp 65001
                python -c "import subprocess; open('bandit-report.txt', 'w', encoding='utf-8').write(subprocess.run(['bandit', '-r', '.'], capture_output=True, text=True).stdout)"
                echo Security scan complete.
                '''
            }
        }

        stage('Deploy') {
            steps {
                bat '''
                call %VENV_DIR%\\Scripts\\activate
                start /B uvicorn main:app --host 127.0.0.1 --port %APP_PORT%
                timeout /T 5 >nul
                echo App deployed to local test environment.
                '''
            }
        }

        stage('Release') {
            steps {
                timeout(time: 2, unit: 'MINUTES') {
                    withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_PAT')]) {
                        bat '''
                        setlocal EnableDelayedExpansion
                        git config --global user.name "Jenkins CI"
                        git config --global user.email "jenkins@example.com"
                        set REMOTE_URL=https://ohwenyi:!GITHUB_PAT!@github.com/ohwenyi/SIT753_Task7.3HD.git
                        git remote set-url origin !REMOTE_URL!
                        git tag -a "v1.0.%BUILD_NUMBER%" -m "Promoting to production: v1.0.%BUILD_NUMBER%"
                        git push origin --tags
                        echo Release promoted to production.
                        endlocal
                        '''
                    }
                }
            }
        }

        stage('Monitoring') {
            steps {
                bat '''
                curl -X POST "https://api.datadoghq.com/api/v1/events" ^
                -H "Content-Type: application/json" ^
                -H "DD-API-KEY: your_datadog_api_key" ^
                -d "{ \\"title\\": \\"SIT753 App Health Check\\", \\"text\\": \\"Production app is live and healthy\\", \\"tags\\": [\\"env:production\\"] }"
                echo Monitoring alert sent to Datadog.
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
