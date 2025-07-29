import os
from dotenv import load_dotenv
import pandas as pd
import webbrowser

from src.data.preprocessor import load_and_preprocess
from src.model.prompt_engine_openai import process_objectives_and_update_df
from src.generator.report_generator import generate_html_report

if __name__ == "__main__":
    load_dotenv()

    RAW_CSV = os.getenv("RAW_CSV_PATH", "./data/datos_materias.csv")
    PROCESSED_CSV = os.getenv("PROCESSED_CSV_PATH", "./data/processed.csv")
    FINAL_RESULTS_CSV = os.getenv("FINAL_RESULTS_CSV_PATH", "./data/final_results.csv")
    SUBJECTS_DATA_PATH = os.getenv("SUBJECTS_DATA_PATH", "./data/datos_materias.csv")

    # 1. Preprocess
    print("Preprocessing raw data...")
    processed_data = load_and_preprocess()
    pd.DataFrame(processed_data).to_csv(PROCESSED_CSV, index=False)

    # 2. Evaluate with prompt engine
    print("Evaluating objectives with model...")
    df = pd.read_csv(PROCESSED_CSV)
    df = df.sample(10)
    df = process_objectives_and_update_df(df)
    df.to_csv(FINAL_RESULTS_CSV, index=False)

    # 3. Generate report
    print("Generating HTML report...")
    objectives_df = pd.read_csv(FINAL_RESULTS_CSV)
    report_path = generate_html_report(objectives_df)

    # 4. Open report in browser
    abs_report_path = os.path.abspath(report_path)
    webbrowser.open(f"file://{abs_report_path}")
    