# Cloudflare Pages + Firebase Setup Checklist

## Naming

- Cloudflare Pages project name: `baakbook` if available.
- Expected production address: `https://baakbook.pages.dev`.
- The Pages subdomain must be checked during project creation; if the name is already reserved, stop and choose an approved alternative rather than silently changing the public address.
- Firebase staging project: `baak-books-staging` or an approved equivalent.
- Firebase production project: a separate approved project, never the staging project.

## Cloudflare Pages configuration

| Setting | Value |
|---|---|
| Source | The selected GitHub repository after the local migration branch is reviewed |
| Build command | To be finalized after frontend adapter migration; do not assume Flask can run on Pages |
| Output directory | To be finalized (`frontend` for a no-build static pass, or the bundler output for the final pass) |
| Production branch | `main` only after the user explicitly authorizes a push |
| Production URL | `https://baakbook.pages.dev` |
| Preview deployments | Enabled for review; not customer-facing |

Cloudflare Pages must not receive `data.json`, service-account files, ImgBB keys, or any admin secret. Browser-visible Firebase Web SDK configuration is not a secret, but it is not an authorization mechanism.

## Firebase configuration

Create separate staging and production projects. Enable only the services required for the current migration:

1. Cloud Firestore.
2. Firebase Authentication for the admin identity provider.
3. Cloud Functions 2nd gen.
4. Emulator Suite for local tests where available.

Before deploying Functions, verify the billing and region prerequisites shown by Firebase for the selected project. Do not upgrade or enable paid services without the user’s explicit authorization.

## Authentication

Create the administrator account in the production project only after the Rules and Functions have been tested in staging. Grant the `admin=true` custom claim from a controlled administrative script or Firebase Admin environment, not from the browser. Record the account identifier in the cutover log without recording a password.

## Secrets and variables

### Cloudflare Pages public variables

- `VITE_FIREBASE_API_KEY` — browser SDK configuration, public but environment-specific.
- `VITE_FIREBASE_AUTH_DOMAIN` — browser SDK configuration.
- `VITE_FIREBASE_PROJECT_ID` — staging or production project ID.
- `VITE_FIREBASE_STORAGE_BUCKET` — only if Storage is used later.
- `VITE_FIREBASE_MESSAGING_SENDER_ID` — browser SDK configuration.
- `VITE_FIREBASE_APP_ID` — browser SDK configuration.

### Functions secrets

- Firebase Admin runtime identity, supplied by the platform rather than committed files.
- `IMGBB_API_KEY` — only when the image upload Function is implemented.
- Notification provider secrets, if notifications are added later.

### Migration operator environment

- `FIREBASE_PROJECT_ID`.
- A short-lived service-account credential supplied outside Git.
- `MIGRATION_BATCH_ID`.
- `SOURCE_EXPORT_PATH`.

Never place any of these values in `.firebaserc`, `firebase.json`, frontend HTML, or the repository.

## External setup gate

The local architecture is ready to be connected, but the following account-level actions are intentionally not automated in this stage:

- Creating Firebase projects.
- Enabling billing or paid services.
- Connecting the GitHub repository to Cloudflare Pages.
- Creating or changing production admin accounts.
- Deploying production Rules, Functions, or Pages.
- Importing live PythonAnywhere data.
- Executing the one-shot cutover.

These actions require the user’s authenticated accounts and are performed only after the local adapter and staging tests are complete.
