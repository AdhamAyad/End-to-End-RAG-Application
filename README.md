# End-to-End RAG Application on GCP

This project demonstrates a complete **Retrieval-Augmented Generation (RAG) architecture** on **Google Cloud Platform (GCP)**:

- Frontend & Backend on **Cloud Run**
- Full **Terraform automation**:
  - Artifact Registry for Docker images
  - Build & push Docker images
  - Deploy Cloud Run, service accounts, VPC & connectors
- **Redis Memory Store** for caching user questions
- **Vertex AI** for embeddings, vector database (index + endpoint), and LLM
- **Pub/Sub** for event-driven file processing
- **Firestore** for metadata storage

---

## Project Diagram

![Diagram](assets/Diagram.svg)

---

## User Flow

1. User submits a question via frontend (Cloud Run)  
2. Backend checks Redis (via VPC connector) for cached answers  
3. If found → return cached answer  
4. Else → call chunk function (Cloud Run)  
5. Generate embeddings via Vertex AI  
6. Query Vertex AI vector database  
7. Send context + question to Vertex AI LLM  
8. Store answer in Redis  
9. Return answer to user  

---

## Admin Flow

1. Admin uploads files via frontend (Cloud Run)  
2. Files go to GCS bucket → triggers Pub/Sub  
3. Pub/Sub subscription sends event to admin backend (Cloud Run)  
4. Backend calls chunk function (Cloud Run)  
5. Generate embeddings via Vertex AI  
6. Insert embeddings into vector database  
7. Store metadata in Firestore  
8. Pub/Sub ensures delivery & retries, with dead-letter topic for failures  

---

## Backend & Infrastructure

- Cloud Run services (frontend, backend, chunk function)  
- Service Accounts with least privilege  
- Docker images built & deployed via Terraform  
- Vertex AI (embedding, vector database, LLM)  
- Redis Memory Store  
- VPC & VPC connector  
- Pub/Sub for reliable event handling  

---

## Project Structure

```bash
📁 Admin_Backend      # Admin backend
📁 Chunk_Function     # Chunk function
📁 Terraform          # Terraform IaC
📁 Users_Backend      # User backend
📁 Admin_Frontend     # Admin frontend
📁 User_Frontend      # User frontend
📁 assets             # Diagram & test video
README.md
