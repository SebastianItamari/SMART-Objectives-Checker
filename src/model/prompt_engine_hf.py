import os
import re
from typing import List, Dict
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import pandas as pd

# Load environment variables
load_dotenv()
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 5))

# Initialize Hugging Face client
client = InferenceClient(token=HF_API_TOKEN)

# Build chat messages for Hugging Face API
def build_messages(batch: List[Dict]) -> List[Dict]:
    messages = [
        {
            "role": "system",
            "content": (
                "Eres un evaluador experto de objetivos SMART. Tu tarea es evaluar con máxima rigurosidad cada objetivo según los cinco criterios SMART: Específico, Medible, Alcanzable, Relevante y Temporal.\n\n"

                "INSTRUCCIONES GENERALES:\n"
                "- Responde SIEMPRE usando el FORMATO DE RESPUESTA al final de este mensaje. No agregues introducciones, conclusiones ni comentarios fuera de ese formato.\n"
                "- Evalúa EXCLUSIVAMENTE lo que esté explícito en el texto del objetivo. No interpretes, completes ni adivines intenciones.\n"
                "- Sé detallado: cada explicación debe citar o parafrasear partes del objetivo para justificar claramente la evaluación de cada criterio.\n\n"

                "CRITERIOS SMART:\n"
                "- *S (Específico)*: El objetivo debe indicar claramente quién realiza la acción (por ejemplo, 'el estudiante') y qué acción específica debe realizar.\n"
                "- *M (Medible)*: El objetivo debe incluir un resultado observable o criterio verificable. Por ejemplo: describir, resolver, identificar, crear.\n"
                "- *A (Alcanzable)*: Evalúa si el objetivo es realista según la información contenida en el texto. No hagas suposiciones externas.\n"
                "- *R (Relevante)*: El objetivo debe tener una conexión clara con propósitos educativos o formativos. Debe contribuir al aprendizaje, desarrollo de habilidades o competencias.\n"
                "- *T (Temporal)*: Debe incluir un marco temporal claro como 'Al finalizar la asignatura' o una fecha/plazo específico. Si no hay referencia temporal explícita, responde no es válido.\n\n"

                "En 'Objetivo Mejorado':\n"
                "- Basate exclusivamente en el contenido del objetivo original. No inventes fechas, cantidades (días, meses, etc), herramientas, temas o acciones.\n"
                "- Si el criterio no cumplido es el temporal, agrega al inicio: 'Al finalizar la asignatura, ' seguido del objetivo sugerido.\n"
                "- Si el objetivo no especifica quién realiza la acción (No Específico), debe agregarse explícitamente el actor 'el estudiante' al objetivo mejorado.\n"
                "- Si el objetivo ya es totalmente adecuado, responde exactamente: 'El objetivo es adecuado y no requiere mejoras.'\n"
                "- Debes entregar siempre un 'Objetivo Mejorado' o indicar que no requiere mejoras. No entregues sugerencias sueltas.\n\n"

                "FORMATO DE RESPUESTA (NO MODIFIQUES ESTO):\n\n"
                "Código: [código de la materia]\n"
                "S: [Sí / No / Parcialmente]. Explicación detallada con referencias textuales.\n"
                "M: [Sí / No / Parcialmente]. Explicación detallada con referencias textuales.\n"
                "A: [Sí / No / Parcialmente]. Explicación detallada con referencias textuales.\n"
                "R: [Sí / No / Parcialmente]. Explicación detallada con referencias textuales.\n"
                "T: [Sí / No / Parcialmente]. Explicación detallada con referencias textuales.\n"
                "Objetivo Mejorado: [texto mejorado o 'El objetivo es adecuado y no requiere mejoras.']"
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

        # Call the API stream
        stream = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            messages=messages,
            max_tokens=2000,
            temperature=0.2,
            stream=True,
        )

        response_parts = []
        for chunk in stream:
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
