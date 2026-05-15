from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid
from datetime import date


class Company(models.Model):
    practice_name = models.CharField(max_length=255)
    company_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.practice_name}"


class Invitation(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("manager", "Manager"),
        ("staff", "Staff"),
    ]

    email = models.EmailField()
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="invitations"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="staff")

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    accepted = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.expires_at is not None and timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.email} invited to {self.company.practice_name} as {self.role}"


class Profile(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("manager", "Manager"),
        ("staff", "Staff"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="profiles"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="staff")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.company.practice_name} - {self.role}"


class Client(models.Model):
    CLIENT_TYPE_CHOICES = [
        ("individual", "Individual"),
        ("business", "Business"),
        ("trust_estate", "Trust / Estate"),
        ("nonprofit", "Nonprofit"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=255)

    client_type = models.CharField(
        max_length=30,
        choices=CLIENT_TYPE_CHOICES,
        default="individual"
    )

    # Optional IDs from CCH, SafeSend, or a master client spreadsheet
    external_client_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional ID from CCH, SafeSend, or imported client spreadsheet."
    )

    primary_contact_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    # Important for fiscal-year entities
    fiscal_year_end_month = models.IntegerField(
        null=True,
        blank=True,
        help_text="Example: 12 for calendar year-end, 6 for June year-end."
    )

    fiscal_year_end_day = models.IntegerField(
        null=True,
        blank=True,
        help_text="Example: 31 for calendar year-end."
    )

    notes = models.TextField(blank=True)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_year_end_date(self, tax_year):
        """
        Returns the client's year-end date for the selected tax year.
        Most clients will be 12/31.
        """
        month = self.fiscal_year_end_month or 12
        day = self.fiscal_year_end_day or 31
        return date(tax_year, month, day)

    def __str__(self):
        return self.name

class FederalReturnType(models.Model):
    CATEGORY_CHOICES = [
        ("individual", "Individual"),
        ("business", "Business Income"),
        ("partnership", "Partnership"),
        ("corporation", "Corporation"),
        ("s_corporation", "S Corporation"),
        ("trust_estate", "Trust / Estate"),
        ("exempt_org", "Exempt Organization / Nonprofit"),
        ("estate_gift", "Estate / Gift / GST"),
        ("employment", "Employment / Payroll"),
        ("information", "Information Return"),
        ("excise", "Excise Tax"),
        ("international", "International / Foreign Reporting"),
        ("retirement", "Retirement / Benefit Plan"),
        ("estimated_tax", "Estimated Tax"),
        ("withholding", "Withholding"),
        ("other", "Other Federal Filing"),
    ]

    FREQUENCY_CHOICES = [
        ("annual", "Annual"),
        ("quarterly", "Quarterly"),
        ("monthly", "Monthly"),
        ("semiweekly", "Semiweekly"),
        ("periodic", "Periodic"),
        ("event_based", "Event Based"),
        ("fiscal_year_based", "Fiscal Year Based"),
        ("one_time", "One Time"),
    ]

    form_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)

    category = models.CharField(
        max_length=40,
        choices=CATEGORY_CHOICES
    )

    frequency = models.CharField(
        max_length=40,
        choices=FREQUENCY_CHOICES
    )

    produced_when = models.CharField(
        max_length=255,
        blank=True,
        help_text="Example: Annually after year-end, quarterly after quarter-end, monthly after month-end, event-triggered, etc."
    )

    default_estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    default_complexity = models.CharField(
        max_length=20,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("very_high", "Very High"),
        ],
        default="medium"
    )

    requires_review = models.BooleanField(default=True)

    active = models.BooleanField(default=True)

    source = models.CharField(
        max_length=255,
        blank=True,
        default="IRS"
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.form_number} - {self.name}"

