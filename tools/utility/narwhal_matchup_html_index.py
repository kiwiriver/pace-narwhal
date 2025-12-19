#!/usr/bin/env python3
"""
HTML Viewer Generator for PACE Data - Single File Selection Version
Generates an HTML viewer for comparing one HTML file from each category.
"""

import os
import argparse
import re
from pathlib import Path

def generate_html_viewer(base_url, title="PACE Data Comparison Viewer", output="index.html", parse_mode="auto"):
    """
    Generate HTML viewer for comparing one file from each of harp2_fastmapol, spexone_fastmapol, and spexone_remotap folders.
    """
    
    # Enhanced date extraction for validation files
    extract_function = '''
function extractDate(filename) {
  // Try date range format first (2025-03-01-2025-10-31 or 20250301-20251031)
  let rangeMatch = filename.match(/(\\d{4}-\\d{2}-\\d{2})-(\\d{4}-\\d{2}-\\d{2})/);
  if (rangeMatch) return `${rangeMatch[1]} to ${rangeMatch[2]}`;
  
  rangeMatch = filename.match(/(\\d{8})-(\\d{8})/);
  if (rangeMatch) {
    const start = formatDateString(rangeMatch[1]);
    const end = formatDateString(rangeMatch[2]);
    return `${start} to ${end}`;
  }
  
  // Try timestamp format (20240906T202704)
  let timestampMatch = filename.match(/(\\d{8}T\\d{6})/);
  if (timestampMatch) return timestampMatch[1];
  
  // Try single date formats (2025-11-09 or 20251109)
  let dateMatch = filename.match(/(\\d{4}-\\d{2}-\\d{2})/);
  if (dateMatch) return dateMatch[1];
  
  dateMatch = filename.match(/(\\d{8})/);
  if (dateMatch) return formatDateString(dateMatch[1]);
  
  return null;
}

function formatDateString(dateStr) {
  if (dateStr.length === 8) {
    return `${dateStr.substr(0, 4)}-${dateStr.substr(4, 2)}-${dateStr.substr(6, 2)}`;
  }
  return dateStr;
}

function formatDisplayValue(value) {
  if (!value) return value;
  
  // If it's already a date range, return as-is
  if (value.includes(' to ')) return value;
  
  // If it's a timestamp format (20240906T202704)
  if (value.length === 15 && value.includes('T')) {
    const year = value.substr(0, 4);
    const month = value.substr(4, 2);
    const day = value.substr(6, 2);
    const hour = value.substr(9, 2);
    const minute = value.substr(11, 2);
    const second = value.substr(13, 2);
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
  }
  
  return value;
}'''

    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    height: 100vh;
  }}
  header {{
    background: #f0f0f0;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex-shrink: 0;
  }}
  .control-row {{
    display: flex;
    align-items: center;
    gap: 15px;
    flex-wrap: wrap;
  }}
  .control-group {{
    display: flex;
    align-items: center;
    gap: 5px;
  }}
  input, select {{
    padding: 5px;
    font-size: 1rem;
  }}
  /* File selection dropdowns */
  .dropdown-row {{
    display: flex;
    gap: 15px;
    align-items: flex-start;
    flex-wrap: wrap;
    margin-top: 10px;
    padding: 15px;
    background: #f8f8f8;
    border: 1px solid #ddd;
    border-radius: 4px;
  }}
  .dropdown-group {{
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: 250px;
    flex: 1;
  }}
  .dropdown-group label {{
    font-weight: bold;
    color: #333;
    font-size: 0.95rem;
  }}
  .dropdown-group select {{
    width: 100%;
    min-width: 250px;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: white;
  }}
  .dropdown-group select:focus {{
    outline: none;
    border-color: #0066cc;
    box-shadow: 0 0 5px rgba(0,102,204,0.3);
  }}
  #columnToggles {{
    display: flex;
    gap: 6px;
    margin-top: 6px;
  }}
  #columnToggles button {{
    background: #0077cc;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 15px;
    cursor: pointer;
    font-size: 0.9rem;
  }}
  #columnToggles button.active {{
    background: #004c99;
  }}
  #columnToggles button:hover {{
    background: #005fa3;
  }}
  .status-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 5px;
    font-size: 0.9rem;
    color: #666;
    padding: 5px 0;
  }}
  .action-buttons {{
    display: flex;
    gap: 10px;
    align-items: center;
  }}
  .action-buttons button {{
    background: #28a745;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 15px;
    cursor: pointer;
    font-size: 0.9rem;
  }}
  .action-buttons button:hover {{
    background: #218838;
  }}
  .sync-button.active {{
    background: #dc3545 !important;
  }}
  .sync-button.active:hover {{
    background: #c82333 !important;
  }}
  main {{
    flex: 1;
    display: flex;
    overflow: hidden;
    min-height: 0;
  }}
  .column {{
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    border-right: 1px solid #ddd;
    display: flex;
    flex-direction: column;
  }}
  .column:last-child {{
    border-right: none;
  }}
  .column h2 {{
    text-align: center;
    background: #fafafa;
    margin: 0 0 10px 0;
    padding: 15px 0;
    color: #0066cc;
    border-bottom: 2px solid #0066cc;
    flex-shrink: 0;
  }}
  .file-container {{
    flex: 1;
    display: flex;
    flex-direction: column;
  }}
  .file-label {{
    font-weight: bold;
    color: #333;
    margin: 0 0 10px 0;
    padding: 10px;
    background: #f9f9f9;
    border-left: 4px solid #0066cc;
    border-radius: 4px;
    flex-shrink: 0;
  }}
  .file-stats {{
    font-size: 0.85rem;
    color: #666;
    margin-top: 5px;
    font-weight: normal;
  }}
  a {{
    text-decoration: none;
    color: #0066cc;
    display: block;
    margin: 0 0 10px 0;
    word-wrap: break-word;
    padding: 5px;
    background: #f0f8ff;
    border-radius: 4px;
    flex-shrink: 0;
  }}
  a:hover {{
    background: #e6f3ff;
    text-decoration: underline;
  }}
  iframe {{
    width: 100%;
    height: 8000px;
    border: 1px solid #ddd;
    border-radius: 5px;
    flex-shrink: 0;
  }}
  .iframe-container {{
    position: relative;
    flex-shrink: 0;
  }}
  .expand-button {{
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(255,255,255,0.9);
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 5px 10px;
    cursor: pointer;
    font-size: 0.8rem;
    z-index: 100;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  }}
  .expand-button:hover {{
    background: rgba(255,255,255,1);
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }}
  .no-files {{
    text-align: center;
    color: #999;
    font-style: italic;
    padding: 40px 20px;
    background: #f8f8f8;
    border-radius: 4px;
    margin: 20px 0;
  }}
  .loading {{
    text-align: center;
    color: #0066cc;
    font-style: italic;
    padding: 20px;
  }}
