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
| `SFT/video-action-recognition/fine-tune-aoai-gpt4-1-action-detection.ipynb` | Blocked | 3 classes, 30 train, 12 validation, 6 test, 2 frames | Download, safe extraction, frame generation, upload, and submission passed on two separate resources. Both rejected all training rows under the people/face content policy; Modified Content Filtering approval is required. |
| `SFT/trace-distillation/notebook.ipynb` | Live | 14 live traces; 11 train, 1 validation, 2 test; `gpt-4.1-mini` | Direct RBAC-authenticated Application Insights export, transform, training, deployment, and both evaluations passed. Base and fine-tuned scores were both 10.0/10 with 100% pass rate; the tiny test set proves mechanics, not lift. |
| `RFT/countdown/demo.ipynb` | Blocked | 20 train, 50 validation, 20 evaluation; `o4-mini`; `gpt-4.1-mini` grader | Fresh data preparation, file processing, evaluation setup, and submission passed. Azure exhausted its internal retries and ended the job with HTTP 500 (`A system error was encountered`), reproducing the service-side failure. |
| `RFT/countdown/demo_with_python_grader.ipynb` | Live | 20 train, 50 validation, 20 evaluation; `o4-mini` | The completed Python-grader RFT job deployed after quota cleanup. At capacity 50, base and fine-tuned evaluations completed with no request errors: 100% versus 95% pass rate. This validates E2E mechanics but did not improve quality on the compact test. |
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
