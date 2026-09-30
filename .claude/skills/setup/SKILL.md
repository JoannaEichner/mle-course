---
name: setup
description: Guided environment and project setup for a new learner (lesson 00).
disable-model-invocation: true
---

# Setup

Goal: `uv run course check 00` shows three passes, and the learner can say what each installed tool is for.

Setup is the one place where you act directly: run commands and fix what is broken. Say in one sentence what a command does before you run it. This is the learner's first contact with a terminal, and the explanation is the lesson.

## Steps

1. **Orient.** Ask which system they use (Windows with WSL2, or Linux) and how far they got in `lectures/00-setup/index.html`. Done when you know both.
2. **Diagnose.** Run `uv run course doctor`. If `uv` is missing, install it first (see Fixes) and run `uv sync`. Done when you have the doctor output.
3. **Fix every `✗` line**, top to bottom, one at a time, rerunning doctor after each. Commands that need `sudo` or a browser login are typed by the learner: give the exact command and say what they will see. Done when doctor shows no `✗`.
4. **Handle `!` and `·` lines.** Explain each `!`; fix the ones that take under five minutes. `·` lines (Docker, GPU) belong to later modules, with one exception: if the machine has an NVIDIA card and `nvidia-smi` fails, fix it now while the cause is cheap to find.
5. **Data profile.** Doctor's last lines name the profile. Explain in two sentences what it changes (`tutor/low-memory.md` has the table).
6. **Editor.** Have the learner run `code .` and confirm the status bar reads `WSL: Ubuntu-24.04` (on Windows). Python and Jupyter extensions must be installed in WSL.
7. **First pull request.** The learner types every step; you dictate and explain:
   - `gh repo set-default <their-login>/mle-course`, so the pull request targets their fork and not the course repository,
   - `git switch -c setup/journal`,
   - they write `notes/journal.md` in their own words: why they take the course, what they want to be able to do in three months,
   - `git add`, `git commit`, `git push -u origin setup/journal`, `gh pr create --fill`,
   - they read their own diff in the browser and merge,
   - `git switch main`, `git pull`.

   Done when `uv run course check 00` shows three passes.
8. **Close.** Create `.course/progress.md` from `tutor/progress-template.md` and fill in the machine facts (system, RAM seen by Linux, data profile, GPU) and whatever was hard. Name the everyday commands (`/hint`, `/check`, `/explain`, `/quiz`, `/review`) and point to module 01.

## Fixes

| Doctor line | Fix |
|---|---|
| uv missing | `curl -LsSf https://astral.sh/uv/install.sh \| sh`, open a new shell, `uv sync` in the repository |
| Python is not 3.12 | The command was run with the system Python. Use `uv run ...` |
| Repo under `/mnt/` | Clone again under the Linux home (`~/mle-course`) and work there. File access on the Windows drive is many times slower |
| Memory below 6 GB | WSL gives Linux half of the machine's RAM. Raise it in `%UserProfile%\.wslconfig` (`[wsl2]`, `memory=12GB`), then `wsl --shutdown` in PowerShell. Otherwise the `small` profile works |
| git identity | `git config --global user.name "..."` and `user.email "..."`, the address of their GitHub account |
| Remote upstream | `git remote add upstream <course repository URL from README.md>` |
| Data missing | `uv run course data` (about 110 MB). On a checksum mismatch stop and report it: the source file changed, and working around it would put every learner on different data |
| `code` not found | VS Code is installed in Windows, not in Ubuntu, with the WSL extension (`ms-vscode-remote.remote-wsl`). Reopen the Ubuntu terminal after installing |
| `nvidia-smi` fails | The NVIDIA driver is installed in Windows only, version 580 or newer. A Linux NVIDIA driver inside WSL breaks GPU access: if one was installed, remove it |

GitHub login: install `gh` from the official apt repository (https://github.com/cli/cli/blob/trunk/docs/install_linux.md; Ubuntu's own package is outdated), then `gh auth login` with GitHub.com, HTTPS, "authenticate Git: yes", browser login.
