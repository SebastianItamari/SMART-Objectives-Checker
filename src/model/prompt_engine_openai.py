import os
import re
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 5))

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Build chat messages for OpenAI API
def build_messages(batch: List[Dict]) -> List[Dict]:
    messages = [
        {
            "role": "system",
            "content": (
                "ROL: Evaluador experto de objetivos SMART\n\n"
                "Tu tarea es analizar cada objetivo según los 5 criterios SMART, con máxima rigurosidad y siguiendo las instrucciones detalladas.\n\n"

                "Responde SOLO de la siguiente manera para cada criterio:\n"
                "- *Sí*: El criterio está claramente presente, escrito de forma explícita y completa.\n"
                "- *No*: El criterio está ausente o no es verificable.\n"
                "- *Parcialmente*: Hay mención ambigua o incompleta.\n\n"

                "TUS CRITERIOS DE EVALUACIÓN:\n"
                "- *S (Específico)*: El objetivo debe indicar quién debe lograrlo (por ejemplo, 'el estudiante') y qué acción específica debe realizar.\n"
                "- *M (Medible)*: El objetivo debe permitir comprobar si se ha alcanzado, estableciendo indicadores o resultados observables.\n"
                "- *A (Alcanzable)*: Evalúa RIGUROSAMENTE si el objetivo es realista según el contenido explícito del texto.\n"
                "- *R (Relevante)*: Evalúa RIGUROSAMENTE, el objetivo debe ser pertinente y contribuir claramente a un propósito educativo o formativo, evidenciado en el texto.\n"
                "- *T (Temporal)*: El objetivo debe incluir expresiones como 'Al finalizar la asignatura' o un plazo definido.\n\n"

                "IMPORTANTE:\n"
                "- En cada criterio, explica detalladamente POR QUÉ diste la respuesta, indicando exactamente qué parte del texto respalda o impide cumplir el criterio.\n"
                "- Las respuestas breves, vacías o genéricas están prohibidas.\n\n"

                "OBJETIVO MEJORADO:\n"
                "1. Usa exclusivamente el contenido original. NO inventes fechas, cantidades, herramientas, temas ni acciones.\n"
                "2. Si el criterio temporal NO se cumple, agrega al inicio: 'Al finalizar la asignatura, ' seguido del objetivo sugerido.\n"
                "3. Si el objetivo NO especifica quién realiza la acción, agrega explícitamente el actor 'el estudiante' al objetivo mejorado.\n"
                "4. En una nueva línea, agrega un listado breve y conciso de sugerencias SOLO para mejorar el objetivo mejorado (no el original), siguiendo este formato:\n"
                "   *Sugerencias para criterio [Criterio SMART]:*\n"
                "   - Sugerencia 1\n"
                "   - Sugerencia 2\n"
                "   - ...\n"
                "   Las sugerencias deben estar acompañadas de ejemplos específicos que ayuden a cumplir plenamente los criterios SMART, incluyendo métricas o acciones observables si es necesario.\n"
                "   **NUNCA incluyas sugerencias para el criterio Temporal.**\n"
                "   **NUNCA incluyas sugerencias para el criterio Específico si la única falla es la ausencia del actor.**\n"
                "   Si el objetivo ya es totalmente adecuado, omite este paso.\n"
                "5. Si el objetivo ya es totalmente adecuado, responde exactamente: 'El objetivo es adecuado y no requiere mejoras.'\n"
                "6. Siempre entrega un 'Objetivo Mejorado' o indica que no requiere mejoras. No entregues sugerencias sueltas.\n\n"

                "FORMATO DE RESPUESTA OBLIGATORIO (no modifiques ni omitas ningún campo):\n"

                "Código: código de la materia\n"
                "S: Sí/No/Parcialmente. Explicación detallada y específica del motivo. [Debe indicar explícitamente al actor, por ejemplo 'el estudiante'.]\n"
                "M: Sí/No/Parcialmente. Explicación detallada y específica del motivo.\n"
                "A: Sí/No/Parcialmente. Explicación detallada y específica del motivo.\n"
                "R: Sí/No/Parcialmente. Explicación detallada y específica del motivo.\n"
                "T: Sí/No/Parcialmente. Explicación detallada y específica del motivo. [Expresiones como 'Al finalizar la asignatura' o similares son válidas.]\n"
                "Objetivo Mejorado: (objetivo mejorado [Utilizar TODO el contenido del objetivo original, NO RESUMIR] o 'El objetivo es adecuado y no requiere mejoras.')\n"

                "NO agregues introducción, conclusión ni explicaciones fuera del formato."
            )
        }
    ]

    content = ""
    for item in batch:
        codigo = item.get("Codigo Materia", "").strip()
        objetivo = item.get("Objetivo de la materia", "").strip()
        content += f"Código: {codigo}\nObjetivo: {objetivo}\n\n"

    messages.append({
        "role": "user",
        "content": content.strip()
    })

    return messages

