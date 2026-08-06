# Pending Tasks
All critical MVP issues have been resolved.

## ~~1. Improve Section Classification~~ (Completed)
**Issue:** The classification of ingested paper sections (e.g., introduction, dataset, architecture) is inaccurate and presents random data.
**Goal:** Improve the heuristics or model used to parse the PDF and classify sections accurately so that the system correctly identifies Introduction, Methodology, Datasets, Results, etc.
**Resolution:** Re-wrote `extract_sections` in `PaperProcessor` to capture all text and safely group unrecognized headings rather than throwing away 90% of the paper's text.

## ~~2. Fix Search Confidence Scores~~ (Completed)
**Issue:** The search system responds with any text from the paper with 100% confidence.
**Goal:** Adjust the retrieval logic (e.g., cosine similarity scoring) to properly normalize and reflect the actual semantic distance, ensuring that only highly relevant matches receive high confidence scores.
**Resolution:** Updated `MemoryBuilder` to use an absolute cosine similarity threshold rather than relative min/max scaling that forced at least one 100% score per query.

## ~~3. Persist User Data Across Sessions~~ (Completed)
**Issue:** User activity is not persisted. If the server restarts or the user logs out and logs back in, data is lost and starts from 0.
**Goal:** Replace or augment the `InMemoryWorkspaceStore` to persist its state to the disk (e.g., SQLite or a JSON file) so that users, papers, and processing events survive server reloads and session changes.
**Resolution:** Wrapped mutating methods in `store.py` with `@auto_save` and implemented a disk-backed JSON store. Fixed an issue where the missing `dateutil` dependency caused silent load failures.
