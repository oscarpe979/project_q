import pdfplumber
import pandas as pd
from datetime import datetime
import re
from typing import List, Dict, Any

from .genai_parser import GenAIParser
from ..config import GEMINI_API_KEY


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

def parse_cd_grid_pdf(file_path: str) -> Dict[str, Any]:
    """
    Parse CD Grid PDF using GenAI.
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        {
            "itinerary": List[Dict],
            "events": List[Dict]
        }
    """
    if GEMINI_API_KEY:
        parser = GenAIParser(GEMINI_API_KEY)
        return parser.parse_cd_grid(file_path)
    else:
        raise ValueError("GEMINI_API_KEY not configured. Please set it in your .env file.")
