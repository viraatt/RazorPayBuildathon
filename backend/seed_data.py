import csv
import random
from datetime import datetime, timedelta

def generate_dataset():
    random.seed(42)  # Deterministic reproducibility
    base_date = datetime(2025, 5, 1)

    bank_records = []
    ledger_records = []
    ground_truth = []

    bank_idx = 100
    ledger_idx = 100

    # 1. Exact Matches (25 pairs)
    exact_vendors = [
        ("AWS EMEA SARL", "Amazon Web Services cloud hosting INV-"),
        ("Google Cloud Platform", "Monthly compute GCP-EU-"),
        ("Slack Technologies Inc", "Slack Business+ Tier license SLK-"),
        ("Snowflake Inc", "Data warehouse usage Q2 SNOW-"),
        ("Figma Inc", "Design team seats FIG-"),
        ("Atlassian Corp", "Jira & Confluence Cloud ATL-"),
        ("Datadog Ireland Ltd", "Infra monitoring DD-"),
        ("Stripe Inc", "Processing fee settlement STR-"),
        ("Twilio Inc", "SMS API usage TW-"),
        ("Zoom Video Comms", "Enterprise video conferencing ZM-"),
        ("Notion Labs Inc", "Team workspace licenses NTN-"),
        ("Vercel Inc", "Frontend Edge Hosting VRC-"),
        ("MongoDB Cloud", "Atlas Database production cluster MNG-"),
        ("GitHub Inc", "GitHub Enterprise team seats GH-"),
        ("OpenAI LLC", "API consumption tier OPENAI-"),
        ("Salesforce Inc", "CRM Enterprise CRM-"),
        ("HubSpot Inc", "Marketing automation HUB-"),
        ("DocuSign Inc", "Corporate e-signature tier DOC-"),
        ("Sendgrid Inc", "Transactional email delivery SG-"),
        ("Linear Orbit Inc", "Linear Issue tracking software LIN-"),
        ("Postman Inc", "API Platform team license PST-"),
        ("Cloudflare Inc", "Enterprise DNS and DDoS CLD-"),
        ("Miro Visual", "Online whiteboard collaboration MR-"),
        ("Supabase Inc", "Postgres enterprise tier SPB-"),
        ("Retool Inc", "Internal tooling software RTL-")
    ]

    for vendor, desc_prefix in exact_vendors:
        bank_idx += 1
        ledger_idx += 1
        amt = round(random.uniform(150.00, 4500.00), 2)
        day_offset = random.randint(1, 25)
        txn_date = (base_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        ref_id = f"REF-{random.randint(100000, 999999)}"
        inv_no = f"INV-{random.randint(10000, 99999)}"
        full_desc = f"{desc_prefix}{inv_no}"

        bank_records.append({
            "reference_id": ref_id,
            "txn_date": txn_date,
            "amount": amt,
            "currency": "USD",
            "counterparty": vendor,
            "description": f"Wire transfer to {vendor} - Ref {ref_id} - {full_desc}"
        })

        ledger_records.append({
            "invoice_number": inv_no,
            "txn_date": txn_date,
            "amount": amt,
            "currency": "USD",
            "vendor_name": vendor,
            "description": f"Bill payout: {full_desc}",
            "gl_account": "6000-TECH-OPEX"
        })

        ground_truth.append({
            "bank_ref": ref_id,
            "ledger_inv": inv_no,
            "expected_match": "TRUE",
            "category": "exact_match",
            "notes": "Exact amount, date, and vendor match"
        })

    # 2. Fuzzy Matches (15 pairs: spelling drift, ACH 1-2 day lag, minor rounding delta)
    fuzzy_cases = [
        ("Acme Corporation", "ACME CORP LLC", 1250.00, 1250.00, 1, "ACH payment lag + legal entity normalization"),
        ("Deloitte Consulting LLP", "Deloitte Advisory", 8450.00, 8450.00, 2, "Vendor name truncation + 2 day bank posting lag"),
        ("Oracle America Inc", "ORACLE CORP", 3400.50, 3400.48, 0, "2 cent rounding difference"),
        ("WeWork Management LLC", "WeWork Coworking", 2100.00, 2100.00, 1, "Vendor alias match"),
        ("KPMG Advisory Services", "KPMG US LLP", 9200.00, 9200.00, 2, "Advisory division naming variance"),
        ("Federal Express Corp", "FedEx Express", 342.10, 342.10, 0, "Abbreviated counterparty branding"),
        ("United Parcel Service", "UPS Freight Delivery", 512.80, 512.80, 1, "Freight brand variant + 1 day lag"),
        ("Intercom R&D Unlimited", "Intercom Inc", 780.00, 779.95, 0, "5 cent wire fee delta"),
        ("Gartner Group Inc", "Gartner Research", 6500.00, 6500.00, 1, "Research subsidiary descriptor"),
        ("Tableau Software Inc", "Tableau Analytics LLC", 1850.00, 1850.00, 2, "Analytics subsidiary naming"),
        ("Mixpanel Inc", "MIXPANEL ANALYTICS", 920.00, 920.00, 1, "All caps with functional suffix"),
        ("Brex Corporate Card", "Brex Card Monthly Spend", 4230.15, 4230.15, 0, "Card statement description match"),
        ("Papertrail SolarWinds", "Solarwinds MSP", 195.00, 195.00, 1, "Product vs parent company brand"),
        ("Deel Global Payroll", "Deel Inc US Payout", 14500.00, 14500.00, 2, "Payroll platform processor tag"),
        ("Ramp Business Card", "Ramp Corporate Pay", 3890.40, 3890.40, 1, "Corporate treasury settlement tag")
    ]

    for b_name, l_name, b_amt, l_amt, date_lag, rationale in fuzzy_cases:
        bank_idx += 1
        ledger_idx += 1
        day = random.randint(1, 20)
        b_date = (base_date + timedelta(days=day + date_lag)).strftime("%Y-%m-%d")
        l_date = (base_date + timedelta(days=day)).strftime("%Y-%m-%d")
        ref_id = f"REF-{random.randint(100000, 999999)}"
        inv_no = f"INV-{random.randint(10000, 99999)}"

        bank_records.append({
            "reference_id": ref_id,
            "txn_date": b_date,
            "amount": b_amt,
            "currency": "USD",
            "counterparty": b_name,
            "description": f"Direct Debit / Wire: {b_name} - {ref_id}"
        })

        ledger_records.append({
            "invoice_number": inv_no,
            "txn_date": l_date,
            "amount": l_amt,
            "currency": "USD",
            "vendor_name": l_name,
            "description": f"AP Ledger entry for {l_name} - Inv {inv_no}",
            "gl_account": "6100-PROF-SERVICES"
        })

        ground_truth.append({
            "bank_ref": ref_id,
            "ledger_inv": inv_no,
            "expected_match": "TRUE",
            "category": "fuzzy_match",
            "notes": rationale
        })

    # 3. Trap Cases (5 pairs: Identical amount and exact same date, but completely unrelated vendors)
    # The agent MUST NOT match these.
    traps = [
        ("Delta Air Lines", "Shell Oil Station", 450.00),
        ("Starbucks HQ Catering", "Home Depot Tools", 120.00),
        ("Uber For Business", "USPS Postal Store", 85.50),
        ("Best Buy Electronics", "Hilton Hotels Booking", 950.00),
        ("Lyft Corporate Rides", "Subway Sandwiches", 65.00)
    ]

    for b_vendor, l_vendor, amt in traps:
        bank_idx += 1
        ledger_idx += 1
        txn_date = (base_date + timedelta(days=random.randint(5, 22))).strftime("%Y-%m-%d")
        ref_id = f"REF-TRAP-{random.randint(100000, 999999)}"
        inv_no = f"INV-TRAP-{random.randint(10000, 99999)}"

        bank_records.append({
            "reference_id": ref_id,
            "txn_date": txn_date,
            "amount": amt,
            "currency": "USD",
            "counterparty": b_vendor,
            "description": f"POS Purchase - {b_vendor}"
        })

        ledger_records.append({
            "invoice_number": inv_no,
            "txn_date": txn_date,
            "amount": amt,
            "currency": "USD",
            "vendor_name": l_vendor,
            "description": f"Expense claim submitted for {l_vendor}",
            "gl_account": "6200-TRAVEL-MEALS"
        })

        ground_truth.append({
            "bank_ref": ref_id,
            "ledger_inv": inv_no,
            "expected_match": "FALSE",
            "category": "trap_do_not_match",
            "notes": "Coincidental identical amount and date, but distinct unrelated counterparties"
        })

    # 4. Bank Exceptions (8 records: Bank debit with zero matching ledger counterpart)
    bank_exceptions = [
        ("Silicon Valley Bank", 45.00, "Monthly Treasury Account Maintenance Fee"),
        ("State Tax Franchise Board", 800.00, "Annual Franchise Tax direct levy"),
        ("Unrecognized International Wire", 3200.00, "Inbound MT103 Wire Unknown Origin"),
        ("JPMorgan Escrow Fee", 250.00, "Quarterly escrow holding charge"),
        ("Foreign Currency Conversion Surcharge", 78.40, "Non-USD transaction fee FX"),
        ("Bank NSF Charge", 35.00, "Returned item handling fee"),
        ("City Parking Authority Meter", 18.00, "Automated parking kiosk debit"),
        ("Overdraft Protection Charge", 50.00, "Treasury line automated draw fee")
    ]

    for cp, amt, desc in bank_exceptions:
        ref_id = f"REF-EXC-{random.randint(100000, 999999)}"
        txn_date = (base_date + timedelta(days=random.randint(1, 28))).strftime("%Y-%m-%d")
        bank_records.append({
            "reference_id": ref_id,
            "txn_date": txn_date,
            "amount": amt,
            "currency": "USD",
            "counterparty": cp,
            "description": desc
        })
        ground_truth.append({
            "bank_ref": ref_id,
            "ledger_inv": "NONE",
            "expected_match": "FALSE",
            "category": "bank_exception_missing_ledger",
            "notes": "Legitimate bank line with missing internal ERP booking"
        })

    # 5. Ledger Exceptions (17 records: Internal bills awaiting payment/clearing or rejected)
    ledger_exceptions = [
        ("Mckinsey Strategy Group", 24000.00, "Consulting milestone #2 invoice (unpaid)"),
        ("Cisco Systems Capital", 5600.00, "Hardware router purchase PO-9883 (check not cashed)"),
        ("WeWork Q3 Security Deposit", 6300.00, "Escrow deposit deferred"),
        ("Ernst & Young Audit", 18000.00, "Year-end financial audit retainer installment"),
        ("Korn Ferry Executive Search", 12500.00, "VP Engineering recruitment fee milestone"),
        ("Palo Alto Networks", 7400.00, "Firewall enterprise subscription renewal"),
        ("Workday Inc", 9800.00, "HRIS implementation phase 3"),
        ("Iron Mountain Storage", 310.00, "Archival storage box collection"),
        ("Shred-It Document Destruction", 145.00, "Bi-weekly secure document bin service"),
        ("Herman Miller Furniture", 4200.00, "Ergonomic seating invoice pending approval"),
        ("CDW Direct Tech Supply", 1890.00, "Monitor mounts and docking stations"),
        ("Anaplan Software", 11200.00, "Financial planning module subscription"),
        ("Splunk Enterprise", 6700.00, "Log aggregation cluster license"),
        ("Zendesk Support Enterprise", 3200.00, "Customer service seat expansions"),
        ("Qualtrics Survey Software", 5400.00, "Employee NPS survey platform"),
        ("Coupa Procurement", 8900.00, "Procure-to-pay cloud software"),
        ("CBRE Facilities Management", 3750.00, "HVAC quarterly maintenance contract")
    ]

    for vendor, amt, desc in ledger_exceptions:
        inv_no = f"INV-EXC-{random.randint(10000, 99999)}"
        txn_date = (base_date + timedelta(days=random.randint(1, 28))).strftime("%Y-%m-%d")
        ledger_records.append({
            "invoice_number": inv_no,
            "txn_date": txn_date,
            "amount": amt,
            "currency": "USD",
            "vendor_name": vendor,
            "description": desc,
            "gl_account": "2000-ACCOUNTS-PAYABLE"
        })
        ground_truth.append({
            "bank_ref": "NONE",
            "ledger_inv": inv_no,
            "expected_match": "FALSE",
            "category": "ledger_exception_uncleared",
            "notes": "Accrued bill not yet reflected in bank clearing"
        })

    # Shuffle for realism
    random.shuffle(bank_records)
    random.shuffle(ledger_records)

    # Write Bank Feed CSV
    with open("data/bank_feed.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["reference_id", "txn_date", "amount", "currency", "counterparty", "description"])
        writer.writeheader()
        writer.writerows(bank_records)

    # Write Ledger CSV
    with open("data/ledger_records.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["invoice_number", "txn_date", "amount", "currency", "vendor_name", "description", "gl_account"])
        writer.writeheader()
        writer.writerows(ledger_records)

    # Write Ground Truth CSV
    with open("data/ground_truth.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["bank_ref", "ledger_inv", "expected_match", "category", "notes"])
        writer.writeheader()
        writer.writerows(ground_truth)

    print(f"Generated:")
    print(f" - data/bank_feed.csv ({len(bank_records)} rows)")
    print(f" - data/ledger_records.csv ({len(ledger_records)} rows)")
    print(f" - data/ground_truth.csv ({len(ground_truth)} benchmark entries)")
    print(f"Total True Matchable Pairs: 40 (25 exact + 15 fuzzy)")
    print(f"Total Trap Pairs (Should reject): 5")
    print(f"Total True Exceptions: 25 (8 bank + 17 ledger)")

if __name__ == "__main__":
    generate_dataset()
