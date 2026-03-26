# TODO: Fix Render Deployment - ModuleNotFoundError: No module named 'accounts'

## Plan Steps:
- [x] Step 1: Edit shopzone/ecomm/settings.py to use explicit app labels ('shopzone.accounts', etc.) in INSTALLED_APPS
- [x] Step 2: Local settings check passed (no errors from Django check)
- [ ] Step 3: Commit and push to trigger Render redeploy
- [ ] Step 4: Verify deployment success on Render
