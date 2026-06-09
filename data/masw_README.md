---
title: MaliciousAgentSkillsBench
license: mit
---

# "Do Not Mention This to the User": Detecting and Understanding Malicious Agent Skills

A comprehensive security benchmark dataset and evaluation framework for Claude Code Agent Skills. We collect **98,380 skills** from two major platforms (skills.rest and skillsmp.com), including **157 malicious samples** identified through systematic security analysis.

## Purpose

The code and data in this repository are intended exclusively for:
- Academic research on AI agent security
- Developing defense mechanisms against malicious agent skills
- Evaluating the robustness of AI agent platforms

## Files

| File | Rows | Description |
|------|------|-------------|
| `skills_dataset.csv` | 98,380 | Complete dataset (safe/suspicious/malicious) |
| `malicious_skills.csv` | 157 | Malicious samples with vulnerability patterns |

## Columns

**skills_dataset.csv:** `source,repo,skill_name,classification,url`

**malicious_skills.csv:** `source,repo,skill_name,classification,Pattern`

## Usage

```python
import pandas as pd

# Load dataset
df = pd.read_csv('skills_dataset.csv')
malicious = pd.read_csv('malicious_skills.csv')
```

## Citation

```bibtex
@misc{malicious_agent_skills_bench,
  title={"Do Not Mention This to the User": Detecting and Understanding Malicious Agent Skills},
  author={Anonymous},
  year={2026},
}
```

**GitHub:** https://github.com/protectskills/MaliciousAgentSkillsBench

## License

MIT License

