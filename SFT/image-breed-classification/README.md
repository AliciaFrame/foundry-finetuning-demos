# Image Breed Classification

This demo compares three approaches to dog-breed classification:

1. Zero-shot classification with a base vision-language model.
2. Supervised fine-tuning of the same model on labeled images.
3. A lightweight MobileNetV3-Small baseline.

The default notebook configuration uses a small, credential-free subset so the
complete download, training, deployment, and evaluation workflow is practical
to reproduce.

## Result

The compact run used three breeds with ten downloaded images per breed. Both
the base and fine-tuned deployments classified all three held-out images
correctly (`3/3`). Mean latency across three sequential requests was about
`3154 ms` for the base deployment and `2254 ms` for the fine-tuned deployment.

This run verifies the complete workflow but is too small to establish an
accuracy or latency advantage.

## Files

| File | Purpose |
|---|---|
| `images_classification_vlm.ipynb` | Data preparation, vision SFT, deployment, and accuracy evaluation |
| `latency_base_ft_models.ipynb` | Base versus fine-tuned latency measurement |
| `cnn_baseline.py` | Optional MobileNetV3-Small comparison |
| `.env.sample` | Required Azure OpenAI configuration |
| `requirements.txt` | Python dependencies |

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.sample .env
```

Configure the base and fine-tuned deployment names in `.env`, then run
`images_classification_vlm.ipynb`. Run `latency_base_ft_models.ipynb` after the
fine-tuned deployment is available.

The notebook supports a compact Hugging Face download path and a larger Kaggle
path. Dataset files are downloaded at runtime and are not redistributed by
this repository.

## Interpreting the comparison

The CNN is a deliberately lightweight reference, not a state-of-the-art
computer-vision baseline. Use a larger independent test set, repeated latency
trials, and a stronger task-specific vision model before comparing production
cost or quality.

## Dataset and attribution

The full workflow is based on the
[Stanford Dogs dataset](http://vision.stanford.edu/aditya86/ImageNetDogs/).
Dataset images retain their original terms. See
[`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md) for repository-wide
attribution.
