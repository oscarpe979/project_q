import pandas as pd

excel_path = "/home/oscarpe979/project_q/docs/Two70 Schedule Excel 1.xls"

try:
    # Read all sheets
    xls = pd.ExcelFile(excel_path)
    print(f"Sheet names: {xls.sheet_names}")
    
    for sheet_name in xls.sheet_names:
        print(f"--- Sheet: {sheet_name} ---")
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        print(df.head(10))
        
except Exception as e:
    print(f"Error: {e}")
