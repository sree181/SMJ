# How We Determine How Strongly a Theory Explains a Phenomenon

## A Simple Explanation

Imagine you're reading a research paper and you want to know: **"Does this theory really explain this phenomenon?"**

Instead of just guessing "yes" or "no," we now have a smart system that gives a **score from 0 to 100%** (like a grade) that tells us how confident we are that the theory explains the phenomenon.

---

## The Old Way (Simple but Limited)

**Before**, we had a very simple system:
- If the theory was the **main theory** of the paper → give it a score of **70%**
- If the theory was a **supporting theory** → give it a score of **50%**

**Problem**: This was too simple. It didn't consider:
- Whether the theory and phenomenon appear in the same section
- Whether they use similar words
- Whether the theory explicitly mentions the phenomenon

---

## The New Way (Smart and Detailed)

**Now**, we look at **5 different clues** to determine the score:

### Clue 1: How Important is the Theory? (0-40 points)

**Think of it like**: Is this theory the star of the show, or just a supporting actor?

- **Main theory** (the star) → **40 points**
- **Supporting theory** (supporting actor) → **20 points**
- **Extending theory** (adds to another theory) → **15 points**
- **Challenging theory** (questions another theory) → **10 points**

**Why this matters**: If a theory is the main focus of the paper, it's more likely to explain the phenomenon.

---

### Clue 2: Are They in the Same Place? (0-20 points)

**Think of it like**: Are they sitting next to each other at a dinner party, or on opposite sides of the room?

- **Same section** (e.g., both in "Introduction") → **20 points**
- **Adjacent sections** (e.g., "Introduction" and "Literature Review") → **10 points**
- **Distant sections** (e.g., "Introduction" and "Results") → **5 points**

**Why this matters**: If the theory and phenomenon appear together in the same part of the paper, they're more likely to be connected.

---

### Clue 3: Do They Use Similar Words? (0-20 points)

**Think of it like**: Do they speak the same language?

We look at the words used to describe the theory and the phenomenon. If they share many important words, they're probably talking about the same thing.

- **Many shared words** (like "resource allocation" appears in both) → **20 points**
- **Some shared words** → **10 points**
- **Few shared words** → **5 points**
- **No shared words** → **0 points**

**Why this matters**: If they use similar language, they're likely discussing related concepts.

---

### Clue 4: Do They Mean Similar Things? (0-20 points)

**Think of it like**: Even if they use different words, do they mean the same thing?

This is like understanding that "car" and "automobile" mean the same thing, even though they're different words.

- **Very similar meaning** → **20 points**
- **Similar meaning** → **15 points**
- **Somewhat similar** → **10 points**
- **Not similar** → **0 points**

**Why this matters**: Sometimes theories and phenomena are connected even if they don't use the exact same words.

---

### Clue 5: Does the Theory Explicitly Mention the Phenomenon? (0-10 bonus points)

**Think of it like**: Does the theory directly say "I explain this phenomenon"?

- **Exact mention** (theory text contains the phenomenon name) → **10 bonus points**
- **Partial mention** (most words from phenomenon name appear) → **5-8 bonus points**
- **No mention** → **0 points**

**Why this matters**: If the theory explicitly mentions the phenomenon, that's the strongest signal of connection.

---

## How We Add It All Up

We add up all the points from the 5 clues:

```
Total Score = Clue 1 + Clue 2 + Clue 3 + Clue 4 + Clue 5
```

**Maximum possible score**: 100 points (or 100%)

**Minimum threshold**: 30 points (or 30%)
- If the score is below 30, we don't create a connection (it's too weak)
- If the score is 30 or above, we create a connection and store the score

---

## Real Example

Let's say we have:

**Theory**: "Resource-Based View" (main theory)
- Used in the **Introduction** section
- Says: "explains how firms allocate resources during financial crises"

**Phenomenon**: "Resource allocation patterns during financial crises"
- Mentioned in the **Introduction** section
- Described as: "How firms allocate resources during financial crises"

### Scoring:

1. **Clue 1 (Importance)**: Main theory → **40 points**
2. **Clue 2 (Same Place)**: Both in Introduction → **20 points**
3. **Clue 3 (Similar Words)**: Many shared words ("resource", "allocate", "crises") → **20 points**
4. **Clue 4 (Similar Meaning)**: Very similar meaning → **20 points**
5. **Clue 5 (Explicit Mention)**: Phenomenon name appears in theory text → **10 bonus points**

**Total Score**: 40 + 20 + 20 + 20 + 10 = **110 points**

Since we cap at 100, this becomes **100 points (100%)** - a **very strong connection**!

---

## What the Scores Mean

| Score Range | What It Means | Example |
|-------------|---------------|---------|
| **80-100%** | **Very Strong** | Theory clearly explains phenomenon. High confidence. |
| **60-80%** | **Strong** | Theory likely explains phenomenon. Good confidence. |
| **40-60%** | **Moderate** | Theory may explain phenomenon. Some confidence. |
| **30-40%** | **Weak** | Theory might explain phenomenon. Low confidence. |
| **0-30%** | **Very Weak** | No connection created (too uncertain). |

---

## Why This Is Better

### The Old Way:
- Only looked at 1 thing (is it the main theory?)
- Only gave 2 possible scores (50% or 70%)
- Couldn't tell the difference between a strong connection and a weak one

### The New Way:
- Looks at 5 different clues
- Gives scores from 0% to 100%
- Can tell the difference between strong, moderate, and weak connections
- More accurate and reliable

---

## In Simple Terms

**Think of it like a detective solving a case:**

Instead of just asking "Is this person a suspect?" (yes/no), the detective now:
1. Checks how important the person is (Clue 1)
2. Checks if they were at the scene (Clue 2)
3. Checks if their story matches the evidence (Clue 3)
4. Checks if their behavior matches the crime (Clue 4)
5. Checks if they directly mentioned the crime (Clue 5)

Then the detective gives a **confidence score** (0-100%) about whether this person is connected to the crime.

**That's exactly what we do** - we're like detectives, but for research papers, trying to figure out if a theory explains a phenomenon!

---

## Summary

- **What we do**: We calculate a score (0-100%) that tells us how strongly a theory explains a phenomenon
- **How we do it**: We look at 5 clues (importance, location, words, meaning, explicit mention) and add up the points
- **Why it matters**: More accurate connections help researchers find better information faster
- **The result**: A smarter system that can tell the difference between strong, moderate, and weak connections

**Bottom line**: Instead of just saying "maybe" or "probably," we now give a precise score that tells you exactly how confident we are!

