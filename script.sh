#! /bin/bash

shortHelp="Usage: ./script.sh [ENVIRONMENT_NAME] [FILE]\nTry'./script --help' for more information.\n"
longHelp="Long help \n"

if [[ $* == *--help* ]]
then
    printf "$longHelp"
    exit 1
fi

if [ $# -lt 2 ]
then
    printf "$shortHelp"
    exit 1
fi

environment=$1
envs_file=$2

envs=`cat $envs_file`

if [ -z "$envs" ]
then
    printf "ERROR: Environment file empty!\n"
    exit 2
fi

joinedEnvs=""

for value in $envs
do
    joinedEnvs+="$value,"
done

joinedEnvs=${joinedEnvs::-1}

# aws elasticbeanstalk update-environment --environment-name my-env --option-settings Namespace=aws:elasticbeanstalk:application:environment,OptionName=PARAM1,Value=ParamValue

read -r -p "Are you sure to update your environment name: $environment with envs from file: $envs_file? [y/N] " response
case "$response" in
    [yY][eE][sS]|[yY]) 
        printf "aws elasticbeanstalk update-environment --environment-name $environment --option-settings Namespace=aws:elasticbeanstalk:application:environment,$joinedEnvs"
        ;;
    *)
        printf "Operation aborted\n"
        exit 1
        ;;
esac


