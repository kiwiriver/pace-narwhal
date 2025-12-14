<img src="logo/narwhal_logo_v1.png" alt="ORCA Logo" width="200"/>

# PACE Toolkit for validation: NARWHAL-Nail down Aerosol Retrieval WitH ALl

### Main Features

*** Validation data included: AERONET (AERONET OC, MAN), PACE-PAX, PVST, EarthCARE
---

## Contribution

This repository is developed and maintained by the **PACE FastMAPOL team**. Any contributions are welcome. 

### Related Projects

---

## Live Examples

---

## API Key Configuration

For development and testing, configure your API keys:

**Earthdata App Key**: Save to `key/earthdata_appkey.txt`

> 🔒 **Security Note**: All files in the `key/` folder are automatically ignored by git



## Installation & Configuration
### File structure
- /tools: source code, do not change this folder name, all modules are imported follow the pattern of import tools.orca_*
- /scripts: script to run the code
- /test: run test here
- /html: html template to show multiple rapid response. Move it to your folder and change its name to index.html
- /logo: orca logos designed by Daniel & Meng.

### Environment Variables
location of the key and the path of the package can be set through environmental variables (see scripts in /run)
```bash
export MAPOLTOOL_KEY_PATH="/mnt/mfs/mgao1/analysis/github/mapoltool/lab/key/"
export MAPOLTOOL_LAB_PATH="/mnt/mfs/mgao1/analysis/github/mapoltool/lab/narwhal/"
```

### Custom HTML Headers for different applications

Configure custom header information in:
```bash
/tools/orca_header.py
```
## Testing

### Example scripts are available in the /script 
Symbolic links are also included in /test folder (results excluded from git)
if not there run
```bash
bash link.sh
```

after testing the code, remove all data except the scripts
```bash
bash clean.sh
```

## Automated Processing
Set up cron jobs for automatic report generation:

### Cron Management Commands
```bash
crontab -l #list
crontab -e #edit
date #system date                                                                                                     
timedatectl #check and set system time
systemctl status cron #check cron job status
```

### Example Cron Configuration

