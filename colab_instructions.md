# Colab Instructions — TakeMeter

Follow these steps inside your copy of the TakeMeter starter Colab notebook.

---

## Before You Start

1. Open your copy of the TakeMeter starter notebook.
2. Go to **Runtime → Change runtime type**, select **T4 GPU**, click **Save**.
3. Add your Groq API key: click the 🔑 icon in the left sidebar, add a secret named `GROQ_API_KEY`.

---

## Section 1 — Label Map and CSV Upload

Paste this label map into the notebook cell:

```python
LABEL_MAP = {
    "analysis": 0,
    "hot_take": 1,
    "reaction": 2,
}
```

When prompted to upload a file, upload `data/nba_dataset.csv` from this repo.

The CSV has three columns: `text`, `label`, `notes`. The notebook uses `text` and `label`.

---

## Section 2 — Dataset Split and Tokenization

Run Section 2 as-is. It will:
- Split the data: 70% train / 15% validation / 15% test
- Tokenize all splits with the DistilBERT tokenizer

Expected split sizes (from 202 examples):
- Train: ~141 examples
- Val: ~30 examples
- Test: ~30 examples

Verify label distribution looks balanced (~33% each) before continuing.

---

## Section 5 — Groq Zero-Shot Baseline

### Classification Prompt

Paste this prompt into the notebook's baseline prompt cell:

```python
BASELINE_PROMPT = """You are classifying NBA subreddit posts into exactly one of three discourse categories.

Label definitions:
- analysis: A structured argument backed by statistics, historical comparisons, or tactical reasoning. Evidence is specific and verifiable. The post reasons toward a conclusion.
- hot_take: A bold confident opinion stated without supporting evidence, or with cherry-picked evidence used rhetorically rather than argumentatively. The post asserts a claim; it does not build toward it.
- reaction: An immediate emotional response to a specific, recent game event, play, or moment. Little or no argument — the post expresses a feeling about something that just happened.

Decision rules:
- If a post cites stats but doesn't reason through them → hot_take (not analysis)
- If a post reacts to a specific live event → reaction (even if it includes mild opinions)
- When unsure between analysis and hot_take: if the claim is the main payload (not the reasoning) → hot_take

Post to classify:
{text}

Respond with exactly one word — the label name: analysis, hot_take, or reaction"""
```

### Running the Baseline

Run all baseline cells. The notebook will:
1. Classify every test example using Groq's `llama-3.3-70b-versatile`
2. Print overall accuracy and per-class precision/recall/F1
3. Flag any unparseable responses

If >10% of responses are unparseable, add this to the prompt:
> "Output only the label name on a single line. Do not include punctuation, explanation, or any other text."

### Save Baseline Numbers

After running, copy the baseline accuracy and per-class metrics to a text file or note them below. You'll need them for the Section 6 comparison.

Expected baseline range: 50–65% accuracy (zero-shot on a nuanced 3-class task)

---

## Section 3 — Fine-Tuning

Run Section 3 with these settings (or adjust and document why):

```python
# Hyperparameters
NUM_EPOCHS = 4          # Increased from default 3; small dataset benefits from more passes
LEARNING_RATE = 2e-5    # Default; standard for DistilBERT fine-tuning
BATCH_SIZE = 8          # Reduced from 16 to account for 202-example dataset size
WARMUP_STEPS = 50       # Warmup helps with small dataset stability
WEIGHT_DECAY = 0.01     # Light regularization
```

**Hyperparameter decision to document in README:**
- Batch size reduced from 16 to 8 because with only ~141 training examples, a batch of 16 means only ~9 gradient updates per epoch, which is too few for stable learning. Batch size 8 gives ~18 gradient updates per epoch.
- Epochs increased from 3 to 4 because early stopping on validation loss typically triggers around epoch 3–4 on small datasets.

Training time: ~5–15 minutes on T4 GPU.

---

## Section 4 — Fine-Tuned Model Evaluation

Run Section 4. It produces:
- Per-class precision, recall, F1 for the fine-tuned model
- `confusion_matrix.png` (download this to the repo)
- Wrong predictions listed with true and predicted labels

Identify 3 wrong predictions to analyze in depth. For each, note:
1. The post text
2. True label vs. predicted label
3. Why the model likely got it wrong (boundary ambiguity, short text, sarcasm, etc.)

---

## Section 6 — Comparison and Export

Run Section 6. It produces:
- Side-by-side comparison: baseline vs. fine-tuned
- `evaluation_results.json` (download this to the repo)

**Download both files** from the Colab Files panel (right-click → Download):
- `evaluation_results.json` → save to repo root
- `confusion_matrix.png` → save to repo root

Then commit both to GitHub:
```bash
git add evaluation_results.json confusion_matrix.png
git commit -m "Add evaluation results and confusion matrix from Colab"
```

---

## After Colab: Update the README

After you have real numbers from Colab, fill in the placeholder sections in `README.md`:
- Replace all `[PLACEHOLDER]` markers with actual metrics
- Write the confusion matrix as a markdown table
- Fill in the 3 wrong prediction analyses
- Complete the sample classifications table with real confidence scores

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Runtime reset | Re-upload CSV, re-run Sections 1, 2, and 5 before continuing |
| >10% unparseable baseline responses | Make the prompt output format more explicit |
| Fine-tuned worse than baseline | Check for label leakage, class imbalance, or wrong label map |
| CUDA out of memory | Reduce batch size to 4 |
| Training loss not decreasing | Increase learning rate to 3e-5, or check that label map matches CSV |
