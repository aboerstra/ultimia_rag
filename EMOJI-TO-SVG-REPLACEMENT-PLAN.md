# Emoji to SVG Replacement Plan

**Total Emojis Found:** 85 instances across 10 component files  
**Status:** Icon component created, ready for systematic replacement

---

## Emoji Mapping Guide

| Emoji | Icon Name | Usage |
|-------|-----------|-------|
| 💬 | `chat` | Chat/conversation indicators |
| 👤 | `user` | User avatars |
| 🤖 | `bot` | AI/bot responses |
| 📋 | `clipboard` | Copy actions, reports |
| 📊 | `bar-chart` | Data analytics, charts |
| 🚀 | `rocket` | Run/start actions |
| 🔄 | `refresh` / `loader` | Loading, refresh states |
| 📄 | `file` / `file-text` | Documents, files |
| 📁 | `folder` | Folders, file systems |
| 📤 | `upload` | Upload actions |
| 📥 | `download` | Download actions |
| 🗑️ | `trash` | Delete actions |
| 👁️ | `eye` | View actions |
| 🔍 | `search` | Search functionality |
| ✅ | `check` / `check-circle` | Success states |
| 🔴 | Circle (status) | Error status |
| 🏥 | `shield` / `activity` | Health monitoring |
| 🧪 | `flask` / `tool` | Testing |
| 💾 | `save` | Save actions |
| 🔐 | `lock` | Security/login |
| 👋 | `hand` (greeting) | Welcome messages |
| 📈 | `trending-up` | Data summary |
| 🎯 | `target` | Jira/goals |
| 📚 | `package` / `database` | Confluence |
| 💡 | `lightbulb` | Tips/info |
| 👥 | `users` | Personas/people |
| 📭 | `inbox` | Empty states |
| ⏳ | `clock` | Loading/time |
| 🔨 | `build` / `tool` | Building |
| 💭 | `chat` | Conversations |

---

## Component-by-Component Replacement Plan

### Priority 1: Most Visible Components

#### 1. Dashboard.tsx (6 emojis)
```tsx
// Before → After
<div className="stat-icon">📊</div>
→ <Icon name="bar-chart" size={24} className="stat-icon" />

<div className="stat-icon">📄</div>
→ <Icon name="file" size={24} className="stat-icon" />

<div className="stat-icon">📋</div>
→ <Icon name="clipboard" size={24} className="stat-icon" />

icon="📋" → icon="clipboard"
icon="📄" → icon="file-text"
icon="📊" → icon="bar-chart"
icon="🔍" → icon="search"
icon="📁" → icon="folder"
icon="👥" → icon="users"
```

#### 2. ChatWorkspace.tsx (6 emojis)
```tsx
<div className="empty-icon">💬</div>
→ <Icon name="chat" size={48} className="empty-icon" />

{message.role === 'user' ? '👤' : '🤖'}
→ <Icon name={message.role === 'user' ? 'user' : 'bot'} size={20} />

📋 Copy → <Icon name="copy" size={16} /> Copy

<span className="sources-icon">📊</span>
→ <Icon name="database" size={16} className="sources-icon" />

<span className="chat-icon">💬</span>
→ <Icon name="chat" size={18} className="chat-icon" />
```

#### 3. RunAnalysis.tsx (4 emojis)
```tsx
<h2>🚀 Run Analysis</h2>
→ <h2><Icon name="rocket" size={20} /> Run Analysis</h2>

<>🔄 Analysis Running...</>
→ <><Icon name="loader" size={16} /> Analysis Running...</>

<>🚀 Start New Analysis</>
→ <><Icon name="rocket" size={16} /> Start New Analysis</>

<h4>🔄 Live Activity</h4>
→ <h4><Icon name="activity" size={16} /> Live Activity</h4>
```

### Priority 2: Data & Configuration Components

#### 4. DataSummary.tsx (9 emojis)
```tsx
<h2>📈 Collected Data Summary</h2>
→ <h2><Icon name="trending-up" size={20} /> Collected Data Summary</h2>

🔄 Refresh → <Icon name="refresh" size={16} /> Refresh

<div className="no-data-icon">📊</div>
→ <Icon name="bar-chart" size={48} className="no-data-icon" />

<div className="card-icon">🎯</div>
→ <Icon name="target" size={24} className="card-icon" />

<div className="card-icon">📚</div>
→ <Icon name="package" size={24} className="card-icon" />

<div className="loading-spinner">🔄</div>
→ <Icon name="loader" size={20} className="loading-spinner" />

💡 Data is refreshed...
→ <Icon name="lightbulb" size={14} /> Data is refreshed...
```