</style>
</head>
<body>
  <header>
    <div class="control-row">
      <h3>{title}</h3>
      <div class="action-buttons">
        <button onclick="clearAllSelections()">Clear All</button>
        <button class="sync-button" onclick="toggleSyncScrolling()">Sync Scroll</button>
        <button onclick="openAllInNewTabs()">Open All in Tabs</button>
      </div>
    </div>

    <!-- File selection dropdowns -->
    <div class="dropdown-row">
      <div class="dropdown-group">
        <label for="harp2Select">HARP2 FastMAPOL Files:</label>
        <select id="harp2Select" onchange="selectFile('col1', this.value)">
          <option value="">Select a file...</option>
        </select>
      </div>
      <div class="dropdown-group">
        <label for="spexoneFastSelect">SPEXone FastMAPOL Files:</label>
        <select id="spexoneFastSelect" onchange="selectFile('col2', this.value)">
          <option value="">Select a file...</option>
        </select>
      </div>
      <div class="dropdown-group">
        <label for="spexoneRemotapSelect">SPEXone REMOTAP Files:</label>
        <select id="spexoneRemotapSelect" onchange="selectFile('col3', this.value)">
          <option value="">Select a file...</option>
        </select>
      </div>
    </div>
    
    <div id="columnToggles">
      <button class="active" data-col="col1">HARP2 FastMAPOL</button>
      <button class="active" data-col="col2">SPEXone FastMAPOL</button>
      <button class="active" data-col="col3">SPEXone REMOTAP</button>
    </div>
    
    <div class="status-row">
      <div id="statusInfo">Loading files...</div>
      <div id="fileStats"></div>
    </div>
  </header>

  <main>
    <div class="column" id="col1">
      <h2>HARP2 FastMAPOL</h2>
      <div class="no-files">Select a file from the dropdown above</div>
    </div>
    <div class="column" id="col2">
      <h2>SPEXone FastMAPOL</h2>
      <div class="no-files">Select a file from the dropdown above</div>
    </div>
    <div class="column" id="col3">
      <h2>SPEXone REMOTAP</h2>
      <div class="no-files">Select a file from the dropdown above</div>
    </div>
  </main>

<script>
const baseURL = "{base_url}";

const folderPaths = {{
  col1: "harp2_fastmapol/html/",
  col2: "spexone_fastmapol/html/",
  col3: "spexone_remotap/html/"
}};

const columnNames = {{
  col1: "HARP2 FastMAPOL",
  col2: "SPEXone FastMAPOL", 
  col3: "SPEXone REMOTAP"
}};

const dropdownIds = {{
  col1: "harp2Select",
  col2: "spexoneFastSelect",
  col3: "spexoneRemotapSelect"
}};

