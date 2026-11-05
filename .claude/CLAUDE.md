# Rules for agents working in clipper1 (read before anything else)

These rules add to the root `CLAUDE.md` and **override it where they disagree**.

## Who you are
- **You are Dev A (engine).** You own `clipper/ingest`, `clipper/analyze` and `clipper/render`.
  Do not change Dev B's folders (`clipper/captions`, `clipper/ui`, `clipper/publish`).
  Changes to shared files (`models.py`, `config.py`, `llm.py`, `cli.py`, `pyproject.toml`,
  docs) still follow the root `CLAUDE.md` contract rules, because they ship to Dev B.
- **`JesseHanda/clipper1` is your private dev environment.** It is not the team repo.
- `Realche3/clipper` is the shared team repo (Dev B, the repo owner, works there), and it is the source of truth.
  Claude has no push access to it. Read it only to sync. Never try to push to it.

## The workflow in clipper1 is different from the root CLAUDE.md
- **No PRs, no reviews, no 👍 in clipper1.** The root `CLAUDE.md` git workflow (PRs, "never
  commit to `main`", approvals) applies only to `Realche3/clipper`.
- You may commit and push to clipper1 `main` directly. Use one `a/<feature>` branch per
  feature while working, then merge it into clipper1 `main` and push.
- The quality bar still applies: `uv run ruff check . && uv run pytest` must pass before you
  call a feature done.
- **The user moves finished features to `Realche3/clipper` by hand** (a new branch there, push,
  and a PR). Don't do that part yourself.

## Sync with Realche3/clipper before any work (every session, every task)
Do this first, before reading task specs or writing code:

1. Make sure `Realche3/clipper` is readable. If it is not in the session, attach it with `add_repo`
   (read access), or run
   `git remote add upstream https://github.com/Realche3/clipper.git` in this repo.
2. `git fetch upstream main && git fetch origin main`
3. `git checkout main && git merge upstream/main && git push origin main`.
   Dev B's work and the PRs the user merged upstream come in this way. Features the user already
   shipped upstream merge cleanly because the code is the same.
   - **If the merge conflicts:** stop and ask the user. Never force-push or rewrite history.
4. Tell the user, in one line, which clipper1 features are not in `Realche3/clipper` yet
   (`git log --oneline upstream/main..main -- clipper tests`).
5. Create your feature branch from the up-to-date `main`.

## Handing a finished feature to the user
`.claude/` exists only in clipper1 and must never reach `Realche3/clipper`. So for each finished
feature:
1. Make a branch `ship/<feature>` from `upstream/main` and add only the feature's changes to it
   (cherry-pick, or check out the changed files). It must contain no `.claude/` files.
2. Run ruff and pytest on that branch, then push it to clipper1.
3. Tell the user that branch name and give them the commands to push it to `Realche3/clipper`
   as `a/<feature>`.

## Git
- Never leave work unpushed. If a push fails, tell the user right away. Unpushed work in a cloud
  session is lost when the session ends.

## Coding guidelines
- Use the `karpathy-guidelines` skill (`.claude/skills/karpathy-guidelines/SKILL.md`) whenever
  you write, review or refactor code: state assumptions, keep it simple, make surgical changes,
  and define how you'll verify the work.
