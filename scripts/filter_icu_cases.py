# scripts/filter_icu_cases.py
import pandas as pd
import numpy as np

def filter_icu_like_cases(clinical_file: str, output_file: str = None) -> pd.DataFrame:
    """
    Filter VitalDB cases that resemble ICU monitoring scenarios
    """
    print("🔄 Loading clinical data...")
    df = pd.read_csv(clinical_file)
    
    print(f"📊 Total cases: {len(df)}")
    
    # ✅ ADDED: Convert columns to proper data types and handle missing values
    # Convert numeric columns
    numeric_columns = ['age', 'asa', 'icu_days', 'emop', 'death_inhosp', 
                      'casestart', 'caseend', 'anestart', 'aneend']
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')  # Convert to numeric, NaN for invalid values
    
    # Fill NaN values with 0 for boolean-like columns
    df['icu_days'] = df['icu_days'].fillna(0)
    df['emop'] = df['emop'].fillna(0)
    df['death_inhosp'] = df['death_inhosp'].fillna(0)
    df['age'] = df['age'].fillna(0)
    df['asa'] = df['asa'].fillna(0)
    
    print(f"✅ Data types converted and cleaned")
    
    # ✅ FINAL: Use only confirmed columns with safe comparisons
    icu_criteria = (
        # 1. Cases with ICU admission
        (df['icu_days'] > 0) |
        
        # 2. Prolonged case duration (> 4 hours)
        ((df['caseend'] - df['casestart']) > 14400) |
        
        # 3. High-risk surgeries
        (df['opname'].str.contains('cardiac|thoracic|aortic|vascular|esophagectomy|pneumonectomy', 
                                   case=False, na=False)) |
        
        # 4. Emergency surgeries
        (df['emop'] == 1) |
        
        # 5. In-hospital mortality
        (df['death_inhosp'] == 1) |
        
        # 6. ASA class 4-5
        (df['asa'].isin([4, 5])) |
        
        # 7. Elderly patients (> 70 years)
        (df['age'] > 70)
    )
    
    icu_cases = df[icu_criteria].copy()
    
    print(f"✅ Filtered ICU-like cases: {len(icu_cases)} ({len(icu_cases)/len(df)*100:.1f}%)")
    
    # Add derived columns
    icu_cases['case_duration_hours'] = (icu_cases['caseend'] - icu_cases['casestart']) / 3600
    icu_cases['anesthesia_duration_hours'] = (icu_cases['aneend'] - icu_cases['anestart']) / 3600
    icu_cases['icu_risk_score'] = (
        (icu_cases['asa'] * 2) +
        (icu_cases['age'] / 10) +
        (icu_cases['icu_days'] * 5) +
        (icu_cases['emop'] * 3) +
        (icu_cases['death_inhosp'] * 10)
    )
    
    # Sort by risk score
    icu_cases = icu_cases.sort_values('icu_risk_score', ascending=False)
    
    if output_file:
        icu_cases.to_csv(output_file, index=False)
        print(f"💾 Saved to: {output_file}")
    
    return icu_cases

def analyze_icu_cases(df: pd.DataFrame):
    """Analyze characteristics of filtered ICU cases"""
    print("\n📈 ICU Cases Analysis:")
    print("=" * 50)
    
    print(f"Total ICU-like cases: {len(df)}")
    print(f"Mean case duration: {df['case_duration_hours'].mean():.1f} hours")
    print(f"Mean anesthesia duration: {df['anesthesia_duration_hours'].mean():.1f} hours")
    print(f"Mean ICU days: {df['icu_days'].mean():.1f} days")
    print(f"Mean age: {df['age'].mean():.1f} years")
    print(f"Mortality rate: {df['death_inhosp'].mean()*100:.1f}%")
    
    print("\nTop surgery types:")
    surgery_counts = df['opname'].value_counts().head(10)
    for surgery, count in surgery_counts.items():
        print(f"  {surgery}: {count}")
    
    print("\nASA distribution:")
    asa_dist = df['asa'].value_counts().sort_index()
    for asa, count in asa_dist.items():
        if pd.notna(asa):  # Skip NaN values
            print(f"  ASA {int(asa)}: {count} ({count/len(df)*100:.1f}%)")

def get_vitaldb_tracks_for_icu():
    """Get recommended VitalDB tracks for ICU monitoring"""
    return [
        'Solar8000/HR',
        'Solar8000/PLETH_SPO2',
        'Solar8000/ART_SBP',
        'Solar8000/ART_DBP',
        'Solar8000/ART_MBP',
        'Solar8000/BT',
        'Solar8000/RR',
    ]

if __name__ == "__main__":
    clinical_file = "data/clinical_data.csv"
    output_file = "data/icu_like_cases.csv"
    
    icu_cases = filter_icu_like_cases(clinical_file, output_file)
    analyze_icu_cases(icu_cases)
    
    print("\n📋 Sample ICU cases:")
    display_cols = ['caseid', 'age', 'asa', 'opname', 'icu_days', 'icu_risk_score']
    print(icu_cases[display_cols].head(10))
    
    print("\n🔧 Recommended VitalDB tracks for ICU:")
    for track in get_vitaldb_tracks_for_icu():
        print(f"  {track}")