let allFiles = {{}};
let selectedFiles = {{}};
let scrollSynced = false;

// Fetch file list from specific folder
async function fetchFileList(folder) {{
  try {{
    const response = await fetch(baseURL + folder);
    if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
    const text = await response.text();
    const matches = [...text.matchAll(/href="([^"]+\\.html)"/g)];
    return matches.map(m => m[1]).filter(f => f.startsWith('val_') && !f.includes('~'));
  }} catch (error) {{
    console.error(`Error fetching files from ${{folder}}:`, error);
    return [];
  }}
}}

// Fetch all files from all folders
async function fetchAllFiles() {{
  document.getElementById('statusInfo').textContent = 'Loading files...';
  
  for (const [colId, folderPath] of Object.entries(folderPaths)) {{
    allFiles[colId] = await fetchFileList(folderPath);
  }}
  
  // Populate dropdowns
  populateDropdowns();
  
  const totalFiles = Object.values(allFiles).reduce((sum, files) => sum + files.length, 0);
  document.getElementById('statusInfo').textContent = `Ready - ${{totalFiles}} files available`;
  updateFileStats();
}}

// Populate dropdown menus with available files
function populateDropdowns() {{
  for (const [colId, files] of Object.entries(allFiles)) {{
    const dropdown = document.getElementById(dropdownIds[colId]);
    dropdown.innerHTML = '<option value="">Select a file...</option>';
    
    if (files && files.length > 0) {{
      // Group files by date for better organization
      const filesByDate = {{}};
      files.forEach(file => {{
        const date = extractDate(file);
        const dateKey = date || 'Unknown Date';
        if (!filesByDate[dateKey]) filesByDate[dateKey] = [];
        filesByDate[dateKey].push(file);
      }});
      
      // Add files organized by date
      Object.keys(filesByDate).sort().forEach(date => {{
        if (filesByDate[date].length === 1) {{
          // Single file - add directly
          const option = document.createElement('option');
          option.value = filesByDate[date][0];
          option.textContent = `${{formatDisplayValue(date)}} - ${{filesByDate[date][0]}}`;
          dropdown.appendChild(option);
        }} else {{
          // Multiple files - create optgroup
          const optgroup = document.createElement('optgroup');
          optgroup.label = formatDisplayValue(date);
          
          filesByDate[date].forEach((file, index) => {{
            const option = document.createElement('option');
            option.value = file;
            option.textContent = `${{index + 1}}. ${{file}}`;
            optgroup.appendChild(option);
          }});
          
          dropdown.appendChild(optgroup);
        }}
      }});
    }} else {{
      const option = document.createElement('option');
      option.value = "";
      option.textContent = "No files available";
      option.disabled = true;
      dropdown.appendChild(option);
    }}
  }}
}}

{extract_function}

// Select and display a specific file for a column
function selectFile(colId, filename) {{
  const col = document.getElementById(colId);
  
  if (!filename) {{
    // Clear selection
    col.innerHTML = `
      <h2>${{columnNames[colId]}}</h2>
      <div class="no-files">Select a file from the dropdown above</div>
    `;
    delete selectedFiles[colId];
    updateFileStats();
    return;
  }}
  
  selectedFiles[colId] = filename;
  const folderPath = folderPaths[colId];
  const date = extractDate(filename);
  
  // Clear column and add selected file
  col.innerHTML = `
    <h2>${{columnNames[colId]}}</h2>
    <div class="file-container">
      <div class="file-label">
        ${{columnNames[colId]}} - ${{formatDisplayValue(date)}}
        <div class="file-stats">File: ${{filename}}</div>
      </div>
      <a href="${{baseURL + folderPath + filename}}" target="_blank">${{filename}}</a>
      <div class="iframe-container">
        <button class="expand-button" onclick="toggleIframeHeight(this, '${{colId}}')">Expand</button>
        <iframe src="${{baseURL + folderPath + filename}}" onload="trackIframeLoad('${{colId}}')"></iframe>
      </div>
    </div>
  `;
  
  updateFileStats();
}}

// Toggle iframe height
function toggleIframeHeight(button, colId) {{
  const iframe = button.nextElementSibling;
  const currentHeight = iframe.style.height || '8000px';
  
  if (currentHeight === '8000px') {{
    iframe.style.height = '4000px';
    button.textContent = 'Expand';
  }} else {{
    iframe.style.height = '8000px';
    button.textContent = 'Shrink';
  }}
}}

// Track iframe loading
function trackIframeLoad(colId) {{
  console.log(`Loaded iframe for ${{colId}}`);
}}

