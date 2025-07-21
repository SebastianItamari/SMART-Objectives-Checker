import pandas as pd
from datetime import datetime
import os
    
def make_dataframe(subject_data_path: str, objectives_dataframe: pd.DataFrame) -> pd.DataFrame:
    subjects_df = pd.read_csv(subject_data_path)
    objectives_df = objectives_dataframe

    # Merge the two DataFrames
    merged_df = pd.merge(subjects_df, objectives_df, left_on='Codigo Materia', right_on='Codigo', how='inner')
    merged_df.drop(columns=['Codigo'], inplace=True)
    
    return merged_df

def create_icon_for_text(text: str) -> str:
    parts = text.split(' ')
    first_part = parts[0].strip()
    icon = ""
    if first_part == "Sí.":
        icon = "✅"
    elif first_part == "Parcialmente.":
        icon = "⚠️"
    elif first_part == "No.":
        icon = "❌"

    first_part_bold = f"<b>{first_part}</b>"
    rest = " ".join([p for p in parts[1:]])
    if rest:
        return f"{icon} {first_part_bold}<br>{rest}"
    else:
        return f"{icon} {first_part_bold}"
    
def replace_newlines_for_html(text: str) -> str:
    # Replace \r\n and \n for <br>
    return text.replace('\r\n', '<br>').replace('\n', '<br>')

def generate_html_report(evaluation_dataframe: pd.DataFrame) -> None:
    # Define the HTML structure
    html_df = evaluation_dataframe.copy()
    html_df = html_df.rename(columns={
        'Codigo Materia': 'Código',
        'Nombre Materia': 'Materia',
        'Objetivo de la materia': 'Objetivo de la Materia',
        'S': 'S (Específico)',
        'M': 'M (Medible)',
        'A': 'A (Alcanzable)',
        'R': 'R (Relevante)',
        'T': 'T (Temporal)'
    })

    for col in ['S (Específico)', 'M (Medible)', 'A (Alcanzable)', 'R (Relevante)', 'T (Temporal)']:
        html_df[col] = html_df[col].apply(create_icon_for_text)
    
    html_df['Objetivo Mejorado'] = html_df['Objetivo Mejorado'].apply(replace_newlines_for_html)
    html_df['Objetivo de la Materia'] = html_df['Objetivo de la Materia'].apply(replace_newlines_for_html)

    html_table = html_df.to_html(index=False, escape=False)

    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Reporte SMART</title>
        <style>
            body {{
                font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f9f9f9;
                margin: 20px 20px 5px 20px;
            }}
            h1 {{
                color: #333;
            }}
            .table-container {{
                height: 90%;
                overflow-y: auto;
                overflow-x: auto;
                background: white;
                padding: 0;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            table {{
                border-collapse: separate;
                border-spacing: 0;
                width: 100%;
                border: 1px solid #ddd;
                border-radius: 10px;
                min-width: 2200px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
                vertical-align: top;
            }}
            th {{
                background-color: #413d83 !important;
                color: white;
                font-weight: bold;
                text-align: center;
                position: sticky;
                top: 0;
                z-index: 1;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            b {{
                color: #333;
            }}
        </style>
    </head>
    <body>
        <h1>Reporte de Evaluación SMART - UPB</h1>
        <div class="table-container">
            {html_table}
        </div>
    </body>
    </html>
    """

    # Create the HTML file
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"Report_{date}.html"
    reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated report: {file_name}")