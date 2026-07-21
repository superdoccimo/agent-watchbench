# Deferred Branch Freshness Check

Use this checklist before pushing or opening a PR from a branch that was held
locally during a quiet window. It is meant to catch stale, conflicting, or
already-equivalent work after `origin/main` has moved.

## Checklist

1. Fetch the current default branch without changing local files:

   ```text
   git fetch --prune origin main
   ```

2. Confirm the deferred branch still contains unique work:

   ```text
   git diff --stat origin/main...HEAD
   git diff --quiet origin/main...HEAD
   ```

   If the second command exits `0`, the branch has no unique patch relative to
   current `origin/main`; do not open a PR. Record the branch as redundant and
   close or archive it.

3. Check whether the same patch already landed on `origin/main` under another
   commit:

   ```text
   git cherry -v origin/main HEAD
   ```

   Treat lines beginning with `-` as equivalent patches already present on
   `origin/main`. If every deferred commit is equivalent, do not open a PR.

4. Check whether the branch can be replayed cleanly before public review:

   ```text
   git merge-base --is-ancestor origin/main HEAD
   ```

   If this exits non-zero, current `origin/main` is not an ancestor of the
   deferred branch. Rebase in a local worktree or close the branch as stale
   before opening a PR.

5. When the branch is still fresh, include the freshness evidence in the PR
   body:

   ```text
   Freshness evidence:
   - origin/main fetched: <timestamp>
   - unique patch present: yes
   - git cherry equivalent patches: none
   - origin/main ancestor of branch: yes
   ```

## Boundary

This check is local repository hygiene only. It does not approve a release,
visibility change, package publish, deployment, credential handling, or any
external service change.
