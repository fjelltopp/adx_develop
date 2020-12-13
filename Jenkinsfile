pipeline {
  agent any
  stages {
    stage('ADX tests') {
      steps {
        dir('adx_develop') {
          checkout scm
        }
        sshagent (credentials: ['githubssh']) {
          echo 'Get ECR login"
          sh """aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 254010146609.dkr.ecr.eu-west-1.amazonaws.com"""
          echo 'Starting ADX tests'
          sh """cd adx_develop && ./ci.sh"""
        }
      }
    }
  }
}

