pipeline {
    agent any
    environment {
        AWS_PROFILE='tots'
        CLUSTER_NAME= 'TOTS'
        SERVICE_NAME= 'TOTSAppServer'
    }
    stages{
        stage('Checkout'){
            steps{
                checkout scm
            }
        }
        stage('Docker Push'){
            steps{
                sh './ecr_push.sh'
            }
        }
        stage('Update ECS Service'){
            steps{
                sh '/usr/local/bin/aws ecs update-service --cluster ${CLUSTER_NAME} --service ${SERVICE_NAME} --force-new-deployment'
            }

        }
    }
}
