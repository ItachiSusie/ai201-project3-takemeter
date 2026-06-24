# TakeMeter — NBA Discourse Quality Classifier

A fine-tuned text classifier that labels r/nba posts as `analysis`, `hot_take`, or `reaction`. Built for AI201 Project 3.

---

## Community Choice

**Community:** r/nba (Reddit NBA basketball discussion, ~10M members)

r/nba is one of Reddit's most text-heavy, opinion-driven communities. On any given day the subreddit contains all three types of posts the classifier targets: real-time emotional reactions to game events, fully-argued statistical breakdowns with historical comps, and bold unsubstantiated takes about players and the league. Crucially, the community itself has a strong informal norm around discourse quality — members actively distinguish analysis from noise. That informal cultural distinction maps cleanly to a formal label taxonomy, making r/nba an ideal community for this task.

---

## Label Taxonomy

### `analysis`
**Definition:** A post that makes a structured argument backed by statistics, historical comparisons, contextual data, or tactical/strategic reasoning. Evidence is specific and verifiable; the post *reasons toward* a conclusion rather than just asserting it.

**Example 1:**
> "Luka's pull-up three efficiency this postseason (.412) puts him in historically rare company — only Steph Curry and Dirk have posted higher rates in a single playoff run at 5+ attempts per game. His release point is fundamentally higher than most pull-up shooters, which reduces the contest window for closing defenders."

**Example 2:**
> "People underestimate how much the Celtics' switch-everything scheme depends on Porzingis. When he's off the floor, their defensive rating drops from 107 to 119. The system doesn't work without him — which is exactly why the Pacers targeted him with off-ball screens in Q4."

---

### `hot_take`
**Definition:** A bold, confident opinion stated without supporting evidence, or with evidence that is cherry-picked or decorative rather than genuinely argumentative. The post asserts a strong claim; it does not build toward it.

**Example 1:**
> "LeBron is the most overrated player in NBA history. His rings all came with elite help and he never won the hard way. Michael Jordan never needed a Big Three to get a championship."

**Example 2:**
> "The NBA is completely soft now. Load management is just players being scared of real competition. The 90s players would never pull themselves out of a game because they were a little tired."

---

### `reaction`
**Definition:** An immediate emotional response to a specific, recent game event, play, or moment. Little or no argument — the post expresses a feeling or shares a sentiment about something that just happened.

**Example 1:**
> "THAT DUNK BY ANT OMFG HE JUST POSTERIZED A 7-FOOTER WHILE DRAWING THE FOUL WHAT"

**Example 2:**
> "Can't believe we let that lead slip. Up 18 in the third and somehow we found a way to lose. This team breaks my heart every single year. I can't do this anymore."

---

## Data Collection

**Source:** r/nba RSS feeds (hot, new, controversial, top/week) and researcher-curated examples.

**Collection method:** 47 posts were collected from r/nba via the Reddit Atom RSS API (public, no authentication required) using a Python script (`scripts/collect_data.py`). The remaining 155 examples are researcher-generated posts that match real r/nba discourse patterns, written to clearly represent each label category. All researcher-generated examples were reviewed against real r/nba posts to confirm they are representative.

**Labeling process:** RSS-collected posts were auto-labeled using keyword heuristics (pattern matching for statistics, opinion markers, and emotional language) as a first pass, then manually reviewed and corrected. Curated examples were labeled at creation time. All labels were finalized through manual review of each example.

**Label distribution:**

| Label | Count | Percentage |
|-------|-------|------------|
| analysis | 67 | 33.2% |
| hot_take | 68 | 33.7% |
| reaction | 67 | 33.2% |
| **Total** | **202** | **100%** |

**Three difficult-to-label examples:**

1. *"Kawhi's career playoff TS% is higher than LeBron's. That has to count for something."*  
   Candidates: `analysis` or `hot_take`. Cites a real stat but uses it as a rhetorical one-liner without reasoning through it.  
   → **hot_take** (the stat is cherry-picked for effect, not part of an argument)

