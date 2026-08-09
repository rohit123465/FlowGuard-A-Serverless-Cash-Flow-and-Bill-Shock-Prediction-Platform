# FlowGuard

**A Serverless Cash-Flow and Bill-Shock Prediction Platform with ML-Powered Financial Risk Detection**

FlowGuard helps people with irregular income understand how much they can safely spend before upcoming bills are due. Unlike a conventional expense tracker that only explains past spending, FlowGuard combines a transparent cash-flow forecast with machine-learning risk predictions.

## Problem

Freelancers, contractors, students, gig workers, and people on variable incomes may have enough money across a whole month but still run short before an important bill. Payment timing and income uncertainty make a monthly budget insufficient.

FlowGuard is designed to answer two questions:

1. **Rule-based forecast:** How much can I safely spend based on my current balance, known bills, expected income, and chosen safety buffer?
2. **ML risk prediction:** How likely am I to fall below that safety buffer during the next 30 days, based on historical behaviour and uncertainty?

The deterministic forecast remains the source of precise calculations. Machine learning will complement it by estimating uncertainty rather than replacing understandable financial rules.

## Revised project objectives

FlowGuard is primarily a software-engineering project with machine learning incorporated as a production subsystem. Its objectives are to:

1. Build a secure, serverless application that scales without managing traditional servers.
2. Help users with irregular income plan around the timing of bills, expenses, and uncertain payments.
3. Calculate an understandable safe-to-spend amount using a deterministic cash-flow engine.
4. Predict the probability of falling below a chosen safety buffer within the next 30 days using machine learning.
5. Keep deterministic calculations and probabilistic ML predictions separate so users can understand what each result means.
6. Protect each user's financial records through authentication, user-scoped database keys, private storage, encryption, and least-privilege IAM permissions.
7. Demonstrate production software-engineering practices through modular design, automated testing, infrastructure as code, CI/CD, logging, monitoring, and failure handling.
8. Support future financial-data ingestion through manual entry, CSV imports, receipt extraction, and optional Open Banking integrations.

## Planned user functionality

- Secure user registration and authentication
- Add, edit, list, and delete expenses
- Record guaranteed, likely, and uncertain income
- Record one-time and recurring financial commitments
- Calculate safe-to-spend from the lowest projected balance
- Display a chronological cash-flow timeline
- Warn about predicted bill shocks and shortfalls
- Run hypothetical purchase and late-income scenarios
- Display monthly analytics
- Upload receipt images securely
- Export financial records as CSV
- Receive scheduled shortfall notifications
- View an ML-generated 30-day shortfall-risk probability

## System architecture

```text
React + TypeScript frontend
          |
Amazon Cognito authentication
          |
API Gateway HTTP API
          |
Python AWS Lambda functions
          |
   +------+-------------------+
   |                          |
DynamoDB                 Amazon S3
financial records        receipts and exports
   |
Feature generation
   |
ML risk model

EventBridge Scheduler -> warning Lambda -> SNS/SES notifications
CloudWatch and X-Ray -> logs, metrics, tracing, and alarms
```

### How the system works

