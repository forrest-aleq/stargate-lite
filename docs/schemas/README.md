# Capability Schema Exports

Generated exports of Stargate's capability schemas for training and integration use.

## Files

| File | Size | Description |
|------|------|-------------|
| `capability-schema-request.md` | 6 KB | Schema request format documentation (tracked) |
| `TAMI-capability-schema-response.md` | ~373 KB | Full capability schema response (gitignored) |
| `TAMI-schemas-export.json` | ~861 KB | Complete schema export as JSON (gitignored) |
| `capability-schemas-for-training.json` | ~667 KB | Training-optimized schema export (gitignored) |

## Regenerating

The three large files are gitignored due to their combined ~1.9 MB size. To regenerate:

```bash
source venv/bin/activate
python tests/scripts/generate_capability_docs.py
```
