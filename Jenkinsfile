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
def notifySlack(String buildStatus = 'STARTED') {
    // Build status of null means success.
    buildStatus = buildStatus ?: 'SUCCESS'

    def color

    if (buildStatus == 'STARTED') {
        color = '#D4DADF'
    } else if (buildStatus == 'SUCCESS') {
        color = '#BDFFC3'
    } else if (buildStatus == 'UNSTABLE') {
        color = '#FFFE89'
    } else {
        color = '#FF9FA1'
    }

    def msg = "${buildStatus}: `${env.JOB_NAME}` #${env.BUILD_NUMBER}:\n${env.BUILD_URL}"

    slackSend(color: color, message: msg)
}

node {
    try {
        notifySlack()

        // Existing build steps.
    } catch (e) {
        currentBuild.result = 'FAILURE'
        throw e
    } finally {
        notifySlack(currentBuild.result)
    }
}

pipeline {
  agent any
  triggers {
        cron('H 23 * * 1-5')
    }
  stages {
    stage('ADX setup tests') {
      steps {
        slackSend (channel: "#unaids", color: '#FFFF00', message: "STARTED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
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
      success {
        slackSend (color: '#00FF00', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
      }

      failure {
        slackSend (color: '#FF0000', message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
      }

  }
}

