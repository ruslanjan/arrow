#!/bin/bash

path=$1 # path to sandbox
memory=$2 # isolate memory limit
time=$3 # isolate time limit
wallTime=$4

shift 4

runCommand=${@}

cd $path || exit

#isolate-check-environment -e
isolate --cg --init

#if [[ $? == 0 ]]
isolate -s --env=HOME=/root --time=${time} --wall-time=${wallTime} --dir=$path/usercode:rw --stdin=$path/usercode/input_file --stdout=$path/usercode/output_file --stderr=$path/usercode/error_file --mem=${memory} --cg --meta=$path/meta --chdir=$path/usercode  --run -- ${runCommand}

isolate --cleanup --cg
