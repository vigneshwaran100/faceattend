# Contributing to FaceAttend

Thank you for contributing to FaceAttend! We welcome contributions that improve features, documentation, security, and stability.

---

## 1. Code of Conduct
Please be respectful, constructive, and collaborative in all discussions, issues, and pull requests.

---

## 2. Conventional Commit Standards

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for structured, readable Git commit histories:

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types
- `feat`: A new feature or capability (e.g., `feat(api): add multi-frame face validation`)
- `fix`: A bug fix (e.g., `fix(kiosk): resolve frame drop during rapid scanner events`)
- `docs`: Documentation changes only (e.g., `docs: update architecture and api guides`)
- `test`: Adding or correcting tests (e.g., `test(attendance): add test for holiday shift calculation`)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Code change that improves performance
- `ci`: Changes to CI/CD workflows and configuration files
- `chore`: Maintenance tasks, dependency bumps, or tool updates

---

## 3. Development & Branching Workflow

1. Create a descriptive branch from `main`:
   - Features: `feature/kiosk-lighting-enhancement`
   - Bugfixes: `bugfix/attendance-eod-duplicate-key`
2. Install dependencies:
   - Backend: `uv sync`
   - Frontend: `cd frontend && npm install`
3. Run tests locally and verify 100% pass rate:
   - Backend: `uv run pytest`
   - Frontend: `cd frontend && npm run build`
4. Submit a Pull Request targeting `main`.

---

## 4. Main Branch Protection Recommendations

For production GitHub repositories, configure the following branch protection rules for `main`:
1. **Require pull request before merging**: Enforce code review by at least one approver.
2. **Require status checks to pass before merging**:
   - `Backend CI / Pytest & Validation`
   - `Frontend CI / TypeScript & Production Build`
   - `CodeQL Analysis`
3. **Require linear history**: Prevent merge commits (use Squash & Merge or Rebase).
4. **Require signed commits**: Ensure commit integrity.
5. **Do not allow force pushes or deletions** on `main`.
