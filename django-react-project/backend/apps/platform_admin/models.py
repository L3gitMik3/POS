from django.db import models


class JobRun(models.Model):
    job_name = models.CharField(max_length=255)
    tenant_schema = models.CharField(max_length=255)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=[("success", "Success"), ("failed", "Failed")])
    message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.job_name}::{self.tenant_schema}"
