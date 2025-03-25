from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from contracts.models import (
    Tenant, ContractTemplate, ServiceLevelIndicator, ServiceLevelAgreement, Contract, Party,
    ReportingPeriod, Measurement
)
import random
from datetime import date

class Command(BaseCommand):
    help = 'Adds demo data to the database for demonstration purposes'

    def generate_random_measurements_for_jan_2023_contract(self, contract):
        """
        Generate random measurement data for each reporting period of the contract.
        The reported value will be half the SLA threshold plus 10% noise.
        """
        self.stdout.write('Generating random measurement data for contract: ' + contract.name)

        # Get all reporting periods for the contract
        reporting_periods = ReportingPeriod.objects.filter(contract=contract)

        # Get all SLAs with SLIs for the contract
        slas = ServiceLevelAgreement.objects.filter(contract=contract, sli__isnull=False)

        # For each reporting period and SLA, create a Measurement
        for period in reporting_periods:
            for sla in slas:
                # Calculate half the threshold value
                half_threshold = sla.threshold_value / 2

                # Add 10% random noise
                noise_factor = 1.0 + (random.random() * 0.2 - 0.1)  # Random value between 0.9 and 1.1
                reported_value = half_threshold * noise_factor

                # Create or update the measurement
                measurement, created = Measurement.objects.update_or_create(
                    reporting_period=period,
                    sli=sla.sli,
                    defaults={
                        'reported_value': reported_value,
                        'calculated_value': reported_value  # For simplicity, set calculated_value equal to reported_value
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'Created measurement for {period} - {sla.name}: {reported_value:.2f}'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Updated measurement for {period} - {sla.name}: {reported_value:.2f}'
                    ))

    def handle(self, *args, **options):
        self.stdout.write('Adding demo data...')

        # Create Demo tenant
        demo_tenant, created = Tenant.objects.get_or_create(
            name='Demo'
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Demo tenant'))
        else:
            self.stdout.write(self.style.WARNING(f'Demo tenant already exists'))

        # Create admin user if it doesn't exist
        admin_username = 'admin'
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                email='admin@example.com',
                password='adminpassword'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user'))
        else:
            self.stdout.write(self.style.WARNING(f'Admin user already exists'))

        # Create Standard Terms 2023 template
        template_2023, created = ContractTemplate.objects.get_or_create(
            tenant=demo_tenant,
            name='Standard Terms 2023',
            defaults={
                'publication_date': date(2023, 1, 1)
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Standard Terms 2023 template'))
        else:
            self.stdout.write(self.style.WARNING(f'Standard Terms 2023 template already exists'))

        # Create Standard Terms 2025 template
        template_2025, created = ContractTemplate.objects.get_or_create(
            tenant=demo_tenant,
            name='Standard Terms 2025',
            defaults={
                'publication_date': date(2025, 1, 1)
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Standard Terms 2025 template'))
        else:
            self.stdout.write(self.style.WARNING(f'Standard Terms 2025 template already exists'))

        # Create SLIs for remediation
        sli_p1, created = ServiceLevelIndicator.objects.get_or_create(
            name='Priority 1 Time to Fix',
            defaults={
                'description': 'Maximum time to fix Priority 1 issues',
                'unit': 'hours'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Priority 1 Time to Fix SLI'))

        sli_p2, created = ServiceLevelIndicator.objects.get_or_create(
            name='Priority 2 Time to Fix',
            defaults={
                'description': 'Maximum time to fix Priority 2 issues',
                'unit': 'hours'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Priority 2 Time to Fix SLI'))

        sli_p3, created = ServiceLevelIndicator.objects.get_or_create(
            name='Priority 3 Time to Fix',
            defaults={
                'description': 'Maximum time to fix Priority 3 issues',
                'unit': 'days'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Priority 3 Time to Fix SLI'))

        # Additional SLIs for 2025 template
        sli_p4, created = ServiceLevelIndicator.objects.get_or_create(
            name='Priority 4 Time to Fix',
            defaults={
                'description': 'Maximum time to fix Priority 4 issues',
                'unit': 'days'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Priority 4 Time to Fix SLI'))

        sli_p5, created = ServiceLevelIndicator.objects.get_or_create(
            name='Priority 5 Time to Fix',
            defaults={
                'description': 'Maximum time to fix Priority 5 issues',
                'unit': 'days'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Priority 5 Time to Fix SLI'))

        # Create Contract instances
        # 1. Standard Terms 2023 - Jan 1, 2023 - Signed
        contract_2023_jan, created = Contract.objects.get_or_create(
            tenant=demo_tenant,
            template=template_2023,
            name='Standard Terms 2023 - Jan 2023',
            defaults={
                'signature_date': date(2022, 12, 15),  # Signed before effective date
                'effective_date': date(2023, 1, 1),
                'expiration_date': date(2026, 1, 1),  # 3 years duration
                'status': 'ACTIVE',  # Signed status
                'reporting_frequency': 'MONTHLY'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Standard Terms 2023 - Jan 2023 contract'))

            # Create a top-level "Mitigation" SLA node
            mitigation_sla, _ = ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2023_jan,
                name='Mitigation',
                defaults={
                    'description': 'Top-level node for mitigation SLAs'
                }
            )

            # Create SLAs for this contract as children of the Mitigation node
            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2023_jan,
                name='Priority 1 Remediation',
                parent=mitigation_sla,
                sli=sli_p1,
                threshold_type='MAX',
                threshold_value=1.0  # 1 hour
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2023_jan,
                name='Priority 2 Remediation',
                parent=mitigation_sla,
                sli=sli_p2,
                threshold_type='MAX',
                threshold_value=24.0  # 24 hours
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2023_jan,
                name='Priority 3 Remediation',
                parent=mitigation_sla,
                sli=sli_p3,
                threshold_type='MAX',
                threshold_value=7.0  # 7 days
            )

        # 2. Standard Terms 2023 - Jan 1, 2024 - Signed
        contract_2023_jan_2024, created = Contract.objects.get_or_create(
            tenant=demo_tenant,
            template=template_2023,
            name='Standard Terms 2023 - Jan 2024',
            defaults={
                'signature_date': date(2023, 12, 15),  # Signed before effective date
                'effective_date': date(2024, 1, 1),
                'expiration_date': date(2027, 1, 1),  # 3 years duration
                'status': 'ACTIVE',  # Signed status
                'reporting_frequency': 'MONTHLY'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Standard Terms 2023 - Jan 2024 contract'))

            # Create a top-level "Mitigation" SLA node
            mitigation_sla, _ = ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2023_jan_2024,
                name='Mitigation',
                defaults={
                    'description': 'Top-level node for mitigation SLAs'
                }
            )

            # Create SLAs for this contract as children of the Mitigation node
            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2023_jan_2024,
                name='Priority 1 Remediation',
                parent=mitigation_sla,
                sli=sli_p1,
                threshold_type='MAX',
                threshold_value=1.0  # 1 hour
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2023_jan_2024,
                name='Priority 2 Remediation',
                parent=mitigation_sla,
                sli=sli_p2,
                threshold_type='MAX',
                threshold_value=24.0  # 24 hours
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2023_jan_2024,
                name='Priority 3 Remediation',
                parent=mitigation_sla,
                sli=sli_p3,
                threshold_type='MAX',
                threshold_value=7.0  # 7 days
            )

        # 3. Standard Terms 2025 - Jan 1, 2025 - Signed
        contract_2025_jan, created = Contract.objects.get_or_create(
            tenant=demo_tenant,
            template=template_2025,
            name='Standard Terms 2025 - Jan 2025',
            defaults={
                'signature_date': date(2024, 12, 15),  # Signed before effective date
                'effective_date': date(2025, 1, 1),
                'expiration_date': date(2028, 1, 1),  # 3 years duration
                'status': 'ACTIVE',  # Signed status
                'reporting_frequency': 'MONTHLY'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Standard Terms 2025 - Jan 2025 contract'))

            # Create a top-level "Mitigation" SLA node
            mitigation_sla, _ = ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_jan,
                name='Mitigation',
                defaults={
                    'description': 'Top-level node for mitigation SLAs'
                }
            )

            # Create SLAs for this contract as children of the Mitigation node
            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_jan,
                name='Priority 1 Remediation',
                parent=mitigation_sla,
                sli=sli_p1,
                threshold_type='MAX',
                threshold_value=1.0  # 1 hour
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_jan,
                name='Priority 2 Remediation',
                parent=mitigation_sla,
                sli=sli_p2,
                threshold_type='MAX',
                threshold_value=24.0  # 24 hours
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_jan,
                name='Priority 3 Remediation',
                parent=mitigation_sla,
                sli=sli_p3,
                threshold_type='MAX',
                threshold_value=7.0  # 7 days
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_jan,
                name='Priority 4 Remediation',
                parent=mitigation_sla,
                sli=sli_p4,
                threshold_type='MAX',
                threshold_value=14.0  # 14 days
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_jan,
                name='Priority 5 Remediation',
                parent=mitigation_sla,
                sli=sli_p5,
                threshold_type='MAX',
                threshold_value=30.0  # 30 days
            )

        # 4. Standard Terms 2025 - Mar 1, 2025 - Draft
        contract_2025_mar, created = Contract.objects.get_or_create(
            tenant=demo_tenant,
            template=template_2025,
            name='Standard Terms 2025 - Mar 2025',
            defaults={
                'signature_date': None,  # No signature date for draft
                'effective_date': date(2025, 3, 1),
                'expiration_date': date(2028, 3, 1),  # 3 years duration
                'status': 'DRAFT',  # Draft status
                'reporting_frequency': 'MONTHLY'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Standard Terms 2025 - Mar 2025 contract (Draft)'))

            # Create a top-level "Mitigation" SLA node
            mitigation_sla, _ = ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_mar,
                name='Mitigation',
                defaults={
                    'description': 'Top-level node for mitigation SLAs'
                }
            )

            # Create SLAs for this contract as children of the Mitigation node
            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_mar,
                name='Priority 1 Remediation',
                parent=mitigation_sla,
                sli=sli_p1,
                threshold_type='MAX',
                threshold_value=1.0  # 1 hour
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_mar,
                name='Priority 2 Remediation',
                parent=mitigation_sla,
                sli=sli_p2,
                threshold_type='MAX',
                threshold_value=24.0  # 24 hours
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_mar,
                name='Priority 3 Remediation',
                parent=mitigation_sla,
                sli=sli_p3,
                threshold_type='MAX',
                threshold_value=7.0  # 7 days
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_mar,
                name='Priority 4 Remediation',
                parent=mitigation_sla,
                sli=sli_p4,
                threshold_type='MAX',
                threshold_value=14.0  # 14 days
            )

            ServiceLevelAgreement.objects.get_or_create(
                contract=contract_2025_mar,
                name='Priority 5 Remediation',
                parent=mitigation_sla,
                sli=sli_p5,
                threshold_type='MAX',
                threshold_value=30.0  # 30 days
            )

        # Create parties
        # Create Shinin as a seller party
        shinin_party, created = Party.objects.get_or_create(
            name='Shinin',
            type='SELLER'
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Shinin party (Seller)'))
        else:
            self.stdout.write(self.style.WARNING(f'Shinin party already exists'))

        # Create Japanese-sounding buyer parties
        japanese_buyer_names = [
            'Tomuto', 'Makobintsu', 'Akimirai', 'Sakura', 'Tanaka',
            'Yamamoto', 'Nakamura', 'Suzuki', 'Takahashi', 'Watanabe'
        ]

        buyer_parties = []
        for name in japanese_buyer_names:
            buyer_party, created = Party.objects.get_or_create(
                name=name,
                type='BUYER'
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created {name} party (Buyer)'))
            else:
                self.stdout.write(self.style.WARNING(f'{name} party already exists'))
            buyer_parties.append(buyer_party)

        # Associate parties with contracts
        contracts = [
            contract_2023_jan,
            contract_2023_jan_2024,
            contract_2025_jan,
            contract_2025_mar
        ]

        # Clear existing parties from contracts and add new ones
        for i, contract in enumerate(contracts):
            contract.parties.clear()
            # Add Shinin as seller to all contracts
            contract.parties.add(shinin_party)
            # Add a different buyer to each contract
            buyer_index = i % len(buyer_parties)
            contract.parties.add(buyer_parties[buyer_index])
            self.stdout.write(self.style.SUCCESS(f'Associated {shinin_party.name} (Seller) and {buyer_parties[buyer_index].name} (Buyer) with {contract.name}'))

        # Generate random measurement data for the first contract from January 2023
        self.generate_random_measurements_for_jan_2023_contract(contract_2023_jan)

        self.stdout.write(self.style.SUCCESS('Demo data added successfully!'))
