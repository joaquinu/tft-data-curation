# Tests

All tests have been relocated here. Run from the project root.

## Prerequisites
- Python 3.8+
- Install dependencies: `pip install -r requirements.txt`
- Environment (for networked tests): set a valid Riot API key
  - Linux/macOS: `export RIOT_API_KEY="RGAPI-xxxx"`
  - Windows (PowerShell): `$env:RIOT_API_KEY = "RGAPI-xxxx"`

## Quick start (pytest)
```bash
pip install pytest
pytest -q tests
```

## Run individual modules (plain Python)
```bash
python tests/test_config_manager.py
python tests/test_identifier_system.py
python tests/test_runner.py
python tests/end_to_end_pipeline.py
python tests/pipeline_validator.py
python tests/visualization_tester.py
```

Notes
- Run commands from the repository root so relative imports resolve.
- Some tests make live API calls; expect rate limiting and set `RIOT_API_KEY`.
