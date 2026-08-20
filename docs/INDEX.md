# Documentation Index - HengJi AMS

Complete list of project documentation for reference and navigation.

---

## Table of Contents

### 📋 Core Project Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| **README.md** | Root | Project overview, quick start guide |
| **CHANGELOG.md** | Root | Version history and release notes |
| **LICENSE** | Root | Licensing terms and usage rights |
| **CONTRIBUTING.md** | `docs/` | Contribution guidelines and coding standards |

### 🏗️ Architecture & Design

| Document | Location | Purpose |
|----------|----------|---------|
| **ADR-0001** | `docs/ARCHITECTURAL_DECISION_RECORDS.md` | Service catalog separation decision |
| **ADR-0002** | `docs/ARCHITECTURAL_DECISION_RECORDS.md` | Mailbox-driven RFQ automation |
| **ADR-0003** | `docs/ARCHITECTURAL_DECISION_RECORDS.md` | Direct dispatch fulfillment workflow |
| **ADR-0004** | `docs/ARCHITECTURAL_DECISION_RECORDS.md` | Hardware-only assets boundary |
| **ADR-0005** | `docs/ARCHITECTURAL_DECISION_RECORDS.md` | Product price lifecycle management |
| **ADR-0006** | `docs/ARCHITECTURAL_DECISION_RECORDS.md` | Import rollback system design |
| **ADR-0007** | `docs/ARCHITECTURAL_DECISION_RECORDS.md` | Multi-role administrator access control |
| **ADR-0008** | `docs/ARCHITECTURAL_DECISION_RECORDS.md` | HTML-to-PDF generation without LibreOffice |
| **ADR-0009** | `docs/ARCHITECTURAL_DECISION_RECORDS.md` | Warehouse slot tracking implementation |
| **ADR-0010** | `docs/ARCHITECTURAL_DECISION_RECORDS.md` | Company contact vs company user model refactoring |

### 🔧 Operational Guides

| Document | Location | Audience |
|----------|----------|----------|
| **API_GUIDE.md** | `docs/` | Developers integrating via API |
| **DEPLOYMENT.md** | `docs/` | DevOps engineers deploying production |
| **WORKFLOW_GUIDE.md** | `docs/` | Business users operating daily workflows |

### 🚀 Getting Started Resources

| Document | Location | Use Case |
|----------|----------|----------|
| **README Quick Start** | `README.md` | First-time developers setting up local environment |
| **DEPLOYMENT Guide** | `docs/DEPLOYMENT.md` | Production setup and infrastructure provisioning |
| **API Documentation** | `docs/API_GUIDE.md` | Understanding available REST endpoints |
| **Workflow Guide** | `docs/WORKFLOW_GUIDE.md` | Learning how to use business features |

### 🐛 Issue Tracking Templates

Located in `.github/ISSUE_TEMPLATE/`:

| Template File | Purpose |
|---------------|---------|
| **bug_report.md** | Report application bugs systematically |
| **feature_request.md** | Request new functionality or improvements |
| **task.md** | Track complex work items and epics |
| **deployment.md** | Request production deployments formally |
| **security.md** | Report security vulnerabilities privately |

### 🎫 GitHub Configuration Files

| File | Purpose |
|------|---------|
| **CODEOWNERS** | Define code review ownership per app/module |
| **LABELS.md** | Standardized label definitions and color codes |
| **PULL_REQUEST_TEMPLATE.md** | PR creation guidance and checklist |
| **PROJECT_WORKFLOW.md** | GitHub Projects board configuration guide |

---

## Documentation Structure Diagram

```
hengji-ams/
├── README.md                      ← Main landing page
├── CHANGELOG.md                   ← Release history  
├── LICENSE                        ← Legal terms
│
├── docs/                          ← Detailed specifications
│   ├── ARCHITECTURAL_DECISION_RECORDS.md     ← ADRs (0001-0010)
│   ├── API_GUIDE.md             ← REST API reference
│   ├── DEPLOYMENT.md            ← Production setup guide
│   ├── CONTRIBUTING.md          ← Contributing guidelines
│   └── WORKFLOW_GUIDE.md        ← Business operations manual
│
└── .github/                       ← GitHub-specific configs
    ├── ISSUE_TEMPLATE/           ← Issue templates folder
    │   ├── bug_report.md
    │   ├── feature_request.md
    │   ├── task.md
    │   ├── deployment.md
    │   └── security.md
    ├── CODEOWNERS                ← Review ownership rules
    ├── LABELS.md                 ← Label definitions
    ├── PULL_REQUEST_TEMPLATE.md  ← PR submission template
    └── PROJECT_WORKFLOW.md       ← Project board instructions
```

