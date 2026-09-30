# Classroom / Workshop Distribution

Read this when the package is intended for a workshop or classroom.

## Direct-download ZIPs (Phase 5)

Prepare direct-download ZIPs rather than asking users to navigate GitHub manually:

```text
https://github.com/{owner}/{repo}/releases/latest/download/{package}-classroom-windows.zip
https://github.com/{owner}/{repo}/releases/latest/download/{package}-classroom-macos.zip
```

## After the commit (Phase 6)

Create or update the GitHub Release ZIP assets and test the direct download links.

## Classroom Package Checklist

- [ ] Full skill set is installed once; lesson tasks use only 1-2 skills at a time
- [ ] Windows ZIP includes `installers/install-windows.cmd`
- [ ] macOS ZIP includes `installers/install-macos.command`
- [ ] `README_FIRST.md` explains unzip -> double-click -> restart -> test prompt
- [ ] Email announcement uses direct GitHub Release download links
- [ ] WSL is documented as an advanced option, not a default requirement
- [ ] First prompts avoid full end-to-end orchestration
