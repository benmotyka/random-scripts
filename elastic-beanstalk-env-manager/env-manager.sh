#!/bin/bash

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
short_help="Usage: ${bold}./script.sh [EB_ENVIRONMENT_NAME] [FILE]${normal}
Try'./script --help' for more information.
"
long_help="Usage: ${bold}./script.sh [EB_ENVIRONMENT_NAME] [FILE]${normal}
Manage environment variables in AWS Elastic Beanstalk environments easily.
Example: ${bold}./env-manager my-app-prod .env.production${normal}
FILE should contain KEY=\"VALUE\" pairs.
This script ${bold}DOES NOT${normal} remove variables that exist in the console but not in the FILE. 

Arguments:
--help            - Print Help (this message) and exit
--auto-approve    - Skip approval before applying
--dry-run         - perform a trial run with no changes made

Dry run outputs:
${cyan}~ \"KEY1\"${normal} - Environment variable has been modified according to the FILE
${green}+ \"KEY2\"${normal} - Environment variable has been added to the console
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
    if [[ ${new_envs[@]} > 0 ]]; then
        printf "${green}+ %s\n${default}" "${new_envs[@]}"
    fi
}

remove_non_existent () {
    existing_envs_not_in_file=TODO
    aws_response=`aws elasticbeanstalk update-environment --environment-name $eb_environment_name --options-to-remove $existing_envs_not_in_file`
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

envs=`cat $envs_file`
sanitized_keys=()
joined_envs=""

if [ ! -f "$envs_file" ]; then
    printf "${red}ERROR: Environment file doesn't exist!\n${default}"
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
        ;;
        *)
            printf "\nOperation aborted\n"
            exit 1
        ;;
    esac
fi

printf "\nUpdating environment...\n"

if [[ $* != *--dry-run* ]]
then
    update_environment
else
    dry_run
fi




