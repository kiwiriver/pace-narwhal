#!/bin/bash
#SBATCH --job-name=val
#SBATCH --ntasks=1
#SBATCH --partition=research
#SBATCH --threads-per-core=1
#SBATCH --cpus-per-task=8
#SBATCH --array=0-100 

##SBATCH --array=0-10%5 #concurrnt 3
##SBATCH --array=0-100%10 #concurrnt 10

### rerun failed case
###SBATCH --array=0,1,7,8

# Your env activation
mamba activate py3.12

file1="/home/mgao/github/mapoltool/tools/aeronet2_batch/run_matchup.py"
file2="/accounts/mgao1/github/mapoltool/tools/aeronet2_batch/run_matchup.py"
if [ -f "$file1" ]; then
    pyfile="$file1"
elif [ -f "$file2" ]; then
    pyfile="$file2"
else
    echo "Neither file exists. Exiting."
    exit 1
fi
echo "Using file: $pyfile"


###########################
#aeronet/man/ data location
val_path='/mnt/mfs/mgao1/develop/aeronet/aeronet_val01/data/aeronet_data_split/'
loc_suite='MAN_AOD15_series'

#product="harp2_fastmapol"
product="spexone_fastmapol"
#product='spexone_remotap'  # Change this to switch between products

if [ "$product" = "harp2_fastmapol" ]; then
    echo "Using HARP2 FastMAPOL configuration"
    all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[30,90], "nv_dolp":[30,90],"quality_flag":[0,5]}'
#    all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[30,90], "nv_dolp":[30,90],"quality_flag":[0,0]}'
    
elif [ "$product" = "spexone_fastmapol" ]; then
    echo "Using SPEXone FastMAPOL configuration"
    all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[120,170], "nv_dolp":[120,170], "quality_flag":[0,5]}'
    #all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[120,170], "nv_dolp":[120,170],"quality_flag":[0,0]}'

    
elif [ "$product" = "spexone_remotap" ]; then
    echo "Using SPEXone RemoTAP configuration"
#    all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[170,170], "nv_dolp":[170,170],"quality_flag":[0,5]}'
    all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[170,170], "nv_dolp":[170,170],"quality_flag":[0,0]}'

else
    echo "Error: Unknown product '$product'"
    echo "Available options: harp2_fastmapol, spexone_fastmapol, spexone_remotap"
    exit 1
fi

# Display the selected configuration
echo "Product: $product"
echo "Rules: $all_rules"

###########################

appkey="KEY_REDACTED"
api_key="KEY_REDACTED"

val_source='MAN'
start_date="2024-03-01"
yesterday=$(date -d "yesterday" +"%Y-%m-%d")
num_days=$(( ($(date -d "$yesterday" +%s) - $(date -d "$start_date" +%s)) / 86400 + 1 ))

#batch_size=70
batch_size=7
#batch_size=600
#batch_size=100
#batch_size=200
batch_size=1

array_id=$SLURM_ARRAY_TASK_ID

#array_id=102 #2024/06/11
#array_id=95 #2024/06/04
#array_id=73 #2024/05/13
#array_id=81 #2024/05/21
array_id=323 #2025/01/18

first_day=$(( array_id * batch_size ))
last_day=$(( first_day + batch_size - 1 ))

echo 'first, last day' $first_day $last_day

# Don't go beyond available days
if [ $last_day -ge $num_days ]; then
    last_day=$(( num_days - 1 ))
fi

folder_name="test0"
mkdir -p "$folder_name"

for day_offset in $(seq $first_day $last_day); do

    sleep 10
    tspan_start=$(date -d "$start_date +$day_offset days" +"%Y-%m-%d")
    tspan_end=$tspan_start

    echo 'tspan start end' $tspan_start $tspan_end
    if [[ "$tspan_start" > "$yesterday" ]]; then
        echo "Date $tspan_start exceeds yesterday ($yesterday), skipping."
        continue
    fi
    
    # Create the Python file in the new folder
    mkdir -p "${folder_name}/python_tmp"
    python_file="${folder_name}/python_tmp/${product}_newpyjob_${tspan_start}.py"
    sed "s/<appkey>/\"$appkey\"/g" $pyfile | sed "s/<api_key>/\"$api_key\"/g" > "$python_file"
    ls "$python_file"
    
    # Run the Python file
    python "$python_file" --val_path ${val_path} --loc_suite ${loc_suite} --input_folder ${folder_name} --tspan_start $tspan_start --tspan_end $tspan_end \
	   --product $product --all_rules "${all_rules}" --no_cloud --val_source "${val_source}"
    #--no_cloud
    #--no_rm

done

echo "Files created in folder: $folder_name"

