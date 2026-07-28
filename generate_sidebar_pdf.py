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
    Two-pass canvas to dynamically compute total page count and draw header/footer.
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

        # Suppress header/footer on cover page
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#475569"))
            self.drawString(54, page_height - 36, "ATHENA AI — SIDEBAR FEATURE GUIDE & MODULE REFERENCE")
            self.setFont("Helvetica", 8)
            self.drawRightString(page_width - 54, page_height - 36, "v1.0 Enterprise")
            
            # Header rule
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.75)
            self.line(54, page_height - 42, page_width - 54, page_height - 42)

            # Footer rule
            self.line(54, 45, page_width - 54, 45)

            # Footer text
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(54, 30, "Confidential & Proprietary — Athena AI Platform")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(page_width - 54, 30, page_text)

        self.restoreState()


def build_sidebar_guide_pdf(filename="Athena_AI_Sidebar_Features_Guide.pdf"):
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
    PRIMARY = colors.HexColor("#1E1B4B")      # Deep Indigo/Navy
    SECONDARY = colors.HexColor("#4F46E5")    # Indigo Accent
    TEXT_DARK = colors.HexColor("#0F172A")    # Slate 900
    TEXT_MUTED = colors.HexColor("#475569")   # Slate 600
    ACCENT_BG = colors.HexColor("#F8FAFC")    # Slate 50
    CARD_BG = colors.HexColor("#EEF2FF")      # Light Indigo Tint
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    # Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=PRIMARY,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=SECONDARY,
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletDark',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4
    )

    badge_style = ParagraphStyle(
        'BadgeText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=PRIMARY
    )

    story = []

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("Athena AI Platform", title_style))
    story.append(Paragraph("Complete Sidebar Features & Functional Specification Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=SECONDARY, spaceAfter=20))

    intro_p1 = ("This official reference document details the purpose, technical architecture, "
                "business value, and primary capabilities of every operational module accessible from "
                "the <b>Athena AI Sidebar Navigation Menu</b>.")
    story.append(Paragraph(intro_p1, body_style))
    story.append(Spacer(1, 15))

    # Overview Table of the 8 Modules
    summary_data = [
        [Paragraph("<b>Sidebar Icon & Feature</b>", badge_style), Paragraph("<b>Primary Function & Description</b>", badge_style), Paragraph("<b>Target Audience</b>", badge_style)],
        [Paragraph("📊 <b>Dashboard</b>", body_style), Paragraph("Real-time telemetry, live WebSockets metrics, memory & department token usage", body_style), Paragraph("DevOps, Admins, CTOs", body_style)],
        [Paragraph("💬 <b>Chat Interface</b>", body_style), Paragraph("RAG document Q&A, context memory, streaming answers, document search", body_style), Paragraph("Analysts, Knowledge Workers", body_style)],
        [Paragraph("🧠 <b>ML Classifier</b>", body_style), Paragraph("Automated machine learning transaction classification & confidence scoring", body_style), Paragraph("Finance, Accountants, Auditors", body_style)],
        [Paragraph("⚡ <b>Workflow Builder</b>", body_style), Paragraph("Visual drag-and-drop orchestration of multi-step AI & code execution pipelines", body_style), Paragraph("Automation Engineers, Analysts", body_style)],
        [Paragraph("🔌 <b>API Hub</b>", body_style), Paragraph("Enterprise connectors, external REST tools, database webhooks, and secret key vault", body_style), Paragraph("Integrators, IT Admins", body_style)],
        [Paragraph("🔐 <b>Security</b>", body_style), Paragraph("Multi-tenant isolation, RBAC department clearance, JWT auth, security logs", body_style), Paragraph("CISOs, Compliance Officers", body_style)],
        [Paragraph("📈 <b>Performance</b>", body_style), Paragraph("GZip compression telemetry, Redis caching hit-ratio, FastAPILimiter rate control", body_style), Paragraph("SREs, Infrastructure Engineers", body_style)],
        [Paragraph("⚙️ <b>Settings</b>", body_style), Paragraph("LLM provider selection (Gemini, OpenAI, Ollama), user profile & theme preferences", body_style), Paragraph("All System Users", body_style)]
    ]

    t_summary = Table(summary_data, colWidths=[2.1*inch, 3.7*inch, 1.4*inch])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), CARD_BG),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_summary)
    story.append(PageBreak())

    # =========================================================================
    # FEATURE 1: DASHBOARD
    # =========================================================================
    story.append(Paragraph("1. 📊 Analytics Dashboard", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceAfter=10))

    p1 = ("The <b>Analytics Dashboard</b> serves as the central command bridge for monitoring platform performance, "
          "operational stability, and multi-tenant resource utilization in real time.")
    story.append(Paragraph(p1, body_style))

    story.append(Paragraph("Key Capabilities:", h2_style))
    story.append(Paragraph("• <b>Live System Telemetry:</b> Establishes a persistent WebSocket connection to <code>/api/v1/metrics/live</code> streaming live CPU/RAM utilization, response latency, and active execution counts.", bullet_style))
    story.append(Paragraph("• <b>Token Usage by Department:</b> Bar chart analytics tracking LLM token consumption across Finance, Legal, HR, Engineering, and Sales for cost allocation.", bullet_style))
    story.append(Paragraph("• <b>Workflow Execution Rate:</b> Pie chart visualizing execution stability (e.g. 85% success vs 15% failure rate).", bullet_style))
    story.append(Paragraph("• <b>Real-Time Latency Time-Series:</b> Time-series line chart updating every second to monitor API responsiveness.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # FEATURE 2: CHAT INTERFACE
    # =========================================================================
    story.append(Paragraph("2. 💬 Chat Interface", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceAfter=10))

    p2 = ("The <b>Chat Interface</b> is a full-screen conversational assistant powered by Retrieval-Augmented Generation (RAG) "
          "and multi-tenant vector memory.")
    story.append(Paragraph(p2, body_style))

    story.append(Paragraph("Key Capabilities:", h2_style))
    story.append(Paragraph("• <b>RAG Document Search:</b> Allows users to query uploaded enterprise documents (PDFs, DOCX, CSVs) with page citations.", bullet_style))
    story.append(Paragraph("• <b>Streaming Token Delivery:</b> Uses Server-Sent Events (SSE) to stream model responses word-by-word with zero delay.", bullet_style))
    story.append(Paragraph("• <b>Session History Management:</b> Persists conversation threads with instant creation, selection, and deletion.", bullet_style))
    story.append(Paragraph("• <b>Multi-Tool Execution:</b> Automatically invokes python execution, web search, or financial database lookups as required.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # FEATURE 3: ML CLASSIFIER
    # =========================================================================
    story.append(Paragraph("3. 🧠 ML Expense Classifier", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceAfter=10))

    p3 = ("The <b>ML Expense Classifier</b> provides automated Machine Learning classification of raw transaction descriptions "
          "into enterprise financial accounting categories.")
    story.append(Paragraph(p3, body_style))

    story.append(Paragraph("Key Capabilities:", h2_style))
    story.append(Paragraph("• <b>Automated Category Inference:</b> Analyzes raw invoice lines (e.g. 'AWS Cloud Compute') and categorizes them into standard accounting buckets.", bullet_style))
    story.append(Paragraph("• <b>Confidence Scoring:</b> Outputs model confidence percentages (e.g. 98.4%) to guarantee audit accuracy.", bullet_style))
    story.append(Paragraph("• <b>Batch Invoice Processing:</b> Ingests multi-row transaction payloads for high-speed ledger posting.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # FEATURE 4: WORKFLOW BUILDER
    # =========================================================================
    story.append(Paragraph("4. ⚡ Workflow Builder", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceAfter=10))

    p4 = ("The <b>Workflow Builder</b> enables users to visually design, schedule, and execute complex multi-step AI automations "
          "and asynchronous background tasks.")
    story.append(Paragraph(p4, body_style))

    story.append(Paragraph("Key Capabilities:", h2_style))
    story.append(Paragraph("• <b>Multi-Step Pipeline Orchestration:</b> Links LLM prompts, Python code sandboxes, SQL queries, and external APIs.", bullet_style))
    story.append(Paragraph("• <b>Asynchronous Celery Execution:</b> Offloads long-running tasks to background Celery workers backed by Redis queues.", bullet_style))
    story.append(Paragraph("• <b>Execution Status Tracking:</b> Real-time status indicators for Pending, Running, Success, and Error states.", bullet_style))
    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # =========================================================================
    # FEATURE 5: API HUB
    # =========================================================================
    story.append(Paragraph("5. 🔌 Enterprise API Hub", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceAfter=10))

    p5 = ("The <b>Enterprise API Hub</b> acts as the central integration portal for managing external SaaS connections, "
          "webhooks, and REST tools.")
    story.append(Paragraph(p5, body_style))

    story.append(Paragraph("Key Capabilities:", h2_style))
    story.append(Paragraph("• <b>Third-Party Connectors:</b> Pre-built tool integrations for Slack, Salesforce, Google Drive, PostgreSQL, and custom REST APIs.", bullet_style))
    story.append(Paragraph("• <b>Secret Vault & Keys:</b> Encrypted storage for API tokens and authentication headers.", bullet_style))
    story.append(Paragraph("• <b>Webhook Event Listeners:</b> Listens for external triggers to launch automated AI workflows.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # FEATURE 6: SECURITY
    # =========================================================================
    story.append(Paragraph("6. 🔐 Enterprise Security", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceAfter=10))

    p6 = ("The <b>Security Module</b> handles Role-Based Access Control (RBAC), tenant data isolation, and authentication security.")
    story.append(Paragraph(p6, body_style))

    story.append(Paragraph("Key Capabilities:", h2_style))
    story.append(Paragraph("• <b>Department RBAC Isolation:</b> Enforces data boundaries between Finance, Procurement, Admin, and HR departments.", bullet_style))
    story.append(Paragraph("• <b>Bcrypt & JWT Security:</b> Hashed passwords and signed JSON Web Tokens for stateless session verification.", bullet_style))
    story.append(Paragraph("• <b>Security Audit Logging:</b> Records user logins, document uploads, and access events for compliance.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # FEATURE 7: PERFORMANCE
    # =========================================================================
    story.append(Paragraph("7. 📈 Performance & Cache", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceAfter=10))

    p7 = ("The <b>Performance Dashboard</b> provides granular monitoring of network optimization, Redis caching hit rates, and rate limiting.")
    story.append(Paragraph(p7, body_style))

    story.append(Paragraph("Key Capabilities:", h2_style))
    story.append(Paragraph("• <b>GZip Compression:</b> Middleware metrics for automatic network payload compression on responses > 1KB.", bullet_style))
    story.append(Paragraph("• <b>Redis Cache Telemetry:</b> Tracks cache hits for vector embeddings and frequent query responses.", bullet_style))
    story.append(Paragraph("• <b>FastAPILimiter Rate Control:</b> Limits request rates per client to prevent API abuse.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # FEATURE 8: SETTINGS
    # =========================================================================
    story.append(Paragraph("8. ⚙️ System Settings", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceAfter=10))

    p8 = ("The <b>Settings Module</b> allows users and administrators to customize LLM providers, model parameters, and UI themes.")
    story.append(Paragraph(p8, body_style))

    story.append(Paragraph("Key Capabilities:", h2_style))
    story.append(Paragraph("• <b>LLM Provider Engine Switching:</b> Seamlessly switch model backends between Google Gemini, OpenAI GPT-4, and Local Ollama Llama 3.2.", bullet_style))
    story.append(Paragraph("• <b>User Profile Management:</b> Update username, email preferences, and password credentials.", bullet_style))
    story.append(Paragraph("• <b>Theme Customization:</b> Dark Mode and glassmorphic UI customization controls.", bullet_style))

    # Build Document using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {os.path.abspath(filename)}")

if __name__ == "__main__":
    build_sidebar_guide_pdf()
