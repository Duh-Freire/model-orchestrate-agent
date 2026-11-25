# Publishing log

Maintainer notes: what was published and how to release the next version.

## Links

- Repository: https://github.com/duphl-wq/model-orchestrate-agent
- skills.sh: https://skills.sh/duphl-wq/model-orchestrate-agent
- Releases: https://github.com/duphl-wq/model-orchestrate-agent/releases

## Releases

| Date | Version | Notes |
| --- | --- | --- |
| 2026-11-25 | v0.7.0 | First public release. The repo was created as `claude-model-orchestrate-agent` and renamed to the skill's own name on the same day (GitHub redirects the old URL). Listed on skills.sh after the first `npx skills add` install. |
| 2026-11-25 | v0.7.1 | Short pitch (what it does, the cannon/crane analogy and one example) at the top of `SKILL.md`, so it shows first on the skills.sh page. About 90 more tokens per run. |

## How the first release was prepared

- **Scrub:** the source folder was copied to a clean local folder and scanned for private data. The only hit was the author's
  personal name in `SKILL.md` and `LICENSE.txt`, replaced with the GitHub login. The old `.skill` package was left out of git
  and rebuilt from the clean files.
- **Commits:** authored with the GitHub noreply address, set only in this repository.
- **SEO:** a short description, 20 topics, a homepage link to the README, and a skills.sh install badge in the README.

## Next release

1. Copy the changed files from the source folder into this repository. Never copy `.git`.
2. Scan for private data again and bump `metadata.version` in `SKILL.md`.
3. Commit and push.
4. Rebuild the `.skill` package from the tracked files and run `gh release create v<version>`.
5. Add a row to the table above.

The `publish-skill-github` skill runs these steps.