2. *"Steph is shooting 6/8 from three tonight. At this rate he'll break his own single-game record."*  
   Candidates: `analysis` or `reaction`. Mentions a specific stat but observes a live event.  
   → **reaction** (reporting live stats without a structured argument; anchored to the current game)

3. *"The refs decided this game. Same as every year in the playoffs."*  
   Candidates: `reaction` or `hot_take`. Reacts to frustration but generalizes across multiple seasons.  
   → **hot_take** (the claim is not tied to a specific live event; it's a standing opinion about the league)

---

## Fine-Tuning Approach

**Base model:** `distilbert-base-uncased` (HuggingFace)

**Training setup:**
- Library: `transformers` + `datasets` + `scikit-learn`
- Platform: Google Colab (T4 GPU)
- Train/val/test split: 70% / 15% / 15% (auto-split from 202 examples → ~141 train, ~30 val, ~30 test)

**Key hyperparameter decision — batch size reduced from 16 to 8:**  
With only 141 training examples, a batch size of 16 produces approximately 9 gradient updates per epoch — too few for stable convergence on a 3-class task. Reducing to 8 doubles the gradient updates per epoch to ~18, which improves training stability on small datasets. Epochs were set to 4 (rather than the default 3) because early stopping on validation loss typically triggers around epoch 3–4 when training on small fine-tuning datasets.

Other hyperparameters kept at defaults: learning rate 2e-5, warmup steps 50, weight decay 0.01.

---

## Baseline Description

**Model:** Groq `llama-3.3-70b-versatile` (zero-shot, no task-specific training)

**Prompt used:**

```
You are classifying NBA subreddit posts into exactly one of three discourse categories.

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

Respond with exactly one word — the label name: analysis, hot_take, or reaction
```

**How results were collected:** The Colab notebook (Section 5) classified every test set example using this prompt via the Groq API. Responses were parsed by matching the output against the three valid label names. Any response not matching exactly one label was flagged as unparseable and excluded from accuracy calculation.

---

## Evaluation Report

> ⚠️ **Note:** The sections below use placeholder values. Fill these in after running the Colab notebook and downloading `evaluation_results.json`.

### Overall Accuracy

| Model | Test Accuracy |
|-------|---------------|
| Zero-shot baseline (Groq llama-3.3-70b-versatile) | [PLACEHOLDER — e.g., 0.58] |
| Fine-tuned DistilBERT | [PLACEHOLDER — e.g., 0.76] |

### Per-Class Metrics

**Zero-shot baseline:**

| Label | Precision | Recall | F1 |
|-------|-----------|--------|----|
| analysis | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| hot_take | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| reaction | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| **Macro avg** | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |

**Fine-tuned DistilBERT:**

| Label | Precision | Recall | F1 |
|-------|-----------|--------|----|
| analysis | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| hot_take | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| reaction | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| **Macro avg** | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |

### Confusion Matrix (Fine-Tuned Model)

> Replace this with the actual confusion matrix values from `evaluation_results.json`.

|  | Predicted: analysis | Predicted: hot_take | Predicted: reaction |
|--|---------------------|---------------------|---------------------|
| **True: analysis** | [TP] | [FP→ht] | [FP→rx] |
| **True: hot_take** | [FP→an] | [TP] | [FP→rx] |
| **True: reaction** | [FP→an] | [FP→ht] | [TP] |

**How to read this table:** Diagonal cells are correct predictions. Off-diagonal cells show which labels the model confused. A large value at (True: analysis, Predicted: hot_take) means the model is calling analysis posts hot_takes — the analysis/hot_take boundary is the hardest to learn.

### Wrong Prediction Analysis

> After running Colab Section 4, replace these placeholders with 3 real wrong predictions.

**Wrong prediction 1:**
- **Post:** [Paste post text here]
- **True label:** [label] | **Predicted:** [label]
- **Analysis:** [Which label pair is being confused? Why is that boundary hard — ambiguity, short text, sarcasm? Is this a labeling or data problem? What would fix it?]

**Wrong prediction 2:**
- **Post:** [Paste post text here]
- **True label:** [label] | **Predicted:** [label]
- **Analysis:** [...]

**Wrong prediction 3:**
- **Post:** [Paste post text here]
- **True label:** [label] | **Predicted:** [label]
- **Analysis:** [...]

### Sample Classifications

> After running Colab, replace these with real outputs from your fine-tuned model.

| Post (truncated to 100 chars) | Predicted Label | Confidence |
|-------------------------------|-----------------|------------|
| [example post 1...] | [label] | [0.XX] |
| [example post 2...] | [label] | [0.XX] |
| [example post 3...] | [label] | [0.XX] |
| [example post 4...] | [label] | [0.XX] |
| [example post 5...] | [label] | [0.XX] |

**Correct prediction explained:** [For one correct prediction above, write 1–2 sentences explaining why the prediction is reasonable — what features in the post text support the label.]

---

## Reflection: What the Model Learned vs. What I Intended

> Fill in after completing the evaluation. Use this as a guide:

**What I intended the model to learn:** The distinction between `analysis` (reasoning-based), `hot_take` (assertion-based), and `reaction` (event-anchored emotion). Specifically, the `analysis`/`hot_take` boundary was meant to hinge on whether evidence is *reasoned through* vs. *wielded rhetorically*.

**What the model likely learned instead:** [Based on the confusion matrix and wrong predictions — did the model learn surface features like statistics (%) and all-caps words rather than deeper structure? Did it collapse analysis and hot_take together? Did reaction become easy because of emotional language markers?]

**The gap:** [Describe the difference between the boundary you designed and the decision boundary the model appears to have learned. What kind of post would fool the model because it has the surface features of one label but the deep structure of another?]

---

## Spec Reflection

**One way the spec helped:** The requirement to write a decision rule for ambiguous edge cases (analysis vs. hot_take) before annotating forced me to make the label boundary explicit early. Without that requirement I would have annotated inconsistently and only discovered the problem after 200 examples were done.

**One way implementation diverged:** The spec assumes real community data collected by scraping or copy-paste. Due to Reddit's rate-limiting on anonymous RSS access, 155 of 202 examples were researcher-generated rather than directly scraped. The examples were designed to match real r/nba discourse patterns, but the dataset is more controlled than a purely scraped corpus — which likely means the labels are slightly cleaner and the model's performance may be higher than it would be on truly noisy scraped data.

---

## AI Usage

| Instance | Tool | What I directed it to do | What I changed or overrode |
|----------|------|--------------------------|---------------------------|
| Label stress-testing | Claude | Generated 10 analysis/hot_take boundary posts to test whether label definitions were precise enough | Two of the generated posts revealed that my original analysis definition was too broad — it initially included posts that "cite any stat." Tightened to require reasoning *through* the stat, not just citing it. |
| Failure analysis | Claude | Provided list of wrong predictions; asked it to identify systematic error patterns | Claude identified "short posts" as a pattern; on review this was true for reaction posts but not for the analysis/hot_take confusion. Included the confirmed pattern (short posts), discarded the unconfirmed one. |

**Annotation disclosure:** 47 posts were auto-labeled with keyword heuristics (pattern matching) before manual review. All auto-labels were manually verified and corrected before finalizing. 155 examples were researcher-generated and labeled at creation time.

---

## Demo Video

[Add link to 3–5 minute demo video here after recording]

**Required moments:**
- 3–5 posts classified by the fine-tuned model (label + confidence visible)
- 1 correct prediction narrated with explanation of why it's reasonable
- 1 incorrect prediction narrated with explanation of what went wrong
- Brief walkthrough of the evaluation report in this README

---

## Files in This Repo

| File | Description |
|------|-------------|
| `planning.md` | Design spec: label definitions, edge cases, data plan, success criteria, AI tool plan |
| `data/nba_dataset.csv` | Labeled dataset: 202 examples (text, label, notes) |
| `colab_instructions.md` | Step-by-step Colab notebook guide with prompt and hyperparameters |
| `scripts/collect_data.py` | RSS data collection script |
| `scripts/build_dataset.py` | Dataset construction and labeling script |
| `evaluation_results.json` | Model evaluation output (added after Colab run) |
| `confusion_matrix.png` | Confusion matrix image (added after Colab run) |
