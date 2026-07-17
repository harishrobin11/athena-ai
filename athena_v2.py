import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Dynamically calculates total page counts and renders professional corporate headers and footers."""
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
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1E293B"))
        
        # Upper Running Header Setup (Suppressed on Page 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "ATHENA AI (V2.0): SYSTEM ARCHITECTURE & 56-SPRINT PLATFORM SPECIFICATION")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
        
        # Lower Running Footer Setup (Applied Globally)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 50, 558, 50)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 38, "CONFIDENTIAL & PROPRIETARY — MASTER ENTERPRISE PLATFORM ARCHITECTURE SPEC")
        self.drawRightString(558, 38, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def generate_athena_v2_master_pdf():
    pdf_filename = "Athena_AI_v2_Enterprise_System_Specification.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Strict Enterprise Typographic Palette
    primary_navy = colors.HexColor("#0F172A")    # Deep Dark Slate Navy
    secondary_teal = colors.HexColor("#0F766E")  # Premium Dark Teal
    text_slate = colors.HexColor("#334155")      # Neutral Slate Body Text
    bg_slate_light = colors.HexColor("#F8FAFC")  # Cell Light Alternate Fill
    
    # Custom Typography Hierarchy Configurations
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=22, leading=26,
        textColor=primary_navy, spaceAfter=4
    )
    tagline_style = ParagraphStyle(
        'DocTagline', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=9.5, leading=13,
        textColor=secondary_teal, spaceAfter=15
    )
    h1_style = ParagraphStyle(
        'SectionH1', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=13, leading=17,
        textColor=primary_navy, spaceBefore=14, spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'SectionH2', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, leading=14,
        textColor=secondary_teal, spaceBefore=10, spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodySlate', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=13.5,
        textColor=text_slate, spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'BulletText', parent=body_style,
        leftIndent=12, firstLineIndent=-8, spaceAfter=3
    )
    table_text = ParagraphStyle(
        'TableText', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=text_slate
    )
    table_header = ParagraphStyle(
        'TableHeader', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.5, leading=12,
        textColor=colors.white
    )

    story = []
    
    # Document Header Title Block
    story.append(Paragraph("ATHENA AI MASTER SPECIFICATION MANIFEST (v2.0)", title_style))
    story.append(Paragraph("A Production-Ready Enterprise AI Operating System & Multi-Agent SaaS Platform Architecture", tagline_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_navy, spaceAfter=12))
    
    # 1. Product Vision & Value Proposition
    story.append(Paragraph("1. System Evolution & Enterprise Core Objectives", h1_style))
    story.append(Paragraph(
        "Athena AI (v2.0) transitions away from basic single-turn Q&A chatbot frameworks into a unified "
        "<b>Enterprise AI Operating System Platform</b>. Built to resolve high knowledge fragmentation, "
        "scattered organizational document storage systems, manual operation loops, and data security exposure risks, "
        "the architecture establishes multi-user structural tenant separation, state-graph orchestration pipelines, "
        "and extensive hybrid semantic search indexing networks[cite: 1, 2].", body_style
    ))
    
    # 2. Tech Stack Dimensions
    story.append(Paragraph("2. Integrated Technology & Infrastructure Spectrum", h1_style))
    
    stack_data = [
        [Paragraph("Structural Dimension", table_header), Paragraph("Integrated Architecture Framework Component", table_header)],
        [Paragraph("<b>API Routing & Gateway</b>", table_text), Paragraph("FastAPI utilizing asynchronous loops (AsyncIO), WebSockets, and Server-Sent Events (SSE)[cite: 1, 2].", table_text)],
        [Paragraph("<b>Orchestration Fabric</b>", table_text), Paragraph("LangGraph cyclic graphs managing supervisor/worker execution loops and persistent checkpoints[cite: 1, 2].", table_text)],
        [Paragraph("<b>Identity & Security</b>", table_text), Paragraph("JWT, OAuth2, and Azure Entra ID providing strict Role-Based Access Control (RBAC)[cite: 1, 2].", table_text)],
        [Paragraph("<b>Knowledge Core</b>", table_text), Paragraph("Azure AI Search, PostgreSQL (pgvector), ChromaDB, and Neo4j Semantic Knowledge Graphs[cite: 1, 2].", table_text)],
        [Paragraph("<b>LLM Infrastructure</b>", table_text), Paragraph("Azure OpenAI Service, Anthropic Claude, DeepSeek, and local Ollama deployments[cite: 1, 2].", table_text)],
        [Paragraph("<b>LLMOps & MLOps</b>", table_text), Paragraph("MLflow prompt/evaluation tracking, Prometheus, Grafana, and input/output guardrails[cite: 1, 2].", table_text)]
    ]
    
    stack_table = Table(stack_data, colWidths=[130, 374])
    stack_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_navy),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_slate_light]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(stack_table)
    story.append(Spacer(1, 8))

    # 3. Complete 56-Sprint Exhaustive Production Roadmap
    story.append(Paragraph("3. Complete 56-Sprint Production Roadmap Roadmap", h1_style))
    
    # Phase 1
    story.append(Paragraph("PHASE 1 — Foundation Platform (Sprints 1–8) [Status: Completed/Hardening]", h2_style))
    story.append(Paragraph("• <b>Sprint 1 (Project Foundation):</b> Setup FastAPI structure, configuration management via Pydantic settings, standardized logging, and initial Docker multi-stage containers[cite: 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 2 (Authentication):</b> Establish secure JWT tokens, user sign-ups, password hashing via bcrypt, refresh tokens, and strict session isolation[cite: 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 3 (Document Management):</b> Build file processing endpoints handling PDF upload validation parsing, file systems, and core storage metadata metadata[cite: 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 4 (Enterprise RAG Core):</b> Deploy text chunk splitters, high-dimensional vector extraction, and local ChromaDB collection spaces[cite: 1, 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 5 (Conversation Engine):</b> Construct relational chat log history storage using SQLite tracking conversation indexes across sessions[cite: 1, 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 6 (Streaming Transmission):</b> Build asynchronous Server-Sent Events (SSE) token transmission loops with dynamic connection drop catching[cite: 1, 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 7 (Hybrid Search Fabric):</b> Fuse sparse token lookups (BM25) and dense semantic search matrices with metadata filtering and citation node mappings[cite: 1, 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 8 (Production API Hardening):</b> Implement global request/response error intercepts, Pydantic validation parameters, and complete unit testing coverage[cite: 2].", bullet_style))
    
    # Phase 2
    story.append(Paragraph("PHASE 2 — Enterprise AI Core (Sprints 9–16) [Status: Mostly Completed/Upgrading]", h2_style))
    story.append(Paragraph("• <b>Sprint 9 (Tool Registry Framework):</b> Construct Python decorators to safely bind sandboxed utility libraries (Calculators, RAG, Web Scrapers)[cite: 1, 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 10 (Multi-Step Planner):</b> Develop an intent analysis compiler that breaks down complex user objectives into structural JSON planning blueprints[cite: 1, 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 11 (Agent Executor Loop):</b> Implement the primary reasoning execution thread (ReAct loops) mapping choices dynamically against expected tool outputs[cite: 1, 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 12 (Cognitive Memory Upgrade):</b> Refactor standard storage to decouple short-term message buffers, permanent conversation tables, and semantic profile caches[cite: 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 13 (Cross-Workspace Search):</b> Deploy multi-document search methods applying functional division permissions over document assets[cite: 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 14 (Context Ranking):</b> Build historical context scorers to automatically order historical entries and inject top relevance arrays into prompts[cite: 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 15 (Multimodal Expansion):</b> Embed vision transformer engines enabling OCR over dense non-textual corporate charts, data sheets, and flow maps[cite: 1, 2].", bullet_style))
    story.append(Paragraph("• <b>Sprint 16 (Operational Telemetry UI):</b> Construct primary evaluation views monitoring data limits, prompt cost patterns, and system exception rates[cite: 2].", bullet_style))

    # Phase 3
    story.append(KeepTogether([
        Paragraph("PHASE 3 — Agentic AI Platform (Sprints 17–24) [Status: Planned]", h2_style),
        Paragraph("• <b>Sprint 17 (LangGraph Integration):</b> Rewrite linear code chains into state-managed cyclic graph networks featuring explicit checkpoint execution rollbacks[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 18 (Supervisor Node Deployment):</b> Implement a primary root Supervisor routing agent that acts as an intent filter to orchestrate tasks to backend worker agents[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 19 (Research Agent Node):</b> Build specialized background nodes that execute multi-query internet scrapers, document validation, and summary reporting[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 20 (Document Intelligence Agent):</b> Program precise data extraction workers capable of pulling tabular relationships directly from large files[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 21 (Relational SQL Agent):</b> Deploy isolated read-only schema analytics agents that autonomously write, fix, and explain database query routines[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 22 (Sandboxed Code Agent):</b> Establish fully containerized execution micro-runtimes where agents securely generate and execute raw data manipulation scripts[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 23 (Workflow Orchestration Agent):</b> Construct continuous long-running background tasks handling deferred steps and direct webhook updates[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 24 (Multi-Agent Team Interaction):</b> Tune specialized peer messaging structures to support parallel workflows and cross-worker confirmation checks[cite: 2]." , bullet_style)
    ]))

    # Phase 4
    story.append(KeepTogether([
        Paragraph("PHASE 4 — Enterprise SaaS Layer (Sprints 25–32) [Status: Planned]", h2_style),
        Paragraph("• <b>Sprint 25 (Multi-Tenant System Isolation):</b> Implement organization ID filters across all tables, separating user data boundaries at the data block tier[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 26 (Corporate Directory Tools):</b> Develop admin toolsets handling secure employee invitations, branch assignments, and organizational mapping[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 27 (Granular RBAC Enforcer):</b> Create full access control gates parsing five core access profiles: Owner, Admin, Manager, Developer, and Viewer[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 28 (Stripe Commercial Integration):</b> Connect dynamic recurring subscription handling hooked into distinct access quota tiers[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 29 (Resource Usage Metering):</b> Code live telemetry log tracks recording compute token volumes, storage footprints, and calculation volumes[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 30 (Central Admin Control Board):</b> Build management panels showing global usage graphs, user logs, and global configuration toggles[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 31 (Asset Lifecycle Versioning):</b> Create document tracking modules tracking sequential workspace document edits, approvals, and collection rollbacks[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 32 (Agent Template Marketplace):</b> Design sharing directories for reuse of standard agent persona configurations and workflow blueprints[cite: 2].", bullet_style)
    ]))

    # Phase 5
    story.append(KeepTogether([
        Paragraph("PHASE 5 — Cloud Infrastructure & MLOps (Sprints 33–40) [Status: Planned]", h2_style),
        Paragraph("• <b>Sprint 33 (Production Container Hardening):</b> Restructure core microservices into secure, minimal, non-root multi-stage Docker builds[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 34 (Managed Enterprise Cloud Shift):</b> Port local code components to cloud hosting, mapping files onto secure private object instances[cite: 1, 2].", bullet_style),
        Paragraph("• <b>Sprint 35 (Azure AI Search Migration):</b> Swap local indexing systems for enterprise Azure AI Search clusters supporting large-scale enterprise indexing[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 36 (High-Speed Redis Deployment):</b> Insert Redis blocks managing low-latency application token limits, API session memory, and common cache tracking[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 37 (Production PostgreSQL Migration):</b> Upgrade data persistence frameworks from local SQLite files into highly available cloud PostgreSQL clusters[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 38 (Declarative CI/CD Pipelines):</b> Deploy Git-driven GitHub Actions flows covering systematic code style testing, unit evaluations, and production push scripts[cite: 1, 2].", bullet_style),
        Paragraph("• <b>Sprint 39 (Observability Matrix Setup):</b> Integrate Prometheus collectors linked to Grafana setups logging network speeds, memory loads, and error logs[cite: 1, 2].", bullet_style),
        Paragraph("• <b>Sprint 40 (Systematic LLMOps Framework):</b> Connect comprehensive MLflow setups monitoring prompts, testing configurations, and alternative models[cite: 2].", bullet_style)
    ]))

    # Phase 6
    story.append(KeepTogether([
        Paragraph("PHASE 6 — Enterprise Intelligence (Sprints 41–48) [Status: Planned]", h2_style),
        Paragraph("• <b>Sprint 41 (Advanced OCR Engine Upgrade):</b> Build high-accuracy text parsers to pull bounding box data points cleanly from financial files and billing rows[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 42 (Neo4j Knowledge Graph Integration):</b> Setup cross-document semantic connection graphs tracking corporate entity rules inside a Neo4j framework[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 43 (Neural Re-ranking Pipeline):</b> Deploy Cross-Encoder modules within retrieval threads to optimize document contexts while saving token limits[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 44 (Durable NLP Service Core):</b> Create localized text utilities running intent profiling, summary parsing, and entities tracking[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 45 (Visual Prompt Studio):</b> Build user screens giving administrators side-by-side prompt testing capabilities and response evaluation metrics[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 46 (Safety Interception Guardrails):</b> Deploy real-time security systems checking fields for malicious code injections, masking PII, and checking context grounding[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 47 (Corporate App Connector Hub):</b> Construct native bridge connections into standard enterprise systems (Slack, Teams, Jira, SAP, Salesforce)[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 48 (Visual Workflow Automation canvas):</b> Build visual drag-and-drop web interfaces letting system admins map agent flows without custom code[cite: 2].", bullet_style)
    ]))

    # Phase 7
    story.append(KeepTogether([
        Paragraph("PHASE 7 — Production Scale & Launch (Sprints 49–56) [Status: Planned]", h2_style),
        Paragraph("• <b>Sprint 49 (Production React Interface):</b> Port frontend frameworks over to optimized React / Next.js single-page tools styled via Tailwind CSS[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 50 (Analytics Dashboard Consolidation):</b> Expand tracking interfaces compiling cross-tenant active resource usage and financial reporting logs[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 51 (Distributed Dispatch Core):</b> Code resilient alert systems firing event pings through modern corporate channels based on health rules[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 52 (Resilient API Gateway Setup):</b> Place smart load balancers to balance user traffic across isolated microservice instances safely[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 53 (Celery Task Worker Grid):</b> Establish background distributed workers via Celery and RabbitMQ to handle large file array processes[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 54 (Performance Optimization Pass):</b> Fine-tune caching layouts, payload serialization rules, and compilation configs to minimize latency[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 55 (Enterprise SSO Integration):</b> Embed industrial SAML2 and OIDC interfaces enabling one-click enterprise sign-ons using Azure Entra ID[cite: 2].", bullet_style),
        Paragraph("• <b>Sprint 56 (System v1.0 Launch Deployment):</b> Finalize formal platform API document guides, developer software kits (SDKs), and push the stable build live[cite: 2].", bullet_style)
    ]))

    # 4. Relational Storage Architecture Definitions
    story.append(KeepTogether([
        Paragraph("4. Core PostgreSQL Multi-Tenant Database Schema", h1_style),
        Paragraph(
            "To guarantee complete tenant isolation before text vectors ever enter the high-dimensional query spaces, "
            "the system operates a relational ledger defining organization boundaries precisely[cite: 1].", body_style
        )
    ]))
    
    # Render Code Snippet as standard text blocks inside a grey visual container
    code_text = (
        "CREATE TABLE organizations (\n"
        "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
        "    name VARCHAR(255) NOT NULL,\n"
        "    tier VARCHAR(50) CHECK (tier IN ('free', 'pro', 'business', 'enterprise')) DEFAULT 'free',\n"
        "    stripe_customer_id VARCHAR(255) UNIQUE,\n"
        "    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP\n"
        ");\n\n"
        "CREATE TABLE users (\n"
        "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
        "    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,\n"
        "    email VARCHAR(255) UNIQUE NOT NULL,\n"
        "    hashed_password VARCHAR(255) NOT NULL,\n"
        "    role VARCHAR(50) CHECK (role IN ('Owner', 'Admin', 'Manager', 'Developer', 'Viewer')) DEFAULT 'Viewer',\n"
        "    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP\n"
        ");\n\n"
        "CREATE TABLE conversations (\n"
        "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
        "    user_id UUID REFERENCES users(id) ON DELETE CASCADE,\n"
        "    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,\n"
        "    title VARCHAR(255) NOT NULL,\n"
        "    state_snapshot JSONB, -- Persistent state snapshots for LangGraph execution nodes\n"
        "    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP\n"
        ");"
    )
    
    code_style = ParagraphStyle(
        'CodeBlock', parent=styles['Normal'],
        fontName='Courier', fontSize=7.5, leading=11,
        textColor=colors.HexColor("#0F172A"), spaceBefore=4, spaceAfter=4
    )
    
    code_cell = [[Paragraph(code_text.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style)]]
    code_table = Table(code_cell, colWidths=[504])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(code_table)

    # Document Compilation
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Master blueprint document successfully compiled: {pdf_filename}")

if __name__ == "__main__":
    generate_athena_v2_master_pdf()