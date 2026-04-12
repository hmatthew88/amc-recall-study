import os
import subprocess
import json
import pandas as pd
import sys
from datetime import datetime

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPER_SCRIPT = os.path.join(BASE_DIR, 'scraper.py')
PROCESSOR_SCRIPT = os.path.join(BASE_DIR, 'processor.py')
RECALLS_EXCEL = os.path.join(BASE_DIR, 'AMC_Recalls.xlsx')
STUDY_APP_HTML = os.path.join(BASE_DIR, 'AMC_Study_App.html')
LOG_FILE = os.path.join(BASE_DIR, 'update_log.txt')

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')

def run_script(script_path):
    log(f"Starting {os.path.basename(script_path)}...")
    try:
        # Stream output in real-time. Use '-u' for unbuffered python output.
        process = subprocess.Popen(
            [sys.executable, '-u', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        for line in process.stdout:
            line = line.strip()
            if line:
                log(f"  [{os.path.basename(script_path)}] {line}")
        
        process.wait()
        if process.returncode == 0:
            log(f"Successfully finished {os.path.basename(script_path)}.")
            return True
        else:
            log(f"Error running {os.path.basename(script_path)}: Exit code {process.returncode}")
            return False
    except Exception as e:
        log(f"Exception running {os.path.basename(script_path)}: {e}")
        return False

def update_study_app():
    log("Updating Study App HTML...")
    if not os.path.exists(RECALLS_EXCEL):
        log(f"Error: {RECALLS_EXCEL} not found.")
        return False

    try:
        # 1. Load data from Excel
        df = pd.read_excel(RECALLS_EXCEL)
        
        # Convert to list of dicts, handling NaN
        recalls = df.to_dict(orient='records')
        # Clean data for JS consumption (handle potential NaN/None)
        cleaned_recalls = []
        for r in recalls:
            cleaned_r = {k: (v if pd.notna(v) else "") for k, v in r.items()}
            cleaned_recalls.append(cleaned_r)
        
        json_data = json.dumps(cleaned_recalls, ensure_ascii=False)
        
        # 2. Read HTML template
        with open(STUDY_APP_HTML, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # 3. Inject data
        # Search for the questionsData variable match
        start_marker = "const questionsData = ["
        end_marker = "];"
        
        start_index = html_content.find(start_marker)
        if start_index == -1:
            log("Error: Could not find 'const questionsData' marker in HTML.")
            return False
            
        end_index = html_content.find(end_marker, start_index)
        if end_index == -1:
            log("Error: Could not find end of questionsData array in HTML.")
            return False
            
        new_line = f"const questionsData = {json_data};"
        new_html = html_content[:start_index] + new_line + html_content[end_index + len(end_marker):]
        
        # 4. Save updated HTML
        with open(STUDY_APP_HTML, 'w', encoding='utf-8') as f:
            f.write(new_html)
            
        log(f"Successfully updated {os.path.basename(STUDY_APP_HTML)} with {len(cleaned_recalls)} recalls.")
        return True
    except Exception as e:
        log(f"Error updating study app: {e}")
        return False

def main():
    log("--- Weekly Update Started ---")
    log(f"Python Executable: {sys.executable}")
    log(f"Base Directory: {BASE_DIR}")
    
    # Step 1: Run Scraper
    if not run_script(SCRAPER_SCRIPT):
        log("Pipeline aborted due to scraper error.")
        return
        
    # Step 2: Run Processor
    if not run_script(PROCESSOR_SCRIPT):
        log("Pipeline aborted due to processor error.")
        return
        
    # Step 3: Update App Data
    if not update_study_app():
        log("Pipeline aborted due to app update error.")
        return
        
    log("--- Weekly Update Completed Successfully ---")

if __name__ == '__main__':
    main()
