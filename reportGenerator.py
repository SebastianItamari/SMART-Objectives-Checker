import pandas as pd
from datetime import datetime
    
def makeDataFrame(subjectDataPath, objectivesDataFrame):
    subjectsDF = pd.read_csv(subjectDataPath)
    objectivesDF = objectivesDataFrame

    # Merge the two DataFrames
    mergedDF = pd.merge(subjectsDF, objectivesDF, left_on='Codigo Materia', right_on='Codigo', how='inner')
    mergedDF.drop(columns=['Codigo'], inplace=True)
    
    return mergedDF

def createIconForText(text):
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

def generateHTMLReport(evaluationDataFrame):
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
    with open(fileName, "w", encoding="utf-8") as f:
        f.write(htmlContent)
    print(f"Generated report: {fileName}")


# Mock data
data = {
    "Codigo": ["CIEHT06", "PSOHT04", "ECO0505", "BIO1001", "ECO0605"],
    "S": ["Sí.\nEl objetivo es bastante claro en cuanto a lo que se quiere lograr: una comprensión técnica del impacto ambiental en obras civiles, junto con la aplicación de normativa y estrategias de mitigación.", "Sí.\nEl objetivo es bastante claro en cuanto a lo que se quiere lograr: una comprensión técnica del impacto ambiental en obras civiles, junto con la aplicación de normativa y estrategias de mitigación.", "Sí.\nEl objetivo es bastante claro en cuanto a lo que se quiere lograr: una comprensión técnica del impacto ambiental en obras civiles, junto con la aplicación de normativa y estrategias de mitigación.", "Sí.\nEl objetivo es bastante claro en cuanto a lo que se quiere lograr: una comprensión técnica del impacto ambiental en obras civiles, junto con la aplicación de normativa y estrategias de mitigación.","Sí.\nEl objetivo es bastante claro en cuanto a lo que se quiere lograr: una comprensión técnica del impacto ambiental en obras civiles, junto con la aplicación de normativa y estrategias de mitigación."],
    "M": ["Parcialmente.\nNo establece indicadores de logro o evidencias claras de que se ha alcanzado la comprensión o la actitud crítica y responsable. Sería ideal especificar cómo se medirá: por ejemplo, mediante estudios de caso, evaluaciones prácticas o informes técnicos.", "Parcialmente.\nNo establece indicadores de logro o evidencias claras de que se ha alcanzado la comprensión o la actitud crítica y responsable. Sería ideal especificar cómo se medirá: por ejemplo, mediante estudios de caso, evaluaciones prácticas o informes técnicos.", "Parcialmente.\nNo establece indicadores de logro o evidencias claras de que se ha alcanzado la comprensión o la actitud crítica y responsable. Sería ideal especificar cómo se medirá: por ejemplo, mediante estudios de caso, evaluaciones prácticas o informes técnicos.","Parcialmente.\nNo establece indicadores de logro o evidencias claras de que se ha alcanzado la comprensión o la actitud crítica y responsable. Sería ideal especificar cómo se medirá: por ejemplo, mediante estudios de caso, evaluaciones prácticas o informes técnicos.","Parcialmente.\nNo establece indicadores de logro o evidencias claras de que se ha alcanzado la comprensión o la actitud crítica y responsable. Sería ideal especificar cómo se medirá: por ejemplo, mediante estudios de caso, evaluaciones prácticas o informes técnicos."],
    "A": ["Sí.\nParece realista para el contexto de una asignatura universitaria, siempre que se brinden los contenidos y herramientas adecuadas.", "Sí.\nParece realista para el contexto de una asignatura universitaria, siempre que se brinden los contenidos y herramientas adecuadas.", "Sí.\nParece realista para el contexto de una asignatura universitaria, siempre que se brinden los contenidos y herramientas adecuadas.", "Sí.\nParece realista para el contexto de una asignatura universitaria, siempre que se brinden los contenidos y herramientas adecuadas.","Sí.\nParece realista para el contexto de una asignatura universitaria, siempre que se brinden los contenidos y herramientas adecuadas."],
    "R": ["Sí.\nEs muy pertinente para estudiantes de ingeniería civil u otras disciplinas afines, en especial por la importancia actual del desarrollo sostenible y la normativa ambiental.", "Sí.\nEs muy pertinente para estudiantes de ingeniería civil u otras disciplinas afines, en especial por la importancia actual del desarrollo sostenible y la normativa ambiental.", "Sí.\nEs muy pertinente para estudiantes de ingeniería civil u otras disciplinas afines, en especial por la importancia actual del desarrollo sostenible y la normativa ambiental.", "Sí.\nEs muy pertinente para estudiantes de ingeniería civil u otras disciplinas afines, en especial por la importancia actual del desarrollo sostenible y la normativa ambiental.", "Sí.\nEs muy pertinente para estudiantes de ingeniería civil u otras disciplinas afines, en especial por la importancia actual del desarrollo sostenible y la normativa ambiental."],
    "T": ["No.\nEl objetivo no menciona un plazo, como por ejemplo: 'al finalizar la asignatura' o 'durante el semestre'. Esto es importante para acotar el logro en el tiempo.", "No.\nEl objetivo no menciona un plazo, como por ejemplo: 'al finalizar la asignatura' o 'durante el semestre'. Esto es importante para acotar el logro en el tiempo.", "No.\nEl objetivo no menciona un plazo, como por ejemplo: 'al finalizar la asignatura' o 'durante el semestre'. Esto es importante para acotar el logro en el tiempo.", "No.\nEl objetivo no menciona un plazo, como por ejemplo: 'al finalizar la asignatura' o 'durante el semestre'. Esto es importante para acotar el logro en el tiempo.", "No.\nEl objetivo no menciona un plazo, como por ejemplo: 'al finalizar la asignatura' o 'durante el semestre'. Esto es importante para acotar el logro en el tiempo."],
    "Objetivo Mejorado": ["Al finalizar la asignatura, el estudiante desarrollará una comprensión técnica del impacto ambiental en proyectos de infraestructura civil, aplicará la normativa vigente y estrategias de prevención y mitigación para evaluar y gestionar sus efectos durante la ejecución y mantenimiento de obras, demostrando una actitud profesional crítica y responsable frente al entorno natural mediante el análisis de casos prácticos y evaluaciones técnicas.", "Al finalizar la asignatura, el estudiante desarrollará una comprensión técnica del impacto ambiental en proyectos de infraestructura civil, aplicará la normativa vigente y estrategias de prevención y mitigación para evaluar y gestionar sus efectos durante la ejecución y mantenimiento de obras, demostrando una actitud profesional crítica y responsable frente al entorno natural mediante el análisis de casos prácticos y evaluaciones técnicas.", "Al finalizar la asignatura, el estudiante desarrollará una comprensión técnica del impacto ambiental en proyectos de infraestructura civil, aplicará la normativa vigente y estrategias de prevención y mitigación para evaluar y gestionar sus efectos durante la ejecución y mantenimiento de obras, demostrando una actitud profesional crítica y responsable frente al entorno natural mediante el análisis de casos prácticos y evaluaciones técnicas.", "Al finalizar la asignatura, el estudiante desarrollará una comprensión técnica del impacto ambiental en proyectos de infraestructura civil, aplicará la normativa vigente y estrategias de prevención y mitigación para evaluar y gestionar sus efectos durante la ejecución y mantenimiento de obras, demostrando una actitud profesional crítica y responsable frente al entorno natural mediante el análisis de casos prácticos y evaluaciones técnicas.", "Al finalizar la asignatura, el estudiante desarrollará una comprensión técnica del impacto ambiental en proyectos de infraestructura civil, aplicará la normativa vigente y estrategias de prevención y mitigación para evaluar y gestionar sus efectos durante la ejecución y mantenimiento de obras, demostrando una actitud profesional crítica y responsable frente al entorno natural mediante el análisis de casos prácticos y evaluaciones técnicas."]
}

objectivesDF = pd.DataFrame(data)

# Example usage
evaluationDF = makeDataFrame('datos_materias.csv', objectivesDF)
generateHTMLReport(evaluationDF)