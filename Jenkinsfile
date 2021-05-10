def extensions = [
  "restricted",
  "dhis2harvester",
  "emailasusername",
  "file_uploader_ui",
  "pages",
  "pdfview",
  "scheming",
  "validation",
  "ytp-request",
  "unaids"
]

pipeline {
  agent any
  triggers {
        cron('H 23 * * 1-5')
    }
  stages {
    stage('ADX setup tests') {
      steps {
        dir('adx_develop') {
          checkout scm
        }
        sshagent (['local-github-ssh']) {
          echo 'Get ECR login'
          sh """aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 254010146609.dkr.ecr.eu-west-1.amazonaws.com"""
          echo 'Starting ADX setup'
          sh """cd adx_develop && ./ci_setup.sh"""
        }
      }
    }
    stage('ADX run tests') {
      steps {
        script {
          for (test in extensions) {
            stage(test) {
              sh """cd adx_develop && ./ci_test.sh ${test}"""
            }
          }
        }
      }
    }

  }
  post { 
      always { 
          sh """cd $WORKSPACE/adx_develop &&docker-compose down --rmi all -v --remove-orphans"""
          cleanWs()
      }
  }
}

