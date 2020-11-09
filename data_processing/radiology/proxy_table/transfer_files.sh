########################### setup pre-conditions ###########################
set -x
LOG_FILE=transfer_files.log
exit_code=0

echo ">>>> writing data transfer logs to $LOG_FILE..."
echo "Running data_processing/radiology/proxy_table/transfer_files.sh with - " >> $LOG_FILE;
echo "BWLIMIT = $BWLIMIT" >> $LOG_FILE;
echo "CHUNK_FILE = $CHUNK_FILE" >> $LOG_FILE;
echo "EXCLUDES = $EXCLUDES" >> $LOG_FILE;
echo "HOST = $HOST" >> $LOG_FILE;
echo "SOURCE_PATH = $SOURCE_PATH" >> $LOG_FILE;
echo "RAW_DATA_PATH = $RAW_DATA_PATH" >> $LOG_FILE;
echo "FILE_COUNT = $FILE_COUNT" >> $LOG_FILE;
echo "\nDATA_SIZE = $DATA_SIZE" >> $LOG_FILE;

# todo: make keys in ingestion template all caps

# validate env vars - check if they exist
[ "${BWLIMIT}" ]
let exit_code=$?+$exit_code
[ "${CHUNK_FILE}" ]
let exit_code=$?+$exit_code
[ "${HOST}" ]
let exit_code=$?+$exit_code
[ "${SOURCE_PATH}" ]
let exit_code=$?+$exit_code
[ "${RAW_DATA_PATH}" ]
let exit_code=$?+$exit_code
[ "${FILE_COUNT}" ]
let exit_code=$?+$exit_code
[ "${DATA_SIZE}" ]
let exit_code=$?+$exit_code

if [ $exit_code -eq 0 ]
then
  { echo "\nvalidated environment variables..." >> $LOG_FILE; }
else
  { echo "\nERROR: file transfer failed. missing required environment variables!" >> $LOG_FILE; exit 1 ; }
fi

# create destination dir if it does not exist
mkdir -p $RAW_DATA_PATH

# set num_procs equal to magnitude of bandwidth.
# i.e. num_proc = bwlimit with last character stripped
bw=$BWLIMIT
num_procs=${bw%?}

########################### transfer files ###########################

# transfer whole files without delta-xfer algorithm from specified source location to destination location.
# spawn one process per unit of network bandwidth
# delete any files in the destination location that are not in the source location
# output stats at the end
# output a log file
# exclude transfer of any files with the excluded file extensions
# limit each process's network utilization to the specified bwlimit
time cat $CHUNK_FILE | xargs -I {} -P $num_procs -n 1 \
rsync -ahW --delete --stats --log-file=$LOG_FILE \
--exclude='*.'{$EXCLUDES} \
--bwlimit=$BWLIMIT  \
$HOST:$SOURCE_PATH/{} $RAW_DATA_PATH

let exit_code=$?+$exit_code
echo "\nexit code after rsync = $exit_code" >> $LOG_FILE

########################### verify post-conditions ###########################

# verify and log and log file counts
file_count=$(find $RAW_DATA_PATH -type f -name "*" | wc -l)
[ $FILE_COUNT -eq $file_count ];

let exit_code=$?+$exit_code
echo "\nexit code after file_count verification = $exit_code" >> $LOG_FILE

# verify and log transfer data size (bytes)
data_size=$(find $RAW_DATA_PATH -type d | xargs du -s | cut -f1)
[ $DATA_SIZE -eq $data_size ];

let exit_code = $? + $exit_code
echo "\nexit code after data_size verification = $exit_code" >> $LOG_FILE

########################### teardown ###########################

# the end
echo "\n" >> $LOG_FILE
echo "=============================================================" >> $LOG_FILE
echo "\n" >> $LOG_FILE

if [ $exit_code -eq 0 ]
then
        { echo "file transfer completed successfully!" ; exit 0 ; }
else
        { echo "file transfer failed! See $LOG_FILE" ; exit 1 ; }
fi
