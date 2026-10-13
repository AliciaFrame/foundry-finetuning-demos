# Supervised Fine-Tuning Demos

Follow the demos in this order:

1. [Distilling sarcasm](distilling-sarcasm/) introduces teacher/student
   distillation with a clear behavioral target.
2. [Bug detection](bug-detection/) shows a conventional text SFT workflow with
   bundled training and validation data.
3. [NL-to-Python distillation](nl-to-python-distillation/) adds synthetic data
   generation and code evaluation.
4. [Image breed classification](image-breed-classification/) introduces
   multimodal fine-tuning.
5. [Video action recognition](video-action-recognition/) expands vision SFT to
   sampled video frames.
6. [Trace distillation](trace-distillation/) turns agent telemetry into
   tool-use training examples.

Historical metrics are retained for context, but model availability and service
behavior change. Reproduce the baseline and fine-tuned evaluation before using
any result for a production decision.
