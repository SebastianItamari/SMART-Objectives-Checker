import pandas as pd
from typing import List, Dict

def read_csv(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    return df

def preprocess_dataframe(df: pd.DataFrame) -> List[Dict]:
    required_columns = [
        'Carrera',
        'Codigo Materia',
        'Nombre Materia',
        'Electiva',
        'Objetivo de la materia'
    ]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df['Carrera'] = df['Carrera'].str.strip()
    df['Codigo Materia'] = df['Codigo Materia'].str.strip()
    df['Nombre Materia'] = df['Nombre Materia'].str.strip()
    df['Electiva'] = df['Electiva'].str.strip()
    df['Objetivo de la materia'] = df['Objetivo de la materia'].str.strip()

    result_rows = []

    grouped = df.groupby('Codigo Materia')

    for _, group in grouped:
        carreras = set(group['Carrera'].str.strip())

        if 'TODAS LAS CARRERAS' in carreras:
            row = group[group['Carrera'].str.strip() == 'TODAS LAS CARRERAS'].iloc[0]
            result_rows.append(row)
        else:
            carreras_combined = ', '.join(sorted(carreras))
            row = group.iloc[0].copy()
            row['Carrera'] = carreras_combined
            result_rows.append(row)

    cleaned_df = pd.DataFrame(result_rows)
    return cleaned_df.to_dict(orient='records')

def load_and_preprocess(filepath: str) -> List[Dict]:
    df = read_csv(filepath)
    return preprocess_dataframe(df)
