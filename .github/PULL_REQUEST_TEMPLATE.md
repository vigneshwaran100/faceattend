## Description

Provide a clear description of the changes introduced in this PR and why they are needed.

Fixes #(issue)

---

## Type of Change

- [ ] `feat`: New feature (non-breaking change which adds functionality)
- [ ] `fix`: Bug fix (non-breaking change which fixes an issue)
- [ ] `refactor`: Code refactor (no behavioral changes)
- [ ] `perf`: Performance improvement
- [ ] `docs`: Documentation update
- [ ] `test`: New or updated tests
- [ ] `ci`: CI/CD workflow updates

---

## Verification & Checklist

- [ ] My code follows the code style and guidelines of this project.
- [ ] I have run `uv run pytest` and all tests pass cleanly.
- [ ] If frontend code changed, I have run `npm run build` in `frontend/` without errors.
- [ ] If database models changed, new Alembic migration revisions are included.
- [ ] I have updated relevant documentation (`docs/`, `README.md`).
- [ ] No secrets, `.env` files, or credentials are included in this PR.
