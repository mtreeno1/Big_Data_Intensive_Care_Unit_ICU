import vitaldb

# Load dataset
cases = vitaldb.find_cases(['SNUADC/ECG_II', 'SNUADC/ART_MBP'])
print(f"Total cases: {len(cases)}")

# Load một case
case_data = vitaldb.load_case(cases[0], ['SNUADC/ECG_II', 'SNUADC/ART_MBP', 'Solar8000/HR'])
print(case_data.head())
