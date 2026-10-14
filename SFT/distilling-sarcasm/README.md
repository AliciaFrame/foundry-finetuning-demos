# Distilling Sarcasm
> or: "how to teach GPT-4.1-nano how to be sarcastic"

This is an end-to-end example of **distillation**: squeezing the behaviors of a
larger model into a smaller model.

## tl;dr

1. Deploy a grader, teacher candidates, and an unfine-tuned student. The
   defaults use `gpt-4.1-mini` for grading, `gpt-4o` and `gpt-4o-mini` as
   teacher candidates, and `gpt-4o-mini` as the student.

2. Create and populate a `.env` file to simplify stuff. In it, put some Azure
   specific details:

```properties
AZURE_OPENAI_ENDPOINT=https://<YOUR OWN ENDPOINT>.openai.azure.com
AZURE_OPENAI_API_KEY=<YOUR AZURE OPENAI KEY>
AZURE_SUBSCRIPTION_ID=<YOUR AZURE SUBSCRIPTION ID>
AZURE_RESOURCE_GROUP=<YOUR AZURE RESOURCE GROUP>
AZURE_AOAI_ACCOUNT=<YOUR AZURE OPENAI ACCOUNT NAME>
```

3. Wrangle the Python stuff. (See below.)

```
$ python3 -m venv .venv
$ . .venv/bin/activate
(venv) $ pip install -r requirements.txt
```

Then launch this sucker in Jupyter notebooks. The easiest way is to fire it up
in **Visual Studio Code**:

```
$ code sarcasm.ipynb
```

Happy distilling. 🧪

For a lower-cost smoke run, set `SARCASM_RECORDS`, `SARCASM_BASE_MODELS`,
`SARCASM_GRADER_MODEL`, `SARCASM_STUDENT_MODEL`, and `SARCASM_EPOCHS`.
The notebook now trains one OpenAI student; the provider-specific Ministral
branch from the original prototype is intentionally omitted.

## Result

The run used 50 factual prompts, selected 14 responses above the distillation
cutoff, and trained on 11 rows with 3 validation rows. On ten held-out prompts,
the fine-tuned `gpt-4o-mini` deployment scored 5.0 average
with an 80% pass rate; an unfine-tuned run scored 5.2 average with a 70% pass
rate. The pass-rate improvement and slightly lower mean conflict, so this small
run validates the workflow but does not establish a clear quality win.

## Background
The basis for this demo is the Distillation [demo](https://github.com/azure-ai-foundry/build-2025-demos/blob/main/Azure%20AI%20Model%20Customization/DistillationDemo/demo.ipynb)
featured at Build 2025:

And the [tutorial](https://learn.microsoft.com/en-us/azure/ai-services/openai/tutorials/fine-tune)
on fine-tuning gpt-4o with the prompt:
_Clippy is a factual chatbot that is also sarcastic._

## Grader
We use a crude grader that rewards two things:

1. The amount of sarcasm from 1 (no sarcasm) to 10 (the most sarcasm)
2. Correct answers to the users questions.

More importantly, it *heavily* penalizes wrong answers by driving the scores to
zero. In practice, I don't think I saw this happen, but it's a fun example.

The grader deployment is configurable; the default is **gpt-4.1-mini**.

## Methodology
More will be written here, but at a high-level the approach takes a few steps.

For now, just read the [notebook](./sarcasm.ipynb) 😉

### 0. Assemble Human Curated Data
We need something of a "gold standard." In this case, we use some pre-canned
examples from the Azure OpenAI docs.

### 1. Build & Test our Grader
We assemble a Grader: a combination of model (o3) and a prompt. The prompt
tells the grader how to score other models' output.

### 2. Benchmark our Base Models
We use the "gold standard" to check if our Grader is doing its job. If we can't
trust the grader, who can we trust?

### 3. Pick our Teacher and our Student
We then give an assignment to our base models (`o3`, `o4-mini`, `4.1-*`,
`4o-*`) and have the Grader decide on their scores.

We use these scores to determine which base model shows the most aptitude
for our use case. That model we pick as our Teacher.

We also figure out who our Student should be based on which model performs the
worst...yet might be much cheaper to use than our Teacher. (We're on a fixed
budget!)

### 4. Distill from the Teacher
We take the Teacher's answers to the questions and consider them what the
Student needs to learn. We turn them into our training data for fine-tuning.

### 5. Train our Student
The Student gets to work learning by studying the Teacher's output.

### 6. Test our Student against its Peer
Now, to keep things fair, we take _new_ data and ask the Student to generate
responses. We also ask its peer, the un-trained version of itself, to do the
same. We then compare the two.

### 7. Celebrate or Cry
If our Student bests the Peer, we celebrate! Our job is done.

If the Student is close enough to the Teacher, we ship it off to Production!

## Troubleshooting

### Common Issues

**Authentication Error**
- Run `az login` to refresh your Azure credentials
- Verify your Azure OpenAI endpoint and API key in `.env`
- Check that you have deployment access for all models (o3, o4-mini, gpt-4.1, etc.)

**Quota Exceeded**
- This demo uses multiple model deployments - ensure you have TPM quota for each
- Request additional quota in Azure Portal → Azure OpenAI → Quotas
- Try running with fewer models if quota is limited

**Model Not Available**
- Check regional availability for gpt-4.1-nano and other newer models
- Some models may require preview access - check Azure documentation

**Training Job Fails**
- Verify data format matches the expected JSONL schema
- Ensure training data doesn't exceed token limits
- Check that grader outputs are valid JSON
