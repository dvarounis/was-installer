#!/bin/sh
 

#set -x
#trap all usual signals
trap finish EXIT
trap sigcatch INT TERM

################################################  DMGR Parameters  #################################################################

DMGR_HOME="/opt/ibm/websphere/appserver/profiles/Dmgr01"
CONNECTOR_TYPE="RMI"
CONNECTOR_PORT=9809
WSADMIN_PARAMS='-javaoption "-Xms256m -Xmx4096m"'

################################################  Local Parameters  ################################################################

BINDIR="$HOME/bin/binaries"
TOPOLOGYXML=$HOME/bin/topology.xml
LOGDIR=$HOME/logs
PID=$$
LOGFILE=$LOGDIR/installer.$PID.log

################################################  Downloading the EARs #############################################################


#Logger function
log ()
{	
    MESSAGE="$@"
    TIMESTAMP=`date "+%d/%m/%Y %H:%M:%S"`
    echo "[$TIMESTAMP] [$(/usr/bin/logname)] $MESSAGE"  | tee -a $LOGFILE 
}

#Cleanup Function
finish ()
{
    log 'Removing EAR files...'
    rm -rfv $BINDIR | tee -a $LOGFILE
    TSTAMP=`date "+%d.%m.%Y_%H.%M.%S"`
    mv $LOGFILE $LOGDIR/installer.$TSTAMP.$PID.log
}

sigcatch ()
{
   log 'Caught TERM or INT signal'
   finish
}

checklogdir ()
{
   LOGPATH="$1"
   if [ ! -d $LOGPATH ]
   then
	mkdir -p $LOGPATH
   fi
   log 'Started Logging at' $LOGFILE
}

#Rebase the hotfolder to allow parallel deployments
changehotfolder ()
{
	
	mkdir -vp $BINDIR/$PID | tee -a $LOGFILE 
	if [[ $? -eq 0 ]]
	then
		find $BINDIR/ -maxdepth 1 -name '*.ear' -print| xargs -i mv -v {} $BINDIR/$PID/ | tee -a $LOGFILE 
		BINDIR=$BINDIR/$PID
		log 'New Binaries directory for Current job: ' $BINDIR
	else 
		exit 1
	fi
	
}

#Extract ears from .zip file from Nexus
handlezipfiles ()
{
	FILEURL="$1"
	
	if [[ $FILEURL == *\.zip ]]
	then
	
		ZFILENAME=$(expr "$FILEURL" : '.*\/\(.*\.zip\)')
		log 'Extracting ear files from' $ZFILENAME '...'
		unzip $BINDIR/$ZFILENAME libs/*.ear -d $BINDIR | tee -a $LOGFILE 
		if [[ $? -eq 0 ]]
		then	
			mv -v $BINDIR/libs/*.ear $BINDIR && rmdir $BINDIR/libs | tee -a $LOGFILE

		fi

		rm -v $BINDIR/$ZFILENAME | tee -a $LOGFILE 

	fi
}

checklogdir "$LOGDIR"

changehotfolder

FSSFLAG=""

#Roll over Arguments as script arguments
while [ $# -gt 0 ]
do

	ARG="$1"
	if [[ $ARG == http:\/\/*   ]]
	then	
		log 'Downloading the EAR from ' $ARG
		wget -a $LOGFILE -nv -P $BINDIR $ARG 
		if [ $? -ne 0 ]
		then
			log 'Problem downloading file: ' $ARG
			log 'The program is exiting...'
			exit 1 
		fi
		handlezipfiles $ARG
	elif [[ $ARG == "-S" ]]
	then
		log 'CAUTION: Force Save/Sync Mode!'
		FSSFLAG="$ARG"
	fi
	shift
done


$DMGR_HOME/bin/wsadmin.sh -lang jython -conntype $CONNECTOR_TYPE -port $CONNECTOR_PORT $WSADMIN_PARAMS -f $HOME/bin/installer.py $FSSFLAG $BINDIR $TOPOLOGYXML | tee -a $LOGFILE


#set +x
