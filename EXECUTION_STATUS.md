# Notebook execution status

Last validated: October 12, 2026.

This matrix records what was actually exercised during the repository review.
Executed notebooks and generated data remain outside the repository because
their outputs contain account-specific endpoints, job identifiers, and report
links. Small smoke samples validate mechanics, not model quality.

| Notebook | Mode | Smoke configuration | Result |
|---|---|---|---|
| `SFT/distilling-sarcasm/sarcasm.ipynb` | Live | 50 prompts; 11 train, 3 validation, 10 evaluation; `gpt-4o-mini` student | Training, deployment, and held-out evaluation passed. Pass rate moved 70% to 80%, while mean score moved 5.2 to 5.0; inconclusive. |
| `SFT/bug-detection/Bug_Detection_Fine_Tuning.ipynb` | Live | 224 train, 20 validation, 10 evaluation; `gpt-4.1-mini` student | Training, deployment, evaluation, and cleanup passed. Mean moved 8.33 to 8.63; pass rate remained 80%. |
| `SFT/nl-to-python-distillation/Text_to_Python_Fine_Tuning.ipynb` | Live | 50 generated, 44 retained, 2 evaluation; `gpt-4.1-mini` student | Data Designer generation, training, deployment, and evaluation passed. Combined score moved 8.25 to 8.75. The tiny evaluation and 2.3x train/validation loss ratio preclude a quality claim. |
| `SFT/image-breed-classification/images_classification_vlm.ipynb` | Live | 3 breeds, 10 downloaded images per breed, 3 held out; `gpt-4o` | Download, preparation, training, deployment, and both inference paths passed. Base and fine-tuned models each scored 3/3. |
| `SFT/image-breed-classification/latency_base_ft_models.ipynb` | Live | 3 sequential requests per model | Both paths passed with no request errors. Mean latency was about 3154 ms base and 2254 ms fine-tuned; n=3 is not a benchmark. |
| `SFT/chart-analysis/fine-tune-aoai-gpt4-1-for-chart-analysis.ipynb` | Live | 20 train, 10 validation, 20 test; `gpt-4.1` | Upload, 100-step training, deployment, vision inference, evaluation, and portable result export passed. Baseline scored 17/20 (85%); fine-tuned scored 16/20 (80%), so this smoke run did not improve quality. |
| `SFT/video-action-recognition/fine-tune-aoai-gpt4-1-action-detection.ipynb` | Blocked | 3 classes, 30 train, 12 validation, 6 test, 2 frames | Download, safe extraction, frame generation, upload, and submission passed. Azure rejected all training rows under the people/face content policy; Modified Content Filtering approval is required. |
| `SFT/trace-distillation/notebook.ipynb` | Fixture-backed live | 43 sanitized traces, 4 held out; `gpt-4.1-mini` | Transform, base evaluation, training, deployment, and fine-tuned evaluation passed. Score moved 8.5 to 10.0 and pass rate 75% to 100%. Live App Insights harvesting was separately blocked by a Private Link requirement. |
| `RFT/countdown/demo.ipynb` | Blocked | 20 train, 10 validation, 20 evaluation; `o4-mini`; `gpt-4.1-mini` grader | Data preparation, file processing, and submission passed. Azure retried preprocessing and ended the job with a service-side HTTP 500. |
| `RFT/countdown/demo_with_python_grader.ipynb` | Live training, blocked deployment | 20 train, 10 validation, 20 evaluation; `o4-mini` | Python-grader RFT training succeeded. Deployment was blocked because no fine-tuned `o4-mini` throughput quota was available, so final inference could not run. |
| `RFT/math-reasoning/rft_math_reasoning.ipynb` | Reused job | Bundled 100 train and 10 validation rows; `o4-mini` | A matching completed job was retrieved, deployed, and invoked successfully. No new training or quality comparison was performed. |
| `RFT/zava-agentic-rft/notebooks/e2e_demo.ipynb` | Artifact-only | Bundled sanitized historical artifacts | The complete offline walkthrough passed. Live agent/tool evaluation and new RFT submission were not run because they require a matching deployment, a reachable tool service, and limited-preview access. |

## Interpretation

- **Live** means real service calls were made. It does not imply a statistically
  meaningful benchmark.
- **Reused job** means deployment and inference were validated against a
  compatible completed job without paying for another training run.
- **Fixture-backed** means only trace collection was replaced by checked-in
  synthetic data; downstream cloud training and evaluation were live.
- **Artifact-only** means the notebook reproduced its checked-in evidence
  without contacting the corresponding preview service.
- **Blocked** identifies the exact external condition that prevented a full
  run. It is not represented as a passing result.

Fine-tuning, deployment, evaluation, and hosted model inference can incur
charges. Model availability, grader compatibility, quota, and preview access
vary by region and subscription.
