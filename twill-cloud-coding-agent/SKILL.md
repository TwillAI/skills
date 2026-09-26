---
name: twill-cloud-coding-agent
description: Use Twill Cloud Coding Agent to manage Twill's public v1 API workflows. Create/list/update tasks, stream and cancel jobs, manage scheduled tasks, list repositories, and export Claude teleport sessions.
compatibility: Requires access to https://twill.ai/api/v1, curl, and a TWILL_API_KEY environment variable.
metadata:
  author: TwillAI
  version: "1.4.0"
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

API keys belong to a cloud workspace and only reach its cloud tasks. Keys from a personal workspace are rejected, and local project chats (Twill Desktop) are not visible through the API: they return `404` or are omitted from lists.

Errors are JSON `{ "error": { "code", "message", "details"? } }`. Rate limits are 100 requests/minute and 1,000/hour per key; a `429` includes `Retry-After`.

## Endpoint Coverage (Public v1)

- `GET /api/v1/auth/me`
- `GET /api/v1/repositories`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/:taskIdOrSlug`
- `POST /api/v1/tasks/:taskIdOrSlug/messages`
- `GET /api/v1/tasks/:taskIdOrSlug/jobs`
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

There is no plan-approval endpoint. Plans and native permission questions are answered in the Twill task chat.

## Auth and Discovery

Validate key and workspace context:

```bash
curl -sS "$TWILL_BASE_URL/api/v1/auth/me" -H "Authorization: Bearer $TWILL_API_KEY"
```

Returns `workspaceId`, `userId`, `apiKeyId`, `workspaceName`, `workspaceSlug`.

List available GitHub repositories for the workspace:

```bash
curl -sS "$TWILL_BASE_URL/api/v1/repositories" -H "Authorization: Bearer $TWILL_API_KEY"
```

Returns `{ repositories: [{ fullName, defaultBranch, description }] }`.

## Tasks

### Create Task

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks" -d '{"command":"Fix flaky tests in CI"}'
```

Repository and branch are not accepted in the request body. The agent picks from the workspace's connected repos at run time.

Required fields:

- `command`

Optional fields:

- `agent`: a complete `provider/model` id, for example `claude-code/sonnet`, `claude-code/opus`, `codex/gpt-5.5`, `open-code/openai/gpt-5.4`. Provider-only values such as `codex` are rejected. Omit it to use the workspace's routing defaults.
- `userIntent` (`SWE`, `DEV_ENVIRONMENT`, `SCHEDULE`): defaults to `SWE`. Legacy `PLAN`, `ASK` and `GOAL` are still accepted but run as `SWE`.
- `reasoningEffort` (`low`, `medium`, `high`, `xhigh`, `max`, `ultra`)
- `parentId` (id of an existing task to spawn this one from)
- `title`
- `files` (array of `{ filename, mediaType, url }`, where `url` must be a `data:` URL such as `data:text/plain;base64,...`; remote `http(s):` URLs are rejected)

To have the agent plan first, start `command` with `/plan`. The user reviews and approves the plan in the Twill task chat.

Response (`201`) is `{ task: { id, slug, title, url }, job: { id, status } }`. Always report `task.url` back to the user.

### List Tasks

```bash
curl -sS "$TWILL_BASE_URL/api/v1/tasks?limit=20&cursor=BASE64_CURSOR" -H "Authorization: Bearer $TWILL_API_KEY"
```

Supports cursor pagination via `limit` (default 20, max 100) and `cursor`. Response is `{ tasks, nextCursor }`; each task includes `id`, `slug`, `title`, `url`, `createdAt`, `latestJobStatus`, and `prs` (array of `{ repoFullName, prNumber, prUrl, title, state }`, where `state` is `open`, `merged` or `closed`).

### Get Task Details

```bash
curl -sS "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG" -H "Authorization: Bearer $TWILL_API_KEY"
```

Returns `task` (`id`, `slug`, `title`, `url`, `createdAt`, `updatedAt`, `prs`) and `latestJob` (`id`, `status`, `type`, `agentProvider`, `startedAt`, `completedAt`, `plan`, `planOutcome`, `finalAnswer`), or `latestJob: null`.

