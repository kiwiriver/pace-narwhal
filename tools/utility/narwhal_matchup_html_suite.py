import base64
from PIL import Image
import os
import re
from collections import defaultdict
from tools.narwhal_matchup_html_tool import *
#sort_variables, parse_filename
from tools.narwhal_matchup_html_file import process_suites_and_generate_html

################ simple function just put image together
def create_html_with_embedded_images(folder_path, ordered_files, output_html='images_embedded.html', 
                                    resolution_factor=2, quality=85,
                                    title="PACE Validation", title2=None, logo_path=None):
    """
    Create an HTML file with all images embedded as Base64,
    putting 'aeronet_match' ones at the top and images as wide as the screen.

    todo:
        logo_path not implemented! only implemented for the combined pages, not daily page
    """    
    html = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        '<meta charset="UTF-8">',
        f'<title>{title}</title>',
        '<style>img {width: 100%; height: auto; display: block; margin-bottom: 32px;}</style>',
        '</head>',
        '<body>',
        f'<h1>{title}</h1>',
        f'<p>{title2 or ""}</p>'
    ]
        
    for fname in ordered_files:
        fpath = os.path.join(folder_path, fname)
        b64 = encode_image_to_base64(fpath, factor=resolution_factor, quality=quality)
        if b64:
            ext = fname.lower().split('.')[-1]
            if ext == "png":
                mime = "png"
            elif ext == "gif":
                mime = "gif"
            elif ext == "bmp":
                mime = "bmp"
            else:
                mime = "jpeg"
            html.append(f'<h3>{fname}</h3>')
            html.append(f'<img src="data:image/{mime};base64,{b64}" alt="{fname}">')
        else:
            html.append(f'<p>Could not encode {fname}</p>')

    html.append('</body>')
    html.append('</html>')

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))
        print("Done creating HTML at", output_html)


################
def create_html_with_embedded_images_and_buttons(folder_path, ordered_files, \
                                                 output_html='images_embedded.html', 
                                               resolution_factor=2, quality=85,
                                               title="FastMAPOL Validation vs AERONET", title2=None,\
                                               logo_path=None):
    """
    Create an HTML file with all images embedded as Base64 and clickable buttons to filter by category.
    """
    # Parse and organize files
    parsed_files, suites, variables_by_suite = parse_and_organize_files(ordered_files)
    
    # Generate HTML content
    html_content = generate_html_header(title, title2, logo_path=logo_path)
    
    # Process suites and generate their HTML
    html_content += process_suites_and_generate_html(parsed_files, suites, folder_path, 
                                                   resolution_factor, quality)
    
    # Add JavaScript and close HTML document
    html_content += generate_javascript_and_footer()
    
    # Write HTML file
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
        print(f"Done creating HTML with cleaned up criteria buttons at {output_html}")


def parse_and_organize_files(ordered_files):
    """Parse all filenames and organize by suite and variable."""
    # Define expected suite names for validation
    expected_suites = {
        'AOD15', 'SDA15', 'ALM15', 'HYB15', 'LWN15', 'SEABASS_ALL', 'SEABASS_OCI',\
        'MAN_AOD15_series', 'MAN_SDA15_series',\
        'HSRL2_R1', 'HSRL2_R0', 'HSRL2_RA', 'ATL_ALD_2A'
    }
    
    parsed_files = {}
    suites = set()
    variables_by_suite = defaultdict(set)
    
    # Debug: Print parsing results
    print("Parsing filenames:")
    print("=" * 80)
    
    for fname in ordered_files:
        suite, variable, wavelength, plot_type = parse_filename(fname)
        
        # Validate suite name
        if suite not in expected_suites and suite not in ['UNKNOWN', 'MAN_UNKNOWN']:
            print(f"WARNING: Unexpected suite name '{suite}' for file '{fname}'")
        
        print(f"  {fname:40} -> Suite: {suite:18} Variable: {variable:20} WV: {str(wavelength):8} Type: {plot_type}")
        
        suites.add(suite)
        variables_by_suite[suite].add(variable)
        
        key = f"{suite}_{variable}"
        if key not in parsed_files:
            parsed_files[key] = {
                'suite': suite,
                'variable': variable, 
                'files': [],
                'has_wavelengths': False,
                'wavelengths': set(),
                'has_corr': False,
                'has_hist': False,
                'has_map': False  # Add global map tracking
            }
        
        parsed_files[key]['files'].append({
            'filename': fname,
            'wavelength': wavelength,
            'plot_type': plot_type
        })
        
        if wavelength:
            parsed_files[key]['has_wavelengths'] = True
            parsed_files[key]['wavelengths'].add(wavelength)
        
        if plot_type == 'corr':
            parsed_files[key]['has_corr'] = True
        elif plot_type == 'hist':
            parsed_files[key]['has_hist'] = True
        elif plot_type == 'map':  # Add global map detection
            parsed_files[key]['has_map'] = True
    
    print("=" * 80)
    print(f"Found suites: {sorted(suites)}")
    print("=" * 80)
    for suite in sorted(suites):
        sorted_vars = sort_variables(list(variables_by_suite[suite]))
        print(f"  {suite:20}: {sorted_vars}")
    print("=" * 80)
    
    return parsed_files, suites, variables_by_suite




