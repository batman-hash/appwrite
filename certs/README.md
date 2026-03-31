# SSL Certificates

Place your HTTPS certificate files in this folder.

Recommended file names:

- `server.crt`
- `server.key`

Suggested environment values:

- `SSL_CERT_FILE=certs/server.crt`
- `SSL_KEY_FILE=certs/server.key`
- `HTTPS_ENABLED=true`

These files are intentionally not committed to git.
The Flask launcher and Docker entrypoint will automatically use them when they are present.
