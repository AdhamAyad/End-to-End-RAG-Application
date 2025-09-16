# 📌 End-to-End RAG Application on GCP

This project demonstrates a complete **End-to-End Retrieval-Augmented Generation (RAG) architecture** using **Google Cloud Platform (GCP)**:

- 🧑‍💻 Frontend & Backend hosted on **Cloud Run**
- ⚙️ Automation with **Terraform**:
  - Artifact Registry for Docker images
  - Building & pushing Docker images
  - Creating Cloud Run services, service accounts, VPC, and VPC connectors
- 🗄️ **Redis Memory Store** for caching user questions
- 📦 **Vertex AI** for embeddings, vector database (index + endpoint), and LLM
- ☁️ Fully internal/external network controls with VPC connector

---

## 🖼️ Project Diagram

![Diagram](Assets/End-to-End Cloud RAG Application Diagram.html)

---

## 🧠 User Flow

1. User submits a question via **frontend** on Cloud Run  
2. Backend checks **Redis** via **VPC connector** for cached answers  
3. If answer exists → return cached answer  
4. If not → backend sends question to **chunk function** (Cloud Run)  
5. Backend receives text chunks and sends them to **Vertex AI embedding model**  
6. Embeddings are used to query the **Vertex AI vector database (index + endpoint)**  
7. Backend sends question + retrieved vectors to **Vertex AI LLM**  
8. Generated answer is stored in **Redis** for future requests  
9. Answer is returned to the user

---

## 🧑‍💼 Admin Flow

1. Admin uploads files via **frontend** (Cloud Run)  
2. Files are uploaded to **GCS bucket**  
3. Bucket triggers **Pub/Sub topic** → Pub/Sub subscription → Admin backend (Cloud Run)  
4. Backend sends files to **chunk function** (Cloud Run)  
5. Backend sends chunks to **Vertex AI embedding model**  
6. Embeddings are inserted into **Vertex AI vector database**  
7. Metadata stored in **Firestore**  
8. Pub/Sub subscription sends acknowledgement to ensure reliable event processing  
9. Dead-letter topic handles failed events

---

## ⚙️ Backend & Infrastructure

- **Cloud Run services** for frontend, backend, and chunk function  
- **Service Accounts** with minimal required permissions  
- **Docker Images** built and pushed via **Terraform automation**  
- **Vertex AI**:
  - Embedding model
  - Vector database (index + endpoint)
  - LLM model
- **Redis Memory Store** for caching user questions  
- **VPC & VPC Connector** for internal communication  

---

## 📁 Project Structure

```bash
📁 Admin_Backend      # Admin backend code (Python/NodeJS) + Dockerfile
📁 Chunk_Function     # Chunk function code + Dockerfile
📁 Terraform          # Terraform scripts for full infrastructure
📁 Users_Backend      # User backend code + Dockerfile
📁 Admin_Frontend     # Admin frontend code + Dockerfile
📁 User_Frontend      # User frontend code + Dockerfile
📁 assets             # Diagram and video test
README.md

