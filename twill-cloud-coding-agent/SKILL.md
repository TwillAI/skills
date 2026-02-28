---
name: twill-cloud-coding-agent
description: Use Twill Cloud Coding Agent to manage Twill's public v1 API workflows. Create/list/update tasks, stream and cancel jobs, manage automations, list repositories, and export Claude teleport sessions.
compatibility: Requires access to https://twill.ai/api/v1, curl, and a TWILL_API_KEY environment variable.
metadata:
  author: TwillAI
  version: "1.1.0"
  category: coding
  homepage: https://twill.ai
  api_base: https://twill.ai/api/v1
---

# Twill Cloud Coding Agent

Use this skill to run Twill workflows through the public `v1` API.

## Setup

Set API key and optional base URL:

```bash
export TWILL_API_KEY="your_api_key"
export TWILL_BASE_URL="${TWILL_BASE_URL:-https://twill.ai}"
```

All API calls use:

`Authorization: Bearer $TWILL_API_KEY`

Use this helper to reduce repetition:

```bash
api() {
  curl -sS "$@" \
    -H "Authorization: Bearer $TWILL_API_KEY" \
    -H "Content-Type: application/json"
}
```

## Endpoint Coverage (Public v1)

- `GET /api/v1/auth/me`
- `GET /api/v1/repositories`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/:taskIdOrSlug`
- `POST /api/v1/tasks/:taskIdOrSlug/messages`
- `GET /api/v1/tasks/:taskIdOrSlug/jobs`
- `POST /api/v1/tasks/:taskIdOrSlug/approve-plan`
- `POST /api/v1/tasks/:taskIdOrSlug/cancel`
- `POST /api/v1/tasks/:taskIdOrSlug/archive`
- `GET /api/v1/tasks/:taskIdOrSlug/teleport/claude`
- `GET /api/v1/jobs/:jobId/logs/stream`
- `POST /api/v1/jobs/:jobId/cancel`
- `GET /api/v1/automations`
- `POST /api/v1/automations`
- `GET /api/v1/automations/:automationId`
- `PATCH /api/v1/automations/:automationId`
- `DELETE /api/v1/automations/:automationId`
- `POST /api/v1/automations/:automationId/pause`
- `POST /api/v1/automations/:automationId/resume`

## Auth and Discovery

Validate key and workspace context:

```bash
curl -sS "$TWILL_BASE_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $TWILL_API_KEY"
```

List available GitHub repositories for the workspace:

```bash
curl -sS "$TWILL_BASE_URL/api/v1/repositories" \
  -H "Authorization: Bearer $TWILL_API_KEY"
```

## Tasks

### Create Task

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks" \
  -d '{"command":"Fix flaky tests in CI","repository":"owner/repo","userIntent":"SWE"}'
```

Required fields:

- `command`
- `repository` (`owner/repo` or full GitHub URL)

Optional fields:

- `branch`
- `agent` (provider or provider/model, for example `codex` or `codex/gpt-5.2`)
- `userIntent` (`SWE`, `PLAN`, `ASK`, `DEV_ENVIRONMENT`, `SCHEDULE`)
- `title`
- `files` (array of `{ filename, mediaType, url }`)

Always report `task.url` back to the user.

### List Tasks

```bash
curl -sS "$TWILL_BASE_URL/api/v1/tasks?limit=20&cursor=BASE64_CURSOR" \
  -H "Authorization: Bearer $TWILL_API_KEY"
```

Supports cursor pagination via `limit` and `cursor`.

### Get Task Details

```bash
curl -sS "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG" \
  -H "Authorization: Bearer $TWILL_API_KEY"
```

Returns task metadata plus `latestJob` including status, type, plan content, and plan outcome when available.

### Send Follow-Up Message

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/messages" \
  -d '{"message":"Please prioritize login flow first","userIntent":"PLAN"}'
```

`userIntent` and `files` are optional.

### List Task Jobs

```bash
curl -sS "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/jobs" \
  -H "Authorization: Bearer $TWILL_API_KEY"
```

### Approve Plan

Use when the latest plan job is completed and ready for approval.

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/approve-plan" \
  -d '{}'
```

### Cancel Task

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/cancel" -d '{}'
```

### Archive Task

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/archive" -d '{}'
```

## Jobs

### Stream Job Logs (SSE)

```bash
curl -N "$TWILL_BASE_URL/api/v1/jobs/JOB_ID/logs/stream" \
  -H "Authorization: Bearer $TWILL_API_KEY" \
  -H "Accept: text/event-stream"
```

Stream emits JSON payloads in `data:` lines and terminates with a `complete` event.

### Cancel Job

```bash
api -X POST "$TWILL_BASE_URL/api/v1/jobs/JOB_ID/cancel" -d '{}'
```

## Automations

### List and Create

```bash
curl -sS "$TWILL_BASE_URL/api/v1/automations" \
  -H "Authorization: Bearer $TWILL_API_KEY"

api -X POST "$TWILL_BASE_URL/api/v1/automations" -d '{
  "title":"Daily triage",
  "message":"Review urgent issues and open tasks",
  "repositoryUrl":"https://github.com/org/repo",
  "baseBranch":"main",
  "cronExpression":"0 9 * * 1-5",
  "timezone":"America/New_York"
}'
```

### Read, Update, Delete

```bash
curl -sS "$TWILL_BASE_URL/api/v1/automations/AUTOMATION_ID" \
  -H "Authorization: Bearer $TWILL_API_KEY"

api -X PATCH "$TWILL_BASE_URL/api/v1/automations/AUTOMATION_ID" -d '{
  "message":"Updated instructions",
  "cronExpression":"0 10 * * 1-5"
}'

curl -sS -X DELETE "$TWILL_BASE_URL/api/v1/automations/AUTOMATION_ID" \
  -H "Authorization: Bearer $TWILL_API_KEY"
```

### Pause and Resume

```bash
api -X POST "$TWILL_BASE_URL/api/v1/automations/AUTOMATION_ID/pause" -d '{}'
api -X POST "$TWILL_BASE_URL/api/v1/automations/AUTOMATION_ID/resume" -d '{}'
```

## Behavior

- Use `userIntent` values, not `mode`, when calling API endpoints directly.
- Create task, report `task.url`, and only poll/stream logs when requested.
- Ask for `TWILL_API_KEY` if missing.
- Do not print API keys or other secrets.
