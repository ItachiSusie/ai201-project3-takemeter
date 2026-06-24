# TakeMeter — Planning Document

**Community:** r/nba  
**Model:** distilbert-base-uncased (fine-tuned)  
**Labels:** `analysis` · `hot_take` · `reaction`

---

## 1. Community

**Chosen community:** r/nba (Reddit NBA basketball discussion, ~10M members)

**Why this community?** r/nba is one of the most text-heavy, opinion-driven sports communities on the internet. Members post reactions to games in real time, write detailed statistical breakdowns, and argue hot takes constantly. Crucially, the community itself has a strong informal norm around discourse quality — members distinguish between posts that make genuine arguments and posts that are just vibes or empty claims. That informal distinction maps cleanly to a formal label taxonomy, making this community ideal for a discourse-quality classifier.

**What makes the discourse varied enough?** On any given day, r/nba contains: game-thread emotional reactions ("THAT BLOCK OMG"), fully argued statistical analyses with comps and percentages, and bold unsubstantiated opinions ("Jordan would have 10 rings in LeBron's era"). The variance is real and meaningful, not just surface-level noise — different post types serve different community functions and receive systematically different reception.

---

## 2. Labels

### `analysis`
A post that makes a structured argument backed by statistics, historical comparisons, contextual data, or tactical/strategic reasoning. Evidence is specific and verifiable; the post *reasons toward* a conclusion rather than just asserting it.

**Example 1:**
> "Luka's efficiency on pull-up threes this postseason (.412 3P%) puts him in rare company — only Steph Curry and Dirk have posted higher rates in a single playoff run with 5+ attempts per game. His step-back geometry is fundamentally different: he releases at a higher apex, meaning defenders closing out get less contest window. This isn't just hot — it's reproducible."

**Example 2:**
> "People are sleeping on how much the Celtics' switch-everything scheme depends on a 7-footer who can guard guards. When Porzingis is off the floor, their defensive rating drops from 107 to 119. The system doesn't work without him — which is exactly why the Pacers targeted him with off-ball screens in Q4."

---

### `hot_take`
A bold, confident opinion stated without supporting evidence, or with evidence that is cherry-picked or decorative rather than genuinely argumentative. The post asserts a strong claim; it does not build toward it.

**Example 1:**
> "LeBron is the most overrated player in NBA history. His ring count only happened because he had elite help every single time. Jordan would have 10 rings in LeBron's era."

**Example 2:**
> "The NBA is soft now. Players take days off for 'load management' and nobody calls it what it is — they're just scared of competing. The 90s players would have laughed at this."

---

### `reaction`
An immediate emotional response to a specific, recent game event, play, or moment. Little or no argument — the post expresses a feeling or shares a sentiment about something that just happened. Often short and anchored to a live context.

**Example 1:**
> "THAT DUNK BY ANT OMFG HE JUST PUT THE WHOLE LEAGUE ON NOTICE"

**Example 2:**
> "Can't believe we let that lead slip. This team breaks my heart every single year. I'm done."

---

## 3. Hard Edge Cases

### Edge case 1: analysis vs. hot_take — stat-backed claims
**Post:** "Kawhi's career playoff TS% is higher than LeBron's. That has to count for something."

This cites a real stat but doesn't reason through it — it uses one number as a rhetorical weapon to assert superiority.

**Decision rule:** If the post provides specific, verifiable evidence that would still support its claim after you strip out the opinion framing, label it `analysis`. If the evidence is cherry-picked, vague, or decorative — just enough to sound credible without genuine reasoning — label it `hot_take`. When in doubt: if the post's main payload is the *claim* (not the reasoning), it's `hot_take`.  
→ This post: **hot_take** (stat is one-liner rhetorical, no argument built from it)

### Edge case 2: reaction vs. hot_take — situational opinions
**Post:** "Why does [Coach] keep playing [Player] 38 minutes? He's been terrible tonight. Fire him."

This reacts to something in a live game but contains an opinion that generalizes ("fire him").

**Decision rule:** If the post is anchored to a specific event that just happened (a game, a play, a trade), label it `reaction`. If it makes a general claim about players, teams, or the league that could stand alone without the event context, label it `hot_take`.  
→ This post: **reaction** (frustration is rooted in the specific game; "fire him" is emotional, not a general argument)

### Edge case 3: analysis vs. reaction — stat-citing post in a game thread
**Post:** "Steph is shooting 6/8 from three tonight. At this rate he'll break his own single-game record."

Mentions a stat in a game thread but doesn't argue anything — it's observing something happening live.

**Decision rule:** Observations of live stats without a structured argument are `reaction`, not `analysis`.  
→ This post: **reaction** (reporting a live stat, not reasoning from it)

### Annotation-time decisions (updated during Milestone 3)

| Post excerpt | Candidates | Decision | Rule applied |
|---|---|---|---|
| "Steph just hit his 4th three of the half. This is inexcusable coaching." | reaction / hot_take | reaction | Anchored to live game event, critique is emotional not argued |
| "Kawhi's playoff TS% > LeBron's. Case closed." | analysis / hot_take | hot_take | One stat, no reasoning |
| "The refs decided this game. Same as every year in the playoffs." | reaction / hot_take | hot_take | Not tied to specific moment, generalizes about pattern |

