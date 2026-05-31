# ML experiments

Exploratory analyses that run **against the already-deployed artefacts** — they
do not retrain, recompute, or change the shipped model or its reported numbers.
Keep anything here clearly separate from the production pipeline in `ml/`.

## threshold_sweep.py — confidence-threshold (selective-prediction) sweep

Evidences the 0.60 low-confidence threshold (report DR-06 / §7.3) by measuring
the **accuracy vs coverage** trade-off of the deployed Stage-3 classifier.

For each threshold τ it reports:
- **coverage** — share of test images the app would diagnose (top softmax ≥ τ),
- **selective accuracy** — accuracy on just those images,
- **rejected** — share routed to the low-confidence warning instead.

### Run
```bash
pip install tensorflow numpy matplotlib pillow
python ml/experiments/threshold_sweep.py
```

### Before running, set the paths at the top of the script
- `MODEL_PATH` → deployed `stage3_disease_float16.tflite`
- `TEST_DIR` → your held-out test split (one subfolder per class)
- `LABELS_PATH` → the app's `labels.json` (defines output-index → class order)

If a test folder's name doesn't match a label, the script warns and lists it —
add an entry to `FOLDER_ALIASES`.

### Outputs (`ml/experiments/results/`)
- `threshold_sweep.json` — the full table
- `threshold_sweep.png` — accuracy & coverage vs τ (a candidate report figure)

### Honesty note
You run this; it prints the real numbers from the shipped model. Do not transcribe
any value into the report that you have not reproduced here yourself.
