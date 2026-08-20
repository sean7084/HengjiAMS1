# GitHub Projects Workflow Setup for HengJi AMS

## Overview

This document describes how to configure and use GitHub Projects for managing the HengJi AMS development lifecycle.

---

## Prerequisites

Before setting up GitHub Projects, ensure you have:

1. ✅ Repository created on GitHub with proper collaborators
2. ✅ `CODEOWNERS` file in place (created earlier)
3. ✅ Issue templates configured (`.github/ISSUE_TEMPLATE/`)
4. ✅ Label definitions established (`.github/LABELS.md`)

---

## Project Board Configuration

### Recommended Views

GitHub Projects supports multiple views. Configure all three for optimal workflow management:

#### 1. **Kanban Board View** (Primary)

Columns:
```
To Do → In Progress → Code Review → Testing → Ready for Deploy → Deployed → Done
```

**Setup Steps**:
1. Create new project "HengJi AMS Development"
2. Select "Customize columns"
3. Rename default columns or add custom workflow stages above
4. Enable auto-mapping for issues/prs

#### 2. **Backlog Board** (Planning Mode)

Columns:
```
Icebox → Next Sprint → Current Sprint → In Progress → Completed
```

**Use Case**: Sprint planning and backlog grooming sessions

#### 3. **Table View** (Detailed Filtering)

Group by priority or component. Useful for cross-board analysis.

---

## Field Schema

Define these custom fields for each issue/task:

| Field Name | Type | Options | Purpose |
|------------|------|---------|---------|
| **Priority** | Single select | P0-Critical, P1-High, P2-Medium, P3-Low | Impact assessment |
| **Component** | Multiple select | assets, quotations, deliveries, invoices, products, accounts, companies, dashboard, reports | Area of code affected |
| **Status** | Auto-populated | By workflow column | Tracks progress state |
| **Sprint** | Date or Number | e.g., "Sprint 26", "Q2-2026" | Iteration tracking |
| **Story Points** | Number | 1, 2, 3, 5, 8, 13 | Estimation metric |
| **Estimated Hours** | Number | - | Time estimate for task |
| **Milestone** | Link to Milestone | vX.Y.Z | Release target |
| **Related Documentation** | Text | URL references | ADR, API docs links |

---

## Automation Rules

GitHub can automatically move issues based on these rules:

### Rule 1: PR Creation
- **Trigger**: Pull request created
- **Action**: Move card to "Code Review" column
- **Conditions**: Branch name not equal to `main`

### Rule 2: PR Merged
- **Trigger**: Pull request merged
- **Action**: 
  - Move card to "Testing" column
  - Add label `test-passed`
  - Link related deployment request issue

### Rule 3: Bug Report Status Change
- **Trigger**: Issue labeled `bug`
- **Action**: Move to "In Progress" if assigned

### Rule 4: Stale Issues
- **Trigger**: No activity for 30 days AND label=`stale`
- **Action**: Archive card (do NOT delete)

### Rule 5: Deployment Requests
- **Trigger**: Issue labeled `deployment` created
- **Action**: Move to "Ready for Deploy" column
- **Notification**: Tag @devops-team on creation

---

## Workflow Stages Defined

### To Do
**Definition**: Issue/PR identified but not yet started  
**Required Fields**: Priority, Component labels  
**Actions**: Assign owner, add estimated hours, link to milestone

### In Progress
**Definition**: Work actively being performed  
**Requirements**: At least one assignee  
**Rules**: Maximum 3 tasks per developer concurrently

### Code Review
**Definition**: PR submitted, awaiting approval  
**Required**: Minimum 1 reviewer from CODEOWNERS  
**Timeout**: Escalate after 48h if unresponsive

### Testing
**Definition**: Code merged, awaiting QA validation  
**Criteria**: All tests green, migration tested  
**Owner**: QA team member

### Ready for Deploy
**Definition**: Verified in staging, approved by product owner  
**Approval**: Product Owner sign-off required  
**Checklist**: Deployment template completed, rollback plan ready

### Deployed
**Definition**: Live in production environment  
**Monitoring**: Observe error logs for 24h post-deploy  
**Success Criteria**: No critical alerts triggered

### Done
**Definition**: Fully delivered and verified end-user facing  
**Activities**: Update release notes, close milestone

---

## Sprint Planning Process

### Weekly Cadence (Every Monday)

**Attendees**: Engineering team, Product Owner, QA lead

**Duration**: 90 minutes

**Agenda**:

1. **Retrospective** (15 min)
   - Review completed items from previous sprint
   - Discuss blockers encountered
   - Action items for process improvement

2. **Backlog Grooming** (30 min)
   - Review upcoming epics/tasks
   - Refine acceptance criteria
   - Estimate story points collectively

3. **Commitment Setting** (45 min)
   - Pull highest-priority items into sprint
   - Balance workload across team members
   - Confirm dependencies resolved

### Output Artifacts
- Updated sprint board view
- Committed user stories with acceptance criteria
- Clear ownership assignment

---

## Milestone Management

### Creating Milestones

Go to **Issues → Milestones → New milestone**

**Example Structure**:

