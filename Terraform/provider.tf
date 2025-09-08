provider "google" {
      credentials = file("end-to-end-rag-application.json") 
      project = var.project_id
      region = var.region
    }