// Update file statistics
function updateFileStats() {{
  const selectedCount = Object.keys(selectedFiles).length;
  const totalFiles = Object.values(allFiles).reduce((sum, files) => sum + files.length, 0);
  
  const stats = [];
  for (const [colId, files] of Object.entries(allFiles)) {{
    const columnName = columnNames[colId].split(' ')[0]; // Get instrument name
    const selectedIndicator = selectedFiles[colId] ? '●' : '○';
    stats.push(`${{selectedIndicator}} ${{columnName}}: ${{files.length}}`);
  }}
  
  document.getElementById('fileStats').textContent = 
    `Selected: ${{selectedCount}}/3 | ${{stats.join(' | ')}}`;
}}

// Clear all selections
function clearAllSelections() {{
  for (const [colId, dropdownId] of Object.entries(dropdownIds)) {{
    document.getElementById(dropdownId).value = '';
    selectFile(colId, '');
  }}
}}

// Toggle synchronized scrolling
function toggleSyncScrolling() {{
  const button = event.target;
  scrollSynced = !scrollSynced;
  
  if (scrollSynced) {{
    button.textContent = 'Unsync Scroll';
    button.classList.add('active');
    
    // Add scroll listeners
    const columns = document.querySelectorAll('.column');
    columns.forEach(col => {{
      col.addEventListener('scroll', handleSyncScroll);
    }});
  }} else {{
    button.textContent = 'Sync Scroll';
    button.classList.remove('active');
    
    // Remove scroll listeners
    const columns = document.querySelectorAll('.column');
    columns.forEach(col => {{
      col.removeEventListener('scroll', handleSyncScroll);
    }});
  }}
}}

function handleSyncScroll(event) {{
  if (!scrollSynced) return;
  
  const sourceCol = event.target;
  const scrollTop = sourceCol.scrollTop;
  const scrollLeft = sourceCol.scrollLeft;
  
  document.querySelectorAll('.column').forEach(col => {{
    if (col !== sourceCol) {{
      col.scrollTop = scrollTop;
      col.scrollLeft = scrollLeft;
    }}
  }});
}}

// Open all selected files in new tabs
function openAllInNewTabs() {{
  let openedCount = 0;
  
  for (const [colId, filename] of Object.entries(selectedFiles)) {{
    const folderPath = folderPaths[colId];
    const url = baseURL + folderPath + filename;
    window.open(url, '_blank');
    openedCount++;
  }}
  
  if (openedCount === 0) {{
    alert('No files selected. Please select files from the dropdowns first.');
  }} else {{
    alert(`Opened ${{openedCount}} files in new tabs.`);
  }}
}}

// Toggle column visibility
document.addEventListener("DOMContentLoaded", () => {{
  const toggleButtons = document.querySelectorAll("#columnToggles button");
  toggleButtons.forEach(btn => {{
    btn.addEventListener("click", () => {{
      const colId = btn.dataset.col;
      const col = document.getElementById(colId);
      const isActive = btn.classList.toggle("active");

      if (isActive) {{
        col.style.display = "flex";
      }} else {{
        col.style.display = "none";
      }}

      // Recalculate visible columns and adjust width
      const visibleCols = [...document.querySelectorAll(".column")]
        .filter(c => c.style.display !== "none");
      const widthPercent = 100 / visibleCols.length;
      visibleCols.forEach(c => (c.style.flex = `0 0 ${{widthPercent}}%`));
    }});
  }});

  // Initialize
  fetchAllFiles();
}});
</script>
</body>
</html>'''

    # Write the HTML file
    with open(output, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"HTML comparison viewer generated: {output}")
    print(f"Base URL: {base_url}")
    print(f"Title: {title}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML comparison viewer for PACE validation data - Single File Selection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This viewer allows selection of one HTML file from each category for comparison:
- harp2_fastmapol/html/
- spexone_fastmapol/html/  
- spexone_remotap/html/

Features:
- Single file selection per category via dropdowns
- Side-by-side comparison with 8000px iframe height
- Synchronized scrolling option
- File organization by date periods
- Clear all selections and open in new tabs options

Example:
  python single_file_viewer.py --base-url "https://oceancolor.gsfc.nasa.gov/fileshare/meng_gao/pace/validation/summary/" --title "PACE Single File Comparison"
        """
    )
    
    parser.add_argument(
        '--base-url',
        required=True,
        help='Base URL for the validation summary directory'
    )
    
    parser.add_argument(
        '--title',
        default='PACE Single File Comparison Viewer',
        help='Title for the HTML page'
    )
    
    parser.add_argument(
        '--output',
        default='single_file_viewer.html',
        help='Output HTML filename'
    )
    
    args = parser.parse_args()
    
    # Ensure base URL ends with /
    base_url = args.base_url
    if not base_url.endswith('/'):
        base_url += '/'
    
    # Generate the HTML viewer
    generate_html_viewer(
        base_url=base_url,
        title=args.title,
        output=args.output
    )

if __name__ == "__main__":
    main()