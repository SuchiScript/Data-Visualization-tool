# Data Visualization Tool

This is a mid-level data visualization web application built with Python, Streamlit, pandas/numpy, Plotly and sqlite3.

## Quick setup

1. Clone or extract this project folder.
2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   # mac / linux
   source venv/bin/activate
   # windows
   venv\\Scripts\\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:

   ```bash
   streamlit run app.py
   ```

5. Open the URL printed by Streamlit (usually http://localhost:8501).

## Included files
- app.py : main Streamlit application
- auth.py : for user authentication helper functions
- utils.py : helper functions for filtering and aggregation
- db.py : tiny sqlite3-backed dataset store
- components.py : small UI helper components
- data/sample.csv : sample dataset for quick testing
- .streamlit/config.toml : streamlit config
- requirements.txt : python dependencies

## Notes
- The sqlite database file `datasets.db` will be created automatically in the project root when you use the save feature.
- For larger datasets you may want to use chunked processing or a proper DB server.