class FederalDueDateRule(models.Model):
    RULE_TYPE_CHOICES = [
        ("fixed_date", "Fixed Calendar Date"),
        ("nth_month_after_year_end", "Nth Month After Year-End"),
        ("quarterly", "Quarterly"),
        ("monthly", "Monthly"),
        ("event_based", "Event Based"),
        ("recipient_and_irs", "Separate Recipient and IRS Deadlines"),
        ("deposit_schedule", "Deposit Schedule"),
        ("varies", "Varies / See Instructions"),
    ]

    return_type = models.ForeignKey(
        FederalReturnType,
        on_delete=models.CASCADE,
        related_name="due_date_rules"
    )

    rule_type = models.CharField(
        max_length=40,
        choices=RULE_TYPE_CHOICES
    )

    due_month = models.IntegerField(null=True, blank=True)
    due_day = models.IntegerField(null=True, blank=True)

    extension_month = models.IntegerField(null=True, blank=True)
    extension_day = models.IntegerField(null=True, blank=True)

    months_after_period_end = models.IntegerField(null=True, blank=True)
    due_day_after_period_end = models.IntegerField(null=True, blank=True)

    applies_to_period = models.CharField(
        max_length=100,
        blank=True,
        help_text="Example: Q1, Q2, Q3, Q4, annual, monthly, recipient copy, IRS paper filing, IRS e-file filing."
    )

    description = models.TextField(blank=True)

    weekend_holiday_adjustment = models.BooleanField(
        default=True,
        help_text="Move to next business day when deadline falls on weekend/federal holiday."
    )

    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.return_type.form_number} - {self.description}"


