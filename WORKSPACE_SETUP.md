# AWC login setup

Deploy `app.py` from the `master` branch on Streamlit Cloud using Python 3.12. Add the following keys under Settings → Secrets (syntax is in `secrets.example.toml`):

- `ADMIN_USERNAME`: your administrator ID.
- `ADMIN_PASSWORD`: your private password, at least 12 characters.
- `DATABASE_URL`: a persistent PostgreSQL connection string.

You may reuse the three private values configured for your Stock-Planning app. Never commit real passwords or the connection string. The AWC app uses `awc_accounts` and `awc_datasets`, keeping its accounts separate from your other apps. Accounts persist when Streamlit sleeps or restarts. SQLite URLs are for local tests only.

Reboot, sign in, and turn on **Manage users** in the sidebar. The administrator can create viewers, reset passwords, and disable/enable accounts. Viewers cannot manage users. Both account types can use the existing AWC clinical, caregiver, image-analysis, comparison and documentation workspaces. The image uploader is part of the existing analysis workflow and remains available to signed-in users; this update does not introduce a shared dataset upload feature.

All AWC views are behind the login gate. Passwords use salted PBKDF2 hashes; repeated failures temporarily lock accounts, and password resets/disabled accounts revoke existing sessions. Sessions expire after 30 minutes without server interaction or eight hours overall. Sign out clears the active session and its assessment state. No default login or public self-registration is enabled. The account login is separate from existing clinician practice fields.

Run `python -m pytest tests` to validate the existing core rules and new account/UI tests. Live deployment still requires your database and Secrets.

Validation for this login update: all 9 account and UI tests pass, including access to every existing workspace. The broader existing suite has an unrelated failure in `test_deep_cavity_wound_triggers_cavity_filler` (expected secondary cover is absent). A missing `Optional` typing import was fixed so those modules can load; recommendation behavior was not changed.