| Milestone Name | Target Date | Description |
|----------------|-------------|-------------|
| v0.2.0 | June 1, 2026 | Performance optimization release |
| v0.3.0 | July 15, 2026 | Mobile app integration phase 1 |
| Q2-2026 Releases | N/A | Quarterly release track |

### Naming Convention
```
vMAJOR.MINOR.PATCH  // Version releases
TEAM-PROJECT        // Team-specific milestones (e.g., TEAM-QA-AUTO)
SPRINT-N            // Iteration numbers (Sprint 26)
QUARTER-YEAR        // Quarter tracking (Q1-2026)
```

### Milestone Closure Checklist
- [ ] All issues moved to appropriate status
- [ ] Documentation updates completed
- [ ] Release notes generated
- [ ] Stakeholder announcement sent
- [ ] Lessons learned documented

---

## Issue Triage Process

### Daily Triage Session (30 mins)

Responsible party: Tech Lead

**Steps**:

1. **Label Application**
   - Confirm priority level
   - Assign component(s)
   - Flag if needs more information

2. **Assignment & Due Date**
   - Assign owner based on expertise
   - Set reasonable due date
   - Link to parent epic/milestone

3. **Comment Protocol**
   - Leave clear action item comment
   - Tag relevant parties if needed
   - Reference related documentation

4. **Escalation Decision**
   - Mark blocked if dependency missing
   - Tag escalation contact if urgent
   - Create follow-up task for blocker resolution

---

## Pull Request Management

### Pre-Submission Requirements

Developers must verify:
- [ ] Unit tests pass locally
- [ ] Integration tests green
- [ ] Linting clean (black/flake8)
- [ ] Self-review checklist completed
- [ ] Related issue linked

### Reviewer Responsibilities

Within 24 business hours:
1. Review code changes thoroughly
2. Comment on logic correctness
3. Verify test coverage adequate
4. Check for breaking changes
5. Approve OR request changes

### Approval Thresholds

| Change Size | Required Approvals | Additional Checks |
|-------------|--------------------|-------------------|
| Trivial (<50 lines) | 1 | None |
| Standard (<500 lines) | 2 | One from CODEOWNER team |
| Large (>500 lines) | 3 | One non-author + one domain expert |
| Breaking change | 3 + PM | Security review mandatory |

---

## Metrics & Reporting

Track these KPIs monthly:

### Velocity Metric
```
Formula: Total story points completed / Sprint duration
Target: Stable 25 ±5 points per sprint (example baseline)
```

### Cycle Time
```
From "To Do" to "Done" (days)
Benchmark: <14 days average; <7 days for bug fixes
```

### Lead Time
```
Issue creation → deployment (total time)
Benchmark: <30 days for feature requests
```

### Defect Rate
```
Bugs reopened within 7 days of closure
Target: <10% reopening rate
```

### Burndown Chart
Available via GitHub Insights tab

---

## Integrations

### Slack Channel
Create #hengji-dev channel with automated notifications:

**Events to notify**:
- PRs requiring review
- Critical bugs created
- Deployments completed
- Milestone closures

**Integration command examples**:
```bash
/slack trigger pr-approve --repository hengji-ams --author @username
/slack deploy-success --tag v0.2.0 --environment production
```

### CI/CD Pipeline Linking
Configure GitHub Actions to update project cards automatically upon webhook events:

**File**: `.github/workflows/project-sync.yml`
```yaml
name: Project Sync

on:
  pull_request:
    types: [opened, closed]
  issues:
    types: [opened, closed]

jobs:
  sync-project:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v6
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            // Custom logic to update project boards
```

---

## Templates for Reuse

### Epic Template
Create standardized epics for large initiatives:

```markdown
Epic Title: [Name]
Description: Problem statement and success criteria

Subtasks:
- [ ] Phase 1: Foundation work
- [ ] Phase 2: Integration testing  
- [ ] Phase 3: User training

Resources:
- Design doc: [link]
- ADR: [number]
- API spec: [link]
```

### Incident Response Board
Temporary Kanban for live incidents:

Columns: Identified → Investigating → Mitigating → Resolved → Post-mortem

Automatically deleted after 7 days of inactivity

---

## Best Practices

### Card Hygiene
- Close/archived cards older than 90 days
- Keep descriptions concise but informative
- Use checkboxes for multi-step actions
- Attach screenshots/mockups directly to cards

### Communication Etiquette
- Tag people instead of assigning to themselves
- Reference issue numbers in commit messages
- Link sub-tasks to parent epic using GitHub's linking syntax
- Celebrate wins publicly in team channels

### Continuous Improvement
Monthly retrospective:
- What slowed us down?
- Which processes worked well?
- How to reduce cycle time next month?

---

## Getting Started Checklist

- [ ] Install GitHub CLI: `gh install gh`
- [ ] Authenticate: `gh auth login`
- [ ] Create project: `gh project create --title "HengJi AMS"`
- [ ] Import labels from LABELS.md
- [ ] Configure automation rules per section above
- [ ] Invite team members with correct roles
- [ ] Schedule first sprint planning session

---

*Last Updated: August 20, 2026*
