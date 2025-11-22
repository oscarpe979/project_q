import pdfplumber
import pandas as pd
from datetime import datetime
import re
from typing import List, Dict, Any

def parse_cd_grid_pdf(file_path: str) -> List[Dict[str, Any]]:
    events = []
    
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            
            for table in tables:
                df = pd.DataFrame(table)
                
                # 1. Find the Date Row
                date_row_idx = -1
                for idx, row in df.iterrows():
                    # Check if any cell in the row contains "DATE" (case insensitive)
                    if row.astype(str).str.contains('DATE', case=False, na=False).any():
                        date_row_idx = idx
                        break
                
                if date_row_idx == -1:
                    continue # Skip table if no date row found

                # 2. Map Columns to Dates
                # The dates are likely in the row BELOW the "DATE" label, or in the same row?
                # Looking at the debug output:
                # Row 2: DATE ... DATE
                # Row 3: 6-Nov-25 ... 10-Nov-25
                # So dates are likely in date_row_idx + 1
                
                date_row = df.iloc[date_row_idx + 1]
                col_date_map = {}
                
                for col_idx, cell_val in date_row.items():
                    if pd.isna(cell_val): continue
                    
                    # Try to parse date
                    try:
                        # Format example: 6-Nov-25
                        date_obj = datetime.strptime(str(cell_val).strip(), "%d-%b-%y")
                        col_date_map[col_idx] = date_obj
                    except ValueError:
                        continue

                if not col_date_map:
                    continue

                # 3. Iterate through Schedule Rows
                # Start after the header rows (e.g., date_row_idx + 2 or 3)
                # We need to find where the times start. Usually column 0 has times.
                
                start_row_idx = date_row_idx + 2
                current_time = None
                
                for idx in range(start_row_idx, len(df)):
                    row = df.iloc[idx]
                    
                    # Check first column for Time
                    time_cell = str(row[0]).strip() if not pd.isna(row[0]) else ""
                    
                    # Regex to find time (e.g., 8:00am, 10:00 AM)
                    time_match = re.search(r'(\d{1,2}:\d{2})\s*(am|pm|AM|PM)?', time_cell)
                    
                    if time_match:
                        current_time = time_match.group(0)
                    
                    if not current_time:
                        continue # Skip rows until we find a time
                        
                    # Parse the time string to get hours/minutes
                    try:
                        # Normalize time string for parsing
                        # This is a simplification; robust parsing needed for production
                        dt_time = datetime.strptime(current_time.replace(" ", "").upper(), "%I:%M%p")
                    except ValueError:
                         try:
                            dt_time = datetime.strptime(current_time.replace(" ", "").upper(), "%H:%M")
                         except ValueError:
                            continue

                    # Check other columns for Events
                    for col_idx, cell_val in row.items():
                        if col_idx not in col_date_map: continue
                        if pd.isna(cell_val) or str(cell_val).strip() == "": continue
                        
                        event_title = str(cell_val).strip()
                        event_date = col_date_map[col_idx]
                        
                        # Combine Date and Time
                        start_datetime = event_date.replace(hour=dt_time.hour, minute=dt_time.minute)
                        # Default duration 1 hour for skeleton
                        end_datetime = start_datetime.replace(hour=start_datetime.hour + 1) 
                        
                        events.append({
                            "title": event_title,
                            "start": start_datetime.isoformat(),
                            "end": end_datetime.isoformat(),
                            "type": "other" # Default type
                        })
                        
    return events

def parse_cd_grid_excel(file_path: str) -> List[Dict[str, Any]]:
    events = []
    try:
        # Read the first sheet
        df = pd.read_excel(file_path)
        
        # 1. Find the Date Row
        date_row_idx = -1
        for idx, row in df.iterrows():
            if row.astype(str).str.contains('DATE', case=False, na=False).any():
                date_row_idx = idx
                break
        
        if date_row_idx == -1:
            return []

        # 2. Map Columns to Dates
        # In Excel, the dates might be in the same row or next row.
        # Based on debug output: Row 1 is DATE.
        # Let's assume dates are in the same row or the one immediately following if the cell with "DATE" is empty?
        # Actually, usually "DATE" is a label, and the dates are in the same row in other columns.
        
        date_row = df.iloc[date_row_idx]
        col_date_map = {}
        
        for col_idx, cell_val in date_row.items():
            if pd.isna(cell_val): continue
            
            # Check if it's a date object or string
            if isinstance(cell_val, datetime):
                col_date_map[col_idx] = cell_val
            else:
                try:
                    # Try parsing string format
                    date_obj = datetime.strptime(str(cell_val).strip(), "%d-%b-%y")
                    col_date_map[col_idx] = date_obj
                except ValueError:
                    continue
        
        if not col_date_map:
             # Try next row
             date_row = df.iloc[date_row_idx + 1]
             for col_idx, cell_val in date_row.items():
                if pd.isna(cell_val): continue
                if isinstance(cell_val, datetime):
                    col_date_map[col_idx] = cell_val
                else:
                    try:
                        date_obj = datetime.strptime(str(cell_val).strip(), "%d-%b-%y")
                        col_date_map[col_idx] = date_obj
                    except ValueError:
                        continue

        if not col_date_map:
            return []

        # 3. Iterate through Schedule Rows
        start_row_idx = date_row_idx + 2 # Skip a few rows
        current_time = None
        
        for idx in range(start_row_idx, len(df)):
            row = df.iloc[idx]
            
            # Check first column for Time
            time_cell = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else ""
            
            # Regex to find time
            time_match = re.search(r'(\d{1,2}:\d{2})\s*(am|pm|AM|PM)?', time_cell)
            
            if time_match:
                current_time = time_match.group(0)
            
            if not current_time:
                continue
                
            try:
                dt_time = datetime.strptime(current_time.replace(" ", "").upper(), "%I:%M%p")
            except ValueError:
                 try:
                    dt_time = datetime.strptime(current_time.replace(" ", "").upper(), "%H:%M")
                 except ValueError:
                    continue

            # Check other columns for Events
            for col_idx, cell_val in row.items():
                if col_idx not in col_date_map: continue
                if pd.isna(cell_val) or str(cell_val).strip() == "": continue
                
                event_title = str(cell_val).strip()
                event_date = col_date_map[col_idx]
                
                start_datetime = event_date.replace(hour=dt_time.hour, minute=dt_time.minute)
                end_datetime = start_datetime.replace(hour=start_datetime.hour + 1)
                
                events.append({
                    "title": event_title,
                    "start": start_datetime.isoformat(),
                    "end": end_datetime.isoformat(),
                    "type": "other"
                })

    except Exception as e:
        print(f"Error parsing Excel: {e}")
        return []
        
    return events