FEDERAL_RETURN_TYPES = [

    # =========================
    # INDIVIDUAL INCOME TAX
    # =========================

    {
        "form_number": "1040",
        "name": "U.S. Individual Income Tax Return",
        "category": "individual",
        "frequency": "annual",
        "produced_when": "Annually after individual tax year-end",
    },
    {
        "form_number": "1040-SR",
        "name": "U.S. Tax Return for Seniors",
        "category": "individual",
        "frequency": "annual",
        "produced_when": "Annually after individual tax year-end",
    },
    {
        "form_number": "1040-NR",
        "name": "U.S. Nonresident Alien Income Tax Return",
        "category": "individual",
        "frequency": "annual",
        "produced_when": "Annually after individual tax year-end",
    },
    {
        "form_number": "1040-SS",
        "name": "U.S. Self-Employment Tax Return",
        "category": "individual",
        "frequency": "annual",
        "produced_when": "Annually for certain self-employed taxpayers",
    },
    {
        "form_number": "1040-PR",
        "name": "Self-Employment Tax Return - Puerto Rico",
        "category": "individual",
        "frequency": "annual",
        "produced_when": "Annually for certain Puerto Rico self-employed taxpayers",
    },
    {
        "form_number": "1040-X",
        "name": "Amended U.S. Individual Income Tax Return",
        "category": "individual",
        "frequency": "event_based",
        "produced_when": "Produced when an individual return is amended",
    },

    # =========================
    # ESTIMATED TAX
    # =========================

    {
        "form_number": "1040-ES",
        "name": "Estimated Tax for Individuals",
        "category": "estimated_tax",
        "frequency": "quarterly",
        "produced_when": "Produced quarterly for individual estimated tax payments",
    },
    {
        "form_number": "1120-W",
        "name": "Estimated Tax for Corporations",
        "category": "estimated_tax",
        "frequency": "quarterly",
        "produced_when": "Produced quarterly for corporate estimated tax payments",
    },
    {
        "form_number": "1041-ES",
        "name": "Estimated Income Tax for Estates and Trusts",
        "category": "estimated_tax",
        "frequency": "quarterly",
        "produced_when": "Produced quarterly for estate and trust estimated tax payments",
    },

    # =========================
    # PARTNERSHIPS
    # =========================

    {
        "form_number": "1065",
        "name": "U.S. Return of Partnership Income",
        "category": "partnership",
        "frequency": "annual",
        "produced_when": "Annually after partnership tax year-end",
    },
    {
        "form_number": "1065-X",
        "name": "Amended Return or Administrative Adjustment Request",
        "category": "partnership",
        "frequency": "event_based",
        "produced_when": "Produced when a partnership return is amended or adjusted",
    },

    # =========================
    # CORPORATIONS
    # =========================

    {
        "form_number": "1120",
        "name": "U.S. Corporation Income Tax Return",
        "category": "corporation",
        "frequency": "annual",
        "produced_when": "Annually after corporate tax year-end",
    },
    {
        "form_number": "1120-S",
        "name": "U.S. Income Tax Return for an S Corporation",
        "category": "s_corporation",
        "frequency": "annual",
        "produced_when": "Annually after S corporation tax year-end",
    },
    {
        "form_number": "1120-F",
        "name": "U.S. Income Tax Return of a Foreign Corporation",
        "category": "corporation",
        "frequency": "annual",
        "produced_when": "Annually after foreign corporation tax year-end",
    },
    {
        "form_number": "1120-H",
        "name": "U.S. Income Tax Return for Homeowners Associations",
        "category": "corporation",
        "frequency": "annual",
        "produced_when": "Annually after homeowners association tax year-end",
    },
    {
        "form_number": "1120-L",
        "name": "U.S. Life Insurance Company Income Tax Return",
        "category": "corporation",
        "frequency": "annual",
        "produced_when": "Annually after life insurance company tax year-end",
    },
    {
        "form_number": "1120-PC",
        "name": "U.S. Property and Casualty Insurance Company Income Tax Return",
        "category": "corporation",
        "frequency": "annual",
        "produced_when": "Annually after property and casualty insurance company tax year-end",
    },
    {
        "form_number": "1120-REIT",
        "name": "U.S. Income Tax Return for Real Estate Investment Trusts",
        "category": "corporation",
        "frequency": "annual",
        "produced_when": "Annually after REIT tax year-end",
    },
    {
        "form_number": "1120-RIC",
        "name": "U.S. Income Tax Return for Regulated Investment Companies",
        "category": "corporation",
        "frequency": "annual",
        "produced_when": "Annually after RIC tax year-end",
    },
    {
        "form_number": "1120-C",
        "name": "U.S. Income Tax Return for Cooperative Associations",
        "category": "corporation",
        "frequency": "annual",
        "produced_when": "Annually after cooperative association tax year-end",
    },
    {
        "form_number": "1120-POL",
        "name": "U.S. Income Tax Return for Certain Political Organizations",
        "category": "corporation",
        "frequency": "annual",
        "produced_when": "Annually after political organization tax year-end",
    },
    {
        "form_number": "1120-X",
        "name": "Amended U.S. Corporation Income Tax Return",
        "category": "corporation",
        "frequency": "event_based",
        "produced_when": "Produced when a corporation return is amended",
    },

    # =========================
    # TRUSTS AND ESTATES
    # =========================

    {
        "form_number": "1041",
        "name": "U.S. Income Tax Return for Estates and Trusts",
        "category": "trust_estate",
        "frequency": "annual",
        "produced_when": "Annually after estate or trust tax year-end",
    },
    {
        "form_number": "1041-N",
        "name": "U.S. Income Tax Return for Electing Alaska Native Settlement Trusts",
        "category": "trust_estate",
        "frequency": "annual",
        "produced_when": "Annually after trust tax year-end",
    },
    {
        "form_number": "1041-QFT",
        "name": "U.S. Income Tax Return for Qualified Funeral Trusts",
        "category": "trust_estate",
        "frequency": "annual",
        "produced_when": "Annually after qualified funeral trust tax year-end",
    },

    # =========================
    # ESTATE, GIFT, AND GST
    # =========================

    {
        "form_number": "706",
        "name": "United States Estate Tax Return",
        "category": "estate_gift",
        "frequency": "event_based",
        "produced_when": "Produced after death when estate tax filing is required",
    },
    {
        "form_number": "706-NA",
        "name": "Estate Tax Return for Nonresident Not a Citizen of the United States",
        "category": "estate_gift",
        "frequency": "event_based",
        "produced_when": "Produced after death for applicable nonresident estates",
    },
    {
        "form_number": "706-GS(D)",
        "name": "Generation-Skipping Transfer Tax Return for Distributions",
        "category": "estate_gift",
        "frequency": "annual",
        "produced_when": "Produced annually when taxable GST distributions occur",
    },
    {
        "form_number": "706-GS(T)",
        "name": "Generation-Skipping Transfer Tax Return for Terminations",
        "category": "estate_gift",
        "frequency": "event_based",
        "produced_when": "Produced when taxable GST terminations occur",
    },
    {
        "form_number": "709",
        "name": "United States Gift and Generation-Skipping Transfer Tax Return",
        "category": "estate_gift",
        "frequency": "annual",
        "produced_when": "Produced annually when reportable gifts or GST transfers occur",
    },

    # =========================
    # EXEMPT ORGANIZATIONS / NONPROFITS
    # =========================

    {
        "form_number": "990",
        "name": "Return of Organization Exempt From Income Tax",
        "category": "exempt_org",
        "frequency": "annual",
        "produced_when": "Annually after exempt organization tax year-end",
    },
    {
        "form_number": "990-EZ",
        "name": "Short Form Return of Organization Exempt From Income Tax",
        "category": "exempt_org",
        "frequency": "annual",
        "produced_when": "Annually after exempt organization tax year-end",
    },
    {
        "form_number": "990-N",
        "name": "Electronic Notice for Tax-Exempt Organizations",
        "category": "exempt_org",
        "frequency": "annual",
        "produced_when": "Annually for eligible small tax-exempt organizations",
    },
    {
        "form_number": "990-PF",
        "name": "Return of Private Foundation",
        "category": "exempt_org",
        "frequency": "annual",
        "produced_when": "Annually after private foundation tax year-end",
    },
    {
        "form_number": "990-T",
        "name": "Exempt Organization Business Income Tax Return",
        "category": "exempt_org",
        "frequency": "annual",
        "produced_when": "Annually when exempt organization has unrelated business taxable income",
    },
    {
        "form_number": "4720",
        "name": "Return of Certain Excise Taxes Under Chapters 41 and 42",
        "category": "exempt_org",
        "frequency": "annual",
        "produced_when": "Produced when certain private foundation or exempt organization excise taxes apply",
    },
    {
        "form_number": "5227",
        "name": "Split-Interest Trust Information Return",
        "category": "trust_estate",
        "frequency": "annual",
        "produced_when": "Annually for split-interest trusts",
    },

    # =========================
    # EMPLOYMENT / PAYROLL RETURNS
    # =========================

    {
        "form_number": "940",
        "name": "Employer's Annual Federal Unemployment Tax Return",
        "category": "employment",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "941",
        "name": "Employer's Quarterly Federal Tax Return",
        "category": "employment",
        "frequency": "quarterly",
        "produced_when": "Produced after each calendar quarter",
    },
    {
        "form_number": "941-X",
        "name": "Adjusted Employer's Quarterly Federal Tax Return or Claim for Refund",
        "category": "employment",
        "frequency": "event_based",
        "produced_when": "Produced when correcting Form 941",
    },
    {
        "form_number": "943",
        "name": "Employer's Annual Federal Tax Return for Agricultural Employees",
        "category": "employment",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "944",
        "name": "Employer's Annual Federal Tax Return",
        "category": "employment",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end for eligible small employers",
    },
    {
        "form_number": "945",
        "name": "Annual Return of Withheld Federal Income Tax",
        "category": "employment",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end for nonpayroll withholding",
    },
    {
        "form_number": "CT-1",
        "name": "Employer's Annual Railroad Retirement Tax Return",
        "category": "employment",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },

    # =========================
    # INFORMATION RETURNS
    # =========================

    {
        "form_number": "W-2",
        "name": "Wage and Tax Statement",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end for employees",
    },
    {
        "form_number": "W-3",
        "name": "Transmittal of Wage and Tax Statements",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually with W-2 filings",
    },
    {
        "form_number": "1096",
        "name": "Annual Summary and Transmittal of U.S. Information Returns",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually as paper transmittal for certain information returns",
    },
    {
        "form_number": "1098",
        "name": "Mortgage Interest Statement",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1098-C",
        "name": "Contributions of Motor Vehicles, Boats, and Airplanes",
        "category": "information",
        "frequency": "event_based",
        "produced_when": "Produced when reportable vehicle, boat, or airplane contributions occur",
    },
    {
        "form_number": "1098-E",
        "name": "Student Loan Interest Statement",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1098-T",
        "name": "Tuition Statement",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-A",
        "name": "Acquisition or Abandonment of Secured Property",
        "category": "information",
        "frequency": "event_based",
        "produced_when": "Produced when acquisition or abandonment of secured property occurs",
    },
    {
        "form_number": "1099-B",
        "name": "Proceeds From Broker and Barter Exchange Transactions",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-C",
        "name": "Cancellation of Debt",
        "category": "information",
        "frequency": "event_based",
        "produced_when": "Produced when reportable debt cancellation occurs",
    },
    {
        "form_number": "1099-DIV",
        "name": "Dividends and Distributions",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-G",
        "name": "Certain Government Payments",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-INT",
        "name": "Interest Income",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-K",
        "name": "Payment Card and Third Party Network Transactions",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-LTC",
        "name": "Long-Term Care and Accelerated Death Benefits",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-MISC",
        "name": "Miscellaneous Information",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-NEC",
        "name": "Nonemployee Compensation",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-OID",
        "name": "Original Issue Discount",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-PATR",
        "name": "Taxable Distributions Received From Cooperatives",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-Q",
        "name": "Payments From Qualified Education Programs",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-R",
        "name": "Distributions From Pensions, Annuities, Retirement or Profit-Sharing Plans, IRAs, Insurance Contracts, etc.",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1099-S",
        "name": "Proceeds From Real Estate Transactions",
        "category": "information",
        "frequency": "event_based",
        "produced_when": "Produced when reportable real estate transactions occur",
    },
    {
        "form_number": "1099-SA",
        "name": "Distributions From an HSA, Archer MSA, or Medicare Advantage MSA",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "3921",
        "name": "Exercise of an Incentive Stock Option",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end when ISO exercises occur",
    },
    {
        "form_number": "3922",
        "name": "Transfer of Stock Acquired Through an Employee Stock Purchase Plan",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end when ESPP transfers occur",
    },
    {
        "form_number": "5498",
        "name": "IRA Contribution Information",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "5498-ESA",
        "name": "Coverdell ESA Contribution Information",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "5498-SA",
        "name": "HSA, Archer MSA, or Medicare Advantage MSA Information",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "8027",
        "name": "Employer's Annual Information Return of Tip Income and Allocated Tips",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "8300",
        "name": "Report of Cash Payments Over $10,000 Received in a Trade or Business",
        "category": "information",
        "frequency": "event_based",
        "produced_when": "Produced when reportable cash payment is received",
    },

    # =========================
    # EXCISE TAX RETURNS
    # =========================

    {
        "form_number": "720",
        "name": "Quarterly Federal Excise Tax Return",
        "category": "excise",
        "frequency": "quarterly",
        "produced_when": "Produced after each calendar quarter",
    },
    {
        "form_number": "720-CS",
        "name": "Carrier Summary Report",
        "category": "excise",
        "frequency": "monthly",
        "produced_when": "Produced monthly by applicable fuel carriers",
    },
    {
        "form_number": "720-TO",
        "name": "Terminal Operator Report",
        "category": "excise",
        "frequency": "monthly",
        "produced_when": "Produced monthly by applicable terminal operators",
    },
    {
        "form_number": "2290",
        "name": "Heavy Highway Vehicle Use Tax Return",
        "category": "excise",
        "frequency": "annual",
        "produced_when": "Produced annually or when a taxable vehicle is first used",
    },
    {
        "form_number": "11-C",
        "name": "Occupational Tax and Registration Return for Wagering",
        "category": "excise",
        "frequency": "annual",
        "produced_when": "Produced annually or when wagering business begins",
    },
    {
        "form_number": "730",
        "name": "Monthly Tax Return for Wagers",
        "category": "excise",
        "frequency": "monthly",
        "produced_when": "Produced monthly for applicable wagering taxes",
    },
    {
        "form_number": "8849",
        "name": "Claim for Refund of Excise Taxes",
        "category": "excise",
        "frequency": "event_based",
        "produced_when": "Produced when claiming refund of excise taxes",
    },

    # =========================
    # INTERNATIONAL / FOREIGN REPORTING
    # =========================

    {
        "form_number": "1042",
        "name": "Annual Withholding Tax Return for U.S. Source Income of Foreign Persons",
        "category": "withholding",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1042-S",
        "name": "Foreign Person's U.S. Source Income Subject to Withholding",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually after calendar year-end",
    },
    {
        "form_number": "1042-T",
        "name": "Annual Summary and Transmittal of Forms 1042-S",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually with Forms 1042-S",
    },
    {
        "form_number": "5471",
        "name": "Information Return of U.S. Persons With Respect to Certain Foreign Corporations",
        "category": "international",
        "frequency": "annual",
        "produced_when": "Annually with related income tax return when required",
    },
    {
        "form_number": "5472",
        "name": "Information Return of a 25% Foreign-Owned U.S. Corporation or Foreign Corporation Engaged in U.S. Trade or Business",
        "category": "international",
        "frequency": "annual",
        "produced_when": "Annually with related income tax return when required",
    },
    {
        "form_number": "8858",
        "name": "Information Return of U.S. Persons With Respect to Foreign Disregarded Entities and Foreign Branches",
        "category": "international",
        "frequency": "annual",
        "produced_when": "Annually with related income tax return when required",
    },
    {
        "form_number": "8865",
        "name": "Return of U.S. Persons With Respect to Certain Foreign Partnerships",
        "category": "international",
        "frequency": "annual",
        "produced_when": "Annually with related income tax return when required",
    },
    {
        "form_number": "8938",
        "name": "Statement of Specified Foreign Financial Assets",
        "category": "international",
        "frequency": "annual",
        "produced_when": "Annually with related income tax return when required",
    },
    {
        "form_number": "3520",
        "name": "Annual Return To Report Transactions With Foreign Trusts and Receipt of Certain Foreign Gifts",
        "category": "international",
        "frequency": "annual",
        "produced_when": "Annually when reportable foreign trust transactions or foreign gifts occur",
    },
    {
        "form_number": "3520-A",
        "name": "Annual Information Return of Foreign Trust With a U.S. Owner",
        "category": "international",
        "frequency": "annual",
        "produced_when": "Annually for foreign trusts with U.S. owners",
    },
    {
        "form_number": "8621",
        "name": "Information Return by a Shareholder of a Passive Foreign Investment Company or Qualified Electing Fund",
        "category": "international",
        "frequency": "annual",
        "produced_when": "Annually with related income tax return when required",
    },
    {
        "form_number": "926",
        "name": "Return by a U.S. Transferor of Property to a Foreign Corporation",
        "category": "international",
        "frequency": "event_based",
        "produced_when": "Produced when reportable property transfers to foreign corporations occur",
    },
    {
        "form_number": "8804",
        "name": "Annual Return for Partnership Withholding Tax",
        "category": "withholding",
        "frequency": "annual",
        "produced_when": "Annually for withholding on foreign partners",
    },
    {
        "form_number": "8805",
        "name": "Foreign Partner's Information Statement of Section 1446 Withholding Tax",
        "category": "information",
        "frequency": "annual",
        "produced_when": "Annually with partnership withholding reporting",
    },
    {
        "form_number": "8288",
        "name": "U.S. Withholding Tax Return for Dispositions by Foreign Persons of U.S. Real Property Interests",
        "category": "withholding",
        "frequency": "event_based",
        "produced_when": "Produced when FIRPTA withholding applies",
    },
    {
        "form_number": "8288-A",
        "name": "Statement of Withholding on Dispositions by Foreign Persons of U.S. Real Property Interests",
        "category": "information",
        "frequency": "event_based",
        "produced_when": "Produced when FIRPTA withholding applies",
    },

    # =========================
    # RETIREMENT / BENEFIT PLAN RETURNS
    # =========================

    {
        "form_number": "5500",
        "name": "Annual Return/Report of Employee Benefit Plan",
        "category": "retirement",
        "frequency": "annual",
        "produced_when": "Annually after plan year-end",
    },
    {
        "form_number": "5500-SF",
        "name": "Short Form Annual Return/Report of Small Employee Benefit Plan",
        "category": "retirement",
        "frequency": "annual",
        "produced_when": "Annually after plan year-end",
    },
    {
        "form_number": "5500-EZ",
        "name": "Annual Return of A One-Participant Retirement Plan or Foreign Plan",
        "category": "retirement",
        "frequency": "annual",
        "produced_when": "Annually after plan year-end",
    },
    {
        "form_number": "8955-SSA",
        "name": "Annual Registration Statement Identifying Separated Participants With Deferred Vested Benefits",
        "category": "retirement",
        "frequency": "annual",
        "produced_when": "Annually after plan year-end when required",
    },
    {
        "form_number": "5330",
        "name": "Return of Excise Taxes Related to Employee Benefit Plans",
        "category": "retirement",
        "frequency": "event_based",
        "produced_when": "Produced when applicable employee benefit plan excise taxes apply",
    },

    # =========================
    # OTHER FEDERAL FILINGS
    # =========================

    {
        "form_number": "8752",
        "name": "Required Payment or Refund Under Section 7519",
        "category": "other",
        "frequency": "annual",
        "produced_when": "Annually for certain partnerships and S corporations with required tax years",
    },
    {
        "form_number": "8872",
        "name": "Political Organization Report of Contributions and Expenditures",
        "category": "other",
        "frequency": "periodic",
        "produced_when": "Produced periodically by political organizations depending on filing status",
    },
]

