# User Persona - QBR Automation System

## Persona Overview

**Name:** Adrian Boerstra  
**Role:** Technical Consultant & Project Lead  
**Company:** Faye BSG  
**Client:** Maxim (Michael Kianmahd)  
**Age:** 30-45  
**Location:** Toronto, Canada  

---

## Background & Context

Adrian is a technical consultant at Faye BSG working on a complex integration project for Maxim. He regularly collaborates with Laura Dolphin (lead consultant), Michael Kianmahd (client stakeholder), and various team members across multiple workstreams.

### Professional Profile

**Experience Level:** Senior/Expert  
- Deep technical knowledge across multiple domains
- Strong project management capabilities
- Client-facing presentation skills
- Data-driven decision maker

**Core Responsibilities:**
- Technical implementation and architecture
- Client relationship management
- QBR preparation and presentation
- Cross-team coordination
- Progress tracking and reporting

---

## Goals & Needs

### Primary Goals

1. **Inspire Client Confidence**
   - Present clear, transparent progress to Michael
   - Demonstrate accountability and realistic planning
   - Show ROI and business impact of work delivered

2. **Save Time on Manual Work**
   - Reduce hours spent gathering data from multiple systems
   - Automate repetitive analysis tasks
   - Focus energy on strategic insights vs data wrangling

3. **Deliver Data-Driven Narratives**
   - Cross-reference multiple data sources for validation
   - Identify patterns and trends Michael cares about
   - Create compelling story backed by evidence

### Secondary Goals

- Maintain detailed records of all client interactions
- Track commitments made vs delivered
- Identify blockers early through pattern recognition
- Build reusable process for future QBRs

---

## Pain Points & Frustrations

### Data Collection Challenges

❌ **"I have data scattered across 5+ systems"**
- 23 meeting transcripts (PDF)
- Jira projects and issues
- Clockify time tracking
- Confluence documentation
- Email trails and Slack messages

❌ **"Manual synthesis takes days"**
- Reading through all transcripts to find patterns
- Cross-referencing discussions with actual delivery
- Calculating metrics manually from Jira
- Reconciling budget vs actual hours

### Analysis Complexity

❌ **"Hard to see the forest for the trees"**
- Too much raw data, not enough insights
- Difficult to identify recurring themes across 6 months
- Michael's real priorities buried in transcript noise
- Commitments made weeks ago forgotten or lost

### Client Presentation Pressure

❌ **"Michael values transparency and accountability"**
- Needs to show progress with high confidence
- Can't afford to miss or misrepresent commitments
- Must demonstrate realistic planning (not over-promising)
- Has to connect technical work to business value

---

## Behaviors & Preferences

### Work Style

✅ **Technical but pragmatic**
- Comfortable with code and APIs
- Prefers automated solutions over manual processes
- Values tools that "just work" without extensive setup
- Willing to invest time upfront for long-term efficiency

✅ **Data-driven storyteller**
- Believes in evidence-based reporting
- Wants to validate claims with multiple sources
- Seeks patterns and trends over anecdotes
- Thinks in terms of metrics and KPIs

✅ **Quality-focused but deadline-conscious**
- Wants comprehensive analysis but has time constraints
- Values 80/20 rule - good enough quickly vs perfect slowly
- Appreciates clear documentation and guides
- Prefers iterative improvement over perfection

### Technology Comfort Level

- **Programming:** High (Python, scripts, APIs)
- **Command Line:** High (comfortable with terminal)
- **AI/LLM Tools:** Medium-High (understanding of capabilities)
- **Project Management Tools:** High (Jira, Confluence expert)
- **Time Tracking:** High (Clockify power user)

### Learning Preferences

- Prefers doing over reading extensive docs
- Values quick start guides and examples
- Appreciates clear error messages and troubleshooting
- Likes to understand "why" not just "how"

---

## Technology & Tools Context

### Systems Currently Used

- **Communication:** Meeting transcripts, email, Slack
- **Project Management:** Jira (issues, sprints, velocity)
- **Documentation:** Confluence
- **Time Tracking:** Clockify
- **Development:** VSCode, Python, Git
- **AI Tools:** Exploring Claude/GPT for analysis

### Tool Expectations

