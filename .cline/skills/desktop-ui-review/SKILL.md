---
name: desktop-ui-review
description: Review and improve desktop-only Flask UI pages using Playwright MCP. Use when asked to inspect, screenshot, test, or refine a page running at http://127.0.0.1:5000.
---

# Desktop UI Review

Follow this workflow:

1. Confirm the target page URL.
2. Confirm which frontend files are allowed to be edited.
3. Use Playwright MCP with a desktop viewport of 1440x900.
4. Save screenshots only in `.playwright-artifacts/`.
5. Before editing, inspect:
   - page loading;
   - visible layout;
   - horizontal overflow;
   - console errors;
   - failed network requests;
   - broken images;
   - spacing, alignment, readability and visual consistency.
6. Preserve the existing design direction. Do not redesign from scratch unless explicitly requested.
7. Never submit forms or enter real credentials unless explicitly requested.
8. Never modify backend code, routes, database, migrations, uploads, dependencies or Git history.
9. Modify only the explicitly allowed files.
10. After each edit, reopen the page and repeat the inspection.
11. Perform no more than 3 edit-test iterations.
12. Stop early when no meaningful problems remain.
13. If an error cannot be fixed safely, stop and report it instead of guessing.
14. Never commit or push automatically.

Final report must include:
- issues found;
- changes made;
- actual diff;
- exact files changed;
- screenshot paths;
- console and network results;
- number of iterations;
- confirmation that backend, database and Git history were untouched.