def format_html_info_matchup(val_source, all_rules, tspan, wvv1, nv_min1, min_aod1, max_aod1):
    """
    Format HTML info for PACE matchup analysis with validation source and criteria.
    """
    
    # Format the rules list nicely
    if isinstance(all_rules, list):
        rules_formatted = ", ".join([str(rule) for rule in all_rules])
    else:
        rules_formatted = str(all_rules)
    
    # Format time span
    if isinstance(tspan, (list, tuple)) and len(tspan) == 2:
        time_range = f"{tspan[0]} to {tspan[1]}"
    else:
        time_range = str(tspan)
    
    # Format wavelength
    if isinstance(wvv1, (list, tuple)):
        wavelength_str = ", ".join([f"{w}nm" for w in wvv1])
    else:
        wavelength_str = f"{wvv1}nm"
    
    title2 = f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 10px 0; font-family: Arial, sans-serif;">
        
        <h3 style="color: #0066cc; margin-bottom: 15px;">PACE with {val_source.upper()} Matchup Analysis</h3>
        
        <div style="background-color: white; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
            <h4 style="color: #333; margin-bottom: 10px;">Matchup Analysis Summary</h4>
            
            <!-- Collapsible Matchup Criteria -->
            <div style="margin: 10px 0;">
                <button id="criteriaToggle" onclick="toggleMatchupCriteria()" 
                        style="background: #0066cc; color: white; border: none; padding: 8px 16px; 
                               border-radius: 4px; cursor: pointer; font-size: 14px; margin-bottom: 10px;
                               transition: background-color 0.3s ease;">
                    📊 Show Matchup Criteria & Data Selection Details
                </button>
                
                <div id="matchupCriteria" style="display: none; background-color: #f8f9fa; 
                                              padding: 15px; border-radius: 4px; border-left: 4px solid #0066cc;
                                              transition: all 0.3s ease; overflow: hidden;">
                    
                    <h5 style="color: #555; margin: 10px 0 5px 0;">Validation Source & Criteria:</h5>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li><strong>Validation Source:</strong> {val_source.upper()}</li>
                        <li><strong>Matchup Criteria:</strong> {rules_formatted}</li>
                    </ul>
                    
                    <h5 style="color: #555; margin: 15px 0 5px 0;">Data Selection Parameters:</h5>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li><strong>Time Range:</strong> {time_range}</li>
                        <li><strong>Wavelength(s):</strong> {wavelength_str}</li>
                        <li><strong>Valid Angles:</strong> nv_ref and nv_dolp ≥ {nv_min1}</li>
                        <li><strong>AOD Range for Aerosol Properties:</strong> {min_aod1} ≤ AOD ≤ {max_aod1}</li>
                    </ul>
                    
                    <div style="background-color: #e8f4f8; padding: 10px; border-radius: 4px; margin-top: 15px;">
                        <p style="margin: 0; font-size: 14px;"><strong>Note:</strong> For aerosol properties analysis (excluding AOD), only pixels within the specified AOD range are considered to ensure data quality and consistency.</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div style="background-color: #e8f4f8; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
            <h4 style="color: #0066cc; margin-bottom: 10px;">About PACE-{val_source.upper()} Matchup Data</h4>
            <p><strong>Data Version:</strong> This analysis utilizes <strong>PACE FastMAPOL (NASA) Level-2 data (Version 3.0, Provisional)</strong> matched with <strong>{val_source.upper()}</strong> validation measurements.</p>                  
            <p><strong>Data Usage:</strong> This matchup analysis page is created by the PACE FastMAPOL team for validation studies and data quality assessment. Please contact Meng Gao (meng.gao@nasa.gov) for further questions.</p> 
        </div>
        
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 6px; border-left: 4px solid #ffc107;">
            <h4 style="color: #856404; margin-bottom: 10px;">Validation Disclaimers</h4>
            <p><strong>Matchup Limitations:</strong> Validation results should be interpreted considering spatial and temporal sampling differences between satellite and ground-based/airborne measurements. Matchup criteria may affect the representativeness of comparisons.</p>
            <p><strong>Data Quality:</strong> Both PACE aerosol products and validation data are subject to their respective uncertainties and quality control procedures. Users should consider these uncertainties when interpreting validation statistics.</p>
        </div>
    </div>
    
    <script>
    function toggleMatchupCriteria() {{
        var criteria = document.getElementById('matchupCriteria');
        var toggleButton = document.getElementById('criteriaToggle');
        
        if (criteria.style.display === 'none' || criteria.style.display === '') {{
            criteria.style.display = 'block';
            toggleButton.innerHTML = '📊 Hide Matchup Criteria & Data Selection Details';
            toggleButton.style.backgroundColor = '#dc3545';
        }} else {{
            criteria.style.display = 'none';
            toggleButton.innerHTML = '📊 Show Matchup Criteria & Data Selection Details';
            toggleButton.style.backgroundColor = '#0066cc';
        }}
    }}
    
    // Add hover effects
    document.addEventListener('DOMContentLoaded', function() {{
        var button = document.getElementById('criteriaToggle');
        if (button) {{
            button.addEventListener('mouseenter', function() {{
                this.style.opacity = '0.9';
            }});
            button.addEventListener('mouseleave', function() {{
                this.style.opacity = '1';
            }});
        }}
    }});
    </script>"""
    
    return title2
    
def generate_html_header(title, title2, logo_path=None, resolution_factor=1.0, quality=95):
    """Generate the HTML header, styles, and opening tags."""
    
    # Check if logo_path is provided and the file exists
    include_logo = False
    logo_src = ""
    
    if logo_path and os.path.isfile(logo_path):
        # Use existing function to encode logo
        b64 = encode_image_to_base64(logo_path, factor=resolution_factor, quality=quality)
        if b64:
            include_logo = True
            # Get file extension and determine MIME type
            fname = os.path.basename(logo_path)
            ext = fname.lower().split('.')[-1]
            if ext == "png":
                mime = "png"
            elif ext == "gif":
                mime = "gif"
            elif ext == "bmp":
                mime = "bmp"
            else:
                mime = "jpeg"
            logo_src = f'data:image/{mime};base64,{b64}'
    
    # Define logo CSS - positioning in upper right corner and 4x bigger
    logo_css = [
        '  .header-logo { position: absolute; top: 10px; right: 20px; z-index: 100; }',
        '  .header-logo img { max-height: 240px; width: auto; border: none; }',  # 4x bigger (60px → 240px)
        '  .header-content { position: relative; padding-right: 260px; margin-bottom: 20px; }',  # Make space for the logo
    ]
    
    # Build the header HTML with the logo
    if include_logo:
        header_html = [
            '<div class="header-content">',
            f'  <h1>{title}</h1>',
            f'  <div class="header-logo"><img src="{logo_src}" alt="Logo"></div>',
            '</div>'
        ]
    else:
        header_html = [f'<h1>{title}</h1>']
        logo_css = []
    
    # The formatted title2 from format_html_info already contains complete HTML
    # No need to wrap it in <p> tags
    title2_html = title2 if title2 else ""
    
    return '\n'.join([
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        '<meta charset="UTF-8">',
        f'<title>{title}</title>',
        '<style>',
        '  body { font-family: Arial, sans-serif; margin: 20px; }',
        *logo_css,
        '  .suite-container { margin: 20px 0; border: 2px solid #ddd; padding: 15px; border-radius: 10px; }',
        '  .suite-title { font-size: 24px; font-weight: bold; color: #2196F3; margin-bottom: 5px; }',
        '  .suite-description { font-size: 16px; color: #666; margin-bottom: 15px; font-style: italic; }',
        '  .variable-buttons { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }',
        '  .variable-btn { padding: 8px 16px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }',
        '  .variable-btn:hover { background-color: #45a049; }',
        '  .variable-btn.active { background-color: #FF5722; }',
        '  .criteria-buttons { margin: 15px 0; text-align: left; border: 1px solid #e0e0e0; padding: 10px; border-radius: 5px; background-color: #f9f9f9; }',
        '  .criteria-btn { padding: 8px 20px; margin: 3px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; font-weight: bold; }',
        '  .criteria-btn.corr { background-color: #4CAF50; color: white; }',
        '  .criteria-btn.hist { background-color: #FF9800; color: white; }',
        '  .criteria-btn.map { background-color: #3F51B5; color: white; }',  # Add map button styling
        '  .criteria-btn.download { background-color: #9C27B0; color: white; }',
        '  .criteria-btn.active { box-shadow: 0 0 10px rgba(0,0,0,0.3); transform: scale(1.05); }',
        '  .download-links { margin: 10px 0; padding: 10px; background-color: #f5f5f5; border-radius: 5px; display: none; }',
        '  .download-links.show { display: block; }',
        '  .download-link { display: inline-block; margin: 5px 10px; padding: 5px 10px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 3px; font-size: 12px; }',
        '  .download-link:hover { background-color: #1976D2; }',
        '  .wavelength-tabs { margin: 10px 0; }',
        '  .wavelength-tab { display: inline-block; padding: 5px 15px; margin: 2px; background-color: #e7e7e7; border: 1px solid #ccc; cursor: pointer; border-radius: 3px; }',
        '  .wavelength-tab.active { background-color: #2196F3; color: white; }',
        '  .image-container { display: none; margin: 20px 0; }',
        '  .image-container.active { display: block; }',
        '  .plot-content { margin: 15px 0; }',
        '  .plot-content.hidden { display: none; }',
        '  img { max-width: 100%; height: auto; display: block; margin: 10px 0; border: 1px solid #ddd; }',
        '  .show-all-btn { padding: 15px 30px; background-color: #FF9800; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 18px; margin: 10px 5px; }',
        '  .man-suite { border-color: #FF5722; }',
        '  .man-suite .suite-title { color: #FF5722; }',
        '  .lwn-suite { border-color: #00BCD4; }',
        '  .lwn-suite .suite-title { color: #00BCD4; }',
        '  .aod-suite { border-color: #4CAF50; }',
        '  .aod-suite .suite-title { color: #4CAF50; }',
        '  .sda-suite { border-color: #9C27B0; }',
        '  .sda-suite .suite-title { color: #9C27B0; }',
        '  .alm-suite { border-color: #FF9800; }',
        '  .alm-suite .suite-title { color: #FF9800; }',
        '  .hyb-suite { border-color: #795548; }',
        '  .hyb-suite .suite-title { color: #795548; }',
        '  .hsrl2-suite { border-color: #E91E63; }',
        '  .hsrl2-suite .suite-title { color: #E91E63; }',
        '  .seabass-suite { border-color: #009688; }',
        '  .seabass-suite .suite-title { color: #009688; }',
        '</style>',
        '</head>',
        '<body>',
        *header_html,
        # Insert title2 content directly without <p> tags since it's already formatted HTML
        title2_html,
        '',
        '<div style="margin: 20px 0;">',
        '<button class="show-all-btn" onclick="showAllImages()">Show All Images</button>',
        '<button class="show-all-btn" onclick="hideAllImages()" style="background-color: #f44336;">Hide All Images</button>',
        '</div>',
        ''
    ])


def generate_javascript_and_footer():
    """Generate JavaScript functions and closing HTML tags."""
    return '\n'.join([
        '',
        '<script>',
        'function toggleVariable(varId) {',
        '  const container = document.getElementById(varId);',
        '  const btn = event.target;',
        '  if (container.style.display === "none" || !container.style.display) {',
        '    container.style.display = "block";',
        '    container.classList.add("active");',
        '    btn.classList.add("active");',
        '  } else {',
        '    container.style.display = "none";',
        '    container.classList.remove("active");',
        '    btn.classList.remove("active");',
        '  }',
        '}',
        '',
        'function showCriteria(varId, criteria) {',
        '  // Update button states',
        '  const parent = document.getElementById(varId);',
        '  const buttons = parent.querySelectorAll(".criteria-btn:not(.download)");',
        '  buttons.forEach(btn => btn.classList.remove("active"));',
        '  event.target.classList.add("active");',
        '  ',
        '  // Hide download section when showing plots',
        '  const downloadSection = document.getElementById(varId + "_downloads");',
        '  if (downloadSection) downloadSection.classList.remove("show");',
        '  ',
        '  // Get the plot sections',
        '  const corrSection = document.getElementById(varId + "_corr");',
        '  const histSection = document.getElementById(varId + "_hist");',
        '  const mapSection = document.getElementById(varId + "_map");',  # Add map section
        '  ',
        '  // Show/hide sections based on criteria',
        '  if (criteria === "corr") {',
        '    if (corrSection) corrSection.style.display = "block";',
        '    if (histSection) histSection.style.display = "none";',
        '    if (mapSection) mapSection.style.display = "none";',
        '  } else if (criteria === "hist") {',
        '    if (corrSection) corrSection.style.display = "none";',
        '    if (histSection) histSection.style.display = "block";',
        '    if (mapSection) mapSection.style.display = "none";',
        '  } else if (criteria === "map") {',  # Add map handling
        '    if (corrSection) corrSection.style.display = "none";',
        '    if (histSection) histSection.style.display = "none";',
        '    if (mapSection) mapSection.style.display = "block";',
        '  }',
        '}',
        '',
        'function toggleDownloadLinks(varId) {',
        '  const downloadSection = document.getElementById(varId + "_downloads");',
        '  const downloadBtn = event.target;',
        '  ',
        '  // Toggle download links visibility',
        '  if (downloadSection) {',
        '    if (downloadSection.classList.contains("show")) {',
        '      downloadSection.classList.remove("show");',
        '      downloadBtn.classList.remove("active");',
        '    } else {',
        '      downloadSection.classList.add("show");',
        '      downloadBtn.classList.add("active");',
        '      ',
        '      // Hide plot sections when showing downloads',
        '      const corrSection = document.getElementById(varId + "_corr");',
        '      const histSection = document.getElementById(varId + "_hist");',
        '      const mapSection = document.getElementById(varId + "_map");',  # Add map section
        '      if (corrSection) corrSection.style.display = "none";',
        '      if (histSection) histSection.style.display = "none";',
        '      if (mapSection) mapSection.style.display = "none";',
        '      ',
        '      // Deactivate other criteria buttons',
        '      const parent = document.getElementById(varId);',
        '      const buttons = parent.querySelectorAll(".criteria-btn:not(.download)");',
        '      buttons.forEach(btn => btn.classList.remove("active"));',
        '    }',
        '  }',
        '}',
        '',
        'function showWavelength(varId, wv, plotType) {',
        '  // Hide all wavelength content for this variable and plot type',
        '  const containers = document.querySelectorAll(`[id^="${varId}_wv_"][id$="_${plotType}_content"]`);',
        '  containers.forEach(c => c.style.display = "none");',
        '  ',
        '  // Show selected wavelength and plot type',
        '  const target = document.getElementById(`${varId}_wv_${wv}_${plotType}_content`);',
        '  if (target) target.style.display = "block";',
        '  ',
        '  // Update tab styling within the same section',
        '  const parent = event.target.closest(".plot-content");',
        '  const tabs = parent.querySelectorAll(".wavelength-tab");',
        '  tabs.forEach(t => t.classList.remove("active"));',
        '  event.target.classList.add("active");',
        '}',
        '',
        'function showAllImages() {',
        '  const containers = document.querySelectorAll(".image-container");',
        '  containers.forEach(c => { c.style.display = "block"; c.classList.add("active"); });',
        '  const buttons = document.querySelectorAll(".variable-btn");',
        '  buttons.forEach(b => b.classList.add("active"));',
        '}',
        '',
        'function hideAllImages() {',
        '  const containers = document.querySelectorAll(".image-container");',
        '  containers.forEach(c => { c.style.display = "none"; c.classList.remove("active"); });',
        '  const buttons = document.querySelectorAll(".variable-btn");',
        '  buttons.forEach(b => b.classList.remove("active"));',
        '}',
        '</script>',
        '</body>',
        '</html>'
    ])
