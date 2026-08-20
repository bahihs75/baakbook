# External Access Status

## Cloudflare

Checked on 2026-08-19. The browser remained at Cloudflare's human-verification page. No project was created, no repository was connected, and no Pages deployment was performed.

## Firebase

Firebase Console is authenticated as **Baak Book1 (baakbook01@gmail.com)**. The first creation attempt did not persist. A second attempt was started with display name **Baak Books Production** and generated the actual Project ID **`baak-books-production-ab2ed`**. Google Developer Programme, Gemini in Firebase, and Google Analytics were disabled. The project creation action was submitted. The console progressed from **Preparing your project, please wait** to **Finishing up…**. The project display name is visible, but the project dashboard is not available yet.

The project is now visible in Firebase Console at `https://console.firebase.google.com/project/baak-books-production-ab2ed/overview` with display name **Baak Books Production** and actual Project ID **`baak-books-production-ab2ed`**. The console shows the **Spark plan ($0/month)**. No Firestore data, application configuration, billing upgrade, or live-data import has been performed. The Firestore route was opened directly at `https://console.firebase.google.com/project/baak-books-production-ab2ed/firestore`. The console confirms the Spark plan, but the Firestore page remains stuck on a loading spinner in repeated checks and has not exposed the database creation wizard. No database was created and no settings were changed. This is being treated as a console-loading issue, not as evidence that Firestore exists. The wizard is now available. It shows **Standard edition** (simple query engine with automatic indexing and core operations) and **Enterprise edition**. Standard is selected for Baak Books; Enterprise is not selected. The database location is now selected as **`europe-west3 (Frankfurt)`**, as approved by the user. Firebase warns that this location cannot be changed after creation. The wizard was advanced to **Configure** with **Production mode** selected, which displays deny-all rules (`allow read, write: if false`). The user-approved **Create** action was submitted. Firebase still shows **Provisioning Cloud Firestore…** after two independent status checks. The Standard database remains configured for `europe-west3 (Frankfurt)` with Production mode deny-all rules. No collections, documents, live-data import, billing upgrade, or public access has been configured. I will not retry the Create action while provisioning is in progress.


## Official documentation checked during Firestore error diagnosis

- Firebase Firestore quickstart: https://firebase.google.com/docs/firestore/quickstart — confirms that a new project can create a Cloud Firestore database, requires selecting a location and a starting security mode, and that Production mode denies mobile/web client reads and writes by default while authenticated server libraries can access the database.
- Firebase pricing: https://firebase.google.com/pricing — confirms Spark is no-cost with no payment method required, while Blaze is pay-as-you-go and unlocks additional services/higher usage; Cloud Functions and some Google Cloud services are listed under paid-plan pricing.
- The Firebase console currently reports `Cannot enable Firestore for this project — An unknown error occurred` after the approved creation attempt. The browser console produced no diagnostic output. The page still shows Spark (`$0/month`) and the project owner/billing widget indicates the current account cannot modify the billing plan because it is not recognized as the project owner in that widget. No billing change has been made.

This does not yet prove that upgrading billing would fix Firestore creation. The next safe decision is to inspect project ownership/permissions and, only if necessary and explicitly approved, consider the Blaze plan. No data import or deployment is allowed while this issue is unresolved.

Source date checked: 2026-08-20.



## IAM ownership check

The Google Cloud IAM page for project `baak-books-production-ab2ed` was opened read-only. After waiting, it still showed a loading state and did not expose the member/role table. No IAM role, owner, billing, or project setting was changed. The Firestore error remains unresolved.



## Firebase settings check

Firebase project settings for `baak-books-production-ab2ed` were opened read-only. The console continued showing a loading state after a second check and did not expose additional ownership or project details. No project setting, IAM role, billing plan, database, or data was changed.



## Google Cloud Firestore console check

The alternate Google Cloud Firestore databases page for `baak-books-production-ab2ed` was opened read-only. After waiting, it remained in a loading state and exposed no database list or actionable creation state. No resource, API, IAM role, billing plan, or database setting was changed.