#### 5. HealthStatus.tsx (10 emojis)
```tsx
return '🔴'
→ return <Icon name="alert-circle" size={12} color="#dc3545" />

<h3>🏥 System Health {isLoading && '🔄'}</h3>
→ <h3><Icon name="activity" size={18} /> System Health {isLoading && <Icon name="loader" size={16} />}</h3>

{isLoading ? '🔄 Testing...' : '🧪 Test All Connections'}
→ {isLoading ? <><Icon name="loader" /> Testing...</> : <><Icon name="tool" /> Test All Connections</>}

{testingService === key ? '🔄' : '🧪'} Test
→ <Icon name={testingService === key ? 'loader' : 'tool'} size={14} /> Test

🔐 Login to Salesforce
→ <Icon name="lock" size={14} /> Login to Salesforce

💾 Save Configuration
→ <Icon name="save" size={14} /> Save Configuration
```

### Priority 3: User Input Components

#### 6. TranscriptUpload.tsx (7 emojis)
```tsx
<h2>📤 Upload Transcripts</h2>
→ <h2><Icon name="upload" size={20} /> Upload Transcripts</h2>

<div className="upload-icon">📁</div>
→ <Icon name="folder" size={48} className="upload-icon" />

<div className="file-icon">📄</div>
→ <Icon name="file" size={20} className="file-icon" />

<h3>📋 Uploaded Transcripts...</h3>
→ <h3><Icon name="clipboard" size={18} /> Uploaded Transcripts...</h3>

<div className="loading-spinner">🔄</div>
→ <Icon name="loader" size={20} className="loading-spinner" />

<div className="transcript-icon">📄</div>
→ <Icon name="file-text" size={18} className="transcript-icon" />

<div className="empty-icon">📭</div>
→ <Icon name="inbox" size={48} className="empty-icon" />
```

#### 7. ContextFiles.tsx (9 emojis)
```tsx
<h2>📁 Custom Context Files</h2>
→ <h2><Icon name="folder" size={20} /> Custom Context Files</h2>

{uploading ? '⏳ Uploading...' : '📤 Choose File'}
→ {uploading ? <><Icon name="clock" /> Uploading...</> : <><Icon name="upload" /> Choose File</>}

<h4>📋 Supported File Types:</h4>
→ <h4><Icon name="clipboard" size={16} /> Supported File Types:</h4>

{indexing ? '⏳ Indexing...' : '🔄 Re-Index...'}
→ {indexing ? <><Icon name="clock" /> Indexing...</> : <><Icon name="refresh" /> Re-Index...</>}

🔄 Refresh → <Icon name="refresh" size={16} /> Refresh

🗑️ → <Icon name="trash" size={16} />

<h3>💡 How It Works</h3>
→ <h3><Icon name="lightbulb" size={18} /> How It Works</h3>
```

### Priority 4: Analysis & Review Components

#### 8. PersonaBuilder.tsx (12 emojis)
```tsx
return <span className="status-badge building">🔄 Building</span>
→ return <span className="status-badge building"><Icon name="loader" size={14} /> Building</span>

<span className="spinner">🔄</span> Building...
→ <Icon name="loader" size={16} /> Building...

👁️ View → <Icon name="eye" size={14} /> View

🔄 Rebuild → <Icon name="refresh" size={14} /> Rebuild

🔨 Build Persona → <Icon name="build" size={14} /> Build Persona

<h2>👥 Persona Builder</h2>
→ <h2><Icon name="users" size={20} /> Persona Builder</h2>

<div className="loading-spinner">🔄</div>
→ <Icon name="loader" size={24} className="loading-spinner" />

📥 → <Icon name="download" size={14} />

<h4>💡 How It Works</h4>
→ <h4><Icon name="lightbulb" size={16} /> How It Works</h4>

<div className="empty-icon">👥</div>
→ <Icon name="users" size={48} className="empty-icon" />

<span className="modal-icon">📊</span>
→ <Icon name="bar-chart" size={20} className="modal-icon" />

📥 Download Markdown → <Icon name="download" size={14} /> Download Markdown
```

