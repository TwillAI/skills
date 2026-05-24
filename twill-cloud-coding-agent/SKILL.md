---
name: twill-cloud-coding-agent
description: Use Twill Cloud Coding Agent to manage Twill's public v1 API workflows. Create/list/update tasks, stream and cancel jobs, manage scheduled tasks, list repositories, and export Claude teleport sessions.
compatibility: Requires access to https://twill.ai/api/v1, curl, and a TWILL_API_KEY environment variable.
metadata:
  author: TwillAI
  version: "1.3.0"
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
  curl -sS "$@" -H "Authorization: Bearer $TWILL_API_KEY" -H "Content-Type: application/json"
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
- `GET /api/v1/scheduled-tasks`
- `POST /api/v1/scheduled-tasks`
- `GET /api/v1/scheduled-tasks/:scheduledTaskId`
- `PATCH /api/v1/scheduled-tasks/:scheduledTaskId`
- `DELETE /api/v1/scheduled-tasks/:scheduledTaskId`
- `POST /api/v1/scheduled-tasks/:scheduledTaskId/pause`
- `POST /api/v1/scheduled-tasks/:scheduledTaskId/resume`

## Auth and Discovery

Validate key and workspace context:

```bash
curl -sS "$TWILL_BASE_URL/api/v1/auth/me" -H "Authorization: Bearer $TWILL_API_KEY"
```

List available GitHub repositories for the workspace:

```bash
curl -sS "$TWILL_BASE_URL/api/v1/repositories" -H "Authorization: Bearer $TWILL_API_KEY"
```

## Tasks

### Create Task

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks" -d '{"command":"Fix flaky tests in CI","userIntent":"SWE"}'
```

Repository and branch are no longer accepted in the request body — the task runs against the workspace's connected repos as resolved by the agent at runtime.

Required fields:

- `command`

Optional fields:

- `agent` (provider or provider/model, for example `codex` or `codex/gpt-5.4`; provider shorthands accepted: `claude-code`, `codex`, `open-code`)
- `userIntent` (`SWE`, `PLAN`, `ASK`, `DEV_ENVIRONMENT`) — defaults to `SWE`
- `reasoningEffort` (`low`, `medium`, `high`, `xhigh`)
- `parentId` (id of an existing task to spawn this one from)
- `title`
- `files` (array of `{ filename, mediaType, url }`)

Response is `{ task: { id, slug, title, url }, job: { id, status } }`. Always report `task.url` back to the user.

### List Tasks

```bash
curl -sS "$TWILL_BASE_URL/api/v1/tasks?limit=20&cursor=BASE64_CURSOR" -H "Authorization: Bearer $TWILL_API_KEY"
```

Supports cursor pagination via `limit` (default 20, max 100) and `cursor`. Response is `{ tasks, nextCursor }`; each task includes `id`, `slug`, `title`, `url`, `createdAt`, `latestJobStatus`, and `pr`.

### Get Task Details

```bash
curl -sS "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG" -H "Authorization: Bearer $TWILL_API_KEY"
```

Returns task metadata plus `latestJob` including `id`, `status`, `type`, `agentProvider`, `startedAt`, `completedAt`, `plan`, `planOutcome`, `finalAnswer` (useful for `ASK` jobs), and `pr` when available.

### Send Follow-Up Message

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/messages" -d '{"message":"Please prioritize login flow first","userIntent":"PLAN"}'
```

Sending a message cancels any in-flight job for the task and starts a fresh run with this message (API/CLI bypass the UI queueing flow).

Optional fields: `userIntent`, `reasoningEffort` (`low`, `medium`, `high`, `xhigh`), `files`.

### List Task Jobs

```bash
curl -sS "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/jobs?limit=30&cursor=BASE64_CURSOR" -H "Authorization: Bearer $TWILL_API_KEY"
```

Supports cursor pagination:
- `limit` defaults to `30` (max `100`)
- `cursor` fetches older pages
- response includes `jobs` and `nextCursor`

### Approve Plan

Use when the latest plan job is completed and ready for approval.

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/approve-plan" -d '{}'
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
curl -N "$TWILL_BASE_URL/api/v1/jobs/JOB_ID/logs/stream" -H "Authorization: Bearer $TWILL_API_KEY" -H "Accept: text/event-stream"
```

Stream emits JSON payloads in `data:` lines and terminates with a `complete` event.

### Cancel Job

```bash
api -X POST "$TWILL_BASE_URL/api/v1/jobs/JOB_ID/cancel" -d '{}'
```

## Scheduled Tasks

### List and Create

```bash
curl -sS "$TWILL_BASE_URL/api/v1/scheduled-tasks" -H "Authorization: Bearer $TWILL_API_KEY"

api -X POST "$TWILL_BASE_URL/api/v1/scheduled-tasks" -d '{
  "title":"Daily triage",
  "message":"Review urgent issues and open tasks",
  "cronExpression":"0 9 * * 1-5",
  "timezone":"America/New_York",
  "agentProviderId":"claude-code/sonnet"
}'
```

Required: `title` (max 200 chars), `message`, `cronExpression`.

Optional: `timezone` (IANA name, defaults to `"UTC"`), `agentProviderId` (provider/model override, e.g. `claude-code/sonnet`, `codex/gpt-5.4`).

Repository / branch are no longer part of the scheduled-task payload — each run resolves repos at agent dispatch time, the same way one-shot tasks do.

Response is `{ scheduledTask: { id, workspaceId, createdById, title, message, cronExpression, timezone, nextRunAt, lastRunAt, enabled, agentProviderId, createdAt, updatedAt } }`.

### Read, Update, Delete

```bash
curl -sS "$TWILL_BASE_URL/api/v1/scheduled-tasks/SCHEDULED_TASK_ID" -H "Authorization: Bearer $TWILL_API_KEY"

api -X PATCH "$TWILL_BASE_URL/api/v1/scheduled-tasks/SCHEDULED_TASK_ID" -d '{
  "message":"Updated instructions",
  "cronExpression":"0 10 * * 1-5",
  "agentProviderId":"codex/gpt-5.4"
}'

curl -sS -X DELETE "$TWILL_BASE_URL/api/v1/scheduled-tasks/SCHEDULED_TASK_ID" -H "Authorization: Bearer $TWILL_API_KEY"
```

PATCH accepts any subset of `title`, `message`, `cronExpression`, `timezone`, `agentProviderId` (pass `null` to clear the override). DELETE returns `{ "success": true }`.

### Pause and Resume

```bash
api -X POST "$TWILL_BASE_URL/api/v1/scheduled-tasks/SCHEDULED_TASK_ID/pause" -d '{}'
api -X POST "$TWILL_BASE_URL/api/v1/scheduled-tasks/SCHEDULED_TASK_ID/resume" -d '{}'
```

## Behavior

- Use `userIntent` (`SWE`, `PLAN`, `ASK`, `DEV_ENVIRONMENT`) when calling API endpoints directly.
- Do **not** send `repository` / `branch` on tasks or `repositoryUrl` / `baseBranch` on scheduled tasks — these fields were removed; repo/branch is resolved by the agent at run time from workspace context.
- Create task, report `task.url`, and only poll/stream logs when requested.
- Ask for `TWILL_API_KEY` if missing.
- Do not print API keys or other secrets.
