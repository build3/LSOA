pipeline {
    agent any
    environment {
        AWS_PROFILE='tots'
        CLUSTER_NAME= 'TOTS'
        SERVICE_NAME= 'TOTSAppServer'
    }
    stages{
        stage('Checkout'){
            scm checkout
        }
        stage('Docker Push'){
            sh './ecr_push.sh'
        }
        stage('Update ECS Service'){
            sh '/usr/local/bin/aws ecs update-service --cluster ${CLUSTER_NAME} --service ${SERVICE_NAME} --force-new-deployment'
        }
    }
}
