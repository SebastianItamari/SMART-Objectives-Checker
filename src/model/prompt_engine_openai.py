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
                "Eres un evaluador experto de objetivos SMART. Tu tarea es evaluar cada objetivo según los 5 criterios SMART. "
                "Recuerda que SMART significa:\n"
                "- **S (Específico)**: ¿El objetivo está claramente definido? ¿Se indica quién debe lograrlo y qué acción debe realizar?\n"
                "- **M (Medible)**: ¿El objetivo permite verificar si se ha alcanzado, mediante indicadores, porcentajes u otros criterios verificables?\n"
                "- **A (Alcanzable)**: ¿El objetivo es realista y posible de lograr en el contexto del curso o actividad?\n"
                "- **R (Relevante)**: ¿El objetivo contribuye significativamente al propósito general del curso o institución?\n"
                "- **T (Temporal)**: ¿El objetivo especifica un plazo claro y definido para su cumplimiento? Se considera correcto si menciona un momento específico como al finalizar la asignatura, antes de X fecha o un periodo temporal determinado. No se considera correcto respuestas vagas o indefinidas\n\n"
                "Evalúa cada objetivo respondiendo ESTRICTAMENTE en este formato exacto, manteniendo la explicación en la misma línea después de la respuesta:\n\n"
                "Código: (código)\n"
                "S: Sí/No/Parcialmente. explicación clara del motivo.\n"
                "M: Sí/No/Parcialmente. explicación clara del motivo.\n"
                "A: Sí/No/Parcialmente. explicación clara del motivo.\n"
                "R: Sí/No/Parcialmente. explicación clara del motivo.\n"
                "T: Sí/No/Parcialmente. explicación clara del motivo.\n"
                "Objetivo Mejorado: versión mejorada del objetivo. Si no es posible mejorarlo, escribe: 'El objetivo es adecuado y no requiere mejoras.'\n\n"
                "Responde siempre en el formato especificado para cada objetivo y código de materia, sin agregar introducción ni conclusión."
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
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=4000,
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

# Script entry point
if __name__ == "__main__":
    csv_path = '../../data/processed.csv'
    output_path = '../../data/final_results.csv'

    print("Loading processed CSV...\n")
    df = pd.read_csv(csv_path).head(4)

    print("Sending objectives to model...\n")
    df = process_objectives_and_update_df(df)

    df.to_csv(output_path, index=False)
    print(f"\nFinal results saved at: {output_path}")
