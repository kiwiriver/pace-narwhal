#!/bin/bash
#SBATCH --job-name=val
#SBATCH --ntasks=1
#SBATCH --partition=research
#SBATCH --threads-per-core=1
#SBATCH --cpus-per-task=4
#SBATCH --array=0-0

# Your env activation
mamba activate py3.12

#file1="/home/mgao/github/mapoltool/tools/aeronet2_batch/run_combine.py"
#file2="/accounts/mgao1/github/mapoltool/tools/aeronet2_batch/run_combine.py"

#if [ -f "$file1" ]; then
#    pyfile="$file1"
#elif [ -f "$file2" ]; then
#    pyfile="$file2"
#else
#    echo "Neither file exists. Exiting."
#    exit 1
#fi
#echo "Using file: $pyfile"

#pyfile="/mnt/mfs/mgao1/analysis/github/mapoltool/tools/aeronet2_batch/run_combine.py"
pyfile="/mnt/mfs/mgao1/analysis/github/pace-narwhal/tools/run/run4_combine.py"

###########################
product="harp2_fastmapol"
product="spexone_fastmapol"
#product='spexone_remotap'  # Change this to switch between products

#val_source='AERONET'
val_source='AERONET_OC'
#val_source='MAN'
#xval_source='PACE_PAX'
#val_source='EARTHCARE' 

if [ "$product" = "harp2_fastmapol" ]; then
    echo "Using HARP2 FastMAPOL configuration"
    all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[30,90], "nv_dolp":[30,90],"quality_flag":[0,0]}'
    all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[30,90], "nv_dolp":[30,90],"quality_flag":[0,5]}'
    subset_rules='{"chi2_max":2, "nv_min":30, "min_aod":0.2, "max_aod":1}'
    subset_rules='{"chi2_max":2, "nv_min":30, "min_aod":0.1, "max_aod":1}'
    subset_rules='{"chi2_max":2, "nv_min":30, "min_aod":0.01, "max_aod":1}'
    #subset_rules='{"chi2_max":2, "nv_min":60, "min_aod":0.2, "max_aod":1}'

    
elif [ "$product" = "spexone_fastmapol" ]; then
    echo "Using SPEXone FastMAPOL configuration"
    all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[120,170], "nv_dolp":[120,170],"quality_flag":[0,0]}'
    #all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[120,170], "nv_dolp":[120,170],"quality_flag":[0,5]}'

    subset_rules='{"chi2_max":2, "nv_min":120, "min_aod":0.2, "max_aod":1}'
    subset_rules='{"chi2_max":2, "nv_min":120, "min_aod":0.1, "max_aod":1}'
    subset_rules='{"chi2_max":2, "nv_min":120, "min_aod":0.01, "max_aod":1}'
    #subset_rules='{"chi2_max":2, "nv_min":160, "min_aod":0.2, "max_aod":1}'
    
elif [ "$product" = "spexone_remotap" ]; then
    echo "Using SPEXone RemoteAP configuration"
    all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[170,170], "nv_dolp":[170,170],"quality_flag":[0,0]}'
    all_rules='{"search_center_radius": 5, "search_grid_delta":10, "delta_hour":2, "chi2":[0,2], "nv_ref":[170,170], "nv_dolp":[170,170],"quality_flag":[0,5]}'

    subset_rules='{"chi2_max":2, "nv_min":170, "min_aod":0.2, "max_aod":1}'
    subset_rules='{"chi2_max":2, "nv_min":170, "min_aod":0.1, "max_aod":1}'
    
else
    echo "Error: Unknown product '$product'"
    echo "Available options: harp2_fastmapol, spexone_fastmapol, spexone_remotap"
    exit 1
fi

# Display the selected configuration
echo "Product: $product"
echo "Rules: $all_rules, $subset_rules"

###########################

#local_dir_base="/accounts/mgao1/mfs_pace/pace/validation/val5/test0/"
#share_dir_base="/mnt/mfs/FILESHARE/meng_gao/pace/validation/share/"

#local_dir_base="/accounts/mgao1/mfs_pace/pace/validation/val6_calibration/test_v3.9.6/"
#share_dir_base="/mnt/mfs/FILESHARE/meng_gao/pace/validation/share/test_v3.9.6"


#local_dir_base="/accounts/mgao1/mfs_pace/pace/validation/val6_calibration/test_v3.9.4/"
#share_dir_base="/mnt/mfs/FILESHARE/meng_gao/pace/validation/share/test_v3.9.4"

local_dir_base="/accounts/mgao1/mfs_pace/pace/validation/val5/test0/"
share_dir_base="/mnt/mfs/FILESHARE/meng_gao/pace/validation/share/"

echo "local directory", ${local_dir_base}
echo "share directory", ${share_dir_base}

tspan_start="2024-03-01"
tspan_end="2025-10-31"

tspan_start="2024-09-01"
tspan_end="2024-09-30"

tspan_start="2024-09-01"
tspan_end="2024-09-30"

tspan_start="2024-07-01"
tspan_end="2025-07-31"

echo 'tspan start end' $tspan_start $tspan_end
    
# Run the Python file
python "$pyfile" --local_dir_base ${local_dir_base} --share_dir_base ${share_dir_base} --product ${product} \
--tspan_start $tspan_start --tspan_end $tspan_end --all_rules "${all_rules}" --subset_rules "${subset_rules}" \
--val_source ${val_source}

echo "Done"

