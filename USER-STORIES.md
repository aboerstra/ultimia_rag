# User Stories - QBR Automation System

Based on the Adrian Boerstra persona, these user stories define functionality for the QBR automation system.

---

## Epic 1: Automated Data Collection

### Story 1.1: Extract Meeting Transcripts
**As a** consultant preparing a QBR  
**I want** to automatically extract text from all PDF transcripts  
**So that** I don't have to manually read through 23+ documents

**Acceptance Criteria:**
- [ ] System processes all PDFs in the raw transcripts folder
- [ ] Extracted text is saved in markdown format
- [ ] Metadata (meeting number, attendees) is parsed from filename
- [ ] Process completes in under 5 minutes for 23 PDFs
- [ ] Errors are reported clearly if PDFs are corrupted

**Priority:** P0 (Must Have)  
**Story Points:** 5  
**Status:** ✅ Implemented

---

### Story 1.2: Collect Jira Project Data
**As a** project lead tracking deliverables  
**I want** to automatically pull issues, sprints, and velocity from Jira  
**So that** I can see actual progress without manual exports

**Acceptance Criteria:**
- [ ] System connects to Jira API with provided credentials
- [ ] Fetches all projects in the workspace
- [ ] Pulls 6 months of issues with status, assignee, dates
- [ ] Calculates velocity trends from sprint data
- [ ] Saves data as structured JSON files
- [ ] Reports count of issues by status (Done, In Progress, etc.)

**Priority:** P0 (Must Have)  
**Story Points:** 8  
**Status:** ✅ Implemented

---

### Story 1.3: Collect Time Tracking Data
**As a** consultant managing budget  
**I want** to automatically pull time entries from Clockify  
**So that** I can reconcile actual hours against budget

**Acceptance Criteria:**
- [ ] System connects to Clockify API
- [ ] Identifies the correct workspace automatically
- [ ] Pulls 6 months of time entries by project
- [ ] Calculates total hours, billable hours per project
- [ ] Saves raw entries and summary data
- [ ] Reports hours breakdown in terminal output

**Priority:** P0 (Must Have)  
**Story Points:** 8  
**Status:** ✅ Implemented

---

## Epic 2: AI-Powered Analysis

### Story 2.1: Analyze Individual Transcripts
**As a** consultant reviewing meeting outcomes  
**I want** Claude to analyze each transcript for key insights  
**So that** I can quickly understand decisions, actions, and concerns

**Acceptance Criteria:**
- [ ] System sends each transcript to Claude via OpenRouter
- [ ] Extracts: date, attendees, summary, topics, decisions
- [ ] Identifies action items with owners
- [ ] Flags concerns and blockers mentioned
- [ ] Highlights what Michael Kianmahd specifically asked about
- [ ] Saves analysis as structured JSON
- [ ] Handles API errors gracefully with retries

**Priority:** P0 (Must Have)  
**Story Points:** 13  
**Status:** ✅ Implemented

---

### Story 2.2: Synthesize Cross-Transcript Insights
**As a** consultant preparing a QBR narrative  
**I want** Claude to identify patterns across all meetings  
**So that** I can see recurring themes and evolution of issues

**Acceptance Criteria:**
- [ ] System combines all transcript analyses
- [ ] Claude generates comprehensive synthesis document
- [ ] Output includes: timeline, themes, Michael's priorities
- [ ] Shows commitments made vs delivered
- [ ] Identifies unresolved issues and blockers
- [ ] Tracks how topics evolved over time
- [ ] Saves as markdown document

**Priority:** P0 (Must Have)  
**Story Points:** 8  
**Status:** ✅ Implemented

---

### Story 2.3: Generate QBR Draft
**As a** consultant creating a quarterly review  
**I want** Claude to combine all data into a QBR presentation  
**So that** I have a solid foundation to refine rather than starting from scratch

**Acceptance Criteria:**
- [ ] System combines transcript synthesis, Jira data, Clockify data
- [ ] Claude generates executive summary with status indicators
- [ ] Includes progress dashboard with metrics
- [ ] Provides value stream updates per workstream
- [ ] Shows business impact and ROI
- [ ] Includes 30/60/90 day roadmap
- [ ] Output is client-ready markdown format

**Priority:** P0 (Must Have)  
**Story Points:** 13  
**Status:** ✅ Implemented

---

## Epic 3: User Experience & Automation

### Story 3.1: One-Command Execution
**As a** busy consultant with limited time  
**I want** to run the entire pipeline with a single command  
**So that** I can start the process and work on other tasks

