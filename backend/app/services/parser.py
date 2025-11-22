import pdfplumber
import pandas as pd
from datetime import datetime
import re
from typing import List, Dict, Any

import pdfplumber
import pandas as pd
from datetime import datetime
import re
from typing import List, Dict, Any

def parse_venue_schedule_pdf(file_path: str) -> List[Dict[str, Any]]:
    events = []
    
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            
            for table in tables:
                df = pd.DataFrame(table)
                
                # 1. Find the Date Row
                date_row_idx = -1
                for idx, row in df.iterrows():
                    if row.astype(str).str.contains('DATE', case=False, na=False).any():
                        date_row_idx = idx
                        break
                
                if date_row_idx == -1:
                    continue 

                # 2. Map Columns to Dates
                date_row = df.iloc[date_row_idx + 1]
                col_date_map = {}
                
                for col_idx, cell_val in date_row.items():
                    if pd.isna(cell_val): continue
                    try:
                        date_obj = datetime.strptime(str(cell_val).strip(), "%d-%b-%y")
                        col_date_map[col_idx] = date_obj
                    except ValueError:
                        continue

                if not col_date_map:
                    continue

                # 3. Iterate through Schedule Rows
                start_row_idx = date_row_idx + 2
                current_time = None
                
                for idx in range(start_row_idx, len(df)):
                    row = df.iloc[idx]
                    
                    time_cell = str(row[0]).strip() if not pd.isna(row[0]) else ""
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
                        
    return events

def parse_venue_schedule_excel(file_path: str) -> List[Dict[str, Any]]:
    events = []
    try:
        df = pd.read_excel(file_path)
        
        date_row_idx = -1
        for idx, row in df.iterrows():
            if row.astype(str).str.contains('DATE', case=False, na=False).any():
                date_row_idx = idx
                break
        
        if date_row_idx == -1:
            return []

        date_row = df.iloc[date_row_idx]
        col_date_map = {}
        
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

        start_row_idx = date_row_idx + 2
        current_time = None
        
        for idx in range(start_row_idx, len(df)):
            row = df.iloc[idx]
            
            time_cell = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else ""
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

def parse_cd_grid_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses the Master CD Grid PDF.
    Structure: Rows = Days, Columns = Venues.
    Target: Extract events for 'TWO70' column.
    """
    events = []
    
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            
            for table in tables:
                df = pd.DataFrame(table)
                
                # 1. Find Header Row with 'TWO70'
                header_row_idx = -1
                two70_col_idx = -1
                date_col_idx = -1
                
                for idx, row in df.iterrows():
                    # Normalize row to strings
                    row_str = row.astype(str).str.upper()
                    
                    if row_str.str.contains('TWO70').any():
                        header_row_idx = idx
                        # Find column indices
                        for col_idx, val in row_str.items():
                            if 'TWO70' in val:
                                two70_col_idx = col_idx
                            if 'DATE' in val:
                                date_col_idx = col_idx
                        break
                
                if header_row_idx == -1 or two70_col_idx == -1:
                    continue

                # 2. Iterate Rows
                for idx in range(header_row_idx + 1, len(df)):
                    row = df.iloc[idx]
                    
                    # Get Date
                    date_str = str(row[date_col_idx]).strip()
                    if not date_str or date_str == 'None': continue
                    
                    try:
                        # Format: 21-Dec-25
                        event_date = datetime.strptime(date_str, "%d-%b-%y")
                    except ValueError:
                        continue
                        
                    # Get Content for Two70
                    content = str(row[two70_col_idx]).strip()
                    if not content or content == 'None': continue
                    
                    # Content format example: "The Silk Road\n7:30 PM & 9:30 PM"
                    # Or "Sailaway Party\n4:30 PM - 5:15 PM"
                    
                    # Simple heuristic: Split by newlines, look for time patterns
                    lines = content.split('\n')
                    
                    for line in lines:
                        # Check for time range: "4:30 PM - 5:15 PM"
                        range_match = re.search(r'(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(\d{1,2}:\d{2}\s*[AP]M)', line, re.IGNORECASE)
                        
                        if range_match:
                            start_str = range_match.group(1)
                            end_str = range_match.group(2)
                            
                            # Parse times
                            try:
                                s_time = datetime.strptime(start_str.upper(), "%I:%M %p")
                                e_time = datetime.strptime(end_str.upper(), "%I:%M %p")
                                
                                start_dt = event_date.replace(hour=s_time.hour, minute=s_time.minute)
                                end_dt = event_date.replace(hour=e_time.hour, minute=e_time.minute)
                                
                                # Title is likely the previous lines? Or the whole cell minus time?
                                # For MVP, let's use the whole cell content as title, or try to extract
                                title = content.replace(line, "").strip()
                                if not title: title = "Event"
                                
                                events.append({
                                    "title": title,
                                    "start": start_dt.isoformat(),
                                    "end": end_dt.isoformat(),
                                    "type": "show" if "Silk Road" in title or "Oceanaria" in title else "other"
                                })
                            except ValueError:
                                pass