---

## 4. Data Collection Plan

**Source:** r/nba RSS feeds (multiple sort types: hot, new, controversial, top/week, top/month)  
**Method:** Python script using `requests` + XML parsing of Atom RSS. No authentication required. Public posts only.

**Target distribution (200+ examples):**
| Label | Target count | Percentage |
|---|---|---|
| analysis | 67+ | ~33% |
| hot_take | 67+ | ~33% |
| reaction | 67+ | ~33% |

**Collection strategy:**
- Fetch `hot`, `new`, `top?t=week`, `top?t=month`, `controversial` feeds (100 posts each)
- Extract post title + self-text content (skip pure link posts with no body)
- De-duplicate by URL
- Auto-label using keyword heuristics as a first pass
- Manual review and correction of all labels

**If a label is underrepresented after 200 examples:**
- Collect from more specific RSS feeds (e.g., game threads for more reactions)
- Search for self-posts (which tend to be more analysis-heavy)
- Add targeted posts from r/nbadiscussion if needed

---

## 5. Evaluation Metrics

**Primary metrics for this task:**

- **Per-class F1 score** (the most important metric): Because the three classes are roughly balanced but each represents a meaningfully different type of discourse, we need to know if the model is learning *each* distinction — not just getting most posts right by luck. F1 = harmonic mean of precision and recall.
- **Confusion matrix**: Critical for understanding which label pairs the model confuses. An analysis→hot_take confusion is a very different failure mode than reaction→analysis, and the matrix reveals these directional patterns.
- **Macro-averaged F1**: The single summary number for comparing fine-tuned vs. baseline, averaging across all 3 classes without size-weighting.

**Why accuracy alone is insufficient:**
If the model learns to predict `hot_take` for everything (the label likely to appear most in general NBA discourse), it could reach ~35–40% accuracy on a balanced dataset while being completely useless. Per-class metrics reveal this failure; overall accuracy hides it.

**Baseline comparison logic:** The zero-shot Groq baseline tells us the task difficulty for a general LLM with no training. If the baseline already gets >70% F1 per class, the labels may be too easy or too distinct. If it struggles below 50%, that confirms the task genuinely requires training signal.

---

## 6. Definition of Success

A classifier is **genuinely useful** if deployed as a community moderation aid (e.g., auto-tagging posts) would meaningfully reduce moderator workload:

**Minimum acceptable threshold:**
- Per-class F1 ≥ 0.65 for all three labels
- Overall accuracy ≥ 0.70 on test set
- Fine-tuned model must beat baseline on macro-F1

**Deployment-ready threshold:**
- Per-class F1 ≥ 0.75 for all three labels
- Confusion matrix shows no single label-pair account for >40% of total errors

**Red flags that indicate rework is needed:**
- Any label with F1 < 0.50 (model hasn't learned that boundary)
- Fine-tuned model performs ≤ baseline (suggests label noise or data leak)
- One label predicted >70% of the time (majority-class collapse)

---

## 7. AI Tool Plan

### Label stress-testing (pre-annotation)
I will provide Claude with my label definitions and the edge case decision rules, and ask it to generate 10 posts that sit at the boundary between `analysis` and `hot_take` — the hardest pair. If more than 3 of those posts can't be cleanly classified using my decision rule, I'll tighten the definitions before annotating 200 examples.

**Prompt template:** "Here are my label definitions for an NBA discourse classifier: [paste definitions]. Generate 10 Reddit posts that sit at the boundary between analysis and hot_take, making them as hard to classify as possible."

### Annotation assistance
I will use a Python heuristic script for first-pass labeling:
- `reaction` if the post contains all-caps words, exclamations, or explicit references to "tonight", "right now", "this game", "that play"
- `hot_take` if the post contains opinion markers ("overrated", "best ever", "worst ever", "soft", "nobody talks about") without structured evidence
- `analysis` if the post contains statistics (%), historical comparisons, or tactical reasoning

All auto-labels will be reviewed and corrected manually before finalizing. The CSV will include a `notes` column flagging which examples were auto-labeled for disclosure.

### Failure analysis (post-evaluation)
After Colab produces wrong predictions, I will:
1. Paste all misclassified examples into Claude with the prompt: "Here are NBA posts that a fine-tuned classifier got wrong. For each: what label was predicted, what was correct, and identify any systematic pattern in the errors."
2. Verify Claude's patterns myself by re-reading the examples
3. Include confirmed patterns in the README evaluation report, noting what I had to correct or discard from Claude's analysis

---

## AI Usage Log
*(Updated throughout the project)*

| Step | Tool used | What I asked it to do | What I changed |
|---|---|---|---|
| Label stress-test | Claude | Generate 10 analysis/hot_take boundary posts | — |
| Failure analysis | Claude | Identify error patterns in wrong predictions | — |
