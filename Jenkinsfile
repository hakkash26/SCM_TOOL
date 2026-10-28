pipeline {
    agent any

    stages {
        stage('Install dependencies') {
            steps {
                bat 'py -3 -m pip install --upgrade pip'
                bat 'py -3 -m pip install -r requirements.txt'
            }
        }

        stage('Run tests') {
            steps {
                bat 'py -3 -m unittest tests/test_system.py'
            }
        }
    }
}
