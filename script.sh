#! /bin/bash

help="Usage: ./script.sh [FILE]\nTry'./script --help' for more information.\n"

if [ $# -eq 0 ]
then
    printf "$help"
    exit 1
fi

if [[ $* == *--help* ]]
then
    printf "Typed help\n"
    exit 1
fi

envs=`cat $1`

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

printf "aws elasticbeanstalk update-environment --environment-name my-env --option-settings Namespace=aws:elasticbeanstalk:application:environment,$joinedEnvs"
