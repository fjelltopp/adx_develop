pipeline {
  agent any
  triggers {
        cron('H 23 * * 1-5')
    }
  stages {
    stage('ADX tests') {
      steps {
        dir('adx_develop') {
          checkout scm
        }
        sshagent (credentials: ['githubssh']) {
          echo 'Get ECR login'
          sh """aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 254010146609.dkr.ecr.eu-west-1.amazonaws.com"""
          echo 'Starting ADX tests'
          sh """cd adx_develop && git checkout ${GIT_BRANCH} && ./ci.sh"""
          sh """cd $WORKSPACE/adx_develop &&docker-compose down --rmi all -v --remove-orphans"""
        }
      }
    }
  }
  post { 
      always { 
          cleanWs()
      }
  }
}

