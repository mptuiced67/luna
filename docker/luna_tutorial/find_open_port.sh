#!/usr/bin/env bash

# requires arguments for min, max values of port range to search in

# check pre-requisites
ERR=$(which nc)
EXIT_VALUE=$?

if [ $EXIT_VALUE != 0 ];
then
    echo "Please install the linux nc (netcat) command"
    echo "redhat: yum install -y nc"
    echo "ubuntu: apt-get install netcat"
    echo "mac: brew install netcat"
    exit 1
fi

unameOut="$(uname -s)"

ERR=$(which seq)
EXIT_VALUE=$?

if [ $EXIT_VALUE != 0 ];
then
    echo "Please install the linux seq command"
    echo "mac: brew install coreutils"
    exit 1
fi

# search for an available port in the specified range
for ii in $(seq $1 $2);
do
    if [[ "$unameOut" == *"Darwin"* ]];  # if mac
    then
	RESULT=$(nc -zvw100 localhost $ii 2>&1)
	# if connection is refused, then port is open
	if [[ "$RESULT" == *"refused"* ]];
        then
           PORT=$ii
           break
         fi
    else   # if linux
	RESULT=$(netstat -nltp | grep $ii 2>&1)
        # if no LISTEN in output, then port is open
        if [[ "$RESULT" != *"LISTEN"* ]];
        then
           PORT=$ii
           break
        fi
    fi 
done

echo "$PORT"
exit 0
