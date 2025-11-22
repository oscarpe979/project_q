import pdfplumber
import pandas as pd

pdf_path = "/home/oscarpe979/project_q/docs/CD Grid Example 1.pdf"

try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages):
            print(f"--- Page {i+1} ---")
            text = page.extract_text()
            print(text[:500]) # Print first 500 chars
            
            tables = page.extract_tables()
            print(f"Found {len(tables)} tables")
            if tables:
                df = pd.DataFrame(tables[0])
                print(df.head(10))
except Exception as e:
    print(f"Error: {e}")
