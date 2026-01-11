# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities
2. Email the maintainer directly at: [your-email@example.com]
3. Include a detailed description of the vulnerability
4. Provide steps to reproduce if possible

You can expect:
- Acknowledgment within 48 hours
- Status update within 7 days
- Fix timeline based on severity

## Security Measures

This scraper implements several security measures:

### Input Validation
- URL scheme validation (http/https only)
- Domain validation
- Private/internal IP blocking (localhost, 127.0.0.1, private ranges)
- Configuration parameter validation

### Output Safety
- CSV injection prevention (sanitizes dangerous characters)
- Path traversal prevention in output directories

### Rate Limiting
- Configurable request delays
- Respects server rate limits (429 responses)
- Exponential backoff with jitter

## Responsible Use

This tool is intended for legitimate purposes such as:
- Collecting data from your own websites
- Research with proper authorization
- SEO auditing
- Building training datasets from public content

Please ensure you have permission to scrape any website and respect:
- robots.txt directives
- Terms of service
- Rate limits
- Copyright and data protection laws

## Known Limitations

- Does not currently parse robots.txt (planned for future release)
- No built-in authentication support
