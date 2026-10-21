# Daniel Mason Pinterest Publisher

OAuth connection preparation for **@danielmason77**, using approved app **1622682**.

Start with [OAUTH_SETUP.md](OAUTH_SETUP.md). On Windows, download and extract this repository, then run **connect-windows.cmd** with Python 3.10 or newer installed.

Status: helper implemented and unit-tested; live OAuth authorization is pending. The existing GitHub token check has returned HTTP 401. No posting scheduler is active. Public publishing requires Standard access approval; Trial Pins and boards are creator-only.

Never commit app secrets or tokens. The local credentials file is excluded by `.gitignore`.
