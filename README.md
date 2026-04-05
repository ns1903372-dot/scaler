---
title: Retail Ops OpenEnv
emoji: "package"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
---

# Retail Ops OpenEnv

`Retail Ops OpenEnv` is a realistic customer-support and back-office operations environment for training or evaluating AI agents on multistep retail case resolution. Instead of a toy game, the agent works through real support workflows: checking orders, reading policy, verifying inventory, fixing shipping details, issuing refunds, creating replacements, communicating with the customer, and closing the case.

The environment follows the standard OpenEnv contract with typed models, `reset()`, `step()`, `state()`, a FastAPI app, and an `openenv.yaml` manifest.

## Scenario

Each episode is a customer-support case with incomplete information. The agent must gather evidence, choose compliant operational actions, and finish with a correct customer-facing resolution.

Included tasks:

1. `easy_address_fix`: Correct a shipping address before warehouse cutoff.
2. `medium_damaged_item`: Replace a damaged item using policy and inventory constraints.
3. `hard_vip_exchange_and_refund`: Resolve a duplicate charge and a VIP size exchange across two orders.

Each task has:

- A deterministic scenario definition
- A dense reward function with partial progress
- A grader returning a score in `[0.0, 1.0]`

## Action Space

The environment accepts a typed `RetailOpsAction` with:

- `command`: one of `inspect_case`, `inspect_order`, `inspect_policy`, `inspect_inventory`, `update_shipping_address`, `issue_refund`, `create_replacement`, `send_message`, `add_internal_note`, `resolve_case`, `escalate_case`
- `order_id`: optional order reference
- `reference_id`: optional policy id or SKU
- `payload`: action-specific structured parameters
- `rationale`: optional explanation for debugging

## Observation Space

The typed `RetailOpsObservation` returns:

- `summary`: short environment response
- `visible_case`: the currently revealed case state
- `last_action_success`: whether the latest operation succeeded
- `last_action_message`: detailed feedback
- `available_commands`: allowed next commands
- `score`: cumulative task score in `[0.0, 1.0]`
- `score_breakdown`: per-task milestone progress
- `done`: whether the episode has ended
- `reward`: cumulative progress reward in `[0.0, 1.0]`

## State Space

`RetailOpsState` extends OpenEnv `State` and tracks:

- `task_id`
- `difficulty`
- `score`
- `remaining_steps`
- `resolution_status`
- `revealed_entities`
- `completed_milestones`
- `action_history`

## Reward Design

Rewards are dense and cumulative. The score increases when the agent:

- reveals the right information sources
- follows policy correctly
- executes the correct operational changes
- communicates clearly to the customer
- closes the case with a valid final resolution

Incorrect refunds, invalid warehouse selections, or premature escalation reduce the final attainable score but the score always stays in `[0.0, 1.0]`.

## Running Locally

Install dependencies:

```bash
pip install -e .
```

Run the API:

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Run the baseline inference:

```bash
python inference.py
```

Run the pre-submission validator:

```bash
python validate_submission.py
```

The validator checks:

- required files
- manifest shape
- imports
- live HTTP endpoints `/health`, `/reset`, `/step`, and `/state`
- task grader score ranges

## Hugging Face Spaces Deployment

This repository includes a root `Dockerfile` for Docker Spaces. After creating a Docker Space:

1. Push this repository to the Space.
2. Set the Space variables `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN`.
3. The Space starts `uvicorn server.app:app` on port `8000`.

### Quick Deploy

Create a Hugging Face Docker Space first, then run:

```powershell
.\deploy_to_hf_space.ps1 -RepoId "<your-username>/<your-space-name>"
```

If you want the script to configure the remote and push in one go with an explicit token:

```powershell
.\deploy_to_hf_space.ps1 -RepoId "<your-username>/<your-space-name>" -HfToken "<your-hf-token>"
```

### Space Settings

In your Hugging Face Space:

1. Choose `Docker` as the Space SDK.
2. Add these Variables/Secrets:
   - `API_BASE_URL`
   - `MODEL_NAME`
   - `HF_TOKEN`
3. Keep the app port as `8000`.
4. Push this repository to the Space remote.

### Health Check

After deploy, verify the Space root or health endpoint responds:

```text
https://huggingface.co/spaces/<your-username>/<your-space-name>
https://<your-username>-<your-space-name>.hf.space/health
```

You can also deploy through the OpenEnv CLI:

```bash
openenv validate --verbose
openenv push --repo-id <your-namespace>/<your-space-name>
```

## Baseline Inference Contract

The root `inference.py`:

- uses the OpenAI client
- reads `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN`
- runs all three tasks
- emits structured stdout lines prefixed with `[START]`, `[STEP]`, and `[END]`
- uses deterministic prompts and `temperature=0`

## Notes

- The environment logic is deterministic and lightweight enough for `vcpu=2` and `8 GB` RAM.
- No external services are required to run the environment itself.
- The environment can be used directly as a Python object or through the HTTP server.
