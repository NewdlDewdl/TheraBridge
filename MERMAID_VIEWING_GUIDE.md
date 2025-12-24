# How to View Mermaid Diagrams

The `COMPLETE_PIPELINE_FLOWCHART.md` contains 11 comprehensive Mermaid diagrams. Here's how to view them:

## Option 1: GitHub/GitLab (Recommended)
Simply push the file to GitHub or GitLab - Mermaid diagrams render automatically!

```bash
git add COMPLETE_PIPELINE_FLOWCHART.md
git commit -m "Add comprehensive Mermaid flowcharts"
git push
```

Then view on GitHub: https://github.com/your-repo/COMPLETE_PIPELINE_FLOWCHART.md

## Option 2: VS Code (Local Development)
1. Install the **Mermaid Preview** extension:
   - Extension ID: `bierner.markdown-mermaid`
2. Open `COMPLETE_PIPELINE_FLOWCHART.md`
3. Press `Cmd+Shift+V` (Mac) or `Ctrl+Shift+V` (Windows) for preview

## Option 3: Online Viewer
1. Go to https://mermaid.live
2. Copy any Mermaid code block from the document
3. Paste into the editor - diagram renders instantly
4. Export as PNG/SVG if needed

## Option 4: CLI Rendering (Generate Images)
Install Mermaid CLI and generate PNGs:

```bash
npm install -g @mermaid-js/mermaid-cli

# Extract and render all diagrams
mmdc -i COMPLETE_PIPELINE_FLOWCHART.md -o diagrams/
```

## Diagram Quick Reference

| Diagram | What It Shows | Best For |
|---------|---------------|----------|
| Graph TB | System architecture, data flow | Understanding overall pipeline |
| Sequence | Component interactions, API calls | Debugging integration issues |
| Flowchart | Service logic, decision trees | Understanding algorithms |
| Gantt | Timeline, parallel execution | Performance optimization |
| ERD | Database schema, relationships | Schema design, queries |

## Tips for Best Viewing Experience

- **GitHub Dark Mode:** Diagrams auto-adapt to dark theme
- **Zoom In:** Use browser zoom (Cmd/Ctrl +) for complex diagrams
- **Print:** Diagrams are print-friendly (use landscape for wide diagrams)
- **Export:** Use mermaid.live to export as SVG (scalable, vector graphics)

## Troubleshooting

**Diagram not rendering?**
- Check syntax: All diagrams start with ` ```mermaid ` and end with ` ``` `
- Verify indentation: Mermaid is whitespace-sensitive
- Test on mermaid.live: Copy diagram code to verify syntax

**Text too small?**
- Increase browser zoom
- Export to SVG and open in vector editor
- Use `%%{init: {'theme':'base', 'themeVariables': { 'fontSize':'16px'}}}%%` at diagram start

---

**Need help?** See Mermaid docs: https://mermaid.js.org/intro/
