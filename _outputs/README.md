# Generated Outputs Directory

This directory contains generated files from running the examples. These files are created automatically when you run various examples and can be safely deleted or ignored.

## Contents

- **Log files** (`.log`): Application execution logs
  - `app.log` - Logs from running `app.py`
  - `transformer_app.log` - Logs from running `transformer_app.py`
  - `pipeline_run.log` - Execution logs from `advanced_pipeline.py`

- **Output files** (`.json`, `.md`): Generated outputs from examples
  - `pipeline_output.json` - Output from `advanced_pipeline.py` with document analysis
  - `output_*.md` - Various output files from example runs
  - `transformed_*.md` - Generated requirements documents from the transformer examples

## Notes

- These files are **regenerated** each time you run the examples
- You can **safely delete** all files in this directory
- This directory is typically **ignored by version control** (see `.gitignore`)
- New output files will be created here automatically when running examples

## Cleanup

To clean up all generated files:

```bash
# Windows (PowerShell)
Remove-Item _outputs\* -Recurse -Force

# macOS/Linux
rm -rf _outputs/*
```