---

## How to Navigate This Documentation

### For New Contributors

1. **Start with**: `README.md` → understand project purpose
2. **Read**: `docs/CONTRIBUTING.md` → learn coding standards
3. **Review**: `docs/ARCHITECTURAL_DECISION_RECORDS.md` → understand architecture decisions
4. **Practice**: Fork repo, fix "good first issue" labeled tickets

### For Production Deployment

1. **Prerequisites check**: `DEPLOYMENT.md` → Step 1
2. **Follow**: Manual installation OR Docker section
3. **Test**: Run migration and verify health endpoint
4. **Monitor**: Configure backup scripts and alerts per deployment guide

### For API Integration

1. **Understand auth**: `docs/API_GUIDE.md` → Authentication section
2. **Browse endpoints**: Filter by resource type (assets, quotations, deliveries)
3. **Test locally**: Use Django test client or Python requests library examples
4. **Reference error format**: Section on standard response structure

### For Daily Operations

1. **Workflow walkthrough**: `docs/WORKFLOW_GUIDE.md` → Order Management section
2. **Step-by-step procedures**: Follow import/export/invoice cycles
3. **Troubleshooting tips**: Appendix sections address common issues

---

## Documentation Maintenance Guidelines

### Update Frequency

| Document Type | Review Cycle | Owner |
|---------------|--------------|-------|
| Technical specs (ADRs) | Per major change | Lead architect |
| API guide | With each release cycle | Backend team |
| Deployment guide | When environment changes | DevOps engineer |
| Workflow guide | Quarterly | Operations lead |
| Issue templates | As needed | Maintainers |

### Change Control

To update documentation:

1. Submit PR modifying target `.md` file
2. Tag relevant reviewer from domain
3. Ensure cross-references updated if moved between files
4. Verify links render correctly before merge

### Quality Standards

All documentation should:
- ✅ Use clear, active voice (avoid passive constructions)
- ✅ Include code examples where applicable
- ✅ Reference specific file paths, line numbers when possible
- ✅ Provide screenshots for visual workflows
- ✅ Link to related internal documentation

---

## Missing Documentation Gap Analysis

### Known Gaps (Future Work Items)

The following documents are planned but not yet created:

- [ ] `docs/DATABASE_SCHEMA.md` - ER diagrams and table relationships
- [ ] `docs/TESTING.md` - Test writing guidelines and coverage requirements
- [ ] `docs/SECURITY_POLICY.md` - Security best practices and vulnerability disclosure policy
- [ ] `docs/RELEASE_PROCEDURE.md` - Step-by-step release process
- [ ] Video tutorials for key workflows (YouTube playlist)

### Priority Matrix

| Gap | Priority | Estimated Effort | Owner |
|-----|----------|------------------|-------|
| DATABASE_SCHEMA.md | High | 4 hours | DBA team |
| TESTING.md | High | 6 hours | QA lead |
| SECURITY_POLICY.md | Medium | 3 hours | Security officer |
| RELEASE_PROCEDURE.md | Medium | 2 hours | Engineering manager |
| Video tutorials | Low | 20 hours | Marketing team |

---

## External Resources Links

### Official References

- **[Django Documentation](https://docs.djangoproject.com/)** - Framework reference
- **[Bootstrap 5 Docs](https://getbootstrap.com/docs/5.0/)** - UI component library
- **[WeasyPrint Examples](https://doc.courtbard.net/projects/weasyprint/en/stable/examples.html)** - PDF rendering samples
- **[Minimax API Docs](https://open.xiaomi.com/)** - AI classification integration

### Community Resources

- **[Django Channels Slack](https://django-channels-community.slack.com/)** - Async development support
- **[Stack Overflow Questions Tagged "Django"]()** - Problem-solving Q&A platform

---

## Contact Information for Documentation Issues

Questions about any document or suggestions for improvement?

📧 Email: docs@hengji.com  
💬 Slack Channel: #documentation-team  
📝 Contribution: Submit PR using contribution guidelines

---

*Last Updated: August 20, 2026*  
*Author: Sean Liu and contributors*