#### 9. CrossValidation.tsx (11 emojis)
```tsx
{ id: 'all', label: 'All Checks', icon: '📊' }
→ { id: 'all', label: 'All Checks', icon: 'bar-chart' }

{ id: 'match', label: 'Passed', icon: '✅' }
→ { id: 'match', label: 'Passed', icon: 'check-circle' }

<h2>🔍 Cross-Validation Dashboard</h2>
→ <h2><Icon name="search" size={20} /> Cross-Validation Dashboard</h2>

{isLoading ? '🔄 Loading...' : '🔄 Refresh'}
→ {isLoading ? <><Icon name="loader" /> Loading...</> : <><Icon name="refresh" /> Refresh</>}

<div className="loading-spinner">🔄</div>
→ <Icon name="loader" size={24} className="loading-spinner" />

<span className="stat-icon">📋</span>
→ <Icon name="clipboard" size={20} className="stat-icon" />

<div className="no-results-icon">🔍</div>
→ <Icon name="search" size={32} className="no-results-icon" />

<div className="empty-icon">📊</div>
→ <Icon name="bar-chart" size={48} className="empty-icon" />
```

#### 10. Reports.tsx (9 emojis)
```tsx
<h2>📊 Generated Reports</h2>
→ <h2><Icon name="bar-chart" size={20} /> Generated Reports</h2>

<div className="loading-spinner">🔄</div>
→ <Icon name="loader" size={24} className="loading-spinner" />

<div className="report-icon">📄</div>
→ <Icon name="file-text" size={24} className="report-icon" />

👁️ View → <Icon name="eye" size={14} /> View

📥 Download → <Icon name="download" size={14} /> Download

<div className="empty-icon">📭</div>
→ <Icon name="inbox" size={48} className="empty-icon" />

<span className="modal-icon">📄</span>
→ <Icon name="file" size={20} className="modal-icon" />

<div className="modal-loading"><div className="loading-spinner">🔄</div>
→ <Icon name="loader" size={24} className="loading-spinner" />

📥 Download → <Icon name="download" size={14} /> Download
```

### Priority 5: Navigation Components

#### 11. ConversationList.tsx (4 emojis)
```tsx
<div className="conversation-icon">💬</div>
→ <Icon name="chat" size={18} className="conversation-icon" />

<h2>💬 Conversations</h2>
→ <h2><Icon name="chat" size={20} /> Conversations</h2>

<div className="empty-icon">💭</div>
→ <Icon name="chat" size={48} className="empty-icon" />
```

#### 12. AIChat.tsx (3 emojis)
```tsx
content: '👋 Hi! I can answer...'
→ content: 'Hi! I can answer...' // or keep greeting text

<span className="chat-icon">💬</span>
→ <Icon name="chat" size={18} className="chat-icon" />

📋 → <Icon name="copy" size={14} />

📊 Sources: → <Icon name="database" size={12} /> Sources:
```

---

## Implementation Strategy

### Option 1: Automated Batch Replacement (Fastest)
1. Create a replacement script that processes all files
2. Run once, verify with test
3. Manual review and adjustments

### Option 2: Component-by-Component (Safest)
1. Update one component at a time
2. Test after each component
3. Ensure no regressions

### Option 3: Priority-Based (Balanced)
1. Start with most visible components (Dashboard, ChatWorkspace)
2. Move to data components
3. Finish with utility components

---

## Import Statement to Add

Each file needs:
```tsx
import Icon from './Icon'
```

---

## CSS Considerations

Some CSS may reference emoji styles that need updating:
- `.empty-icon` - Already works with SVG
- `.stat-icon` - Needs `display: flex` for alignment
- `.loading-spinner` - May need animation class

---

## Testing Checklist

After replacement:
- [ ] All icons render correctly
- [ ] Icon sizes are appropriate
- [ ] Colors match design
- [ ] Hover states work
- [ ] Loading animations function
- [ ] No console errors
- [ ] Mobile responsive
- [ ] Accessibility maintained

---

## Estimated Effort

- **Automated approach:** 2-3 hours
- **Manual approach:** 6-8 hours
- **Testing:** 1-2 hours
- **Total:** 4-10 hours depending on approach

---

## Recommendation

**Preferred Approach:** Priority-Based with automated assistance

1. Start with ChatWorkspace, Dashboard, RunAnalysis (most visible)
2. Use search/replace for repetitive patterns
3. Manual review for complex contextual usage
4. Test incrementally

This balances speed with quality and minimizes risk of breaking changes.
