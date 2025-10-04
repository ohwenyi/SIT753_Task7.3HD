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
                %VENV_DIR%\\Scripts\\python.exe -m pip install --upgrade pip
                %VENV_DIR%\\Scripts\\python.exe -m pip install setuptools
                %VENV_DIR%\\Scripts\\python.exe -m pip install redis
                %VENV_DIR%\\Scripts\\python.exe -m pip install pytest
                %VENV_DIR%\\Scripts\\python.exe -m pip install pytest_asyncio
                %VENV_DIR%\\Scripts\\python.exe -m pip install httpx
                %VENV_DIR%\\Scripts\\python.exe -m pip install fastapi
                %VENV_DIR%\\Scripts\\python.exe -m pip install uvicorn
                %VENV_DIR%\\Scripts\\python.exe -m pip install pydantic-settings
                %VENV_DIR%\\Scripts\\python.exe -m pip install loguru
                %VENV_DIR%\\Scripts\\python.exe -m pip install asyncpg
                %VENV_DIR%\\Scripts\\python.exe -m pip install -r requirements.txt
                %VENV_DIR%\\Scripts\\python.exe -m pip install flake8 pylint black bandit
                echo Build complete.
                '''
            }
        }

        stage('Test') {
            steps {
                bat '''
                %VENV_DIR%\\Scripts\\python.exe -m pytest --junitxml=test-results.xml
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
                %VENV_DIR%\\Scripts\\flake8 . --output-file=flake8-report.txt
                %VENV_DIR%\\Scripts\\pylint main.py > pylint-report.txt
                %VENV_DIR%\\Scripts\\black . > black-report.txt
                echo Code quality checks complete.
                '''
            }
        }

        stage('Security') {
            steps {
                bat '''
                chcp 65001
                %VENV_DIR%\\Scripts\\python.exe -c "import subprocess; open('bandit-report.txt', 'w', encoding='utf-8').write(subprocess.run(['%VENV_DIR%\\\\Scripts\\\\bandit', '-r', '.'], capture_output=True, text=True).stdout)"
                echo Security scan complete.
                '''
            }
        }

        stage('Deploy') {
            steps {
                bat '''
                start /B %VENV_DIR%\\Scripts\\python.exe -m uvicorn main:app --host 127.0.0.1 --port %APP_PORT%
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
                timeout /T 5 >nul
                curl http://127.0.0.1:%APP_PORT%/health > health-check.log
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
