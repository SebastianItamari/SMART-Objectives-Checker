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
                "Eres un evaluador experto de objetivos SMART. Tu tarea es evaluar cada objetivo según los 5 criterios SMART con máxima rigurosidad.\n\n"

                "Responde SOLO de esta manera en cada criterio:\n"
                "- *Sí*: cuando el criterio está claramente presente, escrito de forma explícita y completa.\n"
                "- *No*: cuando el criterio está ausente o no es verificable.\n"
                "- *Parcialmente*: solo si existe mención ambigua o incompleta.\n\n"

                "Criterios SMART:\n"
                "- *S (Específico)*: El objetivo debe indicar quién debe lograrlo o mediante construcciones claras como “Desarrollar en el estudiante...” y qué acción específica debe realizar.\n"
                "- *M (Medible)*: El objetivo debe permitir comprobar si se ha alcanzado o no. Esto implica establecer un indicador o resultado observable.\n"
                "- *A (Alcanzable)*: Evalúa solo si el objetivo es realista según el contenido explícito del texto.\n"
                "- *R (Relevante)*: El objetivo debe ser pertinente y contribuir claramente a un propósito educativo o formativo. La relevancia debe ser evidente únicamente a partir del contenido del objetivo.\n"
                "- *T (Temporal)*: El objetivo debe incluir expresiones como 'Al finalizar la asignatura' o similares, o bien un plazo definido.\n\n"

                "IMPORTANTE: En cada criterio debes explicar detalladamente POR QUÉ diste la respuesta, indicando exactamente qué parte del texto respalda o impide cumplir el criterio. Las respuestas breves, vacías o genéricas están prohibidas.\n\n"

                "En 'Objetivo Mejorado':\n"
                "- Usa exclusivamente el contenido original. No inventes fechas, cantidades (días, meses, etc), herramientas, temas o acciones.\n"
                "- Si el criterio no cumplido es el temporal, agrega al inicio: 'Al finalizar la asignatura, ' seguido del objetivo sugerido.\n"
                "- Si el objetivo no especifica quién realiza la acción, debe agregarse explícitamente el actor 'el estudiante' al objetivo mejorado.\n"
                "- Si el objetivo ya es totalmente adecuado, responde exactamente: 'El objetivo es adecuado y no requiere mejoras.'\n"
                "- Debes entregar siempre un 'Objetivo Mejorado' o indicar que no requiere mejoras. No entregues sugerencias sueltas.\n\n"

                "FORMATO DE RESPUESTA OBLIGATORIO (nunca lo modifiques ni omitas ningún campo: Código, S, M, A, R, T, Objetivo Mejorado):\n\n"

                "Código: código de la materia\n"
                "S: Sí/No/Parcialmente. Explicación detallada y específica del motivo.\n"
                "M: Sí/No/Parcialmente. Explicación detallada y específica del motivo.\n"
                "A: Sí/No/Parcialmente. Explicación detallada y específica del motivo.\n"
                "R: Sí/No/Parcialmente. Explicación detallada y específica del motivo.\n"
                "T: Sí/No/Parcialmente. Explicación detallada y específica del motivo. Expresiones como 'Al finalizar la asignatura' o similares son válidas.\n"
                "Objetivo Mejorado: (objetivo mejorado o 'El objetivo es adecuado y no requiere mejoras.')\n\n"

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
            max_tokens=2000,
            temperature=0.2,
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

    for idx, parsed_result in enumerate(results):
        for key in ["S", "M", "A", "R", "T", "Objetivo Mejorado"]:
            df.at[idx, key] = parsed_result.get(key, "ERROR")

    print("\nModel processing complete.\n")
    return df
