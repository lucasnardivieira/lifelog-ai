# Infrastructure (GCP, Terraform)

No resources are defined yet — they arrive in M3 (Cloud Run, GCS, Secret Manager) and M5 (Cloud Scheduler).

## Cost
Target ~US$0–3/month at personal volume (free tiers for Cloud Run, Scheduler, BigQuery, Speech-to-Text). Set a budget alert on the project.

## Teardown
```bash
terraform destroy
```
Then confirm in the console (Cloud Run, Storage, BigQuery, Secret Manager, Scheduler) and in Billing that nothing billable remains.
