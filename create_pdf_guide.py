import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render total page numbers
    along with professional running headers and footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        page_width, page_height = letter

        # Suppress headers/footers on the first cover page
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#475569"))
            self.drawString(54, page_height - 36, "ATHENA AI — ENTERPRISE PLATFORM USER GUIDE & MANUAL")
            self.setFont("Helvetica", 8)
            self.drawRightString(page_width - 54, page_height - 36, "v2.0 Enterprise SaaS")
            
            # Header line
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(54, page_height - 42, page_width - 54, page_height - 42)

            # Footer line
            self.line(54, 45, page_width - 54, 45)

            # Footer
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(54, 30, "Confidential & Proprietary — Athena AI Platform")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(page_width - 54, 30, page_text)

        self.restoreState()


def build_pdf(filename="Athena_AI_User_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0F172A")      # Dark Slate/Navy
    SECONDARY = colors.HexColor("#1E40AF")    # Royal Blue
    ACCENT = colors.HexColor("#0D9488")       # Teal Accent
    TEXT_DARK = colors.HexColor("#1E293B")    # Body text
    MUTED = colors.HexColor("#64748B")        # Subtitles/Footers
    BG_LIGHT = colors.HexColor("#F8FAFC")     # Card backgrounds
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    # Typography Styles
    style_cover_title = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=PRIMARY,
        spaceAfter=10
    )

    style_cover_subtitle = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=SECONDARY,
        spaceAfter=25
    )

    style_h1 = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceBefore=16,
        spaceAfter=10,
        keepWithNext=True
    )

    style_h2 = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=SECONDARY,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=8
    )

    style_bullet = ParagraphStyle(
        'BulletCustom',
        parent=style_body,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    style_code = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6
    )

    style_callout = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B")
    )

    story = []

    # ---------------------------------------------------------
    # COVER PAGE / HEADER BLOCK
    # ---------------------------------------------------------
    story.append(Spacer(1, 15))
    
    # Title Box Header
    header_table_data = [
        [Paragraph("<b>ATHENA AI PLATFORM</b>", ParagraphStyle('TopTag', fontName='Helvetica-Bold', fontSize=10, textColor=ACCENT, leading=12)),
         Paragraph("<b>v2.0 Enterprise SaaS</b>", ParagraphStyle('TopVer', fontName='Helvetica-Bold', fontSize=10, textColor=MUTED, leading=12, alignment=2))],
    ]
    t_header = Table(header_table_data, colWidths=[250, 254])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceBefore=0, spaceAfter=15))

    story.append(Paragraph("Enterprise Multi-Agent Platform & System User Guide", style_cover_title))
    story.append(Paragraph("A Comprehensive Guide to Architecture, Features, Business Utility & Operational Manual", style_cover_subtitle))

    # Meta Info Table
    meta_data = [
        [Paragraph("<b>Document Type:</b>", style_body), Paragraph("System Capability & User Operation Manual", style_body),
         Paragraph("<b>Author:</b>", style_body), Paragraph("Athena AI Core Engineering", style_body)],
        [Paragraph("<b>Target Audience:</b>", style_body), Paragraph("Enterprise Leadership, IT Admins, & Operations Teams", style_body),
         Paragraph("<b>Gateway URL:</b>", style_body), Paragraph("http://localhost (API Port 8000)", style_body)],
        [Paragraph("<b>Security Standard:</b>", style_body), Paragraph("Multi-Tenant RBAC + Tamper-Evident HMAC Vault", style_body),
         Paragraph("<b>Status:</b>", style_body), Paragraph("<font color='#0D9488'><b>Production Operational</b></font>", style_body)],
    ]
    t_meta = Table(meta_data, colWidths=[90, 160, 90, 164])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))

    # Executive Overview Callout
    callout_data = [[
        Paragraph(
            "<b>Executive Overview:</b> Athena AI is a state-of-the-art Multi-Agent Automation Platform built for enterprise environments. "
            "It unites LangGraph multi-agent orchestration, RAG-powered document vectorization (ChromaDB), multimodal OCR document intelligence, "
            "a visual drag-and-drop workflow engine, enterprise third-party API integrations (Slack, Teams, Jira, Salesforce, SAP), "
            "and real-time telemetry into a single, cohesive, secure platform. This manual details the business ROI, architecture, feature mechanics, "
            "and step-by-step instructions for operating Athena AI.",
            style_callout
        )
    ]]
    t_callout = Table(callout_data, colWidths=[504])
    t_callout.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0F9FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#BAE6FD")),
        ('LINELEFT', (0, 0), (0, -1), 4, SECONDARY),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_callout)
    story.append(Spacer(1, 15))

    # ---------------------------------------------------------
    # SECTION 1: BUSINESS VALUE & UTILITY
    # ---------------------------------------------------------
    story.append(Paragraph("1. How Athena AI Is Useful to Your Organization", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "Athena AI is designed to solve critical enterprise bottlenecks: fragmented data silos, repetitive manual workflows, slow document extraction, "
        "and lack of centralized control over AI deployments. By deploying Athena AI, organizations achieve significant operational impact:",
        style_body
    ))

    roi_items = [
        ("🚀 Operational Speed & Productivity (10x Acceleration):", 
         "Complex multi-step tasks—such as searching cross-department documents, querying SQL databases, reviewing code, and compiling summaries—are executed automatically in seconds by specialized AI agents overseen by an intelligent Supervisor."),
        ("📚 Unified Enterprise Memory & Context:", 
         "Static unstructured company assets (PDF invoices, contracts, technical specifications, policy files) are transformed into a living, queryable knowledge base using hybrid vector and keyword search with exact source citations."),
        ("🎨 No-Code Workflow Automation:", 
         "Domain experts can graphically design complex multi-agent pipelines using the drag-and-drop Workflow Builder, delegating background jobs to distributed Celery task queues without requiring software development bandwidth."),
        ("🔌 Seamless Workplace Integration:", 
         "Connects directly with enterprise tools like Slack, Microsoft Teams, Outlook, Jira, Salesforce, and SAP, enabling automated message processing, ticket creation, and system sync."),
        ("🔒 Bank-Grade Security & Governance:", 
         "Strict multi-tenant workspace isolation, Role-Based Access Control (RBAC), SSO authentication, automated PII redaction, prompt injection defense, and cryptographic HMAC-SHA256 audit logging satisfy enterprise regulatory compliance (SOC2, GDPR)."),
        ("📊 Full Telemetry & Cost Control:", 
         "Real-time WebSocket streaming, token consumption tracking, Prometheus scrapers, and Grafana dashboards ensure complete visibility into latency, execution bottlenecks, and AI expenditure.")
    ]

    for title, desc in roi_items:
        p_item = Paragraph(f"• <b>{title}</b> {desc}", style_bullet)
        story.append(p_item)

    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # SECTION 2: SYSTEM ARCHITECTURE & COMPONENTS
    # ---------------------------------------------------------
    story.append(Paragraph("2. System Architecture & Technical Stack", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    arch_data = [
        [Paragraph("<b>Component Layer</b>", style_h2), Paragraph("<b>Technology Stack</b>", style_h2), Paragraph("<b>Enterprise Role</b>", style_h2)],
        [Paragraph("API Gateway", style_body), Paragraph("Nginx / Docker", style_body), Paragraph("Reverse proxy, SSL termination, rate limiting & static asset routing", style_body)],
        [Paragraph("Backend Core", style_body), Paragraph("FastAPI (Python 3.11)", style_body), Paragraph("High-concurrency REST & WebSocket API layer with dependency injection", style_body)],
        [Paragraph("Agent Orchestration", style_body), Paragraph("LangGraph & LangChain", style_body), Paragraph("Supervisor-driven stateful multi-agent DAG execution and checkpointing", style_body)],
        [Paragraph("AI Memory Vault", style_body), Paragraph("ChromaDB / Vector Store", style_body), Paragraph("Document embedding, semantic search, hybrid retrieval, & memory ranking", style_body)],
        [Paragraph("Frontend UI", style_body), Paragraph("React 18 + Vite + Tailwind", style_body), Paragraph("Responsive Single-Page Application (SPA) with interactive canvas & dashboards", style_body)],
        [Paragraph("Task Workers", style_body), Paragraph("Celery + Redis", style_body), Paragraph("Distributed asynchronous job processing for heavy OCR, parsing & workflows", style_body)],
        [Paragraph("Relational Store", style_body), Paragraph("PostgreSQL / SQLite", style_body), Paragraph("Persistent storage for user credentials, RBAC roles, audit logs & sessions", style_body)],
        [Paragraph("Observability", style_body), Paragraph("Prometheus + Grafana", style_body), Paragraph("Live metrics scraping, memory profiling, and visual operational dashboards", style_body)],
    ]
    t_arch = Table(arch_data, colWidths=[120, 140, 244])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 15))

    # ---------------------------------------------------------
    # SECTION 3: FEATURE BREAKDOWN
    # ---------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("3. Feature-by-Feature Detailed Breakdown", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    features = [
        ("3.1 Multi-Agent Orchestration & AI Supervisor",
         "The core intelligence engine uses a Supervisor pattern built on LangGraph. When a user submits a query, the Supervisor analyzes intent and dynamically routes tasks to specialized agents:\n"
         "• Research Agent: Performs web searches, data aggregation, and fact verification.\n"
         "• Document Agent: Parses PDFs, extracts tabular data, and performs deep document comprehension.\n"
         "• SQL Agent: Translates natural language into sanitized SQL queries, executing read-only database analytics.\n"
         "• Code Agent: Writes, reviews, and executes Python code in a secure execution sandbox.\n"
         "• Workflow Agent: Triggers complex multi-step background API pipelines."),

        ("3.2 AI Memory Vault & Hybrid RAG Retrieval",
         "Stores and indexes organizational knowledge using state-of-the-art vector embeddings in ChromaDB. "
         "Features metadata filtering (by department, tags, user permissions), semantic distance ranking, and hybrid retrieval (combining vector similarity with keyword BM25 scoring). "
         "Every response provides transparent source citations with exact page numbers and snippet references."),

        ("3.3 Multimodal Document AI & OCR Engine",
         "Processes non-textual assets including scanned PDF invoices, financial receipts, diagrams, and images. "
         "Powered by Vision LLMs and Tesseract OCR, the engine performs automatic Named Entity Recognition (NER), structural table extraction, and document classification with high accuracy."),

        ("3.4 Visual Drag-and-Drop Workflow Builder",
         "An interactive canvas allowing users to assemble automated workflows without writing code. "
         "Users connect Trigger Nodes (e.g., File Upload, Webhook, Schedule), Agent Processing Nodes, Logic Gates (If/Else, Loops), API Connectors, and Action Outputs. "
         "Executions are dispatched to distributed Celery background workers."),

        ("3.5 Enterprise API Hub & Third-Party Integrations",
         "Native integration connectors for enterprise software tools including Slack, Microsoft Teams, Outlook, Jira, Salesforce, and SAP. "
         "Enables agents to read incoming channel messages, summarize email threads, create Jira tickets, update CRM opportunities, or trigger SAP transactions directly."),

        ("3.6 Security, RBAC & HMAC Audit Vault",
         "Includes Enterprise SSO (Azure Entra ID / OIDC), granular Role-Based Access Control (Owner, Admin, Manager, Developer, Viewer), "
         "automated PII redaction (masking SSNs, credit cards, emails), prompt injection filtering, and a tamper-evident audit logging system secured with HMAC-SHA256 signatures."),

        ("3.7 Real-Time Telemetry & System Observability",
         "Streams live execution states via WebSockets to the UI, showing step-by-step agent reasoning and node traversals. "
         "Fully instrumented with Prometheus endpoints and pre-configured Grafana dashboards (Port 3001) for real-time memory usage, token throughput, and worker queue depths."),

        ("3.8 Document Classifier & Prompt Studio",
         "Provides an automated document categorization panel alongside a Prompt Engineering Studio. "
         "Prompts can be tested, version-controlled using MLflow, and benchmarked for accuracy and toxicity before deployment to production.")
    ]

    for f_title, f_desc in features:
        story.append(Paragraph(f_title, style_h2))
        for line in f_desc.split('\n'):
            if line.startswith('•'):
                story.append(Paragraph(line, style_bullet))
            else:
                story.append(Paragraph(line, style_body))
        story.append(Spacer(1, 4))

    # ---------------------------------------------------------
    # SECTION 4: STEP-BY-STEP USER MANUAL
    # ---------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("4. Step-by-Step User Manual & Operating Guide", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    steps = [
        ("Step 1: Accessing the Application Portal",
         "1. Open a modern web browser (Chrome, Firefox, Safari, Edge).\n"
         "2. Navigate to: <b>http://localhost</b> (or http://localhost:8000 for raw API docs).\n"
         "3. You will be greeted by the Athena AI authentication screen.\n"
         "4. Enter your employee credentials or select 'Sign in with SSO' (Azure Entra ID)."),

        ("Step 2: Uploading & Managing Documents in the Memory Vault",
         "1. Click on <b>Memory Vault</b> or <b>Document AI</b> in the left navigation sidebar.\n"
         "2. Click the <b>Upload Document</b> button or drag and drop PDF, PNG, JPG, or TXT files onto the drop zone.\n"
         "3. Fill in document metadata: Select <i>Department</i> (e.g., Legal, Finance, Engineering) and add tags.\n"
         "4. Click <b>Process File</b>. The background Celery worker will perform chunking, vector embedding, and OCR extraction.\n"
         "5. Once complete, your document status will display <font color='#0D9488'><b>Indexed & Active</b></font>."),

        ("Step 3: Interacting with the Multi-Agent Chat Interface",
         "1. Navigate to <b>AI Workspace / Chat</b> from the navigation sidebar.\n"
         "2. Type your question or prompt in the bottom message bar (e.g., <i>'Summarize the Q3 financial report and list top 3 risks'</i>).\n"
         "3. Watch the real-time reasoning stream: The <b>Supervisor Agent</b> delegates to the <b>Document Agent</b> and <b>Research Agent</b>.\n"
         "4. Review the generated response alongside source citations and confidence scores.\n"
         "5. Use the <b>Copy</b> or <b>Export Report</b> buttons to save outputs."),

        ("Step 4: Building & Executing Visual Workflows",
         "1. Select <b>Workflow Builder</b> from the sidebar menu.\n"
         "2. Drag a <b>Trigger Node</b> (e.g., 'On Document Upload') onto the grid canvas.\n"
         "3. Drag an <b>Agent Node</b> (e.g., 'OCR + Entity Extraction Agent') and connect the ports with a directional arrow.\n"
         "4. Add an <b>Action Node</b> (e.g., 'Post Summary to Slack #announcements').\n"
         "5. Click <b>Save & Deploy Workflow</b>. Test the pipeline using the 'Run Test Execution' trigger."),

        ("Step 5: Configuring Enterprise Integrations",
         "1. Go to <b>Settings & Integrations</b> -> <b>Integration Panel</b>.\n"
         "2. Click <b>Configure</b> next to your desired service (Slack, Teams, Jira, Salesforce, SAP).\n"
         "3. Input the required OAuth tokens or API credentials (saved securely in Secrets Vault).\n"
         "4. Toggle the integration state to <b>Active</b>."),

        ("Step 6: Monitoring System Telemetry & Grafana",
         "1. Navigate to <b>Performance Dashboard</b> or access Grafana directly at <b>http://localhost:3001</b>.\n"
         "2. Default login credentials: User <code>admin</code> | Password <code>admin</code>.\n"
         "3. View real-time panels for System Memory, CPU Usage, Active Celery Tasks, Token Rate, and Latency.")
    ]

    for s_title, s_desc in steps:
        story.append(Paragraph(s_title, style_h2))
        for line in s_desc.split('\n'):
            story.append(Paragraph(line, style_body))
        story.append(Spacer(1, 4))

    # ---------------------------------------------------------
    # SECTION 5: TROUBLESHOOTING & FAQ
    # ---------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("5. System Troubleshooting & Operations Guide", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    faq_data = [
        [Paragraph("<b>Symptom / Issue</b>", style_h2), Paragraph("<b>Probable Cause</b>", style_h2), Paragraph("<b>Resolution Step</b>", style_h2)],
        [Paragraph("Document stuck in 'Processing'", style_body), Paragraph("Celery worker or Redis down", style_body), Paragraph("Run <code>docker-compose restart worker redis</code>", style_body)],
        [Paragraph("504 Gateway Timeout on Chat", style_body), Paragraph("LLM API rate limit or model timeout", style_body), Paragraph("Check API Key in <code>.env</code> and inspect <code>logs/backend.log</code>", style_body)],
        [Paragraph("Grafana dashboard empty", style_body), Paragraph("Prometheus target unassigned", style_body), Paragraph("Verify Prometheus target state at <code>http://localhost:9090/targets</code>", style_body)],
        [Paragraph("Permission Denied on file upload", style_body), Paragraph("Insufficient RBAC permissions", style_body), Paragraph("Ask Org Admin to update your user role to <i>Manager</i> or <i>Admin</i>", style_body)],
    ]
    t_faq = Table(faq_data, colWidths=[130, 140, 234])
    t_faq.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_faq)

    # Final summary box
    story.append(Spacer(1, 15))
    final_box = [[
        Paragraph(
            "<b>Need Technical Support?</b><br/>"
            "• Technical Documentation: <code>docs/ARCHITECTURE.md</code><br/>"
            "• API Specification: <code>http://localhost/api/v1/docs</code><br/>"
            "• Operations Support: Contact your designated Enterprise System Administrator.",
            style_body
        )
    ]]
    t_final = Table(final_box, colWidths=[504])
    t_final.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_final)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {filename}")

if __name__ == "__main__":
    build_pdf()
