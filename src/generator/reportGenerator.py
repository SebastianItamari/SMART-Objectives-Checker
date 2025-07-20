import pandas as pd
from datetime import datetime
import os
    
def makeDataFrame(subjectDataPath: str, objectivesDataFrame: pd.DataFrame) -> pd.DataFrame:
    subjectsDF = pd.read_csv(subjectDataPath)
    objectivesDF = objectivesDataFrame

    # Merge the two DataFrames
    mergedDF = pd.merge(subjectsDF, objectivesDF, left_on='Codigo Materia', right_on='Codigo', how='inner')
    mergedDF.drop(columns=['Codigo'], inplace=True)
    
    return mergedDF

def createIconForText(text: str) -> str:
    lines = text.split('\n')
    firstLine = lines[0].strip()
    icon = ""
    if firstLine == "Sí.":
        icon = "✅"
    elif firstLine == "Parcialmente.":
        icon = "⚠️"
    elif firstLine == "No.":
        icon = "❌"

    firstLineBold = f"<b>{firstLine}</b>"
    rest = "<br>".join([l for l in lines[1:]])
    if rest:
        return f"{icon} {firstLineBold}<br>{rest}"
    else:
        return f"{icon} {firstLineBold}"

def generateHTMLReport(evaluationDataFrame: pd.DataFrame) -> None:
    # Define the HTML structure
    htmlDF = evaluationDataFrame.copy()
    htmlDF = htmlDF.rename(columns={
        'Codigo Materia': 'Código',
        'Nombre Materia': 'Materia',
        'S': 'S (Específico)',
        'M': 'M (Medible)',
        'A': 'A (Alcanzable)',
        'R': 'R (Relevante)',
        'T': 'T (Temporal)'
    })

    for col in ['S (Específico)', 'M (Medible)', 'A (Alcanzable)', 'R (Relevante)', 'T (Temporal)']:
        htmlDF[col] = htmlDF[col].apply(createIconForText)

    htmlTable = htmlDF.to_html(index=False, escape=False)

    htmlContent = f"""
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
            {htmlTable}
        </div>
    </body>
    </html>
    """

    # Create the HTML file
    date = datetime.now().strftime("%Y-%m-%d")
    fileName = f"Report_{date}.html"
    reportsDir = os.path.join(os.path.dirname(__file__), '..', '..', 'reports')
    os.makedirs(reportsDir, exist_ok=True)
    filePath = os.path.join(reportsDir, fileName)
    with open(filePath, "w", encoding="utf-8") as f:
        f.write(htmlContent)
    print(f"Generated report: {fileName}")