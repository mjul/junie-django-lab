from django.db import models
from django.utils import timezone
import datetime
from dateutil.relativedelta import relativedelta

class Tenant(models.Model):
    """
    Represents a tenant in the multitenant application.
    Each tenant can have their own contract templates and contracts.
    """
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Document(models.Model):
    """
    Represents a document (PDF file) that can be associated with a contract template.
    """
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ContractTemplate(models.Model):
    """
    Represents a contract template that belongs to a tenant.
    Each template has a name, publication date, and associated documents.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='contract_templates')
    name = models.CharField(max_length=255)
    publication_date = models.DateField()
    documents = models.ManyToManyField(Document, related_name='contract_templates', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"

class Party(models.Model):
    """
    Represents a party (buyer or seller) in a contract.
    """
    PARTY_TYPES = [
        ('BUYER', 'Buyer'),
        ('SELLER', 'Seller'),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=PARTY_TYPES)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class Contract(models.Model):
    """
    Represents a contract that belongs to a tenant.
    A contract may be based on a contract template and has parties and dates.
    """
    REPORTING_FREQUENCIES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('TERMINATED', 'Terminated'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='contracts')
    template = models.ForeignKey(ContractTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts')
    name = models.CharField(max_length=255)
    parties = models.ManyToManyField(Party, related_name='contracts')
    signature_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    reporting_frequency = models.CharField(max_length=10, choices=REPORTING_FREQUENCIES, default='MONTHLY')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Generate reporting periods if this is a new contract with an effective date
        if is_new and self.effective_date and self.status == 'ACTIVE':
            self.generate_reporting_periods()

    def generate_reporting_periods(self):
        """
        Generate reporting periods based on the contract's reporting frequency,
        effective date, and expiration date.
        """
        if not self.effective_date:
            return

        start_date = self.effective_date
        end_date = self.expiration_date or (timezone.now().date() + datetime.timedelta(days=365))

        current_start = start_date

        while current_start <= end_date:
            if self.reporting_frequency == 'MONTHLY':
                current_end = current_start + relativedelta(months=1, days=-1)
            elif self.reporting_frequency == 'QUARTERLY':
                current_end = current_start + relativedelta(months=3, days=-1)
            elif self.reporting_frequency == 'YEARLY':
                current_end = current_start + relativedelta(years=1, days=-1)
            else:
                current_end = current_start + relativedelta(months=1, days=-1)

            if current_end > end_date:
                current_end = end_date

            ReportingPeriod.objects.create(
                contract=self,
                start_date=current_start,
                end_date=current_end
            )

            if self.reporting_frequency == 'MONTHLY':
                current_start = current_start + relativedelta(months=1)
            elif self.reporting_frequency == 'QUARTERLY':
                current_start = current_start + relativedelta(months=3)
            elif self.reporting_frequency == 'YEARLY':
                current_start = current_start + relativedelta(years=1)
            else:
                current_start = current_start + relativedelta(months=1)

class ReportingPeriod(models.Model):
    """
    Represents a reporting period for a contract.
    """
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='reporting_periods')
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.contract.name} - {self.start_date} to {self.end_date}"

class ServiceLevelIndicator(models.Model):
    """
    Represents a Service Level Indicator (SLI) - a metric that is measured.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ServiceLevelAgreement(models.Model):
    """
    Represents a Service Level Agreement (SLA) that belongs to a contract.
    An SLA is a tree structure of SLIs with threshold values.
    """
    THRESHOLD_TYPES = [
        ('MIN', 'Minimum'),
        ('MAX', 'Maximum'),
    ]

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='slas')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sli = models.ForeignKey(ServiceLevelIndicator, on_delete=models.CASCADE, null=True, blank=True, related_name='slas')
    threshold_type = models.CharField(max_length=3, choices=THRESHOLD_TYPES, null=True, blank=True)
    threshold_value = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contract.name} - {self.name}"

    class Meta:
        verbose_name = "Service Level Agreement"
        verbose_name_plural = "Service Level Agreements"

class Measurement(models.Model):
    """
    Represents a measurement of an SLI for a specific reporting period.
    """
    reporting_period = models.ForeignKey(ReportingPeriod, on_delete=models.CASCADE, related_name='measurements')
    sli = models.ForeignKey(ServiceLevelIndicator, on_delete=models.CASCADE, related_name='measurements')
    reported_value = models.FloatField()
    calculated_value = models.FloatField()
    is_disputed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reporting_period} - {self.sli.name}"

    class Meta:
        unique_together = ['reporting_period', 'sli']

class ComplianceReport(models.Model):
    """
    Represents a compliance report for a reporting period.
    """
    reporting_period = models.OneToOneField(ReportingPeriod, on_delete=models.CASCADE, related_name='compliance_report')
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Compliance Report for {self.reporting_period}"

    def generate(self):
        """
        Generate compliance report items for all SLAs in the contract.
        """
        # Delete existing report items
        self.items.all().delete()

        # Get all SLAs for the contract
        slas = self.reporting_period.contract.slas.all()

        # Create report items for each SLA with an SLI
        for sla in slas:
            if sla.sli:
                try:
                    measurement = Measurement.objects.get(
                        reporting_period=self.reporting_period,
                        sli=sla.sli
                    )

                    is_compliant = False
                    if sla.threshold_type == 'MIN':
                        is_compliant = measurement.calculated_value >= sla.threshold_value
                    elif sla.threshold_type == 'MAX':
                        is_compliant = measurement.calculated_value <= sla.threshold_value

                    ComplianceReportItem.objects.create(
                        report=self,
                        sla=sla,
                        measurement=measurement,
                        is_compliant=is_compliant
                    )
                except Measurement.DoesNotExist:
                    # No measurement for this SLI in this period
                    pass

class ComplianceReportItem(models.Model):
    """
    Represents an item in a compliance report, linking an SLA to its measurement.
    """
    report = models.ForeignKey(ComplianceReport, on_delete=models.CASCADE, related_name='items')
    sla = models.ForeignKey(ServiceLevelAgreement, on_delete=models.CASCADE)
    measurement = models.ForeignKey(Measurement, on_delete=models.CASCADE)
    is_compliant = models.BooleanField()

    def __str__(self):
        return f"{self.sla.name} - {'Compliant' if self.is_compliant else 'Non-compliant'}"
