# SMART Objectives Checker

This project automates the evaluation of academic objectives written according to the SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound). Based on course data and their objectives, it processes, assesses, and generates interactive reports and detailed statistics to support continuous improvement in objective formulation.

---

## What does this project do?

- **Preprocesses** academic data to organize it properly.
- **Automatically evaluates** the objectives of each course using an AI model, indicating for each criterion whether the objective meets, partially meets, or does not meet the standard.
- **Generates HTML reports** that are easy to navigate, with symbols and formatting that facilitate result interpretation.
- **Provides statistics** grouped by department to identify patterns and areas for improvement.

---

## Initial Setup

For the system to work correctly, create a `.env` file in the project root with the following variables:

| Variable               | Description                                          | Required / Optional           |
|------------------------|------------------------------------------------------|------------------------------|
| `ENDPOINT_URL`         | Endpoint URL to fetch the data                        | Required                     |
| `ACCESS_TOKEN`         | Access token for the endpoint                         | Required                     |
| `OPENAI_API_KEY`       | API key to access the OpenAI model                    | Required                     |
| `BATCH_SIZE`           | (Optional) Batch size for processing                  | Optional (default: 5)        |
| `RAW_CSV_PATH`         | (Optional) Path for raw CSV data                      | Optional (default: `./data/datos_materias.csv`) |
| `PROCESSED_CSV_PATH`   | (Optional) Path for processed CSV data                | Optional (default: `./data/processed.csv`) |
| `FINAL_RESULTS_CSV_PATH` | (Optional) Path for final results CSV                 | Optional (default: `./data/final_results.csv`) |
| `ESTATISTICS_CSV_PATH` | (Optional) Path for career statistics CSV             | Optional (default: `./data/estadisticas_por_carrera.csv`) |

---

## Installation and Setup ⚙️

To get started, it's recommended to create and use a Python virtual environment to isolate project dependencies.

### 1. Create a virtual environment

```bash
python3 -m venv venv
```

### 2. Activate the virtual environment

- On macOS/Linux:

  ```bash
  source venv/bin/activate
  ```

- On Windows (PowerShell):

  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

- On Windows (Command Prompt):

  ```cmd
  .\venv\Scripts\activate.bat
  ```

### 3. Upgrade pip (optional but recommended)

```bash
pip install --upgrade pip
```

### 4. Install project dependencies

```bash
pip install -r requirements.txt
```

## Usage

You can run the analysis with:

```bash
python main.py
```

This will process the CSV file, evaluate objectives, and generate annotated results along with statistical summaries.

## Output Files 📚

- `resultados_finales.csv`: Contains the original data plus SMART evaluations and comments.
- `estadisticas_por_carrera.csv`: Summary of how many objectives did meet SMART criteria by degree program.
- `report.html`: Contains de report of SMART evaluation in html format.

### FAQ 🤔

**Q: What is the purpose of this report?**  
**A:** The report helps analyze how well each subject's objectives align with the SMART criteria: Specific, Measurable, Achievable, Relevant, and Time-bound.

**Q: How do I interpret the symbols in the report?**  
**A:**

  | Symbol | Meaning                     |
  |--------|-----------------------------|
  | ✅     | Yes (criterion met)         |
  | ⚠️     | Partially (criterion partially met) |
  | ❌     | No (criterion not met)      |

**Q: How do I read the results for each subject?**  
**A:** For each subject listed under a career, the report shows whether the objectives meet each of the SMART criteria. If any of them are marked with "No." or "Parcialmente.", it means that criterion is not fully satisfied.

**Q: What do the highlighted suggestions mean?**  
**A:** Each suggestion corresponds to a specific SMART criterion that wasn’t fully met. It provides a short explanation or recommendation to improve the objective. These suggestions are not automatically included in the improved objective text because doing so would involve making inferences that may not reflect the author's original intent.

**Q: What if the AI evaluation fails or returns errors?**  
**A:** The system retries failed evaluations automatically. If issues persist, check your API key and internet connection.
