# skills

A collection of agentic skills for scientific research and ML engineering. Install them via the `skills` npm module, the included `install_skills.py` CLI (for opencode), or just copy a skill's folder into your agent's skills directory.


## Skills

| Skill | Description |
|---|---|
| [git-rules](./git-rules) | Git workflow rules for coding agents — when/how to commit, push, handle conflicts |
| [karpathy-guidelines](./karpathy-guidelines) | Behavioral guidelines to reduce common LLM coding mistakes |
| [pandas-guidelines](./pandas-guidelines) | Pandas DataFrame operations — cleaning, aggregation, merging, time series |
| [uv-env](./uv-env) | Python environment and package management with uv |
| [synthetic-data-gen](./synthetic-data-gen) | Synthetic data generation with Distilabel; export to HF Hub or disk |
| [llm-finetuning](./llm-finetuning) | Fine-tune Hugging Face LLMs with Axolotl & TRL; sane defaults, push to HF Hub |
| [no-bs](./no-bs) | Stop anthropic models from generating unnecessary and complicated descriptions |
| [ultimate-guitar-chords](./ultimate-guitar-chords) | Find and fetch song chords from ultimate-guitar.com without a browser |


## Installation

### Option A — `skills` npm module

```bash
npx skills add ./open-science-skills

# or a single skill
npx skills add ./git-rules
```

This installs into `~/.claude/skills` and `~/.agents/skills` (compatible dirs that opencode also reads), not opencode's native `~/.config/opencode/skills`.

### Option C — manual copy

Copy any skill's folder into your agent's skills directory, e.g.:

```bash
cp -r llm-finetuning ~/.config/opencode/skills/
# or
cp -r llm-finetuning ~/.claude/skills/
```


## License
MIT


## Resources

The following skills were collected from the linked sources:
- [karpathy-guidelines](https://github.com/multica-ai/andrej-karpathy-skills)
- [pandas-guidelines](https://github.com/Jeffallan/claude-skills/blob/main/skills/pandas-pro/SKILL.md)
