import os
import re
from typing import List, Dict
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import pandas as pd

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 5))  # Default batch size 5 if not defined

client = InferenceClient(token=HF_API_TOKEN)

# Build chat messages for Hugging Face API
def build_messages(batch: List[Dict]) -> List[Dict]:
    messages = [
        {
            "role": "system",
            "content": (
                "Eres un evaluador experto de objetivos SMART. "
                "Para cada objetivo, analiza y responde ESTRICTAMENTE en este formato, manteniendo la explicación en la misma línea después de la respuesta:\n\n"
                "Código: (código)\n"
                "S: Si/No/Parcialmente. explicación\n"
                "M: Si/No/Parcialmente. explicación\n"
                "A: Si/No/Parcialmente. explicación\n"
                "R: Si/No/Parcialmente. explicación\n"
                "T: Si/No/Parcialmente. explicación\n"
                "Objetivo Mejorado: versión mejorada.\n\n"
                "Responde siempre en español y con este formato exacto para cada objetivo y codigo de materia, sin comentarios, introduccions o conclusiones adicionales."
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

# Parse response into structured dictionary
def parse_response(text: str) -> Dict[str, str]:
    result = {}

    # Extract Código
    codigo_match = re.search(r"Código:\s*(.+)", text)
    if codigo_match:
        result["Código"] = codigo_match.group(1).strip()
    else:
        result["Código"] = "ERROR"

    patterns = {
        "S": r"S:\s*(Sí\.|No\.|Parcialmente\.)\s*(.*)",
        "M": r"M:\s*(Sí\.|No\.|Parcialmente\.)\s*(.*)",
        "A": r"A:\s*(Sí\.|No\.|Parcialmente\.)\s*(.*)",
        "R": r"R:\s*(Sí\.|No\.|Parcialmente\.)\s*(.*)",
        "T": r"T:\s*(Sí\.|No\.|Parcialmente\.)\s*(.*)",
        "Objetivo Mejorado": r"Objetivo Mejorado:\s*(.*)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if key == "Objetivo Mejorado":
                result[key] = match.group(1).strip()
            else:
                result[key] = f"{match.group(1).strip()} {match.group(2).strip()}"
        else:
            result[key] = "ERROR"

    return result

# Process objectives, call API, and update dataframe
def process_objectives_and_update_df(df, max_retries=3):
    data = df.to_dict(orient='records')
    results = []

    print(f"Total objectives to process: {len(data)}")
    print(f"Batch size: {BATCH_SIZE}")

    for i in range(0, len(data), BATCH_SIZE):
        batch = data[i : i + BATCH_SIZE]
        messages = build_messages(batch)

        print(f"\nProcessing batch {i // BATCH_SIZE + 1}")
        print("Message sent to model:")
        for msg in messages:
            print(f"{msg['role'].upper()}:\n{msg['content']}\n")

        retry_count = 0
        response_parts = []

        while retry_count < max_retries:
            try:
                stream = client.chat.completions.create(
                    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.2,
                    stream=True,
                )
            except Exception as e:
                print(f"ERROR: API call failed at batch {i // BATCH_SIZE + 1} - {str(e)}")
                retry_count += 1
                print(f"Retrying batch {i // BATCH_SIZE + 1} (attempt {retry_count}/{max_retries})...\n")
                continue

            response_parts = []
            response_chunk_count = 0
            error_in_chunk = False

            for chunk in stream:
                if not chunk.choices:
                    print("WARNING: Empty chunk. Skipping...")
                    continue

                delta = chunk.choices[0].delta
                content = delta.get("content") if delta else None

                if content:
                    response_parts.append(content)
                response_chunk_count += 1

            print(f"Batch {i // BATCH_SIZE + 1}: received {response_chunk_count} response chunks.")

            if response_chunk_count == 0 or not response_parts:
                retry_count += 1
                print(f"ERROR: No response parts collected for batch {i // BATCH_SIZE + 1}. Retrying ({retry_count}/{max_retries})...\n")
                continue

            # If we got here, response is valid, break the retry loop
            break

        else:
            # max retries reached without success
            print(f"ERROR: Failed to get valid response for batch {i // BATCH_SIZE + 1} after {max_retries} attempts. Skipping batch.")
            # Fill error results for this batch
            for _ in batch:
                results.append({key: "ERROR" for key in ["S", "M", "A", "R", "T", "Objetivo Mejorado", "Código"]})
            continue

        full_response = "".join(response_parts)
        print(f"Full raw response from model:\n{full_response}\n")

        splitted_responses = full_response.split("Código:")
        print(f"Total response blocks found: {len(splitted_responses) - 1}")

        for block in splitted_responses[1:]:
            response_text = "Código:" + block.strip()
            parsed = parse_response(response_text)
            print(f"Parsed result:\n{parsed}\n")
            results.append(parsed)

    while len(results) < len(df):
        results.append({key: "ERROR" for key in ["S", "M", "A", "R", "T", "Objetivo Mejorado", "Código"]})

    for idx, parsed_result in enumerate(results):
        for key in ["S", "M", "A", "R", "T", "Objetivo Mejorado"]:
            df.at[idx, key] = parsed_result.get(key, "ERROR")

    print("\nModel processing complete.")
    return df

if __name__ == "__main__":
    csv_path = '../../data/processed.csv'
    output_path = '../../data/final_results.csv'

    print("Loading processed CSV...\n")
    df = pd.read_csv(csv_path).head(21)

    print("Sending objectives to model...\n")
    df = process_objectives_and_update_df(df)

    df.to_csv(output_path, index=False)
    print(f"\nFinal results saved at: {output_path}")