**Acceptance Criteria:**
- [ ] Single command: `python scripts/main.py`
- [ ] Runs all 6 steps sequentially
- [ ] Shows clear progress indicators for each step
- [ ] Reports success/failure for each phase
- [ ] Completes full pipeline in 5-15 minutes
- [ ] Can be interrupted safely with Ctrl+C

**Priority:** P0 (Must Have)  
**Story Points:** 5  
**Status:** ✅ Implemented

---

### Story 3.2: Clear Progress Feedback
**As a** user running a long process  
**I want** to see what's happening at each step  
**So that** I know the system is working and roughly how long it will take

**Acceptance Criteria:**
- [ ] Each major step shows a clear header
- [ ] Progress indicators show X of Y items processed
- [ ] Success/failure is clearly marked (✅/❌)
- [ ] Errors include helpful troubleshooting hints
- [ ] Final summary shows where outputs are located
- [ ] Total runtime is reported

**Priority:** P1 (Should Have)  
**Story Points:** 3  
**Status:** ✅ Implemented

---

### Story 3.3: Secure Credential Management
**As a** security-conscious user  
**I want** API credentials stored securely and not in version control  
**So that** I don't accidentally expose sensitive information

**Acceptance Criteria:**
- [ ] All credentials stored in .env file
- [ ] .env is in .gitignore
- [ ] Clear error if credentials are missing
- [ ] No credentials in code files
- [ ] README warns about credential security

**Priority:** P0 (Must Have)  
**Story Points:** 2  
**Status:** ✅ Implemented

---

## Epic 4: Documentation & Onboarding

### Story 4.1: Quick Start Guide
**As a** first-time user  
**I want** a simple guide to get started quickly  
**So that** I can run the system without reading extensive documentation

**Acceptance Criteria:**
- [ ] QUICKSTART.md exists in root directory
- [ ] Shows exact commands to run
- [ ] Lists what outputs to expect
- [ ] Includes troubleshooting for common issues
- [ ] Readable in under 5 minutes

**Priority:** P0 (Must Have)  
**Story Points:** 2  
**Status:** ✅ Implemented

---

### Story 4.2: Technical Documentation
**As a** technical user wanting to customize  
**I want** detailed documentation of the architecture  
**So that** I can understand how it works and modify it

**Acceptance Criteria:**
- [ ] scripts/README.md explains architecture
- [ ] Each script has docstrings
- [ ] Shows how to customize for specific projects
- [ ] Explains configuration options
- [ ] Includes examples of modifications

**Priority:** P1 (Should Have)  
**Story Points:** 5  
**Status:** ✅ Implemented

---

### Story 4.3: User Persona Documentation
**As a** product team understanding users  
**I want** a detailed persona document  
**So that** future enhancements align with user needs

**Acceptance Criteria:**
- [ ] Follows Nielsen Norman Group standards
- [ ] Includes goals, pain points, behaviors
- [ ] Shows real scenarios and use cases
- [ ] Identifies success metrics
- [ ] Documents adoption journey

**Priority:** P2 (Nice to Have)  
**Story Points:** 3  
**Status:** ✅ Implemented

---

## Epic 5: Salesforce Integration (New - Critical)

### Story 5.1: Connect to Salesforce Orgs
**As a** consultant managing a Salesforce implementation project  
**I want** to connect to both production and sandbox Salesforce orgs  
**So that** I can retrieve actual technical delivery data

**Acceptance Criteria:**
- [ ] System connects to Salesforce production org
- [ ] System connects to Salesforce sandbox org
- [ ] Uses secure credential storage (.env)
- [ ] Tests connection before data retrieval
- [ ] Reports connection status and org info
- [ ] Handles authentication errors gracefully

**Priority:** P0 (Must Have)  
**Story Points:** 5  
**Status:** ⏳ Not Yet Implemented

---

### Story 5.2: Collect Salesforce Metadata
**As a** consultant proving technical delivery  
**I want** to retrieve custom objects, Apex classes, and Flows from Salesforce  
**So that** I can show what was actually built in the org

**Acceptance Criteria:**
- [ ] Retrieves all custom objects with field counts
- [ ] Retrieves Apex classes with line counts
- [ ] Retrieves active Flows
- [ ] Collects validation rules
- [ ] Gets test coverage metrics
- [ ] Retrieves deployment history (last 6 months)
- [ ] Saves metadata as structured JSON

