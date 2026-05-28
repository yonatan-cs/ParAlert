# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-05-28

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

- When the user asks to revert commits from the graph, prefer a history rewrite like `git reset --hard` over creating a revert commit.
- If the target commit is the root, use a new root commit or ref rewrite to remove it from the graph instead of trying to reset past it.
- If the user wants zero commits in the graph, convert the branch to an unborn branch and delete all local refs, including remote-tracking refs.

## Key Learnings

- **Project:** Hackathon-Project

- `61aa7ac` is the root commit in this repo; the branch can be moved back to it, but there is no earlier parent to reset behind it.
- A local graph can be re-rooted by creating a new empty root commit with `git commit-tree` and updating branch refs with `git update-ref`.
- An unborn branch with `git symbolic-ref HEAD refs/heads/<name>` and no branch ref results in `git status` showing "No commits yet on <name>".

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->

- [2026-05-28] Do not say a root commit can be removed with `git reset` to an earlier parent; if the user wants it out of the graph, re-root the branch instead.
- [2026-05-28] Do not leave remote-tracking refs in place when the user asks for zero commits in the graph; delete them too.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
