#!/bin/bash

# Example of specific backend creation for a terraform project
# This script creates a S3 bucket and a DynamoDB table for locking state management

function usage(){
     echo "Usage: create-s3-backend.sh -a <account_id> -r <region> -p <project> [-d] "
}

while getopts ":hda:p:r:f:" option
do
    
    case $option in
        h)
            usage
            exit 0
            ;;
        a) 
            ACCOUNT="$OPTARG"
            ;;
        r) 
            REGION="$OPTARG"
            ;;
        p) 
            PROJECT="$OPTARG"
            ;;
        d)
            DRYRUN=true
            ;;
        \?)
            echo "$OPTARG : option invalide"
            usage
            exit 1
            ;;
    esac
done
    
if [[ ( "$PROJECT" = "" ) || ( "$ACCOUNT" = "" ) || ( "$REGION" = "" ) ]]
then
    usage
    exit 1
else
    echo "Command parameters : -f $PROJECT -r $REGION -a $ACCOUNT [-d for dry run]"
    echo " Example of project: 'crypto-robot'"
fi

BUCKET="tfstates-$ACCOUNT-s3bucket"
REGION="$REGION"
LOCK_TABLE="tfstates-$ACCOUNT-lock-table"
KEY="tfstates-$ACCOUNT/$PROJECT/deploy.tfstate"


export AWS_PROFILE="perso" # Specify your AWS profile here -> for use on TD terminal


if [[ $DRYRUN = true ]]
then
    echo "Dry run mode: No changes will be made." 
    echo aws s3api create-bucket --bucket $BUCKET  \
        --region $REGION \
        --create-bucket-configuration LocationConstraint=$REGION
    echo aws s3api put-bucket-versioning --bucket $BUCKET \
        --region $REGION --versioning-configuration Status=Enabled
    echo aws dynamodb create-table \
        --table-name $LOCK_TABLE \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
    exit 0
else
    echo "Creating S3 bucket and DynamoDB table for Terraform backend..."
    aws s3api create-bucket --bucket $BUCKET  \
        --region $REGION \
        --create-bucket-configuration LocationConstraint=$REGION
    aws s3api put-bucket-versioning --bucket $BUCKET --region $REGION --versioning-configuration Status=Enabled
    aws dynamodb create-table \
        --table-name $LOCK_TABLE \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
fi
