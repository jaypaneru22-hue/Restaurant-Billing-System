# GitHub Version Control & Milestone Workflow Guide

- **Project:** Restaurant Billing System
- **Subject:** BBAT104 — Fundamentals of Total Quality Management
- **Student Name:** Jay Paneru
- **Registration Number:** 2410302024
- **Assigned Quality Goal:** Q08 — Improve User Satisfaction
- **Repository URL:** https://github.com/jaypaneru22-hue/Restaurant-Billing-System.git
- **Document Version:** 1.0.0

---

## 1. Version Control Strategy

Git and GitHub serve as primary Total Quality Management artifacts for this project, providing an auditable, verifiable timeline of engineering milestones, defect fixes, tests, and architectural evolutions.

### 1.1 Strict Commit Disciplines
1. **Incremental Milestone Commits:** Code is committed and pushed after every verified functional module, test suite pass, or TQM deliverable. Massive, disconnected end-of-project bulk uploads are strictly prohibited.
2. **Conventional Commit Standard:** Commit messages follow conventional semantic prefixes:
   - `feat:` New user-facing or architectural functionality (e.g. `feat: implement visual report service`).
   - `fix:` Defect resolution identified during quality control (e.g. `fix: adjust validate_discount parameter signature`).
   - `test:` Automated test additions or QA checksheet logs (e.g. `test: add defect checksheet`).
   - `docs:` Formal software engineering specifications or TQM reports (e.g. `docs: add SRS.md`).
   - `chore:` Project dependencies, configuration, or environment setup.
3. **No Secrets or Binary Clutter:** Virtual environments (`.venv/`), database files (`*.db`), bytecode caches (`__pycache__/`), and logs are strictly ignored via `.gitignore`.
4. **Verified Push Policy:** Every local commit is pushed to `origin main` and verified through remote Git status and hash validation.

---

## 2. Standard Feature & Defect Development Cycle

```mermaid
flowchart TD
    A["1. Identify Requirement or Quality Defect"] --> B["2. Implement Modular Code or Bugfix"]
    B --> C["3. Run Automated Pytest Suite"]
    C --> D{"Tests Passing (100%)?"}
    D -- No --> E["Debug, Fix Code & Log in quality/defects.csv"]
    E --> C
    D -- Yes --> F["4. Review Working Tree (git diff & git status)"]
    F --> G["5. Stage Specific Files (git add)"]
    G --> H["6. Create Semantic Commit (git commit)"]
    H --> I["7. Push to GitHub Remote (git push origin main)"]
    I --> J["8. Verify Remote Status & Log in docs/COMMIT_TRACKER.md"]
```

---

## 3. Commit Tracker Maintenance

Every commit hash, message, scope, timestamp, and remote push status is recorded in [docs/COMMIT_TRACKER.md](COMMIT_TRACKER.md). This ensures complete academic traceability for college viva examinations.
