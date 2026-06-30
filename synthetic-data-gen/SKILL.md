---
name: synthetic-data-gen
description: >-
  Synthetic data generation with Distilabel, OpenAI/Anthropic-compatible LLM inference endpoints.
  Enables building fast, reliable, and scalable pipelines for synthetic data generation and AI feedback.
  Supports exporting datasets to HuggingFace Hub and saving to disk in multiple formats.
  Use when generating instruction datasets, preference data, dialogue data, or any synthetic dataset
  for LLM fine-tuning, evaluation, or research purposes.
license: MIT
---

# Synthetic Data Generation with Distilabel

**Expert synthetic data engineer** specializing in building reproducible, auditable pipelines for LLM-based synthetic data generation using Distilabel. Supports OpenAI/Anthropic-compatible endpoints, HuggingFace integration, and disk persistence.

## Overview

This skill provides comprehensive guidance for generating synthetic datasets using:

- **[Distilabel](https://github.com/argilla-io/distilabel)**: Framework for building scalable synthetic data and AI feedback pipelines
- **OpenAI/Anthropic-compatible LLM endpoints**: Support for OpenAI API, Anthropic API, and any OpenAI-compatible inference endpoints
- **HuggingFace Datasets**: Native integration for exporting and sharing datasets
- **Disk persistence**: Save datasets in JSON, CSV, Parquet, and other formats

### Key Capabilities

| Capability | Description |
|------------|-------------|
| Multi-step pipelines | Chain generation, evaluation, and curation steps |
| LLM Integration | Connect to OpenAI, Anthropic, Mistral, Groq, and other providers |
| HF Hub Export | Direct export to HuggingFace Hub with `push_to_hub()` |
| Disk Saving | Save datasets locally in multiple formats |
| Quality Control | Built-in evaluation and filtering mechanisms |
| Research-based | Implements verified methodologies from papers (DEITA, UltraFeedback, etc.) |

## Dependencies

### Required Packages

```bash
# Core installation
pip install distilabel datasets huggingface-hub

# Optional extras for LLM providers
pip install "distilabel[openai]"       # OpenAI API
pip install "distilabel[anthropic]"    # Anthropic API
pip install "distilabel[litellm]"      # LiteLLM (multi-provider)
pip install "distilabel[hf-inference-endpoints]"  # HuggingFace Inference Endpoints
```

### LLM Provider Configuration

Create environment variables for your API keys:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-key"

# HuggingFace
export HF_TOKEN="your-hf-token"  # For push_to_hub
```

## Quick Start

### 1. Basic Synthetic Data Generation

```python
from distilabel.pipeline import Pipeline
from distilabel.steps.tasks import TextGeneration
from distilabel.models import OpenAILLM
from datasets import Dataset

# Define dataset
dataset = Dataset.from_dict({
    "instruction": [
        "Explain the concept of synthetic data generation",
        "Write a Python function to reverse a string",
        "List 5 benefits of using LLMs for data generation"
    ]
})

# Create pipeline
with Pipeline() as pipeline:
    TextGeneration(
        llm=OpenAILLM(
            model_name="gpt-4",
            generation_kwargs={"temperature": 0.7, "max_tokens": 512}
        ),
        input_mappers={"prompt": lambda x: x["instruction"]}
    )

# Run pipeline
distiset = pipeline.run(dataset=dataset)

# Save to disk
distiset.to_json("synthetic_dataset.json")
distiset.save_to_disk("synthetic_dataset")
```

### 2. Export to HuggingFace Hub

```python
# After generating distiset
distiset.push_to_hub(
    repo_id="your-username/your-dataset-name",
    token="your-hf-token",
    private=False
)
```

### 3. Multi-Step Pipeline with Quality Evaluation

```python
from distilabel.steps.tasks import TextGeneration, llm_judge

with Pipeline() as pipeline:
    # Generation step
    TextGeneration(
        llm=OpenAILLM(model_name="gpt-4"),
        input_mappers={"prompt": lambda x: x["instruction"]}
    )
    
    # Quality evaluation step
    llm_judge(
        llm=OpenAILLM(model_name="gpt-4"),
        judge_task="Evaluate the quality of the generated response on a scale of 1-10",
        input_mappers={"response": lambda x: x["generated_text"]}
    )

distiset = pipeline.run(dataset=dataset)

# Filter high-quality responses
high_quality = distiset.filter(lambda x: x["score"] >= 7)
high_quality.push_to_hub("your-username/high-quality-dataset")
```

## Core Workflow

### Phase 1: Pipeline Design

1. **Define your data structure**
   - Identify input fields (instructions, prompts, seeds)
   - Define output fields (responses, scores, metadata)
   - Consider data format: JSON, CSV, Parquet

2. **Select LLM provider**
   - Choose based on: cost, quality, latency, rate limits
   - Configure generation parameters (temperature, max_tokens, etc.)

3. **Design pipeline steps**
   - Generation → Evaluation → Filtering → Export
   - Each step can use different LLMs

### Phase 2: Implementation

```python
from distilabel.pipeline import Pipeline
from distilabel.steps.tasks import (
    TextGeneration,
    llm_judge,
    Filter
)
from distilabel.models import OpenAILLM, AnthropicLLM

# Multi-LLM pipeline
with Pipeline() as pipeline:
    # Step 1: Generate responses using Anthropic
    TextGeneration(
        llm=AnthropicLLM(model_name="claude-3-sonnet-20240229"),
        input_mappers={"prompt": lambda x: x["instruction"]},
        output_mappers={"response": lambda x: x["generated_text"]}
    )
    
    # Step 2: Evaluate with OpenAI
    llm_judge(
        llm=OpenAILLM(model_name="gpt-4"),
        judge_task="Rate the response quality from 1-10 based on accuracy and helpfulness",
        input_mappers={"response": lambda x: x["response"]}
    )
    
    # Step 3: Filter low-quality responses
    Filter(
        filter_condition=lambda x: x["score"] >= 7,
        input_mappers={"score": lambda x: x["score"]}
    )

# Run with dataset
distiset = pipeline.run(dataset=dataset)
```

### Phase 3: Export and Persistence

```python
# Option 1: Save to disk (multiple formats)
distiset.to_json("dataset.json")
distiset.to_csv("dataset.csv")
distiset.to_parquet("dataset.parquet")
distiset.save_to_disk("dataset_directory")  # Saves all files

# Option 2: Export to HuggingFace Hub
distiset.push_to_hub(
    repo_id="username/dataset-name",
    token="hf_token",
    private=False,
    commit_message="Initial synthetic dataset"
)

# Option 3: Save and load later
from distilabel.datasets import Distiset
loaded = Distiset.load_from_disk("dataset_directory")
```

## LLM Provider Integration

### Supported Providers

| Provider | Distilabel Class | Installation | Notes |
|----------|-----------------|--------------|-------|
| OpenAI | `OpenAILLM` | `distilabel[openai]` | Official OpenAI API |
| Anthropic | `AnthropicLLM` | `distilabel[anthropic]` | Claude models |
| Mistral | `MistralAILLM` | `distilabel[mistralai]` | Mistral API |
| Groq | `GroqLLM` | `distilabel[groq]` | Fast inference |
| HuggingFace IE | `InferenceEndpointsLLM` | `distilabel[hf-inference-endpoints]` | Hosted on HF |
| Local (vLLM) | `vLLM` | `distilabel[vllm]` | Self-hosted |
| Local (Ollama) | `OllamaLLM` | `distilabel[ollama]` | Local models |
| Any (LiteLLM) | `LiteLLM` | `distilabel[litellm]` | Unified API |

### OpenAI-Compatible Endpoints

For any OpenAI-compatible endpoint (Anthropic, Mistral, local LLMs with OpenAI API format):

```python
from distilabel.models import OpenAILLM

# Custom endpoint
llm = OpenAILLM(
    model_name="custom-model",
    api_key="your-key",
    api_base_url="https://your-endpoint.com/v1",
    generation_kwargs={
        "temperature": 0.7,
        "max_tokens": 512,
        "top_p": 0.9
    }
)
```

### LiteLLM (Multi-Provider)

```python
from distilabel.models import LiteLLM

# Use any provider with LiteLLM
llm = LiteLLM(
    model_name="anthropic/claude-3-sonnet-20240229",
    api_key="your-key",
    generation_kwargs={"temperature": 0.7}
)
```

## Advanced Patterns

### 1. Structured Generation

Use Instructor or Outlines for structured outputs:

```python
from distilabel.models import OpenAILLM
from distilabel.pipeline import Pipeline
from distilabel.steps.tasks import TextGeneration

# With Instructor integration
pip install "distilabel[instructor]"

# Define output schema
from pydantic import BaseModel

class Response(BaseModel):
    answer: str
    reasoning: str
    confidence: float

with Pipeline() as pipeline:
    TextGeneration(
        llm=OpenAILLM(model_name="gpt-4"),
        input_mappers={"prompt": lambda x: x["instruction"]},
        structured_output=Response  # Enforce structure
    )
```

### 2. Distributed Processing with Ray

```python
from distilabel.pipeline import Pipeline
from distilabel.steps.tasks import TextGeneration

# Enable Ray for distributed processing
with Pipeline(distributed="ray") as pipeline:
    TextGeneration(
        llm=OpenAILLM(model_name="gpt-4"),
        input_mappers={"prompt": lambda x: x["instruction"]}
    )

# Run with parallel workers
distiset = pipeline.run(dataset=dataset, num_workers=4)
```

### 3. Preference Data Generation (DPO/RLHF)

```python
from distilabel.steps.tasks import TextGeneration, PairwiseComparison

# Generate preference pairs
with Pipeline() as pipeline:
    # Generate two responses per prompt
    TextGeneration(
        llm=OpenAILLM(model_name="gpt-4"),
        input_mappers={"prompt": lambda x: x["instruction"]},
        num_generations_per_prompt=2
    )
    
    # Compare and select better response
    PairwiseComparison(
        llm=OpenAILLM(model_name="gpt-4"),
        comparison_task="Select the better response based on quality and helpfulness"
    )

distiset = pipeline.run(dataset=dataset)
```

### 4. Instruction Tuning Dataset Creation

```python
from distilabel.steps.tasks import TextGeneration, llm_judge, Filter

# Full instruction tuning pipeline
with Pipeline() as pipeline:
    # Generate responses
    TextGeneration(
        llm=AnthropicLLM(model_name="claude-3-sonnet-20240229"),
        input_mappers={"prompt": lambda x: x["instruction"]},
        output_mappers={"response": lambda x: x["generated_text"]}
    )
    
    # Evaluate quality
    llm_judge(
        llm=OpenAILLM(model_name="gpt-4"),
        judge_task="Evaluate if response correctly follows the instruction (yes/no)",
        output_mappers={"is_good": lambda x: x["judgment"]}
    )
    
    # Filter valid responses
    Filter(
        filter_condition=lambda x: x["is_good"] == "yes"
    )
    
    # Format for fine-tuning
    # Output: {"instruction": ..., "response": ...}

# Export
distiset.push_to_hub("username/instruction-tuning-dataset")
```

## Export Formats and Options

### Disk Persistence

| Method | Format | Use Case | Example |
|--------|--------|----------|---------|
| `to_json()` | JSON | Human-readable, general purpose | `distiset.to_json("data.json")` |
| `to_csv()` | CSV | Spreadsheet compatible | `distiset.to_csv("data.csv")` |
| `to_parquet()` | Parquet | Efficient, columnar storage | `distiset.to_parquet("data.parquet")` |
| `save_to_disk()` | Multiple | Complete dataset with metadata | `distiset.save_to_disk("data/")` |

### HuggingFace Hub Export

```python
# Basic push
distiset.push_to_hub(
    repo_id="username/dataset-name",
    token="hf_token"
)

# Advanced options
distiset.push_to_disk(
    repo_id="username/dataset-name",
    token="hf_token",
    private=True,  # Private dataset
    commit_message="Adding synthetic data v1",
    create_pr=False,  # Direct commit vs PR
    dataset_script_path="dataset_info.json"  # Custom dataset info
)

# With dataset card
distiset.push_to_hub(
    repo_id="username/dataset-name",
    token="hf_token",
    dataset_card=DatasetCard.load("README.md")
)
```

### Dataset Card Template

```markdown
---
language:
- en
tags:
- synthetic-data
- instruction-tuning
- distilabel
datasets:
- username/dataset-name
---

# Dataset Card for [Dataset Name]

## Dataset Summary

Synthetic dataset generated using Distilabel for [purpose].

## Generation Details

- **Generation Date**: 2025-01-01
- **LLM Provider**: OpenAI/Anthropic/Other
- **Model**: gpt-4/claude-3-sonnet/etc.
- **Pipeline**: [Describe pipeline steps]
- **Total Samples**: X
- **Filtered Samples**: Y

## Data Structure

```python
{
    "instruction": str,
    "response": str,
    "quality_score": float,
    "metadata": dict
}
```

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("username/dataset-name")
```

## Citation

```bibtex
@misc{dataset,
  author = {Your Name},
  title = {Dataset Name},
  year = {2025},
  url = {https://huggingface.co/datasets/username/dataset-name}
}
```
```

## Best Practices

### 1. Prompt Engineering

**DO:**
- Use clear, specific instructions
- Provide examples (few-shot prompting)
- Specify output format explicitly
- Include constraints (length, style, content restrictions)

**DON'T:**
- Use ambiguous or vague language
- Assume the model knows your domain
- Skip validation of outputs

**Example Good Prompt:**
```
You are an expert data scientist. Generate a synthetic dataset of 10 examples 
for customer support conversations. Each example should have:
- customer_query: The customer's question (20-50 words)
- agent_response: The support agent's helpful response (50-150 words)
- category: One of: billing, technical, general

Format output as JSON array:
[
  {"customer_query": "...", "agent_response": "...", "category": "..."},
  ...
]

Generate diverse examples covering all categories.
```

### 2. Quality Control

**Always implement:**
1. **Generation validation**: Check output format, length, content
2. **LLM-based judging**: Use a strong model to evaluate responses
3. **Human review**: Sample and review outputs manually
4. **Diversity metrics**: Track and ensure diversity in generated data

```python
# Quality metrics pipeline
with Pipeline() as pipeline:
    TextGeneration(...)
    
    # Multiple quality checks
    llm_judge(
        llm=OpenAILLM(model_name="gpt-4"),
        judge_task="Check if response is relevant to instruction (yes/no)"
    )
    llm_judge(
        llm=OpenAILLM(model_name="gpt-4"),
        judge_task="Check if response contains any harmful content (yes/no)"
    )
    llm_judge(
        llm=OpenAILLM(model_name="gpt-4"),
        judge_task="Rate response quality 1-10"
    )
    
    # Filter: relevant AND safe AND quality >= 7
    Filter(
        filter_condition=lambda x: (
            x["is_relevant"] == "yes" and 
            x["is_safe"] == "yes" and 
            x["quality"] >= 7
        )
    )
```

### 3. Rate Limiting and API Management

**Best practices:**
- Respect provider rate limits (OpenAI: ~10k RPM, Anthropic: ~100 RPM)
- Implement exponential backoff for retries
- Use batching to minimize API calls
- Cache responses when possible

```python
# Configure rate limiting in Distilabel
from distilabel.models import OpenAILLM

llm = OpenAILLM(
    model_name="gpt-4",
    requests_per_minute=50,  # Stay under limits
    max_retries=5,
    retry_delay=2  # Exponential backoff base
)
```

### 4. Cost Optimization

**Cost-saving strategies:**

| Strategy | Description | Savings |
|----------|-------------|---------|
| Use smaller models for judging | GPT-4 for generation, GPT-3.5 for evaluation | 5-10x cheaper |
| Batch requests | Process multiple prompts in parallel | Reduce latency |
| Cache responses | Store generated data to avoid regeneration | Avoid duplicate costs |
| Filter early | Remove low-quality data before expensive steps | Reduce compute |

```python
# Cost-optimized pipeline
with Pipeline() as pipeline:
    # Use expensive model for generation
    TextGeneration(
        llm=OpenAILLM(model_name="gpt-4"),
        input_mappers={"prompt": lambda x: x["instruction"]}
    )
    
    # Use cheaper model for initial filtering
    llm_judge(
        llm=OpenAILLM(model_name="gpt-3.5-turbo"),  # Cheaper
        judge_task="Quick quality check: is response reasonable? (yes/no)"
    )
    
    Filter(filter_condition=lambda x: x["quick_check"] == "yes")
    
    # Use expensive model for final evaluation
    llm_judge(
        llm=OpenAILLM(model_name="gpt-4"),
        judge_task="Detailed quality evaluation 1-10"
    )
```

### 5. Reproducibility

**Ensure reproducibility by:**

1. **Seeding**: Set random seeds for generation
2. **Versioning**: Track dataset versions
3. **Configuration**: Save all pipeline parameters
4. **Logging**: Record generation process and metrics

```python
import random
import numpy as np

# Set seeds
random.seed(42)
np.random.seed(42)

# Save pipeline configuration
pipeline_config = {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 512,
    "generated_at": "2025-01-01",
    "pipeline_hash": "abc123"
}

# Save config with dataset
distiset = pipeline.run(dataset=dataset)
distiset.save_to_disk("dataset", save_config=True)
```

## Constraints

### MUST DO

- **Validate all inputs**: Check dataset structure before processing
- **Implement rate limiting**: Respect API rate limits at all times
- **Handle API errors gracefully**: Implement retry logic with exponential backoff
- **Validate outputs**: Check generated data format and quality
- **Secure API keys**: Never hardcode keys; use environment variables
- **Document generation**: Include metadata about generation process
- **Test with small batches**: Always test pipeline with 5-10 examples first
- **Monitor costs**: Track token usage and API costs
- **Use version control**: Track dataset versions on HuggingFace Hub

### MUST NOT DO

- Hardcode API keys in scripts or notebooks
- Ignore rate limits and send bursts of requests
- Skip quality validation of generated data
- Assume all LLMs produce consistent outputs
- Use production pipelines without testing
- Generate synthetic data without clear purpose or evaluation criteria
- Share API keys or tokens in public repositories
- Overwrite existing datasets without backup
- Exceed budget limits without warnings

## Common Mistakes

### 1. Prompt Injection Vulnerabilities

**Problem:** User input in prompts can lead to prompt injection attacks.

**Solution:** Sanitize inputs and use structured generation.

```python
# BAD: Direct user input in prompt
prompt = f"Generate a response to: {user_input}"

# GOOD: Sanitized and structured
from distilabel.utils import sanitize_prompt
prompt = sanitize_prompt(user_input)
```

### 2. Ignoring Rate Limits

**Problem:** Hitting rate limits causes failures and delays.

**Solution:** Configure proper rate limiting.

```python
# GOOD: Explicit rate limiting
llm = OpenAILLM(
    model_name="gpt-4",
    requests_per_minute=50,  # Conservative limit
    max_retries=10
)
```

### 3. Not Validating Output Format

**Problem:** Generated data doesn't match expected format, breaking downstream processing.

**Solution:** Use structured generation or post-processing validation.

```python
# GOOD: Validate with Pydantic
from pydantic import BaseModel, ValidationError

class ExpectedOutput(BaseModel):
    answer: str
    score: float

try:
    output = ExpectedOutput(**generated_data)
except ValidationError as e:
    print(f"Invalid output: {e}")
    # Regenerate or handle error
```

### 4. Cost Overruns

**Problem:** Unexpectedly high costs from synthetic data generation.

**Solution:** Implement cost tracking and budget limits.

```python
# Track token usage
from distilabel.utils import TokenCounter

counter = TokenCounter()
llm = OpenAILLM(
    model_name="gpt-4",
    token_counter=counter
)

# After generation
print(f"Total tokens used: {counter.total_tokens}")
print(f"Estimated cost: ${counter.total_tokens * 0.03 / 1000:.2f}")  # gpt-4 pricing

# Set budget limit
if counter.total_tokens > 100000:  # ~$3 for gpt-4
    raise BudgetError("Token budget exceeded")
```

### 5. Lack of Diversity

**Problem:** Generated data lacks diversity, leading to biased models.

**Solution:** Implement diversity checks and prompts.

```python
# Diversity checking pipeline
with Pipeline() as pipeline:
    TextGeneration(...)
    
    # Check for diversity
    llm_judge(
        llm=OpenAILLM(model_name="gpt-4"),
        judge_task="Check if this response is too similar to previous ones (yes/no)"
    )
    
    Filter(filter_condition=lambda x: x["is_diverse"] == "no")
```

## Reference Materials

### Official Documentation

- [Distilabel Documentation](https://distilabel.argilla.io/)
- [Distilabel GitHub](https://github.com/argilla-io/distilabel)
- [HuggingFace Datasets](https://huggingface.co/docs/datasets/)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference)

### Research Papers & Methodologies

| Paper | Methodology | Use Case |
|-------|-------------|----------|
| [DEITA](https://arxiv.org/abs/2402.02398) | Data Evolution via Iterative Adaptation | Instruction tuning data |
| [UltraFeedback](https://arxiv.org/abs/2402.02398) | High-quality feedback generation | Preference data |
| [RLAIF](https://arxiv.org/abs/2309.00267) | Recursive LLM feedback | AI feedback loops |
| [Self-Instruct](https://arxiv.org/abs/2212.10560) | Self-instruction generation | Instruction data |

### Example Datasets Built with Distilabel

- [OpenHermesPreferences](https://huggingface.co/datasets/argilla/OpenHermesPreferences): 1M preference pairs
- [distilabel-intel-orca-dpo-pairs](https://huggingface.co/datasets/argilla/distilabel-intel-orca-dpo-pairs): DPO training data
- [haiku-dpo](https://github.com/davanstrien/haiku-dpo): Haiku-specific preference data

### Community Resources

- [Awesome-LLM-Synthetic-Data](https://github.com/wasiahmad/Awesome-LLM-Synthetic-Data): Curated list of papers and resources
- [LLM-Synthetic-Data](https://github.com/pengr/LLM-Synthetic-Data): Reading list for LLM data synthesis
- [Distilabel Discord](http://hf.co/join/discord): Community support and discussions

## Code Templates

### Template 1: Basic Generation → Export

```python
"""synthetic_data_pipeline.py"""
from distilabel.pipeline import Pipeline
from distilabel.steps.tasks import TextGeneration
from distilabel.models import OpenAILLM
from datasets import load_dataset, Dataset

# Load seed data
dataset = load_dataset("path/to/seed_data", split="train")

# Create pipeline
with Pipeline() as pipeline:
    TextGeneration(
        llm=OpenAILLM(
            model_name="gpt-4",
            generation_kwargs={"temperature": 0.7, "max_tokens": 512}
        ),
        input_mappers={"prompt": lambda x: x["instruction"]}
    )

# Run
distiset = pipeline.run(dataset=dataset)

# Save
distiset.to_json("generated_data.json")
distiset.push_to_hub("username/dataset-name")
```

### Template 2: Multi-Step with Quality Control

```python
"""quality_control_pipeline.py"""
from distilabel.pipeline import Pipeline
from distilabel.steps.tasks import TextGeneration, llm_judge, Filter
from distilabel.models import OpenAILLM, AnthropicLLM

# Define dataset
Dataset.from_dict({
    "instruction": [...],
    "category": [...]
})

# Create pipeline with quality control
with Pipeline() as pipeline:
    # Generation
    TextGeneration(
        llm=AnthropicLLM(model_name="claude-3-sonnet-20240229"),
        input_mappers={"prompt": lambda x: x["instruction"]}
    )
    
    # Safety check
    llm_judge(
        llm=OpenAILLM(model_name="gpt-4"),
        judge_task="Does this response contain harmful content? (yes/no)"
    )
    
    # Quality check
    llm_judge(
        llm=OpenAILLM(model_name="gpt-4"),
        judge_task="Rate quality 1-10"
    )
    
    # Filter
    Filter(
        filter_condition=lambda x: (
            x["is_safe"] == "no" and 
            x["quality"] >= 7
        )
    )

# Run
distiset = pipeline.run(dataset=dataset)

# Export
distiset.save_to_disk("quality_dataset")
```

### Template 3: Preference Data Generation

```python
"""preference_data_pipeline.py"""
from distilabel.pipeline import Pipeline
from distilabel.steps.tasks import TextGeneration, PairwiseComparison
from distilabel.models import OpenAILLM

# Load instructions
instructions = [...]

with Pipeline() as pipeline:
    # Generate multiple responses per instruction
    TextGeneration(
        llm=OpenAILLM(model_name="gpt-4"),
        input_mappers={"prompt": lambda x: x["instruction"]},
        num_generations_per_prompt=2
    )
    
    # Compare responses
    PairwiseComparison(
        llm=OpenAILLM(model_name="gpt-4"),
        comparison_task="Select the better response based on helpfulness and accuracy"
    )

# Run
distiset = pipeline.run(dataset=Dataset.from_dict({"instruction": instructions}))

# Export as DPO format
dpo_dataset = distiset.rename_columns({
    "instruction": "prompt",
    "chosen": "chosen",
    "rejected": "rejected"
})

dpo_dataset.push_to_hub("username/dpo-dataset")
```

## Utility Scripts

### Script: `generate_synthetic_data.py`

```python
#!/usr/bin/env python3
"""
Generate synthetic data using Distilabel with configurable LLM provider.

Usage:
    python generate_synthetic_data.py \
        --input-path input.json \
        --output-path output.json \
        --provider openai \
        --model gpt-4 \
        --num-samples 100
"""

import argparse
import json
import os
from pathlib import Path

from datasets import Dataset
from distilabel.pipeline import Pipeline
from distilabel.steps.tasks import TextGeneration
from distilabel.models import OpenAILLM, AnthropicLLM


def get_llm(provider: str, model: str):
    """Get LLM instance based on provider."""
    if provider == "openai":
        return OpenAILLM(model_name=model)
    elif provider == "anthropic":
        return AnthropicLLM(model_name=model)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def generate_data(
    input_path: str,
    output_path: str,
    provider: str,
    model: str,
    num_samples: int,
    temperature: float = 0.7
):
    """Generate synthetic data from input prompts."""
    # Load input
    with open(input_path) as f:
        data = json.load(f)
    
    dataset = Dataset.from_dict({
        "instruction": data["instructions"][:num_samples]
    })
    
    # Create pipeline
    with Pipeline() as pipeline:
        TextGeneration(
            llm=get_llm(provider, model),
            input_mappers={"prompt": lambda x: x["instruction"]},
            generation_kwargs={"temperature": temperature, "max_tokens": 512}
        )
    
    # Run
    distiset = pipeline.run(dataset=dataset)
    
    # Save
    distiset.to_json(output_path)
    print(f"✓ Generated {len(distiset)} samples, saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data")
    parser.add_argument("--input-path", type=str, required=True, help="Input JSON file with instructions")
    parser.add_argument("--output-path", type=str, required=True, help="Output JSON file")
    parser.add_argument("--provider", type=str, choices=["openai", "anthropic"], required=True, help="LLM provider")
    parser.add_argument("--model", type=str, required=True, help="Model name")
    parser.add_argument("--num-samples", type=int, default=100, help="Number of samples to generate")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    
    args = parser.parse_args()
    generate_data(
        args.input_path,
        args.output_path,
        args.provider,
        args.model,
        args.num_samples,
        args.temperature
    )


if __name__ == "__main__":
    main()
```

### Script: `export_to_huggingface.py`

```python
#!/usr/bin/env python3
"""
Export synthetic dataset to HuggingFace Hub.

Usage:
    python export_to_huggingface.py \
        --dataset-path dataset.json \
        --repo-id username/dataset-name \
        --token hf_token
"""

import argparse
from datasets import Dataset


def export_to_hub(dataset_path: str, repo_id: str, token: str):
    """Export dataset to HuggingFace Hub."""
    dataset = Dataset.load_from_disk(dataset_path)
    
    dataset.push_to_hub(
        repo_id=repo_id,
        token=token,
        private=False
    )
    
    print(f"✓ Dataset exported to https://huggingface.co/datasets/{repo_id}")


def main():
    parser = argparse.ArgumentParser(description="Export to HuggingFace Hub")
    parser.add_argument("--dataset-path", type=str, required=True, help="Path to dataset file or directory")
    parser.add_argument("--repo-id", type=str, required=True, help="HuggingFace repo ID (username/dataset-name)")
    parser.add_argument("--token", type=str, required=True, help="HuggingFace token")
    
    args = parser.parse_args()
    export_to_hub(args.dataset_path, args.repo_id, args.token)


if __name__ == "__main__":
    main()
```

## Validation Checklist

Before deploying a synthetic data generation pipeline:

- [ ] **Input validation**: All input data is properly formatted
- [ ] **Prompt testing**: Prompts tested with 5-10 examples
- [ ] **Rate limiting**: Configured and tested
- [ ] **Error handling**: API errors handled with retries
- [ ] **Quality checks**: LLM-based evaluation implemented
- [ ] **Cost tracking**: Token usage monitored
- [ ] **Output validation**: Generated data format verified
- [ ] **Reproducibility**: Seeds set, configuration saved
- [ ] **Backup**: Original dataset backed up before overwriting
- [ ] **Testing**: Full pipeline tested with small subset
- [ ] **Documentation**: Generation process documented
- [ ] **Export verification**: Exported data can be loaded and used

## Performance Optimization

### Memory Management

```python
# Process in batches for large datasets
from distilabel.pipeline import Pipeline

with Pipeline() as pipeline:
    TextGeneration(...)

# Process in batches of 100
batch_size = 100
for i in range(0, len(dataset), batch_size):
    batch = dataset.select(range(i, min(i + batch_size, len(dataset))))
    batch_result = pipeline.run(dataset=batch)
    batch_result.save_to_disk(f"batch_{i}")
```

### Parallel Processing

```python
# Use Ray for distributed processing
from distilabel.pipeline import Pipeline

with Pipeline(distributed="ray", num_workers=4) as pipeline:
    TextGeneration(...)

result = pipeline.run(dataset=dataset)
```

### Caching

```python
# Cache LLM responses
from distilabel.cache import DiskCache

cache = DiskCache(cache_dir="./cache")

with Pipeline(cache=cache) as pipeline:
    TextGeneration(...)

# Cached responses will be reused for same inputs
```

## Monitoring and Observability

### Token Usage Tracking

```python
from distilabel.utils import TokenCounter

counter = TokenCounter()
llm = OpenAILLM(
    model_name="gpt-4",
    token_counter=counter
)

# After generation
print(f"Prompt tokens: {counter.prompt_tokens}")
print(f"Completion tokens: {counter.completion_tokens}")
print(f"Total tokens: {counter.total_tokens}")
print(f"Estimated cost: ${counter.total_tokens * 0.03 / 1000:.2f}")
```

### Logging

```python
import logging
from distilabel.pipeline import Pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)

with Pipeline(log_level=logging.INFO) as pipeline:
    TextGeneration(...)

# All pipeline events will be logged
```

### Custom Metrics

```python
from distilabel.pipeline import Pipeline
from distilabel.steps.tasks import TextGeneration, llm_judge

metrics = {"total_generated": 0, "passed_quality": 0, "avg_score": 0}

with Pipeline() as pipeline:
    TextGeneration(...)
    
    llm_judge(
        llm=OpenAILLM(model_name="gpt-4"),
        judge_task="Rate quality 1-10",
        output_mappers={"score": lambda x: float(x["judgment"])}
    )
    
    # Custom step to track metrics
    def update_metrics(batch):
        metrics["total_generated"] += len(batch)
        metrics["passed_quality"] += sum(1 for x in batch if x["score"] >= 7)
        metrics["avg_score"] = sum(x["score"] for x in batch) / len(batch)
        return batch

pipeline.run(dataset=dataset)
print(f"Metrics: {metrics}")
```

## Security Considerations

### API Key Management

```python
# NEVER do this
llm = OpenAILLM(api_key="sk-...", model_name="gpt-4")  # Hardcoded key

# DO this instead
import os
from dotenv import load_dotenv

load_dotenv()
llm = OpenAILLM(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="gpt-4"
)

# Or use environment variables directly
llm = OpenAILLM(model_name="gpt-4")  # Reads from OPENAI_API_KEY env var
```

### Input Sanitization

```python
from distilabel.utils import sanitize_prompt

def safe_generation(prompt: str):
    """Safely generate with sanitized prompt."""
    sanitized = sanitize_prompt(prompt)
    
    # Additional checks
    if len(sanitized) > 10000:
        raise ValueError("Prompt too long")
    
    if any(word in sanitized.lower() for word in ["ignore", "forget", "system"]):
        raise ValueError("Potential prompt injection detected")
    
    return sanitized
```

### Output Validation

```python
from pydantic import BaseModel, validator
from typing import Optional

class SafeOutput(BaseModel):
    text: str
    
    @validator('text')
    def validate_text(cls, v):
        if len(v) > 5000:
            raise ValueError("Output too long")
        
        # Check for PII patterns (simplified)
        if any(pattern in v for pattern in ["SSN", "credit card", "password"]):
            raise ValueError("Potential PII detected")
        
        return v
```

## Troubleshooting

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Rate limit errors | Too many requests | Configure `requests_per_minute`, add retries |
| Authentication errors | Invalid API key | Verify environment variables, check key |
| Format errors | Invalid output format | Use structured generation, add validation |
| Memory errors | Large dataset | Process in batches, use streaming |
| Timeout errors | Long generation | Increase timeout, reduce max_tokens |
| Quality issues | Poor prompts | Improve prompt engineering, add examples |

### Debug Mode

```python
from distilabel.pipeline import Pipeline

# Enable debug logging
with Pipeline(debug=True) as pipeline:
    TextGeneration(...)

# Or set environment variable
os.environ["DISTILABEL_DEBUG"] = "true"
```

### Error Handling

```python
from distilabel.errors import RateLimitError, APIError
from distilabel.pipeline import Pipeline

with Pipeline() as pipeline:
    try:
        TextGeneration(
            llm=OpenAILLM(
                model_name="gpt-4",
                max_retries=5,
                retry_delay=2
            )
        )
    except RateLimitError as e:
        print(f"Rate limited: {e}")
        # Implement fallback or wait
    except APIError as e:
        print(f"API error: {e}")
        # Check error details, retry if transient
```

## Success Criteria

A synthetic data generation pipeline is **complete and successful** when:

1. ✅ **Dataset generated**: Output dataset exists with expected size
2. ✅ **Quality validated**: Manual and automated checks pass
3. ✅ **Format correct**: Data structure matches requirements
4. ✅ **Exported successfully**: Dataset saved to disk and/or pushed to HuggingFace Hub
5. ✅ **Reproducible**: Same inputs produce same outputs
6. ✅ **Documented**: Generation process and parameters recorded
7. ✅ **Cost tracked**: Token usage and costs documented
8. ✅ **Tested**: Pipeline validated with subset of data

## Resources

### Learning Materials

- [Distilabel Documentation](https://distilabel.argilla.io/)
- [HuggingFace Datasets Guide](https://huggingface.co/docs/datasets/)
- [OpenAI Cookbook](https://github.com/openai/openai-cookbook)
- [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook)

### Community Support

- [Distilabel GitHub Discussions](https://github.com/argilla-io/distilabel/discussions)
- [HuggingFace Forums](https://discuss.huggingface.co/)
- [OpenAI Community](https://community.openai.com/)
- [Anthropic Discord](https://discord.gg/anthropic)

### Related Tools

| Tool | Purpose | Integration |
|------|---------|-------------|
| [Argilla](https://argilla.io/) | Data labeling and evaluation | Native |
| [AutoTrain](https://huggingface.co/autotrain) | Model fine-tuning | HuggingFace Hub |
| [Weights & Biases](https://wandb.ai/) | Experiment tracking | Logging |
| [LangSmith](https://smith.langchain.com/) | LLM debugging | Logging |

## Conclusion

This skill provides everything needed to build production-ready synthetic data generation pipelines using Distilabel with OpenAI/Anthropic-compatible LLM endpoints. It covers:

- ✅ **Pipeline design** with Distilabel
- ✅ **Multi-provider LLM integration** (OpenAI, Anthropic, Mistral, Groq, etc.)
- ✅ **Quality control** and evaluation
- ✅ **Export to HuggingFace Hub**
- ✅ **Disk persistence** in multiple formats
- ✅ **Best practices** for reliability, cost, and security
- ✅ **Advanced patterns** for preference data, instruction tuning, etc.
- ✅ **Monitoring and observability**
- ✅ **Troubleshooting** common issues

For questions, issues, or contributions, refer to the [Distilabel GitHub](https://github.com/argilla-io/distilabel) or join the [Discord community](http://hf.co/join/discord).
