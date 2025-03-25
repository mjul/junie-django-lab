from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Tenant, Document, ContractTemplate, Party, Contract,
    ReportingPeriod, ServiceLevelIndicator, ServiceLevelAgreement,
    Measurement, ComplianceReport, ComplianceReportItem
)

class DocumentInline(admin.TabularInline):
    model = ContractTemplate.documents.through
    extra = 1

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'uploaded_at', 'file_link')
    search_fields = ('name',)

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View File</a>', obj.file.url)
        return '-'
    file_link.short_description = 'File'

@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'publication_date', 'created_at')
    list_filter = ('tenant', 'publication_date')
    search_fields = ('name', 'tenant__name')
    inlines = [DocumentInline]
    exclude = ('documents',)

class PartyInline(admin.TabularInline):
    model = Contract.parties.through
    extra = 1

class ReportingPeriodInline(admin.TabularInline):
    model = ReportingPeriod
    extra = 0
    readonly_fields = ('start_date', 'end_date', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    list_filter = ('type',)
    search_fields = ('name',)

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'template', 'status', 'effective_date', 'expiration_date')
    list_filter = ('tenant', 'status', 'reporting_frequency')
    search_fields = ('name', 'tenant__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('tenant', 'template', 'name', 'status')
        }),
        ('Dates', {
            'fields': ('signature_date', 'effective_date', 'expiration_date')
        }),
        ('Reporting', {
            'fields': ('reporting_frequency',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [PartyInline, ReportingPeriodInline]
    exclude = ('parties',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Generate reporting periods if needed
        if obj.effective_date and obj.status == 'ACTIVE' and not obj.reporting_periods.exists():
            obj.generate_reporting_periods()

@admin.register(ReportingPeriod)
class ReportingPeriodAdmin(admin.ModelAdmin):
    list_display = ('contract', 'start_date', 'end_date', 'has_compliance_report')
    list_filter = ('contract__tenant', 'start_date')
    search_fields = ('contract__name',)
    readonly_fields = ('created_at',)

    def has_compliance_report(self, obj):
        try:
            return bool(obj.compliance_report)
        except ComplianceReport.DoesNotExist:
            return False
    has_compliance_report.boolean = True
    has_compliance_report.short_description = 'Has Compliance Report'

    actions = ['generate_compliance_reports']

    def generate_compliance_reports(self, request, queryset):
        count = 0
        for period in queryset:
            try:
                report = ComplianceReport.objects.get(reporting_period=period)
            except ComplianceReport.DoesNotExist:
                report = ComplianceReport.objects.create(reporting_period=period)

            report.generate()
            count += 1

        self.message_user(request, f"Generated {count} compliance reports.")
    generate_compliance_reports.short_description = "Generate compliance reports for selected periods"

@admin.register(ServiceLevelIndicator)
class ServiceLevelIndicatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'description')
    search_fields = ('name', 'description')

class ServiceLevelAgreementInline(admin.TabularInline):
    model = ServiceLevelAgreement
    fk_name = 'parent'
    extra = 1
    fields = ('name', 'sli', 'threshold_type', 'threshold_value')

@admin.register(ServiceLevelAgreement)
class ServiceLevelAgreementAdmin(admin.ModelAdmin):
    list_display = ('name', 'contract', 'parent', 'sli', 'threshold_type', 'threshold_value')
    list_filter = ('contract__tenant', 'threshold_type')
    search_fields = ('name', 'contract__name', 'sli__name')
    inlines = [ServiceLevelAgreementInline]

@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ('sli', 'reporting_period', 'reported_value', 'calculated_value', 'is_disputed')
    list_filter = ('reporting_period__contract__tenant', 'is_disputed', 'sli')
    search_fields = ('sli__name', 'reporting_period__contract__name')
    readonly_fields = ('created_at', 'updated_at')

class ComplianceReportItemInline(admin.TabularInline):
    model = ComplianceReportItem
    extra = 0
    readonly_fields = ('sla', 'measurement', 'is_compliant')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = ('reporting_period', 'generated_at', 'compliance_status')
    list_filter = ('reporting_period__contract__tenant',)
    search_fields = ('reporting_period__contract__name',)
    readonly_fields = ('generated_at', 'updated_at')
    inlines = [ComplianceReportItemInline]

    def compliance_status(self, obj):
        items = obj.items.all()
        if not items:
            return 'No data'

        compliant_count = items.filter(is_compliant=True).count()
        total_count = items.count()
        percentage = (compliant_count / total_count) * 100 if total_count > 0 else 0

        if percentage == 100:
            return format_html('<span style="color: green;">Fully Compliant (100%)</span>')
        elif percentage >= 80:
            return format_html('<span style="color: orange;">Mostly Compliant ({:.1f}%)</span>', percentage)
        else:
            return format_html('<span style="color: red;">Non-Compliant ({:.1f}%)</span>', percentage)
    compliance_status.short_description = 'Compliance Status'

    actions = ['regenerate_reports']

    def regenerate_reports(self, request, queryset):
        for report in queryset:
            report.generate()

        self.message_user(request, f"Regenerated {queryset.count()} compliance reports.")
    regenerate_reports.short_description = "Regenerate selected compliance reports"

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
