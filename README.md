# Confident Agent — Theory of Computation

**COMP301 Software Design | Group project**

Confident Agent is a Python/Streamlit application that uses a Gemini large language model to answer introductory finite-automata questions and a simulator-backed verifier to check **structured claims** about string acceptance, regular expressions, and automaton structure. The interface displays the answer alongside a verdict, confidence measure, and supporting evidence where available.

> **Scope:** The verifier checks structured claims, not every statement in the generated explanation. Regex checks test strings up to length six and do not prove full language equivalence. The system uses machine-readable automaton encodings rather than interpreting diagram images directly.

## 1. Requirements

- Python 3.10 or newer (recommended; exact project environment version was not archived)
- Internet connection for Gemini API calls
- A working Google Gemini API key and access to the model specified in `llm/llm.py` (`gemini-3.5-flash-lite`)
- Python packages: `streamlit`, `google-generativeai`, `python-dotenv`, and `pytest` for tests

**Important:** The uploaded project has an empty `requirements.txt`. Populate it with the supplied `requirements_Confident_Agent.txt` before installing. Versions are not pinned, so future SDK/model changes may affect behaviour.

## 2. Installation

1. Extract the submitted ZIP and open a terminal in the **`Confidence-Agent` project root** (the directory containing `main.py`).
2. Create and activate a virtual environment:

   **Windows (PowerShell):**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   **macOS / Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
4. Create a file named `.env` in the project root, using `.env.example` as a template:
   ```env
   GEMINI_API_KEY=replace_with_your_own_key
   ```

## 3. Run the web application

From the project root, with the virtual environment active:

```bash
python -m streamlit run main.py
```

Open the local address displayed in the terminal (normally `http://localhost:8501`). Select a benchmark automaton, inspect its diagram and question, and click **Submit**. The application displays the AI response, structured claim, verification result, and confidence metric.

**Note:** The Streamlit application needs the Gemini API key even to start, because `llm/llm.py` checks for the key when imported. If the configured model is unavailable for the key/account, a Gemini API error may occur; record any model change when reproducing results.

## 4. Run automated tests

From the project root:

```bash
python -m pytest -q
```

These tests exercise simulator and verifier code; they do not independently audit the natural-language responses or benchmark diagrams.

## 5. Run the experiment

A safe first check that **does not call Gemini**:

```bash
python run_experiment.py --dry-run --runs 2 --out dry_run_results.csv
```

To perform a new Gemini-backed run (requires API access and may incur usage charges):

```bash
python run_experiment.py --runs 5 --sleep 3 --out new_results.csv
```

To test only a few items:

```bash
python run_experiment.py --items 1 5 14 --runs 1 --out sample_results.csv
```

The runner processes supported benchmark items with JSON automaton encodings, records model outputs and verifier verdicts, and writes CSV rows. **Use a new output filename** to avoid modifying the supplied `results.csv`; the runner can resume from an existing output file.

## 6. Analyse results

Analyse the archived results without making any API calls:

```bash
python analyze_results.py results.csv
```

Or analyse a newly generated file:

```bash
python analyze_results.py new_results.csv
```

The supplied experiment contains 140 responses from 28 supported entries evaluated five times each. The recorded verifier verdicts were 62 `CORRECT` and 78 `INCORRECT`. These labels represent agreement with the implemented checker, **not independently established hallucination rates**. The `manual_correct` column is empty, so false-acceptance and false-rejection rates cannot be reliably determined from the supplied results alone.

## 7. Project structure

```text
Confidence-Agent/
├── main.py                    # Streamlit entry point
├── Benchmark/
│   ├── questions.json         # Benchmark question entries
│   ├── JSON files/            # Encoded automata used by the verifier
│   ├── Diagrams/              # Diagram images
│   └── app/ui.py              # Streamlit interface
├── llm/llm.py                 # Gemini API call and response formatting
├── verifier/simulator.py      # Automaton simulator
├── verifier/verifier.py       # Structured claim verification
├── extractor/extractor.py     # Optional extractor (not in main evaluated pipeline)
├── run_experiment.py          # Batch evaluation runner
├── analyze_results.py        # CSV analysis
├── results.csv                # Archived experimental results
├── tests/                     # Automated tests
├── requirements.txt           # Python dependencies
└── .env.example               # Safe environment-variable template
```

The question list contains 50 entries, but the submitted experiment uses the 28 entries with supporting encodings. A diagram can support more than one type of question; entries should not automatically be interpreted as distinct automata.

## 8. Troubleshooting

- **`GEMINI_API_KEY not found`**: Check that `.env` is in the project root and contains `GEMINI_API_KEY=...`.
- **`ModuleNotFoundError`**: Activate the correct virtual environment and reinstall `requirements.txt`.
- **Benchmark files not found**: Run commands from the directory containing `main.py`; the UI uses relative file paths.
- **Gemini model / quota error**: Check internet access, API key permissions, available model IDs, and API quota. Record any change to model or SDK.
- **PowerShell refuses activation**: Use Command Prompt (`.venv\Scripts\activate.bat`) or a permitted local activation method.
- **No live API access**: Run the dry-run experiment, existing CSV analysis, and local tests. The Streamlit app itself requires a valid API key.

## 9. Reproducibility and limitations

The experiment used the Gemini model models/gemini-3.5-flash-lite and the google.generativeai Python library. Although this library may produce a deprecation warning, it did not prevent the recorded experiment from running. Any future upgrade to the newer Gemini SDK should be documented and tested.

The verifier checks AI-generated claims against structured JSON representations of finite automata. Its accuracy therefore depends on the correctness of these representations. Regular-expression verification is also limited to strings of length six or less, and differences in regex notation may affect results.

Finally, while the system displays verification results to help users identify potentially incorrect answers, the experiment did not test whether these warnings actually prevent students from relying on incorrect information.

For full experimental results and limitations, refer to the submitted project report.
