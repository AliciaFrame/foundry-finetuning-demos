# Fine-tuning Azure OpenAI GPT-4.1 for Chart Analysis

This notebook demonstrates the process of vision fine-tuning of GPT-4.1 leveraging a chart analysis benchmark dataset for visual and logical reasoning. It covers data preparation, fine-tuning, deployment, and evaluation against GPT-4.1's baseline performance.

We are using the **ChartQA** dataset, a benchmark designed for question answering tasks involving chart images. Each entry in the dataset comprises a chart image, an associated question, and the corresponding answer, facilitating the development and evaluation of models that integrate visual and logical reasoning to interpret and analyze information presented in graphical formats.

__Acknowledgements:__
This project utilizes the ChartQA dataset introduced by Masry et al. in their paper, *ChartQA: A Benchmark for Question Answering about Charts with Visual and Logical Reasoning* (Findings of ACL 2022). We acknowledge the authors for providing this valuable resource. For more details, refer to the publication: [ChartQA: ACL 2022](https://aclanthology.org/2022.findings-acl.177).

The notebook downloads ChartQA through Hugging Face. Dataset files are not
redistributed here; comply with the dataset's original terms.

## Validated smoke result

The October 2026 end-to-end run used 20 training rows, 10 validation rows, and
20 held-out test rows. Fine-tuning completed all 100 expected steps, the model
deployed successfully, and both vision inference paths completed. The GPT-4.1
baseline scored 17/20 (85%); the fine-tuned model scored 16/20 (80%).

This small run validates the workflow but does **not** show a quality
improvement. Use a larger representative split and tune the data and
hyperparameters before drawing a model-quality conclusion. A newly provisioned
fine-tuned vision deployment can also take several minutes after ARM reports
success before its dependent inference backend becomes ready.

## Get started

Create and activate a virtual Python environment for running the code.
The following example shows how to create a Conda environment named `vision-ft`:

```bash
conda create -n vision-ft python=3.12
conda activate vision-ft
```

Install the required packages. Navigate to the `Image_FT_Chart_Analysis` folder and execute the following:

```bash
pip install -r requirements.txt
```

__Required Services:__
- An Azure OpenAI resource with the following model deployments:
   - GPT-4.1

__Optional Services:__
- Azure AI Foundry for managing fine-tuning in the UI

Rename the environemt file template `.env.template` to `.env` and add your credentials by editing the file.

Navigate to the vision fine-tuning notebook:

- [Fine-tuning Azure OpenAI GPT-4.1 for Chart Analysis](fine-tune-aoai-gpt4-1-for-chart-analysis.ipynb)

## Troubleshooting

### Common Issues

**Authentication Error**
- Verify `.env` contains correct API key and endpoint
- Run `az login` to refresh Azure credentials
- Ensure your Azure OpenAI resource has GPT-4.1 deployed

**Training Job Fails**
- Verify JSONL format matches the expected schema
- Ensure base64 image encoding is correct
- Check that images don't exceed size limits

**Content Filter Triggered**
- Some chart images may trigger content filters
- Use the [official form](https://customervoice.microsoft.com/Pages/ResponsePage.aspx?id=v4j5cvGGr0GRqy180BHbR7en2Ais5pxKtso_Pz4b1_xUMlBQNkZMR0lFRldORTdVQzQ0TEI5Q1ExOSQlQCN0PWcu) for policy adjustments if needed

**Quota Exceeded**
- Request additional quota in Azure Portal → Azure OpenAI → Quotas
- Try a different Azure region with available capacity
- Increase `CHART_DEPLOYMENT_CAPACITY` if batch evaluation repeatedly reaches
  the token-rate limit; the notebook defaults to 10K TPM.
