Product Requirements Document (PRD)Project: Intelligent Detection Platform (E2E MLOps with Angular & FastAPI)Version: 2.0.0 (Updated for Enterprise Architecture)Date: May 2026Owner: AI / Full-stack EngineerStatus: Approved for Development1. Project Overview1.1 The ProblemMachine Learning models frequently fail when transitioning from experimentation to production due to monolithic architectures, lack of typed interfaces, and the absence of automation and monitoring. This creates a barrier between Data Science teams and end users.1.2 The SolutionDevelop a comprehensive (End-to-End) platform that demonstrates complete mastery of the software and AI lifecycle. The solution packages a predictive ML model into an asynchronous REST API (FastAPI), consumed by a strictly typed enterprise user interface (Angular), all orchestrated under a continuous integration and deployment (CI/CD) pipeline and monitored to prevent model degradation (Model Drift).2. System Architecture (Full Flow)The architecture follows a decoupled microservices pattern, allowing the frontend and AI backend to scale independently.2.1 E2E Operational FlowUser Interaction: The user interacts with a reactive UI in Angular.Gateway and API: Nginx serves the web app and routes inference requests to FastAPI.Inference (Serving): FastAPI validates the payload (Pydantic), invokes the pre-loaded model from the Model Registry (MLflow), and generates a prediction.Persistence and Observability: The API saves the input, output, and latency in PostgreSQL for future drift monitoring (Data Drift) in Grafana.Retraining (CT): If performance drops, GitHub Actions triggers a new orchestrated training using data versioned with DVC.3. Technology StackLayer / ComponentTechnologyTechnical JustificationFrontend UIAngular 18+ (TypeScript)MVC structure, dependency injection, and robust form validation.Backend APIFastAPI (Python 3.10+)High asynchronous performance, automatic validation with Pydantic, and Swagger UI auto-generation.Model Registry & TrackingMLflowIndustry standard for model versioning and metrics tracking.Data VersioningDVC (Data Version Control)Keeps the Git repository lightweight while versioning datasets in S3/Cloud Storage.DatabasePostgreSQLRelational persistence of inference logs for Drift analysis.InfrastructureDocker + Docker ComposeMulti-stage packaging (Nginx for Angular, Uvicorn for FastAPI).CI/CDGitHub ActionsAutomated testing (Pytest, Karma/Jasmine) and image building.4. Functional and Non-Functional Requirements4.1 Functional Requirements (FR)FR-01 (AI Inference): The backend must expose a /predict endpoint that receives structured parameters and returns the predicted class and its probability.FR-02 (Interactive UI): The frontend must present a validated form that disables the submit button while the inference is being processed.FR-03 (Model Registry): Every successful new training must be automatically registered in MLflow.FR-04 (Auditing): Every successful prediction must be saved in PostgreSQL with a timestamp and its execution latency.4.2 Non-Functional Requirements (NFR)Security: CORS must be strictly configured in FastAPI to accept requests only from the Angular domain.Response Times: Pure model inference must not exceed 150ms.Scalability: Docker containers must be stateless to allow for replicas.5. Structural Design and Assets5.1 E2E Repository Directory Structuremlops-angular-fastapi/
├── .github/workflows/         # CI/CD Pipelines
├── data/                      # Versioned with DVC (.dvc files)
├── backend/                   # Python Environment (AI + FastAPI)
│   ├── src/
│   │   ├── models/            # ML Logic (training, evaluation)
│   │   └── api/               # FastAPI Entrypoint and Routers
│   │       ├── main.py
│   │       └── schemas.py
│   ├── Dockerfile             # Python/Uvicorn Image
│   └── requirements.txt
├── frontend/                  # Angular Environment
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/    # UI Components
│   │   │   ├── models/        # TypeScript Interfaces
│   │   │   └── services/      # HTTP connection logic
│   ├── Dockerfile             # Node (Build) -> Nginx (Serve) Image
│   └── package.json
├── docker-compose.yml         # Local infrastructure orchestration
└── dvc.yaml                   # Data pipeline graph
5.2 Database Schema (PostgreSQL)Implementation to enable Continuous Monitoring:CREATE TABLE inference_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    model_version VARCHAR(50) NOT NULL,
    input_payload JSONB NOT NULL,
    prediction INT NOT NULL,
    probability FLOAT NOT NULL,
    latency_ms INT NOT NULL,
    is_drift_detected BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_timestamp ON inference_logs(timestamp);
6. Technical Implementation (Core Snippets)6.1 Backend: FastAPI with Secure CORS Configuration# backend/src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mlflow.sklearn
import time

app = FastAPI(title="MLOps Prediction API")

# Enable CORS for Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class PredictPayload(BaseModel):
    feature_1: float
    feature_2: float
    category: int

# Model loaded in memory on startup (Singleton)
model = None

@app.on_event("startup")
def load_ml_model():
    global model
    model = mlflow.sklearn.load_model("models:/ProductionModel/latest")

@app.post("/api/predict")
async def predict(data: PredictPayload):
    start_time = time.time()
    try:
        # Transformation and inference
        prediction = model.predict([[data.feature_1, data.feature_2, data.category]])
        probability = model.predict_proba([[data.feature_1, data.feature_2, data.category]]).max()
        
        latency = int((time.time() - start_time) * 1000)
        
        # Logic to save to PostgreSQL using SQLAlchemy would go here
        
        return {
            "prediction": int(prediction[0]),
            "probability": float(probability),
            "latency_ms": latency
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Inference Error")
6.2 Frontend: Typed Angular Service// frontend/src/app/services/ml.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface PredictPayload {
  feature_1: number;
  feature_2: number;
  category: number;
}

export interface PredictResponse {
  prediction: number;
  probability: number;
  latency_ms: number;
}

@Injectable({
  providedIn: 'root'
})
export class MlService {
  private apiUrl = 'http://localhost:8000/api/predict';

  constructor(private http: HttpClient) { }

  getPrediction(data: PredictPayload): Observable<PredictResponse> {
    return this.http.post<PredictResponse>(this.apiUrl, data);
  }
}
6.3 Infrastructure: Docker Compose (Full-Stack Integration)# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ai_user
      POSTGRES_PASSWORD: securepassword
      POSTGRES_DB: mlops_db
    ports:
      - "5432:5432"

  mlflow:
    image: bitnami/mlflow:latest
    ports:
      - "5000:5000"

  backend_api:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - DATABASE_URL=postgresql://ai_user:securepassword@db:5432/mlops_db
    depends_on:
      - db
      - mlflow

  frontend_ui:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend_api
7. Success Metrics (KPIs)Software Quality: 80%+ code coverage in unit tests in both TypeScript (Jasmine/Karma) and Python (Pytest).CI/CD Efficiency: The complete build, test, and deployment pipeline takes < 10 minutes in GitHub Actions.Availability and Performance: The Angular UI loads in < 1 second, and predictions are processed with a backend latency of under 150 ms at the 95th percentile (P95).Verified Sources:Angular Official Documentation: HttpClient, Reactive Forms & Dependency Injection (v18, 2026).FastAPI Advanced: CORS, Dependencies & Async SQL (Tiangolo, 2025).Practitioners Guide to MLOps: Whitepaper (Google Cloud & Deloitte, 2024-2025).Docker Best Practices for Node.js and Python Applications (Docker Docs, 2026).