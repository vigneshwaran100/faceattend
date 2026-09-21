# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

---

## Reporting a Vulnerability

We take the security of FaceAttend seriously. If you believe you have found a security vulnerability, please follow responsible disclosure guidelines.

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security issues privately by emailing the maintainers or creating a private advisory under the GitHub Security Advisories tab.

### What to Include in Your Report
To help us triage and resolve the issue quickly, please provide:
- A description of the vulnerability and its potential impact.
- Clear steps to reproduce the issue (proof-of-concept script, curl commands, or screenshots).
- Any affected components, endpoints, or dependencies.

### Response Timeline
- **Initial Acknowledgement**: Within 48 hours.
- **Triage & Assessment**: Within 5 business days.
- **Fix & Disclosure**: Coordinated release schedule with credit to the reporter.

---

## Secret Scanning & Key Rotation Guidance

FaceAttend requires handling sensitive credentials including database passwords, JWT secrets, and third-party API keys:
1. **Never commit `.env` or credential files**: Keep `.env` listed in `.gitignore`.
2. **Key Rotation**: If any secret (such as database credentials, JWT secret keys, or external AI API keys) is suspected to have been exposed, **rotate and revoke it immediately in the respective cloud/service console**.
3. **Automated Secret Scanning**: GitHub Secret Scanning and Push Protection should be kept enabled on the repository.