**Must Have:**
- Automated data collection from all sources
- AI-powered insight generation
- Cross-source validation and synthesis
- Clear, actionable output (not raw data dumps)

**Nice to Have:**
- Interactive querying of collected data
- Visualization generation
- Historical trend analysis
- Reusable templates

**Deal Breakers:**
- Requires extensive manual configuration
- Produces generic/unhelpful output
- Lacks clear documentation
- High ongoing cost without clear ROI

---

## Scenarios & Use Cases

### Scenario 1: Monthly QBR Preparation

**Context:** It's 3 days before the QBR with Michael. Adrian needs to prepare a comprehensive review covering the last month's progress.

**Current Process (Without Tool):**
1. Read through all meeting transcripts (4-6 hours)
2. Manually note Michael's concerns and priorities
3. Export Jira data, calculate velocity in Excel (2 hours)
4. Pull Clockify reports, reconcile with budget (1 hour)
5. Cross-reference discussions with actual delivery (3 hours)
6. Draft QBR presentation (4 hours)
**Total:** 14-16 hours

**Desired Process (With Tool):**
1. Run automated pipeline (15 minutes)
2. Review AI-generated insights (1 hour)
3. Refine and customize QBR draft (2 hours)
**Total:** 3-4 hours

### Scenario 2: Mid-Sprint Check-in

**Context:** Michael asks for a quick update on a specific workstream mentioned in recent meetings.

**Need:** Quickly find all mentions of that topic across transcripts, see related Jira tickets, check time spent.

**Expectation:** Should take minutes, not hours.

### Scenario 3: Budget Justification

**Context:** Need to explain why certain tasks took longer than estimated.

**Need:** Cross-reference transcript discussions about scope changes with actual time entries and Jira updates.

**Expectation:** Tool should surface the connections automatically.

---

## Key Quote

> *"I need to show Michael clear progress backed by data from multiple sources. I don't have time to manually piece together 6 months of transcripts, Jira tickets, and time logs. Give me the insights that matter, validated across systems, so I can focus on the strategic narrative."*

---

## Design Implications

### For This QBR Automation System

#### ✅ What Works Well

1. **One Command Execution**
   - Matches Adrian's "just work" philosophy
   - `python scripts/main.py` is simple and memorable

2. **Multi-Source Integration**
   - Addresses core pain point of scattered data
   - Automated API connections save manual export/import

3. **AI-Powered Analysis**
   - Removes manual synthesis burden
   - Identifies patterns Adrian would miss

4. **Clear Documentation**
   - QUICKSTART.md matches preference for quick start
   - Technical README.md available for deeper understanding

5. **Transparent Output**
   - Saves intermediate files for validation
   - Adrian can verify AI insights against source data

#### 🔄 Potential Improvements

1. **Interactive Mode**
   - Add ability to query specific topics on-demand
   - "Show me all discussions about data model delays"

2. **Incremental Updates**
   - Support running just new data since last QBR
   - Don't re-analyze everything each time

3. **Visual Dashboard**
   - Generate charts/graphs automatically
   - Velocity trends, burn-down, hour tracking

4. **Confidence Indicators**
   - Mark AI-generated insights with confidence levels
   - Flag where human review is critical

5. **Templates & Customization**
   - Save custom prompts for company/client style
   - Reusable QBR templates

---

## Success Metrics

**Adrian considers this tool successful if:**

1. **Time Savings:** QBR prep reduced from 14-16 hours to 3-4 hours
2. **Quality:** Michael responds positively to data-backed insights
3. **Accuracy:** AI synthesis matches Adrian's own analysis (when spot-checked)
4. **Reliability:** Tool runs without errors or manual intervention needed
5. **ROI:** $1-2 API cost justified by 10+ hours saved

---

## Adoption Journey

### Phase 1: Initial Trial (Current)
- Run pipeline on existing data
- Validate output quality
- Identify gaps or errors

### Phase 2: First Real QBR
- Use generated QBR as starting point
- Refine and customize
- Present to Michael

### Phase 3: Iteration
- Provide feedback on what worked/didn't
- Request enhancements
- Integrate into regular workflow

### Phase 4: Expansion
- Use for other clients
- Share with team members
- Build on foundation (visualizations, RAG)

---

*Persona created following Nielsen Norman Group UX research standards*
