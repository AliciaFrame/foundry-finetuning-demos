# Video Motion Recognition

Fine-tune a vision model to classify motion from frames sampled across short
video clips.

The default path downloads non-human CIFAR-10 vehicle images and turns them
into deterministic horizontal-pan, vertical-pan, and zoom clips. The classes
use neutral labels (`motion_alpha`, `motion_beta`, and `motion_gamma`) so the
model must learn the task mapping instead of relying on descriptive label
names.

UCF101 remains available as an optional data source for Azure resources
approved to fine-tune images containing people.

## What the notebook does

1. Downloads or generates the video dataset.
2. Samples timestamped frames from each clip.
3. Creates multimodal fine-tuning JSONL.
4. Trains and deploys a vision model.
5. Evaluates the base and fine-tuned deployments on the same held-out clips.

## Result

The end-to-end run used 90 training clips, 30 validation clips, and 30
held-out test clips across three balanced motion classes.

| Model | Accuracy |
|---|---:|
| Base `gpt-4.1-mini` | 26.7% (8/30) |
| Fine-tuned `gpt-4.1` | 33.3% (10/30) |

The fine-tuned deployment completed every request, but predicted
`motion_beta` for all 30 test clips. The run therefore verifies the full video
fine-tuning pipeline but does not demonstrate a useful classifier. Increase
dataset diversity and evaluate stronger temporal representations before using
this approach for a real action-recognition system.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
az login
```

Set the resource configuration:

```powershell
$env:AZURE_OPENAI_ENDPOINT = "https://<resource>.services.ai.azure.com"
$env:AZURE_SUBSCRIPTION_ID = "<subscription-id>"
$env:AZURE_RESOURCE_GROUP = "<resource-group>"
$env:AZURE_ACCOUNT_NAME = "<resource-name>"
$env:VIDEO_BASE_DEPLOYMENT = "gpt-4.1"
$env:VIDEO_FT_MODEL = "gpt-4.1-2025-04-14"
```

The notebook uses `DefaultAzureCredential` when
`AZURE_OPENAI_API_KEY` is not set.

The default configuration is:

```powershell
$env:VIDEO_DATA_SOURCE = "synthetic"
$env:VIDEO_CLASS_COUNT = "3"
$env:VIDEO_TRAIN_SAMPLES = "90"
$env:VIDEO_VAL_SAMPLES = "30"
$env:VIDEO_TEST_SAMPLES = "30"
$env:VIDEO_FRAMES = "3"
$env:VIDEO_FT_EPOCHS = "3"
```

Run
[`fine-tune-aoai-gpt4-1-action-detection.ipynb`](fine-tune-aoai-gpt4-1-action-detection.ipynb).

`VIDEO_REUSE_FT_JOB_ID` can resume a job created by an interrupted execution
without paying for duplicate training.

## Optional UCF101 path

Set `VIDEO_DATA_SOURCE=huggingface` for the compact
[`sayakpaul/ucf101-subset`](https://huggingface.co/datasets/sayakpaul/ucf101-subset)
archive or `VIDEO_DATA_SOURCE=kaggle` for the larger Kaggle package. UCF101
contains people and generally requires Modified Content Filtering approval for
vision fine-tuning.

Original notebook contribution: Andreas Kopp. UCF101:
[dataset](https://www.crcv.ucf.edu/research/data-sets/ucf101/) and
[paper](https://arxiv.org/abs/1212.0402).

## Limitations

The generated motion dataset is a compact instructional task, not a benchmark
for general video understanding. Use real domain data and a larger independent
test set before drawing production conclusions.
