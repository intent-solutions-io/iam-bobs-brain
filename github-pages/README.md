# Bob's Brain - GitHub Pages Site

This directory contains the GitHub Pages site for Bob's Brain.

## Site URL

https://jeremylongshore.github.io/bobs-brain/

## Configuration

To enable GitHub Pages from this directory:

1. Go to repository Settings → Pages
2. Under "Source", select: **Deploy from a branch**
3. Under "Branch", select: **main** and **/docs**
4. Click **Save**

The site will be live at the URL above within a few minutes.

## Files

- `index.html` - Main page structure and content
- `style.css` - Grayscale professional stylesheet
- `README.md` - This file

## Design Notes

- **Palette:** Clean grayscale (no neon/glow effects)
- **Typography:** System sans-serif font stack
- **Responsive:** Mobile-first design with breakpoints
- **Accessibility:** Semantic HTML, sufficient contrast, keyboard navigation
- **Performance:** Static HTML/CSS only, no build tools required

## Updating Content

To update the site content:

1. Edit `index.html` for content changes
2. Edit `style.css` for styling changes
3. Commit and push to main branch
4. GitHub Pages will automatically rebuild

## Version Sync

The version badge is currently hardcoded to `v0.9.0`. When updating the VERSION file in the root, also update line 28 in `index.html`:

```html
<span class="badge badge-version">v0.9.0</span>
```

## Links Inventory

All links point to the current repository structure:

- **GitHub Repository:** https://github.com/jeremylongshore/iam-bob-adk
- **Documentation:** https://github.com/jeremylongshore/iam-bob-adk/tree/main/000-docs
- **README:** https://github.com/jeremylongshore/iam-bob-adk/blob/main/README.md
- **CLAUDE.md:** https://github.com/jeremylongshore/iam-bob-adk/blob/main/CLAUDE.md
- **CHANGELOG:** https://github.com/jeremylongshore/iam-bob-adk/blob/main/CHANGELOG.md
- **DevOps Playbook:** https://github.com/jeremylongshore/iam-bob-adk/blob/main/000-docs/120-AA-AUDT-appaudit-devops-playbook.md
- **LIVE3 Guide:** https://github.com/jeremylongshore/iam-bob-adk/blob/main/000-docs/121-DR-GUIDE-live3-dev-smoke-test.md
- **Issues:** https://github.com/jeremylongshore/iam-bob-adk/issues
- **License:** https://github.com/jeremylongshore/iam-bob-adk/blob/main/LICENSE
- **Intent Solutions:** https://intentsolutions.io
- **Google ADK:** https://cloud.google.com/vertex-ai/docs/agent-development-kit
- **Vertex AI Agent Engine:** https://cloud.google.com/vertex-ai/docs/agent-engine

All links verified as of 2025-11-20.