### Send Follow-Up Message

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/messages" -d '{"message":"Please prioritize login flow first"}'
```

Sending a message cancels any in-flight job for the task and starts a fresh run with this message. The response is `{ job: { id, status } }`.

Optional fields: `userIntent`, `reasoningEffort`, `files` (same rules as create), and `agent`. `agent` may change the model but not the harness: switching from `claude-code/...` to `codex/...` returns `400`. Start a new task to use another harness.

### List Task Jobs

```bash
curl -sS "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/jobs?limit=30&cursor=BASE64_CURSOR" -H "Authorization: Bearer $TWILL_API_KEY"
```

Supports cursor pagination:
- `limit` defaults to `30` (max `100`)
- `cursor` fetches older pages
- response is `{ jobs, nextCursor }`; each job has `id`, `status`, `type`, `agentProvider`, `finalAnswer`, `plan`, `planOutcome`, `error`, `createdAt`, `completedAt`

### Cancel Task

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/cancel" -d '{}'
```

### Archive Task

```bash
api -X POST "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/archive" -d '{}'
```

### Export Claude Teleport Session

```bash
curl -sS "$TWILL_BASE_URL/api/v1/tasks/TASK_ID_OR_SLUG/teleport/claude" -H "Authorization: Bearer $TWILL_API_KEY" -o session.tar
```

Returns a tar of the task's Claude Code session JSONL files (headers `X-Twill-Session-Id`, `X-Twill-Job-Id`, `X-Twill-File-Count`). Only works for Claude Code tasks while the task sandbox is still alive; otherwise it returns `400`, `404` or `409`.

## Jobs

### Stream Job Logs (SSE)

```bash
curl -N "$TWILL_BASE_URL/api/v1/jobs/JOB_ID/logs/stream" -H "Authorization: Bearer $TWILL_API_KEY" -H "Accept: text/event-stream"
```

Each `data:` line is a JSON object with a `type`:

- `connected`: first event.
- Finished jobs: `trace_url` (`url`, `expiresAt`), a short-lived signed URL to download the full trace, then `historical_complete` and `complete` (`status`: `completed`, `failed` or `cancelled`).
- Running jobs: `trace_chunks` (signed chunk URLs) and `trace_records` for history, then `historical_complete`, then live log and status events until `complete`.
- `error`: the stream failed.

To get a job's result without parsing the trace, prefer `finalAnswer` from Get Task Details or List Task Jobs.

### Cancel Job

```bash
api -X POST "$TWILL_BASE_URL/api/v1/jobs/JOB_ID/cancel" -d '{}'
```

## Scheduled Tasks

Creating scheduled tasks requires a paid plan (Pro or Max); otherwise the API returns `403`.

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

Optional: `timezone` (IANA name, defaults to `"UTC"`), `agentProviderId` (complete `provider/model` override, e.g. `claude-code/sonnet`, `codex/gpt-5.5`). The server does not validate `agentProviderId` when saving, so an invalid id only fails when the schedule runs.

Repository and branch are not part of the scheduled-task payload. Each run picks repos at dispatch time, like one-shot tasks.

Response is `{ scheduledTask: { id, workspaceId, createdById, title, message, cronExpression, timezone, nextRunAt, lastRunAt, enabled, agentProviderId, createdAt, updatedAt } }`.

### Read, Update, Delete

```bash
curl -sS "$TWILL_BASE_URL/api/v1/scheduled-tasks/SCHEDULED_TASK_ID" -H "Authorization: Bearer $TWILL_API_KEY"

api -X PATCH "$TWILL_BASE_URL/api/v1/scheduled-tasks/SCHEDULED_TASK_ID" -d '{
  "message":"Updated instructions",
  "cronExpression":"0 10 * * 1-5",
  "agentProviderId":"codex/gpt-5.5"
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

- Use `userIntent` `SWE` (default), `DEV_ENVIRONMENT` or `SCHEDULE`. For planning, prefix the command with `/plan` instead of sending `PLAN`.
- Do **not** send `repository` / `branch` on tasks or `repositoryUrl` / `baseBranch` on scheduled tasks. Twill picks repos and branches at run time from workspace context.
- Always pass `agent` / `agentProviderId` as a complete `provider/model` id.
- Inline attachments as `data:` URLs.
- Create the task, report `task.url`, and only poll or stream logs when requested.
- Plan approvals and permission questions happen in the Twill task chat. A follow-up message does not answer them.
- Ask for `TWILL_API_KEY` if missing.
- Do not print API keys or other secrets.
