# scripts/check_clinical_columns.py
import pandas as pd

def check_clinical_columns(file_path: str):
    """Check actual column names in clinical_data.csv"""
    print("🔍 Checking clinical data columns...")
    
    try:
        df = pd.read_csv(file_path)
        print(f"📊 Total columns: {len(df.columns)}")
        print(f"📊 Total rows: {len(df)}")
        
        print("\n📋 All columns:")
        for i, col in enumerate(df.columns, 1):
            # ✅ Fixed: Print column index and name
            print(f"  {i:2d}. {col}")
        
        print("\n🔍 ICU-related columns:")
        icu_keywords = ['icu', 'vent', 'death', 'mortality', 'asa', 'age', 'emop']
        icu_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in icu_keywords)]
        
        if icu_cols:
            for col in icu_cols:
                print(f"  ✅ {col}")
        else:
            print("  No ICU-related columns found with these keywords")
        
        # Sample data
        print("\n📋 Sample data (first 5 rows, selected columns):")
        sample_cols = ['caseid', 'age', 'asa'] if all(col in df.columns for col in ['caseid', 'age', 'asa']) else df.columns[:5]
        print(df[sample_cols].head())
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clinical_file = "data/clinical_data.csv"
    check_clinical_columns(clinical_file)