**Priority:** P0 (Must Have)  
**Story Points:** 8  
**Status:** ⏳ Not Yet Implemented

---

### Story 5.3: Compare Production vs Sandbox
**As a** consultant managing configuration  
**I want** to compare production and sandbox environments  
**So that** I can identify configuration drift and promotion gaps

**Acceptance Criteria:**
- [ ] Compares custom objects in both orgs
- [ ] Identifies objects only in production
- [ ] Identifies objects only in sandbox
- [ ] Detects field count differences
- [ ] Flags objects not promoted to production
- [ ] Generates comparison report
- [ ] Highlights deployment readiness issues

**Priority:** P1 (Should Have)  
**Story Points:** 8  
**Status:** ⏳ Not Yet Implemented

---

### Story 5.4: Cross-Validate Discussed vs Built (The Killer Feature)
**As a** consultant ensuring accountability  
**I want** to validate what was discussed in meetings against what exists in Salesforce  
**So that** I can identify gaps between promises and delivery

**Acceptance Criteria:**
- [ ] Extracts object mentions from meeting transcripts
- [ ] Matches mentions to Salesforce custom objects
- [ ] Links to related Jira tickets
- [ ] Identifies discussed features not in Salesforce
- [ ] Identifies Jira tickets "Done" but not deployed
- [ ] Generates gap analysis report
- [ ] Provides evidence for complete features

**Priority:** P0 (Must Have) - This is the differentiator  
**Story Points:** 13  
**Status:** ⏳ Not Yet Implemented

---

### Story 5.5: Calculate Technical Delivery Metrics
**As a** consultant demonstrating ROI  
**I want** to show concrete technical delivery metrics  
**So that** I can prove value beyond hours logged

**Acceptance Criteria:**
- [ ] Counts custom objects deployed in date range
- [ ] Calculates total lines of Apex code
- [ ] Reports test coverage percentage
- [ ] Counts active vs inactive Flows
- [ ] Identifies recent deployments
- [ ] Shows deployment frequency
- [ ] Presents metrics in QBR format

**Priority:** P0 (Must Have)  
**Story Points:** 5  
**Status:** ⏳ Not Yet Implemented

---

## Epic 6: Data Validation & Quality

### Story 5.1: Cross-Source Validation
**As a** consultant presenting data to clients  
**I want** to cross-reference transcript discussions with Jira delivery  
**So that** I can identify gaps between commitments and reality

**Acceptance Criteria:**
- [ ] System identifies commitments made in transcripts
- [ ] Matches commitments to Jira tickets where possible
- [ ] Flags commitments with no corresponding delivery
- [ ] Highlights where actual delivery exceeded discussion
- [ ] Generates gap analysis report

**Priority:** P1 (Should Have)  
**Story Points:** 13  
**Status:** ⏳ Not Yet Implemented

---

### Story 5.2: Data Quality Checks
**As a** user relying on automated analysis  
**I want** the system to validate data quality  
**So that** I can trust the outputs or know when to investigate

**Acceptance Criteria:**
- [ ] Checks that PDFs extracted successfully (non-zero text)
- [ ] Verifies API connections before processing
- [ ] Flags transcripts where AI analysis failed
- [ ] Reports if Jira/Clockify returned no data
- [ ] Generates data quality summary report

**Priority:** P1 (Should Have)  
**Story Points:** 5  
**Status:** ⏳ Not Yet Implemented

---

## Epic 6: Interactive Features (Future)

### Story 6.1: Query Specific Topics
**As a** consultant answering ad-hoc questions  
**I want** to ask "show me all discussions about data model"  
**So that** I can quickly find relevant information without re-reading everything

**Acceptance Criteria:**
- [ ] Command-line interface for queries
- [ ] Can search across transcripts, Jira, Clockify
- [ ] Returns relevant excerpts with context
- [ ] Shows which meetings and when topics were discussed
- [ ] Links to related Jira tickets and time entries

**Priority:** P2 (Nice to Have)  
**Story Points:** 13  
**Status:** 🔮 Future Enhancement

---

### Story 6.2: Incremental Updates
**As a** user running monthly QBRs  
**I want** to process only new data since last run  
**So that** I don't waste time and API costs on unchanged data

**Acceptance Criteria:**
- [ ] System tracks when it last ran
- [ ] Only processes new transcripts
- [ ] Only fetches new Jira issues/time entries
- [ ] Merges with previous analysis
- [ ] Updates synthesis with new insights
- [ ] Saves complete + incremental outputs

