#! /bin/bash

if [ $# -eq 0 ]
    then
        printf "Usage: ./script.sh [FILE]\nTry'./script --help' for more information.\n"
        exit 1
fi 

if [[ $* == *--help* ]]
    then
        printf "Typed help\n"
        exit 1
fi

envs=`cat $1`
joinedEnvs=""

for value in $envs
    do
    joinedEnvs+="$value,"
done

aws elasticbeanstalk update-environment --environment-name my-env --option-settings Namespace=aws:elasticbeanstalk:application:environment,OptionName=PARAM1,Value=ParamValue

echo $joinedEnvs
