# InsightFlow — GCP Deployment Guide
# Budget: $5 | Estimated actual spend: $0.15–$0.50

Project ID : insightflow-496519
Region     : us-central1
Service acct: insightflow@insightflow-496519.iam.gserviceaccount.com

---

## STEP 1 — Enable APIs (GCP Console, 5 min)

1. Go to https://console.cloud.google.com
2. Select project: insightflow-496519
3. Search and Enable each of these APIs:
   - Vertex AI API
   - Cloud Run API
   - Secret Manager API
   - Cloud Firestore API
   - Cloud Build API
   - Artifact Registry API

---

## STEP 2 — Grant IAM Roles (GCP Console, 5 min)

IAM & Admin → IAM → find insightflow@insightflow-496519.iam.gserviceaccount.com
Add these roles:
  - Vertex AI User
  - Cloud Datastore User   (covers Firestore)
  - Secret Manager Secret Accessor

---

## STEP 3 — Create Secrets in Secret Manager (10 min)

GCP Console → Secret Manager → Create Secret for each:

Secret name          Value (copy from .env)
────────────────     ─────────────────────────────────────
GOOGLE_API_KEY       AIzaSyBQ...
OPENROUTER_API_KEY   sk-or-v1-...
GROQ_API_KEY         gsk_...  (get free from console.groq.com)
SMTP_USER            shayanmukhtiar77@gmail.com
SMTP_PASS            almy lecb ovto whoc
NOTIFY_EMAIL         zainabraza1960@gmail.com
GOOGLE_SHEET_ID      1Bz-9O_i2qTteySBKzIRs1BTonre9bxmaWi3ynhGFTFM
GOOGLE_SA_JSON       (paste the full JSON from .env)
SLACK_WEBHOOK_URL    https://hooks.slack.com/services/...

After creating each secret:
  → Click the secret → Permissions → Add Principal
  → Principal: insightflow@insightflow-496519.iam.gserviceaccount.com
  → Role: Secret Manager Secret Accessor

---

## STEP 4 — Deploy Backend to Cloud Run (15 min)

Install gcloud CLI: https://cloud.google.com/sdk/docs/install

In your terminal:

  gcloud auth login
  gcloud config set project insightflow-496519

  cd backend
  gcloud run deploy insightflow-backend \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 3 \
    --set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest,\
OPENROUTER_API_KEY=OPENROUTER_API_KEY:latest,\
GROQ_API_KEY=GROQ_API_KEY:latest,\
SMTP_USER=SMTP_USER:latest,\
SMTP_PASS=SMTP_PASS:latest,\
NOTIFY_EMAIL=NOTIFY_EMAIL:latest,\
GOOGLE_SHEET_ID=GOOGLE_SHEET_ID:latest,\
GOOGLE_SA_JSON=GOOGLE_SA_JSON:latest,\
SLACK_WEBHOOK_URL=SLACK_WEBHOOK_URL:latest" \
    --set-env-vars "GCP_PROJECT=insightflow-496519,GCP_LOCATION=us-central1"

Cloud Run will return a URL like:
  https://insightflow-backend-xxxx-uc.a.run.app

Save this URL — you need it for Step 6 and 7.

---

## STEP 5 — Set Up Firestore (10 min)

GCP Console → Firestore → Create Database
  - Mode: Native mode
  - Location: us-central1
  - Click Create

That's it. The code changes (history_store.py, auth.py, feedback_store.py)
handle everything automatically when FIRESTORE_ENABLED=true is set.

Add to Cloud Run env vars:
  gcloud run services update insightflow-backend \
    --region us-central1 \
    --set-env-vars "FIRESTORE_ENABLED=true,GCP_PROJECT=insightflow-496519,GCP_LOCATION=us-central1"

---

## STEP 6 — Deploy Frontend to Vercel (free, 10 min)

Vercel is free and purpose-built for Next.js. No GCP credits needed.

1. Go to https://vercel.com → Sign in with GitHub
2. Import repository: zainabraza06/AIseekho
3. Set Root Directory: frontend-next
4. Add Environment Variable:
     NEXT_PUBLIC_API_URL = https://insightflow-backend-xxxx-uc.a.run.app
5. Click Deploy

Vercel returns a URL like: https://aiseekho.vercel.app

---

## STEP 7 — Update Mobile App (Flutter)

Edit nexus_mobile/lib/config.dart:

  static const String baseUrl = 'https://insightflow-backend-xxxx-uc.a.run.app';

Rebuild APK:
  cd nexus_mobile
  flutter build apk --release

---

## STEP 8 — Update NEXUS_BASE_URL

In GCP Console → Cloud Run → insightflow-backend → Edit & Deploy New Revision
  Add env var: NEXUS_BASE_URL = https://insightflow-backend-xxxx-uc.a.run.app

---

## Cost Estimate

Service            Free Tier                    Beyond Free
──────────────     ──────────────────────────   ─────────────────────────
Vertex AI Flash    —                            $0.10/1M input tokens
Cloud Run          2M req/month, 180K cpu-sec   $0.00000024/vCPU-sec
Secret Manager     10K access ops/month         $0.06/10K ops
Firestore          50K reads + 20K writes/day   $0.06/100K reads
Artifact Registry  0.5 GB free                  $0.10/GB

Estimated total for 200 analysis runs: ~$0.15
Estimated total for 1000 runs: ~$0.75
Your $5 credit covers ~3,000 full analysis runs.

---

## Architecture After Deployment

  Flutter App  ──┐
  Next.js Web  ──┼──► Cloud Run (FastAPI) ──► Vertex AI Gemini
                 │          │                ► OpenRouter (primary)
                 │          ├──► Firestore (users, history, feedback)
                 │          ├──► Secret Manager (all credentials)
                 │          ├──► Gmail SMTP (Step 2 email)
                 │          ├──► Google Sheets (Step 3 dashboard)
                 │          └──► Slack Webhook (Step 4 alert)
