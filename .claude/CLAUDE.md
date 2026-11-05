# Rules for agents working in clipper1 (read before anything else)

These rules add to the root `CLAUDE.md`. Follow both.

## Who you are
- **You are Dev B (distribution).** You own `clipper/captions`, `clipper/ui` and `clipper/publish`.
  Do not change Dev A's folders (`clipper/ingest`, `clipper/analyze`, `clipper/render`).
  Shared files follow the root `CLAUDE.md` rules.
- **Your dev environment is this repo, `JesseHanda/clipper1`.** Branch, commit, push and open PRs here.
- `Realche3/clipper` is the shared repo that Dev A also works in, and it is the source of truth.
  Claude has no push access to it. Read it only to sync. Never try to push to it.

## Sync both repos before any work (every session, every task)
Do this first, before reading task specs or writing code:

1. Make sure `Realche3/clipper` is readable. If it is not in the session, attach it with `add_repo`
   (read access), or run
   `git remote add upstream https://github.com/Realche3/clipper.git` in this repo.
2. `git fetch upstream main && git fetch origin main`
3. Compare them: `git rev-list --left-right --count origin/main...upstream/main`
   - **`0 0`:** in sync. Go ahead.
   - **Upstream is ahead and clipper1 has nothing extra:** fast-forward clipper1 with
     `git checkout main && git merge --ff-only upstream/main && git push origin main`.
     This mirrors upstream; it is not a new commit on `main`.
   - **clipper1 has commits that upstream lacks** (Dev B work not yet in `Realche3/clipper`):
     stop and tell the user which commits, before doing anything else.
   - **The fast-forward fails (the repos diverged):** stop and ask the user. Never force-push and
     never rewrite history to make them match.
4. Rebase or create your feature branch from the up-to-date `main`.

## Git
- Branch names: `b/<feature>`.
- Never commit work you can't push. If a push fails, tell the user right away. Unpushed work
  in a cloud session is lost when the session ends.
- This file is specific to clipper1. Never copy it into `Realche3/clipper`.

## Coding guidelines
- Use the `karpathy-guidelines` skill (`.claude/skills/karpathy-guidelines/SKILL.md`) whenever
  you write, review or refactor code: state assumptions, keep it simple, make surgical changes,
  and define how you'll verify the work.
