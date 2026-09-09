# CivicLens AI — AI & Machine Learning Pipeline Reference

This document describes the design, feature pipelines, and inference equations for all AI components in `CivicLensAI/ai/models`.

---

## 1. Multimodal Issue Classifier (`MultimodalIssueClassifier`)

Combines image visual cues with natural language token matching for instant zero-latency categorization across 11 municipal categories:
- `POTHOLE`, `DAMAGED_ROAD`, `STREETLIGHT`, `GARBAGE`, `DRAINAGE`, `WATER_LEAKAGE`, `DAMAGED_SIGN`, `FOOTPATH`, `OPEN_MANHOLE`, `ILLEGAL_DUMPING`, `PUBLIC_FACILITY`.

### 1.1 Visual Signal Extraction
- Resizes input image to $128 \times 128$ RGB.
- Computes mean color channels ($\mu_R, \mu_G, \mu_B$) and luminance variance $\text{Var}(I_{\text{gray}})$.
- Measures edge density via discrete gradient approximation:
  $$\text{EdgeDensity} = \frac{1}{W \times H} \sum_{x, y} \left( |I(x+1, y) - I(x, y)| + |I(x, y+1) - I(x, y)| \right)$$

### 1.2 Softmax Temperature Scaling
Text match activations and visual modulations are combined into logits $z_k$ and passed through Softmax with temperature $T=2.5$:
$$P(c_k) = \frac{e^{z_k \cdot 2.5}}{\sum_j e^{z_j \cdot 2.5}}$$

---

## 2. Spatio-Temporal Duplicate Detector (`SpatioTemporalDuplicateDetector`)

Prevents municipal queue overload by clustering proximate complaints into unified action units.

### 2.1 Distance & Spatial Decay
Calculates exact great-circle distance $d$ via the Haversine equation ($R = 6,371,000 \text{ m}$):
$$\text{GeoSim}(d) = \begin{cases} 
1.0 & \text{if } d \le 10\text{ m} \\
\max(0, 1 - \frac{d}{200}) & \text{if } 10 < d \le 200\text{ m} \\
0.0 & \text{if } d > 200\text{ m}
\end{cases}$$

### 2.2 Temporal Exponential Decay
Accounts for seasonal repairs and recurring defects:
$$\text{TimeSim}(\Delta t) = e^{-\frac{\Delta t_{\text{days}}}{30}}$$

### 2.3 Composite Similarity
$$\text{CompositeScore} = 0.40 \cdot \text{GeoSim} + 0.25 \cdot \text{CatMatch} + 0.15 \cdot \text{TextJaccard} + 0.10 \cdot \text{TimeSim} + 0.10 \cdot \text{ImgSim}$$
Pairs with $\text{CompositeScore} \ge 0.70$ are flagged as candidate duplicates.

---

## 3. Explainable Multi-Factor Priority Engine (`ExplainablePriorityEngine`)

Outputs priority levels ($P_1$: Emergency $\le 6$h, $P_2$: High $\le 24$h, $P_3$: Medium $\le 72$h, $P_4$: Low $\le 168$h) and produces audit-ready human explanations:

$$\text{PriorityScore} = w_{\text{sev}} S_{\text{sev}} + w_{\text{safe}} S_{\text{safe}} + w_{\text{traf}} S_{\text{traf}} + w_{\text{dup}} S_{\text{dup}} + w_{\text{dur}} S_{\text{dur}}$$
- **Safety Risk Boost**: Categories like `OPEN_MANHOLE` and `WATER_LEAKAGE` inject a $+0.85$ safety bias.
- **Traffic Factor**: Main arterial roads / school zones receive $+0.90$.
- **Duplicate Reinforcement**: High citizen report density ($> 5$ duplicates) escalates tickets to $P_1$ or $P_2$.
