# Video Recording Skills

This folder groups two agent skills that are most useful together when you want human-friendly video proof of a feature.

## Skills in this folder

### `video-recording`

Repo path: `video-recording/video-recording/SKILL.md`

This is the workflow skill.

Its helper scripts live in:

- `video-recording/video-recording/scripts/twill-video-build-config.py`
- `video-recording/video-recording/scripts/twill-video-build-config`
- `video-recording/video-recording/scripts/twill-video-record`

### `webreel`

Repo path: `video-recording/webreel/SKILL.md`

This is the reference skill.

## Recommended usage

Use both skills together:

1. Start with `video-recording` for the workflow.
2. Use `webreel` whenever you need config details, pacing rules, or troubleshooting.

## Compatibility notes

- Use `agent-browser` or an equivalent browser automation workflow for selector discovery before recording.
- You need a working `webreel` install plus Chrome or Chromium and `ffmpeg`.
- If the published WebReel release does not yet include the fixes you need, install from the currently used fix branch and pinned commit:

```bash
git clone --depth 1 --branch fix/type-inserttext https://github.com/arielconti10/webreel.git /tmp/webreel
cd /tmp/webreel
git checkout 2c35fe930dfbed7278643b6e736319da0caa5d7a
pnpm install --frozen-lockfile
pnpm build
pnpm --filter ./packages/webreel deploy --legacy /opt/webreel
```

That branch and commit include fixes for:

- `type + selector` crashes
- React input compatibility
- `charDelay: 0` hangs
- stale navigation frames
- orphaned Chrome processes

Once those fixes are fully available in a stable WebReel release, this custom install flow may no longer be necessary.

## Why this is grouped

The two skills serve different roles, but in practice they are usually used together:

- `video-recording` answers "how do I capture proof of this feature?"
- `webreel` answers "how do I make the video look good and debug the recorder?"