FEDERAL_DUE_DATE_RULES = [
    {
        "form_number": "1040",
        "rule_type": "fixed_date",
        "due_month": 4,
        "due_day": 15,
        "extension_month": 10,
        "extension_day": 15,
        "applies_to_period": "annual",
        "description": "Generally due April 15 after calendar year-end; extension generally October 15.",
    },
    {
        "form_number": "1065",
        "rule_type": "fixed_date",
        "due_month": 3,
        "due_day": 15,
        "extension_month": 9,
        "extension_day": 15,
        "applies_to_period": "annual",
        "description": "Generally due March 15 for calendar-year partnerships; extension generally September 15.",
    },
    {
        "form_number": "1120-S",
        "rule_type": "fixed_date",
        "due_month": 3,
        "due_day": 15,
        "extension_month": 9,
        "extension_day": 15,
        "applies_to_period": "annual",
        "description": "Generally due March 15 for calendar-year S corporations; extension generally September 15.",
    },
    {
        "form_number": "1120",
        "rule_type": "fixed_date",
        "due_month": 4,
        "due_day": 15,
        "extension_month": 10,
        "extension_day": 15,
        "applies_to_period": "annual",
        "description": "Generally due April 15 for calendar-year C corporations; extension generally October 15.",
    },
    {
        "form_number": "1041",
        "rule_type": "fixed_date",
        "due_month": 4,
        "due_day": 15,
        "extension_month": 9,
        "extension_day": 30,
        "applies_to_period": "annual",
        "description": "Generally due April 15 for calendar-year estates and trusts; extension generally September 30.",
    },
    {
        "form_number": "990",
        "rule_type": "nth_month_after_year_end",
        "months_after_period_end": 5,
        "due_day_after_period_end": 15,
        "extension_month": None,
        "extension_day": None,
        "applies_to_period": "annual",
        "description": "Generally due the 15th day of the 5th month after exempt organization year-end.",
    },
    {
        "form_number": "941",
        "rule_type": "quarterly",
        "applies_to_period": "Q1/Q2/Q3/Q4",
        "description": "Quarterly payroll return. Due after each calendar quarter, subject to IRS calendar rules.",
    },
    {
        "form_number": "940",
        "rule_type": "fixed_date",
        "due_month": 1,
        "due_day": 31,
        "applies_to_period": "annual",
        "description": "Annual FUTA return generally due January 31 after calendar year-end.",
    },
    {
        "form_number": "1099-NEC",
        "rule_type": "recipient_and_irs",
        "due_month": 1,
        "due_day": 31,
        "applies_to_period": "annual",
        "description": "Generally due to recipients and IRS by January 31.",
    },
    {
        "form_number": "W-2",
        "rule_type": "recipient_and_irs",
        "due_month": 1,
        "due_day": 31,
        "applies_to_period": "annual",
        "description": "Generally due to employees and SSA by January 31.",
    },
    {
        "form_number": "720",
        "rule_type": "quarterly",
        "applies_to_period": "Q1/Q2/Q3/Q4",
        "description": "Quarterly federal excise tax return.",
    },
    {
        "form_number": "730",
        "rule_type": "monthly",
        "applies_to_period": "monthly",
        "description": "Monthly wagering tax return.",
    },
]

