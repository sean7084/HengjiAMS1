---
name: 🚀 Deployment Request
about: Request production deployment
title: "[DEPLOY] Deploy version vX.Y.Z"
labels: ["deployment", "release"]
assignees: []
---

## Release Information
- Version tag: vX.Y.Z
- Branch: develop/main

## Changes Included
Summary of features, bug fixes, and breaking changes.

## Testing Status
- [ ] All unit tests passing
- [ ] Integration tests green
- [ ] Migration tested in staging

## Rollback Plan
If deployment fails, revert to previous stable image.

## Post-Deploy Verification Checklist
- [ ] Application starts without errors
- [ ] Database migrations applied successfully
- [ ] Health check endpoint returns 200
- [ ] Critical workflows verified

## Stakeholder Approval
- Developer: [Signed]
- QA: [Approved]
- Product Owner: [Authorized]
