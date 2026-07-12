# OWASP Cheat Sheet Knowledge Base

## SQL Injection Prevention
Source: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html

Use parameterized queries and prepared statements for all database access. Never concatenate untrusted input into SQL statements. Validate input against a strict allow-list when a fixed set of values is expected. Limit database permissions for application accounts so a compromise has reduced impact.

## Hardcoded Secrets
Source: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html

Do not hardcode API keys, passwords, tokens, or private keys in source code. Store secrets in environment variables, a secrets manager, or a secure configuration mechanism. Rotate credentials regularly and audit where secrets are used.

## Cross-Site Scripting Prevention
Source: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html

Encode output for the correct context, especially HTML, JavaScript, and URLs. Use context-aware escaping instead of trying to blacklist dangerous characters. Prefer frameworks that provide automatic output encoding.
