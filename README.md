# Integration Engineer deliverable

## Files
- `integration.py`: central orchestration layer. Keep Person 1 and Person 2
  source files separate.
- `test_integration.py`: tests using fake generator functions.
- `PERSON3_FRONTEND_GUIDE.md`: exact calls for Streamlit.

## Important status
This is a tested integration adapter, not yet a live connection to Person 1's
actual AI/API implementation. Person 1's module was not supplied when this
adapter was built. Once received, either pass their functions directly or set
`AI_ENGINE_MODULE` to their module name.

## Run tests
Place `integration.py`, `lore_guard.py`, and `fact_extractor.py` together,
then run:
```powershell
python -m unittest -v test_integration.py
```
