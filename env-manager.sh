#! /bin/bash

bold=$(tput bold)
normal=$(tput sgr0)

short_help="Usage: ./script.sh [EB_ENVIRONMENT_NAME] [FILE]\nTry'./script --help' for more information.\n"
long_help="Long help \n"

update_environment () {
    printf "aws elasticbeanstalk update-environment --environment-name $eb_environment_name --option-settings Namespace=aws:elasticbeanstalk:application:environment,$joined_envs"
}

dry_run () {
    printf "aws elasticbeanstalk describe-configuration-options --environment-name $eb_environment_name --option-settings Namespace=aws:elasticbeanstalk:application:environment"

}

if [[ $* == *--help* ]]
then
    printf "$long_help"
    exit 1
fi

if [ $# -lt 2 ]
then
    printf "$short_help"
    exit 1
fi

eb_environment_name=$1
envs_file=$2

if [ ! -f "$envs_file" ]; then
    printf "ERROR: File doesn't exist!\n"
    exit 2
fi

envs=`cat $envs_file`

if [ -z "$envs" ]
then
    printf "ERROR: Environment file empty!\n"
    exit 2
fi

joined_envs=""

for value in $envs
do
    joined_envs+="$value,"
done

joined_envs=${joined_envs::-1}

if [[ $* != *--auto-approve* ]]
then
    read -r -p "Are you sure to update your environment name:${bold} $eb_environment_name ${normal}with envs from file:${bold} $envs_file? ${normal}[y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY])
            continue
        ;;
        *)
            printf "Operation aborted\n"
            exit 1
        ;;
    esac
fi

if [[ $* != *--dry-run* ]]
then
    update_environment
else
    dry_run
fi



