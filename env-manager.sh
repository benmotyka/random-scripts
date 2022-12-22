#! /bin/bash

# Font settings
bold=$(tput bold)
normal=$(tput sgr0)

# Colors
default='\033[0m' # No Color
red='\033[0;31m'
green='\033[0;32m' 
yellow='\033[0;33m' 
cyan='\033[0;36m' 


# Longer texts
short_help="Usage: ./script.sh [EB_ENVIRONMENT_NAME] [FILE]\nTry'./script --help' for more information.\n"
long_help="Long help \n"

eb_environment_name=$1
envs_file=$2

envs=`cat $envs_file`
sanitized_keys=()
joined_envs=""


update_environment () {
    aws_response=`aws elasticbeanstalk update-environment --environment-name $eb_environment_name --option-settings $joined_envs`
}

dry_run () {
    aws_response=`aws elasticbeanstalk describe-configuration-options --environment-name $eb_environment_name --options Namespace=aws:elasticbeanstalk:application:environment`

    existing_envs=( $(jq '.Options[].Name' <<< $aws_response) )
    envs_difference=(`echo ${sanitized_keys[@]} ${existing_envs[@]} | tr ' ' '\n' | sort | uniq -u`)
    new_envs=(`echo ${sanitized_keys[@]} ${envs_difference[@]} | tr ' ' '\n' | sort | uniq -D | uniq`)
    changed_envs=(`echo ${new_envs[@]} ${sanitized_keys[@]} | tr ' ' '\n' | sort | uniq -u`)

    printf "\nDry run results:\n"
    printf "%s\n${default}" "${changed_envs[@]}"
}

printf "\n"

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


if [ ! -f "$envs_file" ]; then
    printf "${red}ERROR: File doesn't exist!\n${default}"
    exit 2
fi

if [ -z "$envs" ]
then
    printf "${red}ERROR: Environment file empty!\n${default}"
    exit 2
fi


for value in $envs
do
    if [[ $value != *"="* ]]; then
        printf "${yellow}WARNING: Invalid variable: $value, ignoring it\n${default}"
        continue
    fi
    env_key=`echo "$value" | cut -d "=" -f 1`
    env_value=`echo "$value" | cut -d "=" -f 2`
    sanitized_keys+=("\"$env_key\"")
    joined_envs+=" Namespace=aws:elasticbeanstalk:application:environment,OptionName=$env_key,Value=$env_value"
done

if [[ $* != *--auto-approve* ]]
then
    printf "\n"
    read -r -p "Are you sure to update your environment name:${bold} $eb_environment_name ${normal}with environment variables from file:${bold} $envs_file? ${normal}[y/N]: " response
    case "$response" in
        [yY][eE][sS]|[yY])
            printf "\nUpdating environment...\n"
        ;;
        *)
            printf "\nOperation aborted\n"
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




