# Haru Japanese conversation on Modal

This dedicated evaluation deployment reuses the official Haru web client and server.
No model weights or Python dependencies are installed on the Mac.
Source is maintained here; cloud runners build the image and Modal stores/executes the model.

## Current authorization and cost boundary
- User requested Modal free credits only, no large local storage.
- Workspace: yuki14, environment main, app haru-ja-free.
- Dashboard verified on 2026-11-17: $1 available credits and $1 usage limit; no payment method.
  The advertised $30/month requires a payment method, and has NOT been unlocked.
- Do not add a payment method, increase budgets, or start a paid subscription.
- Initial deployment uses one L4, 0 minimum containers, maximum 1, 10-second idle scale-down,
  maximum 180 seconds per Haru conversation. These controls reduce use; the provider's
  workspace usage limit is the actual spending boundary.
- A browser tab/request can wake the GPU again and consume remaining free credits.
- The initial deployment workflow must NOT run in a private repository unless included
  Actions availability is confirmed. Public standard runners avoid Actions compute charges.
- Temporary Modal token authorization is required before the cloud deploy can proceed.
  Token lifetime is 1 hour. No Modal token is stored in repository contents or GitHub Secrets.
  The dedicated endpoint password is stored as a private Actions secret.

## User flow
Open the deployed HTTPS endpoint and authenticate with username haru and the generated password.
Language defaults to Japanese. Select a character card and upload or record a reference voice
(3 seconds or more, a voice you have the right to use), then start the conversation.
The official client receives/plays streamed audio; there is no local model inference.
The endpoint password is supplied through the private HARU_PASSWORD Actions secret.
No passwords, Modal tokens, voice recordings, or conversation data are placed in source or artifacts.

## Source and reuse
- Official Haru: https://github.com/higurashi-ai/Haru
- Reviewed upstream commit: 7fe6b7665f8bf035998f401f8cb779fbe53f2751.
- Official model: higurashi-ai/Haru-4B, revision 8d6e83bcd3701a76fc27a764965665da1df7da78.
- Reviewed: haru/haru/server.py, backends.py, models/loaders.py, haru/pyproject.toml.
- UniAgent reviewed commit: 50325f63b14497e9cb7d27185c2b63537ffdf0fe; no existing Modal
  integration in reviewed workflow scope. This is a standalone demo, no UniAgent changes.
- Reuse decision: use the bundled official client/server, adding authentication and cloud
  resource configuration only. No new speech model or product integration is implemented.
- Code and model are Apache 2.0; upstream third-party notices remain in the installed package.

## Verification contract
- Static: Python syntax and authentication acceptance/denial tests.
- Remote: exact deployed source, model loading, default Japanese setting, unauthenticated 401,
  successful authenticated client load, generated Japanese text/audio, connection close,
  scale-down and current credits.
- Quality oracle: preserve prior Haru failures (unknown reservation fee and meal follow-up);
  this deployment is not proof of corrected grounding or assistant-grade factual reliability.
- A deployment/build success alone does not count as a verified conversation.
- No automated recurring jobs, public recording collection, or extra paid resources.

## Status
Prepared; remote build/deployment, billing enforcement in execution, and actual Japanese
conversation remain unverified until the authorized cloud workflow is run.
