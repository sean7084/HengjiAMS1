# Quick Setup Guide - Project Automation Rules

**Date:** August 24, 2026  
**Project URL:** https://github.com/users/sean7084/projects/1  
**Time Required:** 3-5 minutes  

---

## 🎯 What You Need to Do

Your GitHub project board is already created! Now just add automation rules to make it work automatically.

### Step-by-Step Instructions:

1️⃣ **Open Your Project Board**
   - Go to: https://github.com/users/sean7084/projects/1
   
2️⃣ **Find the "Automate" Button**
   - Look at the top-right corner of your project board
   - Click the **"Automate"** dropdown menu
   
3️⃣ **Add Automation Rules**
   
Click **"Add rule"** and select these templates:

---

## 📋 Recommended Automation Rules

### Rule 1: Pull Request Created
```
Trigger: When pull request is created
Action: Move card to column "Code Review"
```

### Rule 2: Pull Request Merged
```
Trigger: When pull request is merged
Actions: 
  • Move card to column "Testing"
  • Add label "test-passed"
```

### Rule 3: Bug Issue Labeled
```
Trigger: When issue is labeled with "bug"
Action: If assigned, move to "In Progress"
```

### Rule 4: Stale Issues
```
Trigger: When no activity for 30 days
AND label = "stale"
Action: Archive card (don't delete)
```

---

## 💡 Pro Tips

✅ **You can modify rules anytime** - Just click "Edit" on any rule  
✅ **Rules work for issues AND pull requests** - Not limited to one type  
✅ **Multiple rules can trigger on same event** - Create complex workflows  
✅ **Deactivate rules without deleting** - Use the toggle switch  

---

## 🔧 After Setting Up Automation

Add custom fields to track important information:

1. Click **+ New field** on your project board
2. Add these fields:
   - **Priority** (Single select): P0-Critical, P1-High, P2-Medium, P3-Low
   - **Component** (Multiple select): assets, quotations, deliveries, invoices, products, accounts, companies, dashboard, reports
   - **Story Points** (Number): 1, 2, 3, 5, 8, 13
   - **Sprint** (Text): Sprint 26, Sprint 27, etc.

---

## 🎉 That's It!

Your project board is now fully configured with:
- ✅ Automated workflow rules
- ✅ Proper labeling system
- ✅ Custom tracking fields

**Next Steps:**
- Invite team members to the project
- Create your first sprint board
- Start moving tasks through the workflow!

---

## 📖 Additional Resources

- **Full Workflow Guide:** `.github/PROJECT_WORKFLOW.md`
- **Label Definitions:** `.github/LABELS.md`
- **Automation Script Reference:** `scripts/setup-github-project-automation.ps1`

---

*Last Updated: August 24, 2026*
