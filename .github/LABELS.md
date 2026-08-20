# Labels for HengJi AMS

Organize issues using these standardized labels:

## Status Labels

| Label | Color | Description |
|-------|-------|-------------|
| `triage` | #E9D75F | Needs initial review and categorization |
| `awaiting response` | #0E8A16 | Waiting on author feedback |
| `blocked` | #BDBDBD | Cannot proceed due to dependency |
| `stale` | #EEEEEE | No activity for 30 days |

## Priority Labels

| Label | Color | Description |
|-------|-------|-------------|
| `P0 - Critical` | #B60205 | Blocks release; needs immediate fix |
| `P1 - High` | #D93F0B | Important bug/feature for next sprint |
| `P2 - Medium` | #FBCA04 | Regular backlog item |
| `P3 - Low` | #EDEDED | Nice-to-have, low priority |

## Category Labels

| Label | Color | Description |
|-------|-------|-------------|
| `bug` | #D73A4A | Something isn't working correctly |
| `enhancement` | #A2EEEF | New feature request |
| `documentation` | #0075CA | Improvements to docs |
| `good first issue` | #7057FF | Easy for newcomers |
| `help wanted` | #008672 | Contribution needed |
| `question` | #CC3147 | More information needed |
| `discussion` | #CCE329 | Topics requiring community input |

## Component Labels

| Label | Color | App/Area |
|-------|-------|----------|
| `component: accounts` | #1D76EB | User management, authentication |
| `component: assets` | #0052CC | Asset CRUD, assignments |
| `component: companies` | #54AE5F | Company/location structures |
| `component: quotations` | #FBE75F | Quotation lifecycle |
| `component: deliveries` | #FBF29D | Delivery orders |
| `component: invoices` | #A2EEEF | Invoice processing |
| `component: products` | #5791EF | Price list, service catalog |
| `component: dashboard` | #FFFFFF | Main landing page |
| `component: reports` | #79CB23 | Analytics & charts |

## Impact Labels

| Label | Color | Description |
|-------|-------|-------------|
| `breaking change` | #B60205 | Incompatible API/model changes |
| `deprecation` | #D8744E | Deprecated feature scheduled for removal |
| `migration-required` | #BF5D73 | Database migration required |

## Testing Labels

| Label | Color | Description |
|-------|-------|-------------|
| `needs testing` | #FFEBD6 | Awaiting QA validation |
| `test-passed` | #84b6ef | Verified in staging |
| `e2e-test-needed` | #7057FF | End-to-end test coverage gap |

## Deployment Labels

| Label | Color | Description |
|-------|-------|-------------|
| `deployment` | #C2E0C6 | Ready for deployment |
| `release-notes` | #0366D6 | Must be included in changelog |
| `security` | #EB6420 | Security-related fix |
| `performance` | #C6CFCF | Speed/performance improvement |

## Usage Guidelines

### Adding Labels
1. Assign appropriate **status** label immediately upon creation
2. Add **priority** based on impact assessment
3. Categorize with component-specific labels

### Automation Rules (future)
- Bug → triage + component label
- Feature request → enhancement + ideas
- Production-ready milestone → deployment + release-notes

### Maintenance
- Remove `needs testing` when QA signs off
- Archive stale issues after 60 days of inactivity
