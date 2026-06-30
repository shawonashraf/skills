# open-science-skills

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


## Installation

### Option A — opencode (recommended for opencode users)

opencode discovers skills in `~/.config/opencode/skills/<name>/SKILL.md` (global) and `.opencode/skills/<name>/SKILL.md` (per-project), plus the compatible `~/.claude/skills/` and `~/.agents/skills/` dirs. The `skills` npm module does not write to opencode's native dir — the included CLI does:

```bash
# list skills available in this repo
python install_skills.py list

# install all skills globally into ~/.config/opencode/skills (symlinks)
python install_skills.py add all

# install specific skills
python install_skills.py add git-rules uv-env

# install per-project instead of global
python install_skills.py add all --project

# copy files instead of symlinking; overwrite existing
python install_skills.py add all --copy --force

# also mirror into ~/.claude/skills and ~/.agents/skills (for other tools)
python install_skills.py add all --compatible

# show what's installed
python install_skills.py installed

# re-sync when the repo changes
python install_skills.py update

# remove
python install_skills.py remove git-rules
python install_skills.py remove all
```

Requires Python 3.8+ and stdlib only (no pip dependencies). The installer validates each skill against opencode's rules (frontmatter `name` matches the dir, matches `^[a-z0-9]+(-[a-z0-9]+)*$`, `description` ≤1024 chars) and records installs in a `.science-skills.lock.json` for `update`/`remove`. Run `python install_skills.py --help` for the full reference.

### Option B — `skills` npm module

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
