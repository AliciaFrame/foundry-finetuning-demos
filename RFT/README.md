# Reinforcement Fine-Tuning Demos

1. [Countdown](countdown/) is the smallest complete RFT example. It uses an
   arithmetic task with automatically verifiable outputs.
2. [Math reasoning](math-reasoning/) scales the same idea to an attributed
   OpenR1-Math subset.
3. [Zava agentic RFT](zava-agentic-rft/) demonstrates partial-credit grading,
   tool calls, calibration, checkpoint selection, and evaluation with held-out
   retail scenarios.

RFT is useful when outputs can be scored reliably but there are multiple valid
solution paths. Calibrate the reward before submitting a job: an always-passing
or always-failing base model provides little learning signal. Do not treat the
training grader as the only production acceptance test.

For reusable validators and current API guidance, see the
[Foundry fine-tuning skill](https://github.com/AliciaFrame/foundry-finetuning-skill).
