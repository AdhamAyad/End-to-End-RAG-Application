resource "google_compute_network" "rag_vpc" {
  name                    = "rag-vpc"
  auto_create_subnetworks = false
}
resource "google_compute_subnetwork" "rag_subnet" {
  name          = "rag-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.rag_vpc.id
  private_ip_google_access = true
}

resource "google_compute_firewall" "allow_redis" {
  name    = "allow-redis-from-vpc-connector"
  network = google_compute_network.rag_vpc.id

  allow {
    protocol = "tcp"
    ports    = ["6379"]
  }

  source_ranges = ["10.0.0.0/28"] 
}

resource "google_vpc_access_connector" "cloud_run_connector" {
  name          = "cloud-run-redis-connector"
  region        = var.region
  network       = google_compute_network.rag_vpc.id
  ip_cidr_range = "10.0.1.0/28"
  min_instances = 2
  max_instances = 5
}