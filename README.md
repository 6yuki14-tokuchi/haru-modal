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

The app uses 1 L4 maximum, 0 minimum containers, a 10-second idle scale-down window,
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

## Status
Prepared. Remote build, deployment, Japanese conversation and cost verification are
not yet completed.