class TaxReturnProject(models.Model):
    DOCUMENT_STATUS_CHOICES = [
        ("no_docs", "No documents received"),
        ("partial_docs", "Partial documents received"),
        ("minor_info_missing", "Waiting on minor information"),
        ("all_docs_received", "All documents received"),
    ]

    WORK_STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("ready_to_start", "Ready to Start"),
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("waiting_on_client", "Waiting on Client"),
        ("under_review", "Under Review"),
        ("complete", "Complete"),
        ("blocked", "Blocked"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    COMPLEXITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("very_high", "Very High"),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="tax_projects"
    )

    return_type = models.ForeignKey(
        FederalReturnType,
        on_delete=models.PROTECT,
        related_name="client_projects"
    )

    due_date_rule = models.ForeignKey(
        FederalDueDateRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_projects",
        help_text="Specific deadline rule used for this client project."
    )

    tax_year = models.IntegerField()

    period_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Useful for quarterly, monthly, fiscal-year, or event-based filings."
    )

    period_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Usually 12/31 for calendar-year annual returns."
    )

    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Calculated from the federal due date rule, but can be overridden."
    )

    extended_due_date = models.DateField(
        null=True,
        blank=True
    )

    extension_filed = models.BooleanField(default=False)

    document_status = models.CharField(
        max_length=30,
        choices=DOCUMENT_STATUS_CHOICES,
        default="no_docs"
    )

    docs_received_date = models.DateField(
        null=True,
        blank=True,
        help_text="Used for FIFO scheduling once documents are complete."
    )

    work_status = models.CharField(
        max_length=30,
        choices=WORK_STATUS_CHOICES,
        default="not_started"
    )

    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    complexity = models.CharField(
        max_length=20,
        choices=COMPLEXITY_CHOICES,
        default="medium"
    )

    manager_priority_override = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="normal"
    )

    priority_score = models.IntegerField(default=0)

    assigned_preparer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_preparation_projects"
    )

    assigned_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_review_projects"
    )

    scheduled_start_date = models.DateField(null=True, blank=True)
    scheduled_end_date = models.DateField(null=True, blank=True)

    internal_notes = models.TextField(blank=True)
    client_notes = models.TextField(blank=True)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "due_date",
            "-priority_score",
            "client__name",
        ]

    def set_defaults_from_return_type(self):
        """
        Pull default estimated hours and complexity from FederalReturnType.
        This gives every project a starting workload estimate.
        """
        if self.estimated_hours is None:
            self.estimated_hours = self.return_type.default_estimated_hours

        if not self.complexity:
            self.complexity = self.return_type.default_complexity or "medium"

    def set_default_period_dates(self):
        """
        For annual work, default to the client's fiscal/calendar year.
        For quarterly, monthly, or event-based filings, these can be set manually.
        """
        if not self.period_end_date and self.return_type.frequency in ["annual", "fiscal_year_based"]:
            self.period_end_date = self.client.get_year_end_date(self.tax_year)

    def set_due_date_rule_if_missing(self):
        """
        Grabs the first active due date rule for this return type.
        Later, you can make this smarter for Q1/Q2/Q3/Q4, e-file vs paper, etc.
        """
        if not self.due_date_rule:
            self.due_date_rule = (
                self.return_type.due_date_rules
                .filter(active=True)
                .first()
            )

    def calculate_basic_due_dates(self):
        """
        Basic version.
        Handles fixed-date annual returns.
        More advanced quarterly/monthly/fiscal-year/event logic can come later.
        """
        if not self.due_date_rule:
            return

        rule = self.due_date_rule

        if rule.rule_type == "fixed_date" and rule.due_month and rule.due_day:
            self.due_date = date(
                self.tax_year + 1,
                rule.due_month,
                rule.due_day
            )

        if rule.extension_month and rule.extension_day:
            self.extended_due_date = date(
                self.tax_year + 1,
                rule.extension_month,
                rule.extension_day
            )

    def save(self, *args, **kwargs):
        self.set_defaults_from_return_type()
        self.set_default_period_dates()
        self.set_due_date_rule_if_missing()

        if not self.due_date:
            self.calculate_basic_due_dates()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client.name} - {self.return_type.form_number} - {self.tax_year}"