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
short_help="Usage: ./script.sh [EB_ENVIRONMENT_NAME] [FILE]
Try'./script --help' for more information.
"
long_help="Usage: ./script.sh [EB_ENVIRONMENT_NAME] [FILE]
Manage environment variables in AWS Elastic Beanstalk environments easily.
Example: ./env-manager my-app-prod .env.production
FILE should contain key and value pairs.

Arguments:
--help         - Print Help (this message) and exit
--auto-approve - Skip approval before applying
--dry-run      - perform a trial run with no changes made
"
env_update_success="
${green}Environment updated successfully
"

update_environment () {
    aws_response=`aws elasticbeanstalk update-environment --environment-name $eb_environment_name --option-settings $joined_envs`

    if [ $? -ne 0 ]; then
        exit 2
    fi

    printf "${env_update_success}"
}

dry_run () {
    aws_response=`aws elasticbeanstalk describe-configuration-options --environment-name $eb_environment_name --options Namespace=aws:elasticbeanstalk:application:environment`
    
    if [ $? -ne 0 ]; then
        exit 2
    fi

    existing_envs=( $(jq '.Options[].Name' <<< $aws_response) )
    envs_difference=(`echo ${sanitized_keys[@]} ${existing_envs[@]} | tr ' ' '\n' | sort | uniq -u`)
    new_envs=(`echo ${sanitized_keys[@]} ${envs_difference[@]} | tr ' ' '\n' | sort | uniq -D | uniq`)
    changed_envs=(`echo ${new_envs[@]} ${sanitized_keys[@]} | tr ' ' '\n' | sort | uniq -u`)

    printf "\nDry run results:\n"
    printf "${cyan}~ %s\n${default}" "${changed_envs[@]}"
    printf "${green}+ %s\n${default}" "${new_envs[@]}"
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

if [ ! -f "$envs_file" ]; then
    printf "${red}ERROR: File doesn't exist!\n${default}"
    exit 2
fi

if [ -z "$envs" ]
then
    printf "${red}ERROR: Environment file empty!\n${default}"
    exit 2
fi

eb_environment_name=$1
envs_file=$2

envs=`cat $envs_file`
sanitized_keys=()
joined_envs=""

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




