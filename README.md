# Psychometric trainer

A static Hebrew-interface trainer with separate **math, Hebrew, and English** modes. It presents a random original question image, accepts answers 1–4, checks against the official key, and removes correctly answered questions from subsequent sessions.

## Data and grading

The app includes 8,532 gradable questions from 69 official Hebrew exam sittings, 2011–2026: 2,819 math, 3,286 Hebrew, 2,427 English. Campus simulations and the two unscored questions are excluded. Original images preserve mathematics, bold text, missing-word lines, diagrams and reading passages. Shared instructions and the full section are available alongside each question.

`site/data/catalog.json` indexes questions. `site/data/exams/<exam>.json` stores each question's image references, shared contexts, salt and answer digest. The build reads the private official answer keys from the parent question bank and computes SHA-256 of `question-id:answer-number:salt`. On submission the browser calculates the selected answer's digest and compares it to the stored digest. Exactly one answer, 1–4, matches. Private database files and answer-key page images are excluded from the site. As with any static app, a determined user can derive the answer from these four possible values; this is a personal practice app.

Correct answers and attempt counts are stored in localStorage, scoped to the site path. Progress persists in the same browser/device. Use **ההתקדמות שלי** to export/import a JSON backup across devices or between local and deployed sites, or confirm a reset. Clearing browser data clears progress. No account or cross-device server storage is used.

## Structure

- `src/`: HTML, CSS and JavaScript source.
- `scripts/build.py`: packages the verified parent question bank into the static site; requires Pillow and the original local question bank.
- `site/`: complete deployable site, including exam shards, question images and context crops. Checked into Git so deployment doesn't require the private source database.
- `tests/`: automated logic, all-question asset/grading checks, browser integration tests.
- `.github/workflows/pages.yml`: tests and publishes `site/` to GitHub Pages.
- `reports/`: ignored local verification reports and screenshots.

## Run locally

```sh
npm test
npm run serve
```

Open http://127.0.0.1:8787/. No frontend dependencies or build server are needed. Rebuild from the source bank with a Python interpreter that has Pillow: `python3 scripts/build.py`.

Browser test: `node tests/browser.cjs` (set `PLAYWRIGHT_PATH` to an installed Playwright package if using another computer; uses installed macOS Google Chrome). Set `APP_URL` to test the deployed site. The exhaustive data test checks all 8,532 questions, 34,128 answer choices, context references and image existence.

## Hosting

This repository publishes a static site using GitHub Pages. All asset paths work under a repository URL prefix. Browser storage belongs to each origin; export/import a backup to carry local progress to GitHub. The site contains original educational exam material; rights remain with its owners.
