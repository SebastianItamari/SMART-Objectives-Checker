import pandas as pd

def smart_statistics(final_results_csv, output_csv="estadisticas_por_carrera.csv"):
    df = pd.read_csv(final_results_csv)

    # Replace NaN with empty string to avoid errors with .str
    for col in ["S", "M", "A", "R", "T"]:
        df[col] = df[col].fillna("").astype(str)

    stats = df.groupby("Carrera Padre").agg(
        Total_asignaturas=("Codigo Materia", "nunique"),
        Total_S=("S", lambda x: x.str.startswith(("Sí.")).sum()),
        Total_M=("M", lambda x: x.str.startswith(("Sí.")).sum()),
        Total_A=("A", lambda x: x.str.startswith(("Sí.")).sum()),
        Total_R=("R", lambda x: x.str.startswith(("Sí.")).sum()),
        Total_T=("T", lambda x: x.str.startswith(("Sí.")).sum())
    ).reset_index()

    stats.rename(columns={"Carrera Padre": "Carrera"}, inplace=True)

    # Add summary row with totals including all careers
    totals = stats.sum(numeric_only=True)
    totals["Carrera"] = "TOTAL GENERAL"
    stats = pd.concat([stats, pd.DataFrame([totals])], ignore_index=True)

    stats.to_csv(output_csv, index=False)
    print(f"Statistics saved in {output_csv}")
