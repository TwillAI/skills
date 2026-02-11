---
name: twill-cloud-coding-agent
description: Use Twill Cloud Coding Agent to run async coding workflows in Twill. Create tasks, monitor status, send follow-ups, approve plans, and cancel tasks through the Twill API.
compatibility: Requires access to https://twill.ai/api/v1, curl, and a TWILL_API_KEY environment variable.
metadata:
  author: TwillAI
  version: "1.0.0"
  category: coding
  homepage: https://twill.ai
  api_base: https://twill.ai/api/v1
---

# Twill Cloud Coding Agent

Use Twill Cloud Coding Agent to delegate coding tasks, track active work, and manage plan approvals and follow-ups.

## Setup

Set the `TWILL_API_KEY` environment variable before making API calls.

```bash
export TWILL_API_KEY="your_api_key"
```

All requests require this header:

`Authorization: Bearer $TWILL_API_KEY`

Detect repository from `git remote get-url origin` when possible, or use `TWILL_REPOSITORY=owner/repo`.

## Create a Task

```bash
curl -sS -X POST https://twill.ai/api/v1/tasks \
  -H "Authorization: Bearer $TWILL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command":"your task description","repository":"owner/repo","mode":"code"}'
```

Optional fields: `mode` (`code` or `plan`, default `code`), `agent`, `branch`, `title`.

Response includes `task.id`, `task.slug`, `task.url`, `task.status`, `job.id`, `job.status`.

Always report `task.url` back to the user.

## Get Task Status

```bash
curl -sS https://twill.ai/api/v1/tasks/TASK_ID_OR_SLUG \
  -H "Authorization: Bearer $TWILL_API_KEY"
```

Statuses: `PLANNING`, `PENDING_FEEDBACK`, `IMPLEMENTING`, `PENDING_REVIEW`, `COMPLETED`, `FAILED`, `CANCELLED`.

## Send a Follow-Up

```bash
curl -sS -X POST https://twill.ai/api/v1/tasks/TASK_ID_OR_SLUG/messages \
  -H "Authorization: Bearer $TWILL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":"your follow-up instructions"}'
```

## Approve a Plan

Use when task status is `PENDING_FEEDBACK` and the user asks to proceed.

```bash
curl -sS -X POST https://twill.ai/api/v1/tasks/TASK_ID_OR_SLUG/approve-plan \
  -H "Authorization: Bearer $TWILL_API_KEY"
```

## Cancel a Task

```bash
curl -sS -X POST https://twill.ai/api/v1/tasks/TASK_ID_OR_SLUG/cancel \
  -H "Authorization: Bearer $TWILL_API_KEY"
```

## Behavior

- Default to `mode=code` unless user asks for plan-first behavior.
- Create the task, report the URL, and stop polling unless asked.
- Ask for `TWILL_API_KEY` if it is missing.
