# Common Setup Issues

The top issues physicians and clinical researchers run into during MedSci Skills setup, with copy-paste fixes.

---

## 1. `python` runs Python 2 instead of Python 3

**Symptom**: `python --version` shows `Python 2.7.x`.

**Cause**: macOS and some old Windows installs default `python` to version 2.

**Fix**: Use `python3` explicitly.
```bash
python3 --version   # should show 3.11.x
```
If `python3` also shows 2.x, your PATH is misconfigured. On Mac, ensure pyenv is initialized in `~/.zshrc` (see [`mac.md`](mac.md) Step 2). On Windows, reinstall via winget and reopen PowerShell.

---

## 2. `command not found: claude` (or `python3`, `Rscript`, `node`)

**Cause**: PATH not refreshed after install.

**Fix**: Close and reopen Terminal (Mac) or PowerShell (Windows). If it still fails:

**Mac**:
```bash
echo 'export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"' >> ~/.zshrc
exec zsh
```

**Windows**: Sign out and sign back in to your user account, or restart the computer.

---

## 3. Apple Silicon (M1/M2/M3/M4) Rosetta confusion

**Symptom**: Some Python packages fail to compile, or you see "wrong architecture" errors.

**Cause**: Mixing arm64 (Apple Silicon native) and x86_64 (Intel via Rosetta) installs.

**Fix**: Stay native arm64. Verify Homebrew is in `/opt/homebrew` (not `/usr/local`):
```bash
which brew
```
Expected: `/opt/homebrew/bin/brew` on Apple Silicon.

If you see `/usr/local/bin/brew`, you have the Intel Homebrew. Uninstall it and reinstall with the native arm64 installer.

---

## 4. Antivirus / SmartScreen blocks the installer (Windows)

**Symptom**: Windows Defender SmartScreen warns "Windows protected your PC" when running `install-windows.cmd`.

**Cause**: The `.cmd` file is unsigned (we don't pay for code-signing certificates). The script is open-source and you can read it before running.

**Fix**: Click **More info** → **Run anyway**. Or run from PowerShell:
```powershell
.\installers\install-windows.cmd
```

---

## 5. `git clone` fails with SSL certificate error

**Cause**: Hospital network proxies often intercept HTTPS, breaking certificate validation.

**Fix**: Use SSH instead:
```bash
git clone git@github.com:Aperivue/medsci-skills.git
```
(Requires you to add an SSH key at <https://github.com/settings/keys>.)

Or temporarily disable verification (not recommended for security):
```bash
git -c http.sslVerify=false clone https://github.com/Aperivue/medsci-skills.git
```

---

## 6. `claude mcp add` writes JSON with syntax errors

**Symptom**: `claude mcp list` doesn't show the server you just added.

**Cause**: A previous `claude mcp add` failed mid-way and left malformed JSON in `~/.claude.json` (Mac/Linux) or `%APPDATA%\Claude\claude.json` (Windows).

**Fix**:
1. Open `~/.claude.json` in a text editor.
2. Look for `"mcpServers": { ... }` — verify it's valid JSON (matched braces, commas between entries, no trailing commas).
3. If broken, paste it into <https://jsonlint.com/> to find the error.
4. Fix and save.
5. Try `claude mcp add ...` again.

---

## 7. R package install fails: "Cannot find compiler"

**Symptom**: `install.packages("metafor")` (or similar) fails with `xcrun: error: invalid active developer path`.

**Mac fix**: Install Xcode Command Line Tools (one-time):
```bash
xcode-select --install
```
Click "Install" in the popup; takes 10-20 minutes.

**Windows fix**: Install Rtools (matched to your R version):
- R 4.4: <https://cran.r-project.org/bin/windows/Rtools/rtools44/>
- Run the installer, default options.

---

## 8. Demo 1 stalls when running `/orchestrate --e2e`

**Possible causes**:

| Symptom | Likely cause | Fix |
|---|---|---|
| "API rate limit exceeded" | Free Anthropic plan or hit daily quota | Wait an hour or upgrade |
| Stuck at "loading scikit-learn" | Python venv not active | Run `python3 -c "import sklearn"` to confirm install |
| Stuck at "rendering figures" | matplotlib backend issue | Run `python3 -c "import matplotlib; matplotlib.use('Agg')"` |
| Stuck at "writing draft" | Network proxy blocking Anthropic API | Test with `curl https://api.anthropic.com` |

---

## 9. Zotero MCP shows "Disconnected"

**Cause**: Zotero desktop isn't running, OR the API key was revoked, OR `ZOTERO_LOCAL=true` is set but Zotero isn't running locally.

**Fix sequence**:
1. Open Zotero desktop. Wait for sync to finish.
2. Re-verify API key at <https://www.zotero.org/settings/keys> (regenerate if unsure).
3. Re-run `claude mcp add zotero ...` with `--force` to overwrite.
4. `claude mcp list` to verify ✓.

---

## 10. OneDrive sync conflicts with the cloned repo (Windows)

**Symptom**: Files appear and disappear, or scripts fail with "file locked."

**Cause**: OneDrive auto-sync is constantly touching the files Claude Code is reading.

**Fix**: Move the repo out of OneDrive-tracked folders:
```powershell
# Don't put it in Documents (synced)
git clone https://github.com/Aperivue/medsci-skills.git C:\medsci-skills
```

Or in OneDrive settings, exclude the `medsci-skills` folder from sync.

---

## Still Stuck?

1. Run `/setup-medsci` inside Claude Code — it prints a diagnostic checklist with the specific failure point.
2. Open an issue at <https://github.com/Aperivue/medsci-skills/issues> with:
   - Your OS (Mac/Windows/Linux + version)
   - Output of `/setup-medsci`
   - The exact error message
3. We respond within 1-3 days.
