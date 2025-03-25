from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from django.contrib import messages
from django.utils import timezone

from .models import (
    Tenant, Contract, ReportingPeriod, 
    ComplianceReport, ComplianceReportItem,
    ServiceLevelAgreement, Measurement,
    ContractTemplate, Document
)

@login_required
def dashboard(request):
    """
    Dashboard view showing all tenants, contracts, and summary statistics.
    """
    tenants = Tenant.objects.all()
    contracts = Contract.objects.all().select_related('tenant', 'template')

    # Get counts for each tenant
    for tenant in tenants:
        tenant.contract_count = Contract.objects.filter(tenant=tenant).count()
        tenant.active_contract_count = Contract.objects.filter(
            tenant=tenant, 
            status='ACTIVE'
        ).count()

    # Get compliance statistics for each contract
    for contract in contracts:
        # Get the latest reporting period with a compliance report
        latest_period = ReportingPeriod.objects.filter(
            contract=contract,
            compliance_report__isnull=False
        ).order_by('-end_date').first()

        if latest_period:
            try:
                report = latest_period.compliance_report
                items = report.items.all()
                compliant_count = items.filter(is_compliant=True).count()
                total_count = items.count()

                if total_count > 0:
                    contract.compliance_percentage = (compliant_count / total_count) * 100
                else:
                    contract.compliance_percentage = None

                contract.latest_report_date = report.generated_at
                contract.latest_period = latest_period
            except ComplianceReport.DoesNotExist:
                contract.compliance_percentage = None
                contract.latest_report_date = None
                contract.latest_period = None
        else:
            contract.compliance_percentage = None
            contract.latest_report_date = None
            contract.latest_period = None

    context = {
        'tenants': tenants,
        'contracts': contracts,
        'total_contracts': Contract.objects.count(),
        'total_active_contracts': Contract.objects.filter(status='ACTIVE').count(),
    }

    return render(request, 'contracts/dashboard.html', context)

@login_required
def tenant_detail(request, tenant_id):
    """
    Tenant detail view showing all contracts for a tenant.
    """
    tenant = get_object_or_404(Tenant, id=tenant_id)
    contracts = Contract.objects.filter(tenant=tenant)

    # Get compliance statistics for each contract
    for contract in contracts:
        # Get the latest reporting period with a compliance report
        latest_period = ReportingPeriod.objects.filter(
            contract=contract,
            compliance_report__isnull=False
        ).order_by('-end_date').first()

        if latest_period:
            try:
                report = latest_period.compliance_report
                items = report.items.all()
                compliant_count = items.filter(is_compliant=True).count()
                total_count = items.count()

                if total_count > 0:
                    contract.compliance_percentage = (compliant_count / total_count) * 100
                else:
                    contract.compliance_percentage = None

                contract.latest_report_date = report.generated_at
            except ComplianceReport.DoesNotExist:
                contract.compliance_percentage = None
                contract.latest_report_date = None
        else:
            contract.compliance_percentage = None
            contract.latest_report_date = None

    context = {
        'tenant': tenant,
        'contracts': contracts,
    }

    return render(request, 'contracts/tenant_detail.html', context)

@login_required
def contract_detail(request, contract_id):
    """
    Contract detail view showing all reporting periods and their compliance status.
    Allows filtering by reporting period and number of periods to show.
    """
    contract = get_object_or_404(Contract, id=contract_id)

    # Get filter parameters from request
    months = request.GET.get('months', '12')  # Default to 12 months
    try:
        months = int(months)
        if months <= 0:
            months = 12
    except ValueError:
        months = 12

    # Get all reporting periods for this contract
    all_periods = ReportingPeriod.objects.filter(contract=contract).order_by('-start_date')

    # Apply filter if specified
    if months:
        # Get the last N months of reporting periods
        reporting_periods = all_periods[:months]
    else:
        reporting_periods = all_periods

    # Get compliance statistics for each reporting period
    for period in reporting_periods:
        try:
            report = period.compliance_report
            items = report.items.all()
            compliant_count = items.filter(is_compliant=True).count()
            total_count = items.count()

            if total_count > 0:
                period.compliance_percentage = (compliant_count / total_count) * 100
            else:
                period.compliance_percentage = None

            period.has_report = True
        except (ComplianceReport.DoesNotExist, AttributeError):
            period.compliance_percentage = None
            period.has_report = False

    context = {
        'contract': contract,
        'reporting_periods': reporting_periods,
        'all_periods_count': all_periods.count(),
        'months': months,
    }

    return render(request, 'contracts/contract_detail.html', context)

