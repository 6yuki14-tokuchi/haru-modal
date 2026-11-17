# Japanese Haru on Modal

A standalone evaluation deployment that reuses the official Haru browser client/server.
The model and runtime dependencies live in Modal. Deployment tooling runs on a cloud
runner, so the client computer does not download model weights or install this runtime.

## Before deployment
Modal requires a valid payment method on file for every GPU type, even when using free credits.
See https://modal.com/docs/guide/gpu. Payment-method registration must be completed by
the account owner. Verify a net spend limit of $0 before starting a free-only deployment.
Confirm the actual available Modal credits and usage/spend limits in your workspace.
Do not add payment methods, increase budgets, or start a subscription without authorization.
No free-credit amount is guaranteed by this code.

The app uses 1 GPU maximum (L4, A10, then L40S fallbacks), 0 minimum containers,
a 10-second idle scale-down window,
and a maximum of 180 seconds per Haru conversation. Opening a browser tab/request may
wake the GPU and consume credits. Provider-side limits are the real spending boundary;
the resource settings alone are not a hard monetary cap.

The workflow is manual-only. Use a standard public GitHub-hosted runner for free Actions
compute, or verify the included Actions allowance before running it privately.
Set the private HARU_PASSWORD Actions secret to a newly generated password of at least
32 characters. Never commit it. The workflow requests a 1-hour Modal API token using
the official browser authorization flow. It does not save that Modal token in source,
Actions artifacts, or GitHub Secrets.

## Conversation
After deployment, open the HTTPS endpoint and authenticate as haru with the private
password. Japanese is selected by default. Select a character and upload/record a
reference voice of at least 3 seconds, using a voice you have the right to use.
Start the conversation. The official client exchanges streaming audio with Haru.
No voice recordings or conversation data are committed to this repository.
Close the conversation tab when finished: the upstream setup screen polls readiness
and can keep the GPU active even before a conversation begins.

## Pinned upstream
- Code: https://github.com/higurashi-ai/Haru
- Commit: 7fe6b7665f8bf035998f401f8cb779fbe53f2751
- Model: higurashi-ai/Haru-4B
- Revision: 8d6e83bcd3701a76fc27a764965665da1df7da78
- Reviewed: haru/haru/server.py, backends.py, models/loaders.py, haru/pyproject.toml.
- Code and model are Apache 2.0; the installed upstream retains its third-party notices.

## Verification
The auth tests cover valid credentials, missing/malformed/wrong credentials, and
fail-closed behavior for an empty/short configured password. Syntax checks run in CI.
Deployment verification must additionally confirm model loading, Japanese defaults,
401 for unauthenticated HTTP/WebSocket requests, authenticated client load, actual
Japanese text/audio generation, disconnect/idle scale-down, and credits remaining.
A passing build or deployed URL alone is not proof of a successful conversation.

Haru is a base conversation model with factuality/instruction-following limitations.
This deployment does not establish assistant-grade accuracy or correct prior failures.

## Verified evaluation (2026-11-17)
Cloud build/deployment, 3 auth unit tests, model readiness, authenticated config,
unauthenticated HTTP 401 and 2 real Japanese WebSocket audio streams completed.
Evidence: https://github.com/6yuki14-tokuchi/haru-modal/actions/runs/44038389354
Runtime/test revision: 05a0860eea9ca02650504dea5ac6d3c9c354cc5a.

The model returned 24.96 seconds of audio for casual chat and 34.96 seconds for
a two-turn shop scenario. This proves transport and generation, not answer quality:
chat included unrelated/repeated introductions, and the shop reply incorrectly
said closing time was 20:00 when the prompt specified 18:00. It did correctly say
the reservation fee was unconfirmed. Do not use these results as a factuality pass.

Inputs were existing synthesized Japanese fixtures transported privately as 8 kbps
Opus; no physical microphone or subjective listening score was tested. Initial
readiness took 97.35 seconds including network/startup; this is not response latency.
The first returned audio chunk is not a measured response to a finished utterance.

The workflow optionally runs cloud_smoke.py when temporary private
HARU_TEST_REFERENCE, HARU_TEST_CHAT and HARU_TEST_GROUNDING secrets contain base64
Opus. Delete those fixture secrets after testing. Missing fixtures are explicitly
reported as an unrun speech test; build/auth success does not imply speech success.
Only the private application password is required for normal deployment.
