# xbrlval

A professional-grade XBRL validation tool. Early foundation version.

## Quick start

- Install Python 3.10+
- Create a virtualenv and install dependencies:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Validate an XBRL instance:

```
xbrlval validate path-or-url-to-instance.xml --json
```

- Run the API server:

```
xbrlval api --host 0.0.0.0 --port 8080
```

## Roadmap (high level)

- DTS discovery across schemas and linkbases
- Complete calculation, definition, presentation graph checks
- Dimensions 1.0 validation
- XBRL Formula 1.0 rules execution
- Inline XBRL (iXBRL) parsing and extraction
- Pluggable rules engine and profile presets (ESMA, SEC, etc.)
- High-performance caching and parallelization
- Rich reports (JSON, SARIF, HTML)
