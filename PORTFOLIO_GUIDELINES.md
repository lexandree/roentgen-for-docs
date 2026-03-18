# Instructions for Project Agents: Portfolio Export Standard

To ensure seamless integration of this project into the main portfolio website (**Schaufenster**), please generate a `portfolio-export.md` file in the root of the repository following this exact structure.

## 1. Structure Requirements

The file MUST consist of two parts:
1.  **YAML Frontmatter**: Metadata for the project card on the main page.
2.  **Markdown Body**: Technical details for the dedicated project page.

## 2. Formatting Template

```markdown
---
title: "Project Name"
description: "A 1-2 sentence high-impact summary. Focus on WHAT it does and the primary TECH. Avoid marketing fluff."
pubDate: YYYY-MM-DD
tags: ["Tech1", "Tech2", "Methodology"]
githubUrl: "https://github.com/lexandree/repo-name"
featured: false
order: 10
---

## Problem Statement
Briefly describe the challenge. Why was this built? What gap does it fill? (Use "hacker-style" directness if appropriate).

## Approach / Architecture
Technical breakdown of the solution. 
- Highlight key components (Inference engines, DBs, Tunnels).
- Mention specific optimizations (ROI cropping, FFT, GBNF grammars, WandB logging).
- Explain the data flow or connectivity (e.g., Secure Reverse SSH).

## Results / Metrics
Quantifiable outcomes or architectural wins.
- **Metric/Win Name**: Description of accuracy improvements, performance benchmarks.
- **Metric/Win Name**: Description of system reliability or security compliance.
```

## 3. Best Practices for Content

*   **Scannability**: Start every bullet point in the Approach and Results sections with a **Bold Term** (e.g., **Secure Tunneling**: ...). Keep descriptions punchy.
*   **Seniority Signals**: Use specific technical terms (e.g., `multi-slot KV cache`, `triples extraction`, `FFT seasonality`).

*   **Business Value**: If applicable, mention metrics (e.g., "reduced hallucinations by X%", "captured seasonality missed by Prophet").
*   **Tone**: Dev-to-Dev. Sharp, professional, but not "corporate". Be honest about the "hacker" nature of the project if it was built to bypass expensive/slow alternatives.
*   **Language**: The file MUST be written in **English**.

## 4. Automation Note
This file will be automatically fetched by the portfolio's GitHub Action and converted into a live page. Ensure the frontmatter fields strictly match the template.
