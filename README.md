# Twill AI skills

This repository contains reusable agent skills extracted from Twill workflows.

Skills are organized by directory and may either live directly at the top level or be grouped under a shared parent when they are designed to be used together. A skill directory typically includes:

- `SKILL.md`: agent-facing instructions and conventions
- `README.md`: human-facing setup and usage notes
- optional `scripts/`: helper utilities bundled with the skill

## Skill catalog

### [`twill-cloud-coding-agent`](./twill-cloud-coding-agent)

Use Twill's public `v1` API to create tasks, inspect jobs, manage scheduled tasks, and export Claude teleport sessions.

- Install URL: [`https://twill.ai/skill.md`](https://twill.ai/skill.md)
- Agent docs: [`twill-cloud-coding-agent/SKILL.md`](./twill-cloud-coding-agent/SKILL.md)
- Package page: [skills.sh/twillai/skills/twill-cloud-coding-agent](https://skills.sh/twillai/skills/twill-cloud-coding-agent)

### [`video-recording`](./video-recording)

Grouped video proof skills for validating a feature, rendering a polished recording with WebReel, and troubleshooting the recording flow.

- Human docs: [`video-recording/README.md`](./video-recording/README.md)
- Agent docs: [`video-recording/video-recording/SKILL.md`](./video-recording/video-recording/SKILL.md)
- Agent docs: [`video-recording/webreel/SKILL.md`](./video-recording/webreel/SKILL.md)

### [`computer-use-cli`](./computer-use-cli)

Automate Linux desktop apps in an X11 session with screenshot, mouse, keyboard, drag, and scroll helpers.

- Human docs: [`computer-use-cli/README.md`](./computer-use-cli/README.md)
- Agent docs: [`computer-use-cli/SKILL.md`](./computer-use-cli/SKILL.md)
