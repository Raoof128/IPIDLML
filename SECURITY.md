# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of IPI-Shield seriously. If you believe you have found a security vulnerability in this project, please report it to us as described below.

### **Do NOT open a public issue on GitHub.**

### Reporting Process

1.  **Email**: Send a detailed description of the vulnerability to [security@ipi-shield.dev](mailto:security@ipi-shield.dev).
2.  **Encryption**: If possible, encrypt your message using our PGP key (ID: `0xDEADBEEF`).
3.  **Details**: Include as much information as possible:
    *   Type of vulnerability (e.g., XSS, Injection, RCE)
    *   Affected versions
    *   Steps to reproduce (PoC code is highly appreciated)
    *   Potential impact

### Response Timeline

*   **Acknowledgment**: We will acknowledge your report within 24 hours.
*   **Assessment**: We will assess the severity and impact within 3 days.
*   **Fix**: We aim to release a fix for critical vulnerabilities within 7 days.
*   **Disclosure**: We will coordinate public disclosure with you once the fix is released.

### Safe Harbor

We support safe harbor for security researchers. We will not pursue legal action against researchers who:

*   Report vulnerabilities to us in good faith.
*   Do not exploit the vulnerability for malicious purposes.
*   Do not access or modify user data without permission.
*   Give us reasonable time to fix the issue before public disclosure.

## Threat Model

Please refer to [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) for our detailed threat model and known limitations. Note that IPI-Shield is a defense-in-depth layer and should not be relied upon as the sole security mechanism for LLM applications.
