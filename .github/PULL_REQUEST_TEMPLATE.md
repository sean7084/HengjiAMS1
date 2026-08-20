# Pull Request Template

## Description
Explain the purpose and scope of changes made in this pull request.

## Type of Change
- [ ] Bugfix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring (no behavior changes)
- [ ] Tests added
- [ ] Performance improvement

## Affected Components
List files or apps modified:
- `apps/assets/views.py`
- `templates/assets/asset_list.html`

## How to Test
Detailed instructions for verifying the changes:
1. Apply migration: `python manage.py migrate`
2. Navigate to: `/assets/`
3. Create new asset with serial number "TEST123"
4. Verify it appears in asset list immediately

## Screenshots (UI Changes)
Attach GIF/screenshot comparisons showing before vs after.

## Checklist
- [ ] Self-reviewed my code
- [ ] Added/updated tests accordingly
- [ ] Commented hard-to-understand sections
- [ ] Made corresponding documentation changes
- [ ] Ran lint/format checks with no warnings
- [ ] Rebased onto/up-to-date with base branch
- [ ] Confirmed no regression in existing functionality

## Related Issues
Fixes #[issue_number]

## Notes
Any additional context or questions for reviewers.
