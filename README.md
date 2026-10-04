# Psychometric trainer

Private app for the owner’s personal use only. No other person has permission to use, copy or redistribute this app. Availability at an Internet address grants no permission. Original exam-content rights remain with their respective owners.

A static Hebrew-interface trainer with separate **math, Hebrew, and English** modes. It presents a random original question image, accepts answers 1–4, checks against the official key, and removes correctly answered questions from subsequent sessions.

## Data and grading

The app includes 8,532 gradable questions from 69 official Hebrew exam sittings, 2011–2026: 2,819 math, 3,286 Hebrew, 2,427 English. Campus simulations and the two unscored questions are excluded. Original images preserve mathematics, bold text, missing-word lines, diagrams and reading passages. Shared instructions and the full section are available alongside each question.

`site/data/catalog.json` indexes questions. `site/data/exams/<exam>.json` stores each question's image references, shared contexts, salt and answer digest. The build reads the private official answer keys from the parent question bank and computes SHA-256 of `question-id:answer-number:salt`. On submission the browser calculates the selected answer's digest and compares it to the stored digest. Exactly one answer, 1–4, matches. Private database files and answer-key page images are excluded from the site. As with any static app, a determined user can derive the answer from these four possible values; this is a personal practice app.

Correct answers and attempt counts are stored in localStorage, scoped to the site path. Progress persists in the same browser/device. Use **ההתקדמות שלי** to export/import a JSON backup across devices or between local and deployed sites, or confirm a reset. Clearing browser data clears progress. No account or cross-device server storage is used.

## Structure

- `src/`: HTML, CSS and JavaScript source.
- `scripts/build.py`: packages the verified parent question bank into the static site; requires the packages in `scripts/requirements-builder.txt` and the original local question bank.
- `site/`: complete deployable site, including exam shards, question images and context crops. Checked into Git so deployment doesn't require the private source database.
- `tests/`: automated logic, all-question asset/grading checks, browser integration tests.
- `.github/workflows/pages.yml`: tests and publishes `site/` to GitHub Pages.
- `reports/`: ignored local verification reports and screenshots.

## Run locally

```sh
npm test
npm run serve
```

Open http://127.0.0.1:8787/. No frontend dependencies or build server are needed. Rebuild from the source bank with a Python interpreter with the builder dependencies: `python3 scripts/build.py`.

Browser test: `node tests/browser.cjs` (set `PLAYWRIGHT_PATH` to an installed Playwright package if using another computer; uses installed macOS Google Chrome). Set `APP_URL` to test the deployed site. The exhaustive data test checks all 8,532 questions, 34,128 answer choices, context references and image existence.

## Hosting

This repository publishes a static site using GitHub Pages. All asset paths work under a repository URL prefix. Browser storage belongs to each origin; export/import a backup to carry local progress to GitHub. The site contains original educational exam material; rights remain with its owners.

## iPhone simulator verification

The simulator suite uses the real iOS WebKit engine in a minimal WKWebView host and genuine XCTest screen taps. Safari WebDriver's scrolling-coordinate errors and its native-input lock prevent combining its inspection session with native taps reliably. The test host runs exactly the same static app; it is only a testing tool.

Run `bash scripts/test-iphone.sh` with Xcode installed and the local site running. Set `SIMULATOR_UDID` for another installed simulator and `APP_URL` for the deployed website. The tests check correct/incorrect grading, touch answer selection, retirement after reload, all three modes, zoom, settings/reset cancellation and horizontal overflow. Chrome tests also cover backup/import, completion and network/storage failures. Test reports and screenshots are saved locally in `reports/`.

The local and GitHub Pages versions have been verified in Chrome and on an iPhone SE simulator with iOS 18.2 WebKit and native XCTest taps. All 8,532 grading digests were checked against the original official answer keys, and the GitHub workflow validates every packaged question and image reference.

Search-indexing directives (`noindex`, `nofollow`, `noarchive`) discourage crawler discovery of the website. They do not provide access control or guarantee that a public site or repository cannot be discovered. Repository privacy and website access restrictions must be configured separately.

## Image readability

Questions, passages and diagrams use the available screen width, with small phone gutters and safe-area padding. Each image has inline **+**, **−** and **fit-to-width** controls. Enlarged images pan horizontally within their own container; the surrounding page stays within the screen. Click an image to open its complete original in the zoom dialog.

`site/data/image-crops.json` contains reversible viewport coordinates computed by `scripts/crop-metadata.py`. Original images and answer keys are unchanged. The crop generator recognizes repeated page-edge decorations, retains all other source PDF text/drawing/image bounds with padding, and checks remaining raster ink. Ambiguous margins stay visible. Vertical content is never trimmed. It verified 11,070 image viewports across 3,044 source pages. If optional crop metadata cannot load, the app displays the original images.

Install builder dependencies using `python3 -m pip install -r scripts/requirements-builder.txt`. `scripts/build.py` regenerates crop metadata after packaging the source bank. `node tests/readability.cjs` checks desktop and phone widths, inline zoom/fit, original-image access and crop-data network fallback. The iPhone test also performs a native horizontal swipe on an enlarged question.