# Parse model response into structured dictionary
def parse_response(text: str) -> Dict[str, str]:
    result = {}

    codigo_match = re.search(r"Código:\s*(.+)", text)
    if codigo_match:
        result["Código"] = codigo_match.group(1).strip()
    else:
        result["Código"] = "ERROR"

    patterns = {
        "S": r"S:\s*(Sí|No|Parcialmente)[.,]?\s*(.*)",
        "M": r"M:\s*(Sí|No|Parcialmente)[.,]?\s*(.*)",
        "A": r"A:\s*(Sí|No|Parcialmente)[.,]?\s*(.*)",
        "R": r"R:\s*(Sí|No|Parcialmente)[.,]?\s*(.*)",
        "T": r"T:\s*(Sí|No|Parcialmente)[.,]?\s*(.*)",
        "Objetivo Mejorado": r"Objetivo Mejorado:\s*([\s\S]*)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            result[key] = "ERROR: no evaluado."
        else:
            if key == "Objetivo Mejorado":
                contenido = match.group(1).strip()
                if contenido == "":
                    result[key] = "El objetivo es adecuado y no requiere mejoras."
                else:
                    result[key] = contenido
            else:
                respuesta = match.group(1).capitalize()
                explicacion = match.group(2).strip()
                result[key] = f"{respuesta}. {explicacion}"

    return result

# Process objectives, call API, and update dataframe
def process_objectives_and_update_df(df, max_retries=5):
    data = df.to_dict(orient='records')
    total_records = len(data)
    results = [None] * total_records

    print(f"Total objectives to process: {total_records}")
    print(f"Batch size: {BATCH_SIZE}")

    pending_indices = list(range(total_records))
    retry_tracker = {idx: 0 for idx in pending_indices}

    while pending_indices:
        current_batch_indices = pending_indices[:BATCH_SIZE]
        batch = [data[idx] for idx in current_batch_indices]
        messages = build_messages(batch)

        print(f"\n--- NEW BATCH with {len(current_batch_indices)} objectives ---\n")
        for msg in messages:
            print(f"{msg['role'].upper()}:\n{msg['content']}\n")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4000,
            temperature=0.3,
            stream=True,
        )

        response_parts = []
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and hasattr(chunk.choices[0].delta, "content"):
                content = chunk.choices[0].delta.content
                if content:
                    response_parts.append(content)

        full_response = "".join(response_parts).strip()

        print("\n--- Raw model response ---\n")
        print(full_response)
        print("\n--- End of raw response ---\n")

        if full_response == "" or "Código:" not in full_response:
            for idx in current_batch_indices:
                retry_tracker[idx] += 1
            print(f"Batch failed (empty or invalid response). Retrying individual items in next round...\n")
        else:
            splitted_responses = full_response.split("Código:")
            print(f"Total response blocks found: {len(splitted_responses) - 1}")

            parsed_batch_results = []
            for block in splitted_responses[1:]:
                response_text = "Código:" + block.strip()
                parsed = parse_response(response_text)
                parsed_batch_results.append(parsed)

            for batch_idx, parsed_result in zip(current_batch_indices, parsed_batch_results):
                results[batch_idx] = parsed_result

        pending_indices = [
            idx for idx in range(total_records)
            if results[idx] is None or any(
                results[idx].get(field, "").startswith("ERROR")
                for field in ["S", "M", "A", "R", "T", "Objetivo Mejorado"]
            )
        ]

        pending_indices = [
            idx for idx in pending_indices
            if retry_tracker[idx] < max_retries
        ]

        print(f"\nRemaining objectives to reprocess: {len(pending_indices)}")

    for idx, row in df.iterrows():
        codigo = row["Codigo Materia"]
        parsed_result = next(
            (r for r in results if r and r.get("Código") == codigo), None
        )
        if parsed_result:
            for key in ["S", "M", "A", "R", "T", "Objetivo Mejorado"]:
                df.at[idx, key] = parsed_result.get(key, "ERROR")

    print("\nModel processing complete.\n")
    return df
