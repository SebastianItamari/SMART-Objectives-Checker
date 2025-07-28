import pandas as pd
from typing import List, Dict

def read_csv(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    return df

def preprocess_dataframe(df: pd.DataFrame) -> List[Dict]:
    required_columns = [
        'Carrera Padre',
        'Carreras Hijos',
        'Codigo Materia',
        'Nombre Materia',
        'Electiva',
        'Objetivo de la materia'
    ]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    for col in required_columns:
        df[col] = df[col].astype(str).str.strip()

    df['Carreras Hijos'] = df['Carreras Hijos'].replace(['\\N', r'\N'], 'Ninguna')

    cleaned_df = df[required_columns].copy()
    print(cleaned_df)
    return cleaned_df.to_dict(orient='records')

def load_and_preprocess(filepath: str) -> List[Dict]:
    df = read_csv(filepath)
    return preprocess_dataframe(df)
