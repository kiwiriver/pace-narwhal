#!/bin/bash
#SBATCH --job-name=val
#SBATCH --ntasks=1
#SBATCH --partition=research
#SBATCH --array=0-10%3 #concurrnt 3

### rerun failed case
###SBATCH --array=0,1,7,8

# Your env activation
mamba activate py3.12

start_date="2024-03-01"
yesterday=$(date -d "yesterday" +"%Y-%m-%d")
num_days=$(( ($(date -d "$yesterday" +%s) - $(date -d "$start_date" +%s)) / 86400 + 1 ))

batch_size=70

array_id=$SLURM_ARRAY_TASK_ID
first_day=$(( array_id * batch_size ))
last_day=$(( first_day + batch_size - 1 ))

echo 'first, last day' $first_day $last_day

# Don't go beyond available days
if [ $last_day -ge $num_days ]; then
    last_day=$(( num_days - 1 ))
fi

folder_name="test1_download_test"
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
    
    # Run the Python file
    python "$python_file" --input_folder ${folder_name} --tspan_start $tspan_start --tspan_end $tspan_end \

done

echo "Files created in folder: $folder_name"

