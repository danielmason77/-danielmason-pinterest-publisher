# Daniel Mason Pinterest connection

Target profile: **@danielmason77**. Approved app: **1622682**.

The app is administered by a different Daniel Mason Pinterest login. That is separate
from the profile granting permission through OAuth. Do not replace or recreate the app.

## One-time setup on Windows

1. Download this repository as a ZIP (**Code > Download ZIP**) and extract it.
2. Ensure Python 3.10 or newer is installed from https://www.python.org/downloads/.
3. Using the login that owns app 1622682, open its Configure page:
   https://developers.pinterest.com/apps/1622682/
4. Add this exact **Redirect URI**, including the final slash:

   `http://localhost:8765/`

5. Double-click **connect-windows.cmd** in the extracted folder. Alternatively run
   `python connect_pinterest.py` in that folder.
6. When prompted locally, paste the **App secret key** for app 1622682. The program
   hides it and sends it only to Pinterest's HTTPS token endpoint. Do not put it in chat,
   a GitHub file, a screenshot, or a command-line argument.
7. In the browser opened by the program, select **@danielmason77** and review the
   permissions. Authorize the app only when that profile is selected. If the wrong
   profile is selected, cancel and switch accounts before running the program again.
8. The local callback exchanges the code, checks all requested scopes, and calls
   Pinterest to verify the username. It refuses to save a different account.
9. On success it saves `.pinterest_credentials.json` in this folder. This private file
   contains the access and refresh tokens; the app secret is not saved. It is excluded
   by `.gitignore`. Never upload the file to GitHub or share it in chat.
10. Copy only the `access_token` value (without JSON quotes) into the repository's
    Actions secret **PINTEREST_ACCESS_TOKEN**, using GitHub's secret form. Retain the
    refresh token privately for the future renewal setup. This program does not
    automatically upload credentials to GitHub or configure recurring refresh.

GitHub secret form:
https://github.com/danielmason77/-danielmason-pinterest-publisher/settings/secrets/actions

Then run **Pinterest connection check** from Actions and confirm successful reads.
The existing check validates read access only; the local program also checks identity
and the `pins:write` grant in the OAuth response. No publishing occurs in either check.

## Requested permissions

- `user_accounts:read`: verify the selected account.
- `boards:read`: select a destination board.
- `pins:read`: inspect created Pins during future reconciliation.
- `pins:write`: create Pins after explicit selection and authorization.

No ads, billing, private-board, or account-edit permissions are requested.

## Trial access and next stage

Trial access creates Pins and boards visible only to their creator. It does not enable
public promotional posting. Public publishing requires Standard access approval.
This repository currently implements connection and read-only checks, not a scheduler.
After a successful connection, prepare a working publishing demo with one selected
test Pin and submit the Standard-access review with the required video.

The callback listens only on the local computer, validates a random OAuth state, ignores
unmatched callbacks, and stops after one authorization or a ten-minute timeout. Nothing
is published and no private API response body is logged. A previous credentials file
is never overwritten; move it securely if reconnecting is necessary.

## Validation

`python -m unittest -v test_connection.py`

Tests cover callback path/state validation, duplicate parameters, wrong-profile rejection,
missing permissions, and the authorization URL. They do not substitute for live OAuth.

Official references:
- https://developers.pinterest.com/docs/getting-started/set-up-authentication-and-authorization/
- https://developers.pinterest.com/docs/key-concepts/access-tiers/
