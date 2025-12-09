"""
locations: https://asdc.larc.nasa.gov/data/PACE-PAX/AircraftRemoteSensing_ER2_HSRL2_Data_1/
"""
import re
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def get_h5_links(base_url):
    """Extract all .h5 file links from the webpage"""
    
    # Send GET request
    response = requests.get(base_url)
    response.raise_for_status()
    
    # Parse HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all links ending with .h5
    h5_links = []
    
    # Look for all <a> tags
    for link in soup.find_all('a', href=True):
        href = link['href']
        
        # Check if the link ends with .h5
        if href.endswith('.h5'):
            # Convert relative URLs to absolute URLs
            full_url = urljoin(base_url, href)
            h5_links.append(full_url)

    h5_links=sorted(list(set(h5_links)))
    
    return h5_links

def download_h5_files(h5_files, download_dir="hsrl2_r1"):
    """
    Download all .h5 files from a list of URLs into a specified directory
    
    Args:
        h5_files (list): List of URLs to download
        download_dir (str): Directory to save files (default: 'hsrl2_r1')
    """
    
    # Create the download directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)
    
    successful_downloads = 0
    failed_downloads = 0
    
    print(f"Starting download of {len(h5_files)} files into '{download_dir}' folder...")
    print("-" * 60)
    
    for i, url in enumerate(h5_files, 1):
        # Extract filename from URL
        filename = os.path.basename(urlparse(url).path)
        filepath = os.path.join(download_dir, filename)
        
        print(f"[{i}/{len(h5_files)}] Downloading: {filename}")
        
        try:
            # Download the file
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save the file
            with open(filepath, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            
            print(f"✓ Successfully downloaded: {filename}")
            successful_downloads += 1
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to download {filename}: {e}")
            failed_downloads += 1
        except Exception as e:
            print(f"✗ Error saving {filename}: {e}")
            failed_downloads += 1
    
    print("-" * 60)
    print(f"Download complete!")
    print(f"✓ Successful downloads: {successful_downloads}")
    print(f"✗ Failed downloads: {failed_downloads}")
    print(f"Files saved to: {os.path.abspath(download_dir)}")