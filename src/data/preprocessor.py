import os
import requests
import pandas as pd
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

def fetch_json() -> List[Dict]:
    base_url = os.getenv('ENDPOINT_URL')
    token = os.getenv('ACCESS_TOKEN')

    if not base_url or not token:
        raise ValueError("Define ENDPOINT_URL and ACCESS_TOKEN in .env")

    url = f"{base_url}?access-token={token}"
    response = requests.get(url, verify=False)
    response.raise_for_status()
    return response.json()

def json_to_df(data: List[Dict]) -> pd.DataFrame:
    column_map = {
        'carrera_servicio': 'Carrera Padre',
        'carrera': 'Carreras Hijos',
        'codigo_materia': 'Codigo Materia',
        'nombre_materia': 'Nombre Materia',
        'electiva': 'Electiva',
        'objectivo_materias': 'Objetivo de la materia'
    }
    df = pd.DataFrame(data).rename(columns=column_map)
    
    parent_map = {}
    for _, row in df.iterrows():
        code = row['Codigo Materia']
        if not row['Carrera Padre'] or row['Carrera Padre'].strip() == "":
            parent_map[code] = row['Carreras Hijos'].strip()

    result_rows = []
    for code, real_parent in parent_map.items():
        course_rows = df[df['Codigo Materia'] == code]
        
        children_set = set()
        for _, row in course_rows.iterrows():
            child = row['Carreras Hijos'].strip()
            if child != real_parent and child not in ["", "Ninguna"]:
                children_set.add(child)
        
        first_row = course_rows.iloc[0]
        result_rows.append({
            'Carrera Padre': real_parent,
            'Carreras Hijos': '\n'.join(sorted(children_set)) if children_set else 'Ninguna',
            'Codigo Materia': code,
            'Nombre Materia': first_row['Nombre Materia'],
            'Electiva': first_row['Electiva'],
            'Objetivo de la materia': first_row['Objetivo de la materia']
        })
    
    return pd.DataFrame(result_rows)

def preprocess_df(df: pd.DataFrame) -> List[Dict]:
    required_cols = [
        'Carrera Padre',
        'Carreras Hijos',
        'Codigo Materia',
        'Nombre Materia',
        'Electiva',
        'Objetivo de la materia'
    ]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    for col in required_cols:
        df[col] = df[col].astype(str).str.strip()

    df['Carreras Hijos'] = df['Carreras Hijos'].replace(['\\N', r'\N'], 'Ninguna')

    cleaned = df[required_cols].copy()
    cleaned = cleaned.sort_values(by='Carrera Padre', ascending=True)
    print(cleaned)
    return cleaned.to_dict(orient='records')

def load_and_preprocess() -> List[Dict]:
    raw_data = fetch_json()
    df = json_to_df(raw_data)
    return preprocess_df(df)
