# HLA Compatibility Matcher

A research demonstration of HLA allele **catalog lookup** and simple typed-allele string overlap, with a Python CLI, a browser-only interface, and a separate FastAPI demonstration service.

**Not a clinically validated transplant compatibility tool.** This repository does **not** implement true donor–recipient compatibility, allele-level mismatch grading, an eplet database, virtual crossmatching, haplotype inference, KDPI calculation, or graft-outcome prediction. Do not use its results for donor selection or patient care.

## Browser application

The static application lives in `docs/`; it performs all calculations and CSV processing in the browser. No account, backend, external fonts, analytics or network request is needed.

Run locally from the repository root:

```bash
python -m http.server 8080
# Open http://localhost:8080/docs/
```

Functions:
- Eight-entry demo catalog lookup for A, B, C, DRB1 and DQB1 strings. Legacy shorthand such as `A02` maps to an entry in this limited catalog but is **not** equivalent to high-resolution clinical typing.
- Donor/recipient allele-string overlap. It counts literal normalized full-string matches only; it is **not** an immunologic mismatch grade or compatibility percentage.
- CSV lookup with quoted-field handling and CSV download, limited to 2 MB / 10,000 rows. Queries use the `query` or `hla` column, or the first column. The `lookup_score` value of 10 indicates a catalog hit, **not** statistical confidence. Spreadsheet formula-like values are neutralized during download.

## Python setup and CLI

Python 3.10–3.12:

```bash
git clone https://github.com/abusuraihsakhri/hla-compatibility-matcher.git
cd hla-compatibility-matcher
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python hla_matcher.py single "A*02:01"
python hla_matcher.py batch --input sample.csv --output results.csv
python -m pytest -q
```

`hla_matcher.py` uses the same fixed, eight-allele catalog as the browser demo. The batch processor adds `top_hit` and `lookup_score` columns. Both implementations are educational, not exhaustive HLA allele parsers.

The separate `cli.py` and `agents/` subsystem demonstrates rule-based worker alerts for arbitrary numeric thresholds, a deterministic mock reply and an in-memory HMAC-chained audit log:

```bash
python cli.py audit --task-id DEMO-01 --primary 28.5 --secondary 14.2
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python simulator.py 100
```

The thresholds (25 and 12) are demonstration values, **not** clinical cutoffs. The named modules in `enrichment.py` are threshold-based scaffolds rather than functional transplant models. Changing `MODEL_PROVIDER` does not activate an external model; current provider choices return a mock implementation.

## API and Docker

Create a local `.env` from `.env.example`. Set `API_ACCESS_TOKEN` to a fresh random value (e.g. `python -c "import secrets; print(secrets.token_urlsafe(32))"`). Keep tokens outside version control.

```bash
python cli.py serve --host 127.0.0.1 --port 8000
# Browser demo: http://127.0.0.1:8000/
# Health: http://127.0.0.1:8000/health
# API docs: http://127.0.0.1:8000/docs
```

To call sensitive endpoints, send `Authorization: Bearer <your-token>` to `POST /api/audit`, `POST /api/chat`, and `GET /api/audit/logs`. Without `API_ACCESS_TOKEN`, these endpoints return HTTP 503. Other than these demonstrations, no clinical API validation is claimed.

Docker: `docker compose up --build` after creating `.env`. The service binds port 8000; do not expose it directly on an untrusted network without appropriate transport security, access control and operational review.

## Privacy and audit limitations

- The browser app keeps all input in the current browser session and makes no network requests. Do not enter real patient data in this demo.
- The API/CLI's PHI regex checks can detect **some** identifier patterns, but are **not** a de-identification system, HIPAA compliance mechanism, or guarantee that all PHI will be blocked.
- The audit chain now recomputes HMAC-SHA256 for each entry during verification and protects returned copies against mutation. Its key and records are held in process memory; records are **not persisted**, so this is not a production-grade immutable audit ledger.
- The static interface works without Python/Pyodide; the API requires a running Python service.

## Development and verification

```bash
python -m compileall -q agents hla_matcher.py enrichment.py cli.py simulator.py
python -m pytest -q
node --check docs/matcher.mjs
node --test tests/browser.test.mjs
```

GitHub Actions runs Python tests on 3.10–3.12 and browser module tests under Node 20. The static app uses native browser ES modules, Blob downloads and File APIs (current Chromium, Firefox and Safari). A Pages workflow is included, subject to repository Pages configuration.

**Technology:** Python standard library, FastAPI, Pydantic, pytest, vanilla JavaScript, HTML/CSS. **License:** MIT, see [LICENSE](LICENSE).
