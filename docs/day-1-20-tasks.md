# Day 1-20 Aleq Task Catalog

> **What is Day 1-20?**
> - Autonomy level: 20% → 52%
> - Primary mode: `guidance_seeking` → `action_proposal`
> - Aleq CAN: Retrieve data, generate reports, analyze, parse documents, PROPOSE actions
> - Aleq NEEDS APPROVAL: Creating entries, applying payments, making transfers
> - Aleq WON'T DO: Bank releases, autonomous payments, unsupervised journal entries

---

## Table of Contents

1. [Data Retrieval Tasks](#1-data-retrieval-tasks)
2. [Report Generation Tasks](#2-report-generation-tasks)
3. [Analysis Tasks](#3-analysis-tasks)
4. [Document Parsing Tasks](#4-document-parsing-tasks)
5. [Lookup & Search Tasks](#5-lookup--search-tasks)
6. [Research Tasks](#6-research-tasks)
7. [Calculation Tasks](#7-calculation-tasks)
8. [Monitoring & Alerts](#8-monitoring--alerts)
9. [**UTILITIES - OCR & File Operations**](#9-utilities---ocr--file-operations)

---

## 1. Data Retrieval Tasks

### 1.1 Bank Balance Collection
**Source:** Angela Park (StorageCorner) - Story 16

**Prompt:**
```
"What's our current cash position across all banks? I need balances for Chase, Glacier FCB, and Heritage Bank."
```

**Integrations:**
- `balance.get` (Stargate)
- Bank API connections (Chase, Glacier, Heritage)

**Expected Output:** Total portfolio cash with breakdown by bank and account type

---

### 1.2 Property-Level Cash Position
**Source:** Angela Park (StorageCorner) - Story 16

**Prompt:**
```
"Show me the operating account balances for each property. Flag any that are below $50,000."
```

**Integrations:**
- `balance.get` (Stargate)
- `account.list` (filter by property)

**Expected Output:** Table of property balances with low-balance alerts

---

### 1.3 Vendor Payment History
**Source:** Kevin Chen (Dockwa) - Story 2

**Prompt:**
```
"Pull up our payment history with AquaTech Solutions. I need to see the last 6 months of payments."
```

**Integrations:**
- `vendor.get` (Stargate)
- `bill.list` (filter by vendor)
- `payment.list` (filter by vendor)

**Expected Output:** Payment timeline with amounts, dates, and payment methods

---

### 1.4 Customer Outstanding Balance
**Source:** Alex Thompson (Dockwa) - Story 1

**Prompt:**
```
"What's the outstanding balance for Hartwell Marina? They're claiming they're current on payments."
```

**Integrations:**
- `customer.get` (Stargate)
- `invoice.list` (filter by customer, status=open)
- `payment.list` (filter by customer)

**Expected Output:** AR aging for specific customer with invoice details

---

### 1.5 Stripe Payout Status
**Source:** Kevin Chen (Dockwa) - Story 2

**Prompt:**
```
"Check our Stripe dashboard - did yesterday's payouts settle to Chase? How much was the total?"
```

**Integrations:**
- Stripe API (`payouts.list`)
- `balance.get` (Chase account)

**Expected Output:** Payout status, amounts, and settlement confirmation

---

### 1.6 Loan Balance Summary
**Source:** Amanda Torres (StorageCorner) - Story 23

**Prompt:**
```
"What's our total outstanding debt across all loan facilities? Break it down by lender."
```

**Integrations:**
- Bank portal APIs
- Loan tracking system

**Expected Output:** Debt summary by lender with rates and maturities

---

### 1.7 AP Aging Report
**Source:** Kevin Chen (Dockwa) - Story 2

**Prompt:**
```
"Give me our AP aging - I need to see what's due in the next 7 days and anything overdue."
```

**Integrations:**
- `bill.list` (Stargate)
- Filter by due date ranges

**Expected Output:** AP aging buckets with vendor breakdown

---

### 1.8 AR Aging Report
**Source:** Alex Thompson (Dockwa) - Story 1

**Prompt:**
```
"Pull the AR aging for all marina customers. Who's 60+ days past due?"
```

**Integrations:**
- `invoice.list` (Stargate)
- `customer.list` (Stargate)

**Expected Output:** AR aging with customer breakdown and contact info

---

## 2. Report Generation Tasks

### 2.1 Weekly Cash Position Report
**Source:** Angela Park / Michael Davis (StorageCorner) - Stories 16, 17

**Prompt:**
```
"Generate the weekly cash position report. Include week-over-week changes and any significant variances."
```

**Integrations:**
- `balance.get` (multiple accounts)
- `report.cashflow` (Stargate)
- Historical data comparison

**Expected Output:** Formatted report with totals, changes, and variance explanations

---

### 2.2 Budget-to-Actual Report
**Source:** StorageCorner scenarios

**Prompt:**
```
"Create a budget-to-actual report for Q3. Break it down by property and highlight variances over 10%."
```

**Integrations:**
- `report.profitloss` (Stargate)
- Budget data (internal)
- Variance calculations

**Expected Output:** B2A report with variance analysis by category

---

### 2.3 P&L Report by Property
**Source:** StorageCorner scenarios

**Prompt:**
```
"Generate P&L reports for each of our 23 properties for October. Export as Excel."
```

**Integrations:**
- `report.profitloss` (Stargate, filter by class/location)
- Export formatting

**Expected Output:** Multi-property P&L with consolidation

---

### 2.4 Manager Expense Report
**Source:** StorageCorner scenarios

**Prompt:**
```
"Create expense reports for each property manager showing their controllable expenses vs budget."
```

**Integrations:**
- `report.profitloss` (filter by manager/location)
- Budget data
- Filter for controllable expense categories

**Expected Output:** Manager-specific expense reports with budget comparison

---

### 2.5 Fee Allocation Report
**Source:** Rachel Kim (GGHC) - Story 6

**Prompt:**
```
"Generate the monthly fee allocation summary for November. Show management fees and performance fees by client."
```

**Integrations:**
- Power BI data extraction
- Fee calculation engine
- Client billing rates

**Expected Output:** Fee summary with client breakdown and totals

---

### 2.6 Treasury Management Report
**Source:** Michael Davis (StorageCorner) - Story 17

**Prompt:**
```
"Create the weekly treasury report with cash forecast, investment positions, and transfer recommendations."
```

**Integrations:**
- `balance.get` (all accounts)
- Investment tracking
- Forecast model

**Expected Output:** Comprehensive treasury report with action items

---

### 2.7 Vendor Payment Summary
**Source:** Kevin Chen (Dockwa) - Story 2

**Prompt:**
```
"Generate a payment summary for this week showing all scheduled payments, amounts, and payment methods."
```

**Integrations:**
- `bill.list` (scheduled payments)
- `payment.list` (pending)

**Expected Output:** Payment schedule with totals by method

---

### 2.8 Monthly Reconciliation Report
**Source:** Sarah Martinez (Dockwa) - Story 4

**Prompt:**
```
"Create the bank reconciliation report for October. Show matched items, unmatched items, and variances."
```

**Integrations:**
- Bank statement data
- `transaction.list` (GL)
- Matching algorithm

**Expected Output:** Reconciliation summary with exception list

---

## 3. Analysis Tasks

### 3.1 Expense Variance Investigation
**Source:** StorageCorner scenarios

**Prompt:**
```
"We're over budget on repairs and maintenance by $15,000. Can you break down what's driving that variance?"
```

**Integrations:**
- `report.profitloss` (detail by account)
- Transaction drill-down
- Historical comparison

**Expected Output:** Variance breakdown by transaction with explanations

---

### 3.2 Cash Flow Forecast
**Source:** Michael Davis (StorageCorner) - Story 17

**Prompt:**
```
"Build a 4-week cash flow forecast based on expected rent collections, scheduled payments, and known obligations."
```

**Integrations:**
- `invoice.list` (expected inflows)
- `bill.list` (expected outflows)
- Historical patterns
- Known upcoming payments

**Expected Output:** Week-by-week forecast with net cash flow

---

### 3.3 Debt Covenant Analysis
**Source:** Amanda Torres (StorageCorner) - Story 23

**Prompt:**
```
"Calculate our current DSCR for each property. Flag any that are within 20% of covenant minimums."
```

**Integrations:**
- NOI calculations
- Debt service data
- Covenant requirements

**Expected Output:** DSCR table with covenant status (Green/Yellow/Red)

---

### 3.4 LTV Ratio Analysis
**Source:** Amanda Torres (StorageCorner) - Story 23

**Prompt:**
```
"What's our current LTV ratio for Denver Storage Center? The lender is asking for an update."
```

**Integrations:**
- Loan balance data
- Property valuation (appraisal or estimate)
- Covenant requirements

**Expected Output:** LTV calculation with covenant comparison

---

### 3.5 Investment Yield Analysis
**Source:** Michael Davis (StorageCorner) - Story 17

**Prompt:**
```
"Compare our current cash positions to available investment options. What yield improvement could we get?"
```

**Integrations:**
- Current balance data
- Money market rates
- CD rates
- Treasury yields

**Expected Output:** Investment comparison with projected additional income

---

### 3.6 Competitive Analysis
**Source:** Jordan Blake (Dockwa) - Story 5

**Prompt:**
```
"Analyze the recent funding rounds for HarborTech and AquaMarina. What do they imply about valuations and competitive positioning?"
```

**Integrations:**
- Web search (Perplexity)
- Crunchbase data
- Internal metrics comparison

**Expected Output:** Competitive analysis with strategic implications

---

### 3.7 Market Sizing Analysis
**Source:** Jordan Blake (Dockwa) - Story 5

**Prompt:**
```
"Estimate the TAM for yacht club management software in North America. Use bottom-up methodology."
```

**Integrations:**
- Web search (industry data)
- Market research sources
- Financial modeling

**Expected Output:** TAM calculation with assumptions and segmentation

---

### 3.8 Payment Method Cost Analysis
**Source:** Kevin Chen (Dockwa) - Story 2

**Prompt:**
```
"Compare the cost of wire vs ACH for our urgent AquaTech payment. Is the $35 wire fee worth it?"
```

**Integrations:**
- Payment terms lookup
- Late fee calculations
- Cost comparison

**Expected Output:** Cost-benefit analysis with recommendation

---

### 3.9 Distribution Coverage Analysis
**Source:** StorageCorner scenarios

**Prompt:**
```
"Calculate our distribution coverage ratio for Q4. Do we have sufficient cash flow to cover investor distributions?"
```

**Integrations:**
- NOI projections
- Distribution schedule
- Cash reserves

**Expected Output:** Coverage ratio with go/no-go assessment

---

### 3.10 Property Performance Comparison
**Source:** StorageCorner scenarios

**Prompt:**
```
"Rank our properties by NOI margin. Which 5 are performing best and which 5 need attention?"
```

**Integrations:**
- `report.profitloss` (by property)
- NOI calculations
- Performance metrics

**Expected Output:** Property ranking with key metrics

---

## 4. Document Parsing Tasks

### 4.1 Lockbox PDF Extraction
**Source:** Alex Thompson (Dockwa) - Story 1

**Prompt:**
```
"I just got today's lockbox PDF. Can you extract all the check details - customer names, amounts, and any invoice references?"
```

**Integrations:**
- PDF parsing (OCR)
- Data extraction
- Structured output

**Expected Output:** Table of checks with customer, amount, check number, invoice references

---

### 4.2 Invoice PDF Parsing
**Source:** Lisa Chen (GGHC) - Story 8

**Prompt:**
```
"Parse this vendor invoice and extract: vendor name, invoice number, amount, due date, and line items."
```

**Integrations:**
- PDF parsing (Stampley/OCR)
- Vendor matching
- GL code suggestion

**Expected Output:** Structured invoice data with confidence scores

---

### 4.3 Bank Statement Parsing
**Source:** Sarah Martinez (Dockwa) - Story 4

**Prompt:**
```
"Parse our October Chase bank statement and extract all transactions for reconciliation."
```

**Integrations:**
- PDF/CSV parsing
- Transaction categorization
- Structured output

**Expected Output:** Transaction list with dates, amounts, descriptions

---

### 4.4 Fee Schedule Extraction
**Source:** Rachel Kim (GGHC) - Story 6

**Prompt:**
```
"Extract the fee rates from this client agreement. I need the tiered rates and any performance fee terms."
```

**Integrations:**
- PDF parsing
- Contract extraction
- Rate table structuring

**Expected Output:** Fee schedule with rates by tier

---

### 4.5 Loan Document Analysis
**Source:** Amanda Torres (StorageCorner) - Story 23

**Prompt:**
```
"Review this loan agreement and extract all covenant requirements - DSCR, LTV, net worth, and any other financial covenants."
```

**Integrations:**
- PDF parsing
- Legal document analysis
- Covenant extraction

**Expected Output:** Covenant summary with thresholds and cure periods

---

## 5. Lookup & Search Tasks

### 5.1 Customer Lookup with Fuzzy Matching
**Source:** Alex Thompson (Dockwa) - Story 1

**Prompt:**
```
"I have a check from 'Hartwell Marina Inc' but I can't find them in Recurly. Can you search for similar names?"
```

**Integrations:**
- `customer.list` (Stargate)
- Fuzzy matching algorithm
- Name variation detection

**Expected Output:** List of potential matches with confidence scores

---

### 5.2 Invoice Lookup by Reference
**Source:** Alex Thompson (Dockwa) - Story 1

**Prompt:**
```
"Find invoice DW-2025-0847. The customer is asking about it."
```

**Integrations:**
- `invoice.get` (Stargate)
- Invoice search

**Expected Output:** Invoice details with status and payment history

---

### 5.3 Vendor Lookup
**Source:** Kevin Chen (Dockwa) - Story 2

**Prompt:**
```
"Look up AquaTech Solutions in our vendor database. What are their payment terms and preferred payment method?"
```

**Integrations:**
- `vendor.get` (Stargate)
- Vendor profile data

**Expected Output:** Vendor profile with payment preferences

---

### 5.4 GL Account Lookup
**Source:** All scenarios

**Prompt:**
```
"What GL account should I use for IoT sensor maintenance? Is there a specific account for that?"
```

**Integrations:**
- Chart of accounts lookup
- Account description matching

**Expected Output:** Recommended GL code with account hierarchy

---

### 5.5 Entity/Property Lookup
**Source:** StorageCorner scenarios

**Prompt:**
```
"Which entity owns the Phoenix Storage Hub? And which bank accounts are associated with it?"
```

**Integrations:**
- Entity database
- Bank account mapping
- Property registry

**Expected Output:** Entity details with associated accounts

---

### 5.6 Historical Transaction Search
**Source:** Multiple scenarios

**Prompt:**
```
"Find all payments we've made to Wilson Legal Services in 2025."
```

**Integrations:**
- `payment.list` (filter by vendor, date range)
- Transaction search

**Expected Output:** Payment history with amounts and dates

---

## 6. Research Tasks

### 6.1 Company Research
**Source:** Jordan Blake (Dockwa) - Story 5

**Prompt:**
```
"Research HarborTech Solutions - their funding history, key features, and competitive positioning."
```

**Integrations:**
- Web search (Perplexity)
- Crunchbase
- News sources

**Expected Output:** Company profile with key metrics and analysis

---

### 6.2 Market Research
**Source:** Jordan Blake (Dockwa) - Story 5

**Prompt:**
```
"What's the current state of the marina management software market? Any recent trends or consolidation?"
```

**Integrations:**
- Web search
- Industry reports
- News aggregation

**Expected Output:** Market overview with trends and key players

---

### 6.3 Regulatory Research
**Source:** Jordan Blake (Dockwa) - Story 5

**Prompt:**
```
"What are the regulatory requirements for marina operations in the UK? We're considering expansion."
```

**Integrations:**
- Web search
- Regulatory databases
- Legal sources

**Expected Output:** Regulatory summary with compliance requirements

---

### 6.4 Vendor Research
**Source:** Lisa Chen (GGHC) - Story 8

**Prompt:**
```
"We're onboarding a new vendor - Marina Technology Solutions from Canada. Can you research them?"
```

**Integrations:**
- Web search
- Business registries
- Credit sources

**Expected Output:** Vendor profile with background check results

---

### 6.5 Investment Research
**Source:** GGHC scenarios

**Prompt:**
```
"Research fundamental analysis for Coastal Pension Fund's top 5 equity holdings."
```

**Integrations:**
- Financial data APIs
- News sources
- Analyst reports

**Expected Output:** Investment research summary with key metrics

---

## 7. Calculation Tasks

### 7.1 Fee Calculation
**Source:** Rachel Kim (GGHC) - Story 6

**Prompt:**
```
"Calculate the management fee for Hartwell Industries. They have $47.3M AUM with our standard tiered rate schedule."
```

**Integrations:**
- Fee rate lookup
- Tiered calculation engine
- AUM data

**Expected Output:** Fee calculation breakdown by tier

---

### 7.2 Proration Calculation
**Source:** Rachel Kim (GGHC) - Story 6

**Prompt:**
```
"Patterson LLC opened on October 15th. Calculate their prorated fee for the partial month."
```

**Integrations:**
- Fee calculation
- Date math
- Proration formula

**Expected Output:** Prorated fee with calculation detail

---

### 7.3 Currency Conversion
**Source:** Lisa Chen (GGHC) - Story 8

**Prompt:**
```
"Convert this CAD invoice to USD. The invoice is for $20,592.34 CAD."
```

**Integrations:**
- FX rate lookup
- Currency conversion
- Rate source verification

**Expected Output:** USD amount with exchange rate and date

---

### 7.4 Interest Calculation
**Source:** StorageCorner scenarios

**Prompt:**
```
"Calculate the interest expense for our Heritage bridge loan this month. Principal is $2.85M at 7.2% annual."
```

**Integrations:**
- Loan data
- Interest calculation
- Accrual logic

**Expected Output:** Interest amount with calculation detail

---

### 7.5 Net Worth Calculation
**Source:** Amanda Torres (StorageCorner) - Story 23

**Prompt:**
```
"Calculate our corporate net worth as of November 30 for the Glacier FCB covenant test."
```

**Integrations:**
- Balance sheet data
- Asset/liability totals
- Covenant definition lookup

**Expected Output:** Net worth calculation per covenant definition

---

### 7.6 Occupancy Rate Calculation
**Source:** Amanda Torres (StorageCorner) - Story 23

**Prompt:**
```
"What's the current occupancy rate for Denver Storage Center?"
```

**Integrations:**
- Property management data
- Unit count
- Lease status

**Expected Output:** Occupancy percentage with unit breakdown

---

### 7.7 Variance Calculation
**Source:** Multiple scenarios

**Prompt:**
```
"Calculate the budget variance for Phoenix Storage Hub's utilities expense. We budgeted $75,000 for Q3."
```

**Integrations:**
- Actual expense data
- Budget data
- Variance formula

**Expected Output:** Variance amount and percentage with analysis

---

## 8. Monitoring & Alerts

### 8.1 Low Balance Alert
**Source:** Angela Park (StorageCorner) - Story 16

**Prompt:**
```
"Are any of our property operating accounts below the $50,000 minimum? If so, flag them for transfer."
```

**Integrations:**
- `balance.get` (all accounts)
- Threshold comparison
- Alert generation

**Expected Output:** List of accounts below threshold with recommended actions

---

### 8.2 Covenant Warning Alert
**Source:** Amanda Torres (StorageCorner) - Story 23

**Prompt:**
```
"Check all our loan covenants. Are any within 10% of their limits?"
```

**Integrations:**
- Covenant calculations
- Threshold comparison
- Risk categorization

**Expected Output:** Covenant status dashboard with warnings

---

### 8.3 Payment Due Alert
**Source:** Kevin Chen (Dockwa) - Story 2

**Prompt:**
```
"What bills are due in the next 3 days that haven't been paid yet?"
```

**Integrations:**
- `bill.list` (filter by due date)
- Payment status check
- Urgency flagging

**Expected Output:** Urgent payment list with amounts and vendors

---

### 8.4 Invoice Aging Alert
**Source:** Alex Thompson (Dockwa) - Story 1

**Prompt:**
```
"Flag any customer invoices that are 45+ days past due. I need to follow up."
```

**Integrations:**
- `invoice.list` (filter by age)
- Customer contact info
- Collection status

**Expected Output:** Aged invoice list with customer details

---

### 8.5 Unusual Activity Alert
**Source:** Sarah Martinez (Dockwa) - Story 4

**Prompt:**
```
"Are there any unusual transactions in our Chase account this week? Anything over $25,000 or to unfamiliar payees?"
```

**Integrations:**
- Transaction monitoring
- Pattern detection
- Threshold alerts

**Expected Output:** Flagged transactions with risk assessment

---

### 8.6 Autopay Failure Alert
**Source:** Kevin Chen (Dockwa) - Story 2

**Prompt:**
```
"Did all our autopay bills process correctly? Check for any failures or rejections."
```

**Integrations:**
- Payment status monitoring
- Error detection
- Vendor notification status

**Expected Output:** Autopay status report with any failures highlighted

---

### 8.7 Reconciliation Exception Alert
**Source:** Sarah Martinez (Dockwa) - Story 4

**Prompt:**
```
"Show me any unmatched items in this month's bank reconciliation that are over $1,000."
```

**Integrations:**
- Reconciliation engine
- Exception detection
- Materiality filtering

**Expected Output:** Unmatched items with suggested matches

---

### 8.8 Cash Forecast Variance Alert
**Source:** Michael Davis (StorageCorner) - Story 17

**Prompt:**
```
"Compare our actual cash position to what we forecasted last week. Are we on track?"
```

**Integrations:**
- Current balances
- Historical forecast
- Variance calculation

**Expected Output:** Forecast accuracy report with variance analysis

---

## 9. UTILITIES - OCR & File Operations

### 9.1 Parse Invoice PDF
**Source:** Lisa Chen (GGHC) - Story 8, All AP scenarios

**Prompt:**
```
"I just received this invoice PDF from AquaTech Solutions. Can you extract the vendor name, invoice number, amount, due date, and line items?"
```

**Integrations:**
- `ocr.invoice.parse` (Stargate)
- `file.upload` (if needed)

**Expected Output:** Structured invoice data with all fields extracted

---

### 9.2 Parse Bank Statement PDF
**Source:** Sarah Martinez (Dockwa) - Story 4

**Prompt:**
```
"Here's our October Chase bank statement. Extract all transactions so we can reconcile."
```

**Integrations:**
- `ocr.bankstatement.parse` (Stargate)
- Transaction list extraction

**Expected Output:** Table of transactions with date, description, amount, running balance

---

### 9.3 Parse W-9 Form
**Source:** Vendor onboarding scenarios

**Prompt:**
```
"New vendor sent their W-9. Can you extract the business name, tax ID, and address?"
```

**Integrations:**
- `ocr.w9.parse` (Stargate)

**Expected Output:** Vendor tax information structured for system entry

---

### 9.4 Extract Text from Photo/Image
**Source:** Receipt capture, field documentation

**Prompt:**
```
"I took a photo of this receipt at the hardware store. What's the total and what did we buy?"
```

**Integrations:**
- `ocr.text.extract` (Stargate)
- `ocr.gemini.extract` (for complex images)

**Expected Output:** Extracted text with key fields identified

---

### 9.5 Extract Tables from Document
**Source:** Financial statements, rate schedules

**Prompt:**
```
"This PDF has a fee schedule table. Can you extract it into a format I can use?"
```

**Integrations:**
- `ocr.gemini.tables` (Stargate)

**Expected Output:** Structured table data (JSON or markdown table)

---

### 9.6 Upload Document to QuickBooks
**Source:** W-9 attachment, invoice backup

**Prompt:**
```
"Attach this W-9 to the AquaTech vendor record in QuickBooks."
```

**Integrations:**
- `document.upload` (Stargate → QuickBooks)
- `vendor.get` (to find vendor ID)

**Expected Output:** Confirmation of attachment with document ID

---

### 9.7 Upload to Google Drive
**Source:** Document archival, sharing

**Prompt:**
```
"Save this month-end report to our Finance shared drive in the 'November 2025' folder."
```

**Integrations:**
- `gdrive.file.upload` (Stargate)
- `gdrive.file.list` (to find folder)

**Expected Output:** File uploaded with shareable link

---

### 9.8 Download File from Drive
**Source:** Retrieving stored documents

**Prompt:**
```
"Pull the vendor contract for Marina Supplies from our contracts folder on Drive."
```

**Integrations:**
- `gdrive.file.list` (search)
- `gdrive.file.download` (retrieve)

**Expected Output:** File content or download link

---

### 9.9 Get Email Attachment
**Source:** Invoice/document processing from email

**Prompt:**
```
"There's an invoice attached to the email from Wilson Legal. Can you grab it and parse it?"
```

**Integrations:**
- `email.download_attachment` (Stargate)
- `ocr.invoice.parse` (chained)

**Expected Output:** Extracted invoice data from email attachment

---

### 9.10 Parse Lockbox PDF (Multi-Check Extraction)
**Source:** Alex Thompson (Dockwa) - Story 1

**Prompt:**
```
"Today's lockbox report has 23 checks. Extract all of them with customer names, amounts, check numbers, and any invoice references."
```

**Integrations:**
- `ocr.gemini.tables` (for check table)
- `ocr.text.extract` (for memo lines)
- Custom lockbox parsing logic

**Expected Output:** Table of 23 checks with all details

---

### 9.11 Upload Vendor Document to NetSuite
**Source:** Enterprise vendor management

**Prompt:**
```
"Attach this signed contract to the AquaTech vendor record in NetSuite."
```

**Integrations:**
- `netsuite.vendor.upload_document` (Stargate)

**Expected Output:** Document attached with NetSuite file cabinet reference

---

### 9.12 List Files in Folder
**Source:** Document discovery

**Prompt:**
```
"What files do we have in the 'Q4 Invoices' folder on OneDrive?"
```

**Integrations:**
- `onedrive.file.list` (Stargate)

**Expected Output:** File listing with names, sizes, dates

---

### 9.13 Extract Data from Web Page
**Source:** Competitive research, rate lookups

**Prompt:**
```
"Go to the Treasury Direct website and get the current 13-week T-bill rate."
```

**Integrations:**
- `browser.extract_data` (Stargate)
- Web navigation + extraction

**Expected Output:** Current rate with source timestamp

---

### 9.14 Multi-Page PDF Processing
**Source:** Long financial statements, contracts

**Prompt:**
```
"This quarterly report is 47 pages. Extract the summary financials from pages 3-5 and the segment breakdown from page 12."
```

**Integrations:**
- `ocr.gemini.extract` (with page targeting)
- `ocr.gemini.tables` (for financial tables)

**Expected Output:** Extracted data from specified pages

---

### 9.15 Image-Based Receipt Processing
**Source:** Expense reporting, field staff

**Prompt:**
```
"Process this photo of a gas receipt. I need the date, amount, and gallons for the expense report."
```

**Integrations:**
- `ocr.gemini.extract` (Stargate)
- Field extraction logic

**Expected Output:** Structured receipt data for expense entry

---

## Integration Summary

### Core Financial Capabilities

| Integration | Stargate Capability | Use Cases |
|-------------|---------------------|-----------|
| `customer.list` | ✅ | Customer lookup, AR aging, fuzzy matching |
| `customer.get` | ✅ | Customer details, balance inquiry |
| `invoice.list` | ✅ | AR reports, aging, search |
| `invoice.get` | ✅ | Invoice details, status |
| `vendor.list` | ✅ | Vendor lookup, AP reports |
| `vendor.get` | ✅ | Vendor details, payment prefs |
| `bill.list` | ✅ | AP aging, payment scheduling |
| `bill.get` | ✅ | Bill details, status |
| `payment.list` | ✅ | Payment history, reconciliation |
| `balance.get` | ✅ | Cash position, bank balances |
| `report.profitloss` | ✅ | P&L reports, variance analysis |
| `report.balancesheet` | ✅ | Net worth, covenant calcs |
| `report.cashflow` | ✅ | Cash flow analysis |
| `transaction.list` | ✅ | GL detail, reconciliation |

### OCR & Document Processing

| Integration | Stargate Capability | Use Cases |
|-------------|---------------------|-----------|
| `ocr.invoice.parse` | ✅ | Invoice PDF extraction |
| `ocr.bankstatement.parse` | ✅ | Bank statement parsing |
| `ocr.w9.parse` | ✅ | W-9 form extraction |
| `ocr.text.extract` | ✅ | Generic text OCR |
| `ocr.gemini.extract` | ✅ | Complex image OCR (Gemini) |
| `ocr.gemini.tables` | ✅ | Table extraction from PDFs |

### File Operations

| Integration | Stargate Capability | Use Cases |
|-------------|---------------------|-----------|
| `file.upload` | ✅ | Generic file upload |
| `document.upload` | ✅ | QuickBooks attachments |
| `gdrive.file.upload` | ✅ | Google Drive upload |
| `gdrive.file.download` | ✅ | Google Drive download |
| `gdrive.file.list` | ✅ | Google Drive browsing |
| `onedrive.file.upload` | ✅ | OneDrive upload |
| `onedrive.file.download` | ✅ | OneDrive download |
| `onedrive.file.list` | ✅ | OneDrive browsing |
| `email.download_attachment` | ✅ | Email attachment extraction |
| `netsuite.vendor.upload_document` | ✅ | NetSuite document attachment |

### External Data

| Integration | Stargate Capability | Use Cases |
|-------------|---------------------|-----------|
| `browser.extract_data` | ✅ | Web scraping, rate lookups |
| `search.extract` | ✅ | Search and data extraction |
| Web Search | Perplexity | Research, market analysis |
| FX Rates | API | Currency conversion |

---

## Task Count Summary

| Category | Task Count |
|----------|------------|
| Data Retrieval | 8 |
| Report Generation | 8 |
| Analysis | 10 |
| Document Parsing | 5 |
| Lookup & Search | 6 |
| Research | 5 |
| Calculation | 7 |
| Monitoring & Alerts | 8 |
| **Utilities (OCR & Files)** | **15** |
| **TOTAL** | **72 tasks** |

---

## Day 1-20 Progression

| Day Range | Expected Behavior |
|-----------|-------------------|
| Day 1-5 | Asks clarifying questions for most tasks. "What date range?" "Which format?" |
| Day 6-10 | Starts remembering preferences. Fewer clarifications on repeat tasks. |
| Day 11-15 | Can handle routine lookups autonomously. Still asks for complex analysis. |
| Day 16-20 | ~50% autonomous on data retrieval and reports. Proposes actions for review. |

---

*Generated for Baby MARS E2E Testing - Day 1-20 Aleq Capability Catalog*