1. **Frontend:** The React and TypeScript web application lets users manage expenses, expected income, recurring commitments, safety-buffer settings, receipts, and forecast scenarios.
2. **Authentication:** Amazon Cognito registers users, manages sign-in, and issues JSON Web Tokens. The frontend includes a token with protected API requests.
3. **API layer:** API Gateway exposes REST-style HTTPS endpoints, validates Cognito tokens, and sends authorised requests to the appropriate Lambda function.
4. **Application layer:** Python Lambda functions validate requests and coordinate the domain services. The authenticated Cognito user ID is used to scope every database operation.
5. **Deterministic forecast:** The cash-flow engine orders income, bills, and expenses by date, calculates projected balances, identifies the lowest balance and first shortfall date, and returns the user's safe-to-spend amount.
6. **Database:** DynamoDB stores expenses, expected income, commitments, preferences, and other structured financial records. Partition keys isolate each user's data, while a secondary index supports chronological queries.
7. **File storage:** Private S3 buckets store receipt images, uploaded transaction files, generated CSV exports, training datasets, and versioned ML model artifacts. Temporary presigned URLs provide controlled uploads and downloads.
8. **ML subsystem:** A shared feature builder transforms historical financial records into model inputs. The inference component returns a 30-day shortfall probability alongside the rule-based forecast. If ML inference fails, the deterministic forecast remains available.
9. **Scheduled warnings:** EventBridge Scheduler invokes a warning Lambda periodically. Users predicted to cross their safety buffer can be notified through Amazon SNS or SES.
10. **Observability:** CloudWatch collects structured logs, metrics, dashboards, and alarms, while X-Ray traces requests across the serverless components.
11. **Deployment:** AWS SAM and CloudFormation define the infrastructure. CI/CD will run tests and validation before deploying application and infrastructure changes.

### Forecast and ML responsibilities

```text
Known balance, income, bills, and expenses
                    |
          Deterministic forecast
                    |
  Safe-to-spend, timeline, and shortfall date

Historical patterns and uncertain behaviour
                    |
              ML risk model
                    |
       30-day shortfall probability
```

The deterministic result answers what will happen if the supplied financial events occur as entered. The ML result estimates additional risk from historical variability and uncertainty. The interface will label them separately rather than presenting an ML probability as a guaranteed outcome.

## Technology stack

### Backend

- Python 3.12
- Pydantic for data validation
- boto3 for AWS access
- AWS Lambda Powertools for future logging, tracing, and metrics
- pytest and moto for isolated tests

### AWS

- AWS Lambda
- API Gateway HTTP API
- Amazon Cognito
- Amazon DynamoDB
- Amazon S3
- Amazon EventBridge Scheduler
- Amazon SNS or SES
- Amazon CloudWatch and AWS X-Ray
- AWS SAM and CloudFormation

### Frontend

- React
- TypeScript
- Vite
- TanStack Query
- Recharts

### Machine learning

- pandas and scikit-learn for feature engineering and model training
- Amazon S3 for versioned training data and model artifacts
- AWS Lambda for initial serverless inference
- Amazon SageMaker as an optional later training and model-management platform



## Local backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Run the complete backend test suite:

```powershell
python -m pytest -v -p no:cacheprovider
```

The deployed-AWS integration and system tests are opt-in. They discover API
and Cognito identifiers from the `flowguard-dev` CloudFormation stack, create
temporary Cognito users and financial records, and clean them up afterward.

From the `backend` directory, run all deployed-AWS tests with:

```powershell
python -m pytest tests\integration tests\system --run-aws-tests --aws-profile flowguard-dev --aws-region eu-west-2 --stack-name flowguard-dev -v
```

Run only integration or system tests with:

```powershell
python -m pytest -m integration --run-aws-tests -v
python -m pytest -m system --run-aws-tests -v
```

These tests contact real AWS services and can incur small charges. Never put
passwords, access tokens, or permanent AWS access keys in the test files.

## Frontend development

The React and TypeScript frontend includes Cognito sign-in and sign-out,
protected routes, the dashboard shell, complete expense, income, and commitment
CRUD interfaces, and an interactive deterministic cash-flow forecast with a
safe-to-spend summary, buffer warnings, chart, and event timeline.

It also includes these user-facing features:

- **Receipt upload:** attach a JPEG, PNG, or PDF receipt (up to 5 MB) to an
  expense. The file is uploaded directly to a private encrypted S3 bucket using
  a five-minute signed upload, while DynamoDB stores only its object key. Signed
  download links are also short-lived. FlowGuard verifies the uploaded file's
  signature, shows upload progress, and automatically removes the S3 object
  when its expense is deleted.
