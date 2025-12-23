## Find all matching folders and show their sizes
##find . -type d \( -name "data_l1c" -o -name "data_l2" \) -exec du -sh {} \;

#!/bin/bash
echo "=== FOLDER SIZE ANALYSIS ==="
echo "Searching for data_l1c and data_l2 folders..."

# Find and display folders with sizes
folders=$(find . -type d \( -name "data_l1c" -o -name "data_l2" \))

if [ -z "$folders" ]; then
    echo "No matching folders found."
    exit 0
fi

echo "Found folders and their sizes:"
echo "=============================="
total_size=0

while IFS= read -r folder; do
    if [ -d "$folder" ]; then
        size=$(du -sm "$folder" | cut -f1)
        size_human=$(du -sh "$folder" | cut -f1)
        echo "$size_human  $folder"
        total_size=$((total_size + size))
    fi
done <<< "$folders"

echo "=============================="
echo "Total size: ${total_size} MB"
echo ""
echo "Folders to be deleted:"
echo "$folders"
echo ""
read -p "Do you want to proceed with deletion? (y/N): " confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    echo "Deleting folders..."
    find . -type d \( -name "data_l1c" -o -name "data_l2" \) -exec rm -rf {} +
    echo "Deletion completed."
else
    echo "Operation cancelled."
fi
