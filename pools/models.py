from django.db import models


class CityPool(models.Model):
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['state', 'name']
        unique_together = ['name', 'state']

    def __str__(self):
        return f"{self.name}, {self.state}"

    @property
    def driver_count(self):
        return self.driverprofile_set.filter(is_active=True).count()

    @property
    def company_count(self):
        return self.companyprofile_set.count()

    @property
    def open_job_count(self):
        return self.joblisting_set.filter(status='active').count()