@login_required
def reporting_period_detail(request, period_id):
    """
    Reporting period detail view showing the compliance report with SLA details.
    """
    period = get_object_or_404(ReportingPeriod, id=period_id)

    # Check if a compliance report exists, if not, create one
    try:
        report = period.compliance_report
    except ComplianceReport.DoesNotExist:
        report = ComplianceReport.objects.create(reporting_period=period)
        report.generate()
        messages.success(request, "A new compliance report has been generated.")

    # Get all report items
    report_items = report.items.all().select_related('sla', 'measurement')

    # Calculate overall compliance
    total_items = report_items.count()
    compliant_items = report_items.filter(is_compliant=True).count()

    if total_items > 0:
        compliance_percentage = (compliant_items / total_items) * 100
    else:
        compliance_percentage = None

    # Organize items by SLA hierarchy
    root_slas = ServiceLevelAgreement.objects.filter(
        contract=period.contract,
        parent__isnull=True
    )

    # Build a tree structure for the template
    sla_tree = []
    for root_sla in root_slas:
        sla_node = _build_sla_tree(root_sla, report_items)
        if sla_node:
            sla_tree.append(sla_node)

    context = {
        'period': period,
        'contract': period.contract,
        'report': report,
        'report_items': report_items,
        'compliance_percentage': compliance_percentage,
        'compliant_items': compliant_items,
        'total_items': total_items,
        'sla_tree': sla_tree,
    }

    return render(request, 'contracts/reporting_period_detail.html', context)

@login_required
def generate_report(request, period_id):
    """
    Generate or regenerate a compliance report for a reporting period.
    """
    period = get_object_or_404(ReportingPeriod, id=period_id)

    try:
        report = period.compliance_report
    except ComplianceReport.DoesNotExist:
        report = ComplianceReport.objects.create(reporting_period=period)

    report.generate()
    messages.success(request, "Compliance report has been generated successfully.")

    return redirect('reporting_period_detail', period_id=period.id)

@login_required
def template_detail(request, template_id):
    """
    Contract template detail view showing template information and related contracts.
    """
    template = get_object_or_404(ContractTemplate, id=template_id)
    related_contracts = Contract.objects.filter(template=template).select_related('tenant')

    # Get compliance statistics for each related contract
    for contract in related_contracts:
        # Get the latest reporting period with a compliance report
        latest_period = ReportingPeriod.objects.filter(
            contract=contract,
            compliance_report__isnull=False
        ).order_by('-end_date').first()

        if latest_period:
            try:
                report = latest_period.compliance_report
                items = report.items.all()
                compliant_count = items.filter(is_compliant=True).count()
                total_count = items.count()

                if total_count > 0:
                    contract.compliance_percentage = (compliant_count / total_count) * 100
                else:
                    contract.compliance_percentage = None

                contract.latest_report_date = report.generated_at
            except ComplianceReport.DoesNotExist:
                contract.compliance_percentage = None
                contract.latest_report_date = None
        else:
            contract.compliance_percentage = None
            contract.latest_report_date = None

    context = {
        'template': template,
        'related_contracts': related_contracts,
        'documents': template.documents.all(),
    }

    return render(request, 'contracts/template_detail.html', context)

def _build_sla_tree(sla, report_items):
    """
    Helper function to build a tree structure of SLAs with their report items.
    """
    # Find the report item for this SLA
    report_item = None
    for item in report_items:
        if item.sla_id == sla.id:
            report_item = item
            break

    # Build node for this SLA
    node = {
        'sla': sla,
        'report_item': report_item,
        'children': []
    }

    # Add children recursively
    for child_sla in sla.children.all():
        child_node = _build_sla_tree(child_sla, report_items)
        if child_node:
            node['children'].append(child_node)

    return node
