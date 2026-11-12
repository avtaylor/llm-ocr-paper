Pink Card HTML-only app

What this version is:
- pure HTML, CSS, and JavaScript
- no Tauri, no Rust, no npm build required
- keeps the uploaded pink form unchanged in pink-form-original.html

How to run:
1. Open index.html in Chrome or Edge.
2. For best results, serve the folder with a simple local server instead of opening by file://
   Example if Python is installed:
   python3 -m http.server 8000
   then open http://localhost:8000
3. Use Select Folder to choose a working directory.
4. Select a 2-page PDF.
5. Open PDF Workspace, rotate if needed, and click Create Page Images.
6. Open Form to use the original pink card form.

Important browser note:
- Saving directly into a chosen folder uses the File System Access API.
- That works in Chromium-based browsers such as Chrome and Edge.
- In browsers without that API, files fall back to normal downloads.
