terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.1.1"
    }
  }

  backend "gcs" {
    bucket      = "terrraform-rag-app-state"
    prefix      = "dev"
    credentials = "end-to-end-rag-application.json"  
  }
}