**Priority:** P2 (Nice to Have)  
**Story Points:** 8  
**Status:** 🔮 Future Enhancement

---

### Story 6.3: Visual Dashboard Generation
**As a** presenter creating client-facing materials  
**I want** automatic chart generation for key metrics  
**So that** I don't have to manually create visualizations

**Acceptance Criteria:**
- [ ] Generates velocity trend charts
- [ ] Creates burn-down/burn-up charts
- [ ] Shows hours by project pie chart
- [ ] Produces timeline visualization
- [ ] Exports as PNG/SVG for presentations
- [ ] Embedded in QBR draft markdown

**Priority:** P2 (Nice to Have)  
**Story Points:** 13  
**Status:** 🔮 Future Enhancement

---

## Epic 7: Confluence Integration (Future)

### Story 7.1: Fetch Confluence Documentation
**As a** consultant with technical docs in Confluence  
**I want** to automatically pull relevant pages  
**So that** technical decisions are included in QBR context

**Acceptance Criteria:**
- [ ] Connects to Confluence API
- [ ] Fetches pages in specific space
- [ ] Converts HTML to markdown
- [ ] Includes in analysis context
- [ ] Links technical decisions to transcripts
- [ ] Saves locally for reference

**Priority:** P2 (Nice to Have)  
**Story Points:** 8  
**Status:** 🔮 Future Enhancement

---

## Epic 8: RAG System (Future)

### Story 8.1: Build Vector Database
**As a** user with growing historical data  
**I want** a RAG system for intelligent querying  
**So that** I can ask complex questions across all QBRs

**Acceptance Criteria:**
- [ ] Embeds all transcripts, analyses, data
- [ ] Stores in vector database (e.g., Chroma)
- [ ] Supports semantic search
- [ ] Returns relevant context for queries
- [ ] Updates incrementally with new data
- [ ] Low-latency query response

**Priority:** P3 (Optional)  
**Story Points:** 21  
**Status:** 🔮 Future Enhancement

---

### Story 8.2: Conversational Interface
**As a** user preparing presentations  
**I want** to have a conversation with my QBR data  
**So that** I can explore insights dynamically

**Acceptance Criteria:**
- [ ] Chat-like interface (CLI or web)
- [ ] Supports follow-up questions
- [ ] Cites sources for claims
- [ ] Can compare across time periods
- [ ] "Why did X take longer than expected?"
- [ ] "What did Michael say about Y in Q2 vs Q3?"

**Priority:** P3 (Optional)  
**Story Points:** 21  
**Status:** 🔮 Future Enhancement

---

## Epic 9: Team Collaboration (Future)

### Story 9.1: Share QBR Insights
**As a** team lead  
**I want** to share generated insights with my team  
**So that** everyone has the same context

**Acceptance Criteria:**
- [ ] Exports QBR as PDF
- [ ] Generates shareable HTML version
- [ ] Creates PowerPoint slides from markdown
- [ ] Email integration for distribution
- [ ] Web dashboard for team viewing

**Priority:** P3 (Optional)  
**Story Points:** 13  
**Status:** 🔮 Future Enhancement

---

## Epic 10: Multi-Client Support (Future)

### Story 10.1: Client-Specific Configurations
**As a** consultant working with multiple clients  
**I want** to manage separate configurations per client  
**So that** I can reuse the system across all my work

**Acceptance Criteria:**
- [ ] Support multiple .env profiles
- [ ] Client-specific data directories
- [ ] Reusable templates per client
- [ ] Switch between clients easily
- [ ] Historical comparison across clients

**Priority:** P3 (Optional)  
**Story Points:** 13  
**Status:** 🔮 Future Enhancement

---

## Story Status Legend

- ✅ **Implemented** - Currently available in the system
- ⏳ **Not Yet Implemented** - Planned for near-term
- 🔮 **Future Enhancement** - Low priority, nice to have

## Priority Definitions

- **P0 (Must Have)** - Core functionality, system unusable without it
- **P1 (Should Have)** - Important for user satisfaction, implement soon
- **P2 (Nice to Have)** - Enhances experience, implement when able
- **P3 (Optional)** - Low priority, implement if resources allow

## Story Points Guide

- **2-3**: Simple change, < 1 day
- **5**: Moderate complexity, 1-2 days
- **8**: Complex, 3-5 days
- **13**: Very complex, 1-2 weeks
- **21**: Epic-level effort, 2-4 weeks

---

*User stories created following Agile/Scrum best practices*