- **Textract receipt suggestions:** after upload, users can select **Scan** to
  call Amazon Textract `AnalyzeExpense`. FlowGuard extracts the highest-
  confidence vendor name, receipt date, and total, normalises supported values,
  and presents them in an editable review dialog. Nothing is written to the
  expense until the user selects **Apply to expense**; the original receipt
  remains in private S3 storage.
- **CSV export:** download the expenses for the selected date range as a CSV
  file for Excel, Google Sheets, accounting, or personal backups. Monetary
  values are exported as readable pounds rather than internal minor units.
- **Monthly analytics:** summarise a selected month using total income, total
  spending, net cash flow (income minus expenses), savings rate, transaction
  counts, essential versus discretionary spending, and spending by category.
  These are descriptive calculations from the user's stored records; they are
  not ML predictions or financial advice.
- **Scheduled bill-shock warnings:** an opted-in EventBridge schedule runs at
  07:00 UTC each day. It uses the user's saved balance, safety buffer and
  forecast window to run the deterministic forecast. If the projected minimum
  balance falls below the buffer, a user-scoped notification is stored in
  DynamoDB. The authenticated React application checks for warnings every
  minute and shows a dismissible banner. Users configure this under **Warning
  settings** and should keep their current balance accurate.

The local AWS development identifiers are stored in an ignored `.env.local`
file. Use `.env.example` when configuring another environment.

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and sign in with a confirmed Cognito application
user. The SAM API CORS configuration currently allows this origin.

Run the frontend checks with:

```powershell
npm test
npm run build
```

## Infrastructure validation and deployment

From the project root:

```powershell
sam validate --template-file infrastructure\template.yaml
sam build --template-file infrastructure\template.yaml
sam deploy --guided
```

Deployments create an environment-specific table such as:

```text
flowguard-financial-records-dev
```

The table uses on-demand capacity, server-side encryption, point-in-time recovery, and retention policies that protect records if the CloudFormation stack is removed.

## ML baseline

FlowGuard now includes a binary logistic-regression baseline estimating whether
the user's balance will fall below their safety buffer during the selected
forecast window. It supplements rather than replaces the deterministic engine.
The deterministic result explains the scheduled events exactly; ML estimates
additional uncertainty represented in its training scenarios.

Potential features include:

- Current balance and safety buffer
- Essential bills due within 30 days
- Guaranteed and uncertain expected income
- Days until the next income payment
- Average expense and income variability
- Recent minimum balance
- Previous shortfalls
- Recent discretionary spending

The reproducible baseline is trained with a fixed seed on 12,000 explicitly
synthetic scenarios. The first held-out evaluation produced accuracy 0.8107,
precision 0.8080, recall 0.8218, F1 0.8149, ROC-AUC 0.8958, and Brier score
0.1306. These results measure performance on simulated data only and must not be
presented as evidence of real-world financial accuracy.

Train it from the backend virtual environment:

```powershell
python -m pip install -r requirements-ml.txt
python ..\ml\train_baseline.py
```

The script writes a portable JSON model, metrics, and a small evaluation sample
under `ml/artifacts`. The deployed artifact is stored in a private encrypted,
versioned S3 bucket. Lambda loads the scaler values and coefficients and performs
inference without packaging scikit-learn. The authenticated `GET /ml/risk`
endpoint returns a probability, low/medium/high band, feature values, leading
factor directions, model version, synthetic-data label, and disclaimer.

## Delivery roadmap

1. Deterministic forecast engine and unit tests
2. DynamoDB persistence and repository tests
3. Lambda handlers and REST API
4. Cognito authentication and user isolation
5. React cash-flow dashboard
6. S3 receipt uploads and CSV exports
7. Scheduled shortfall warnings
8. Shared ML feature builder
9. Reproducible model training and evaluation
10. Serverless ML inference endpoint
11. CI/CD, security checks, monitoring, and model observability

## Important disclaimer

FlowGuard is an engineering project and forecasting aid, not financial advice. ML predictions are probabilistic and must not be presented as guaranteed outcomes.
