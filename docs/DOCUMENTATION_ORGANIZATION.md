# Documentation Organization

## 📁 Directory Structure

The project documentation is now organized into two main directories:

### 📚 `docs/` - Main Documentation
Contains production documentation, user guides, and system documentation:

- **Feature Documentation**: New features and enhancements
- **User Guides**: How to use the application
- **System Documentation**: Architecture and design decisions
- **Development Rules**: Coding standards and guidelines
- **Localization**: Internationalization documentation

### 🔧 `debug/` - Debug & Troubleshooting
Contains debugging materials, troubleshooting guides, and temporary test code:

- **`debug/documentation/`**: Bug fixes and troubleshooting guides
- **`debug/css/`**: Temporary CSS debugging styles
- **`debug/js/`**: Temporary JavaScript debugging code
- **`debug/templates/`**: Temporary template debugging files

## 🎯 Purpose of Reorganization

### Benefits:
1. **Clean Separation**: Production docs separate from debugging materials
2. **Better Organization**: Easy to find relevant documentation
3. **Cleaner Codebase**: Debugging code isolated from production code
4. **Team Collaboration**: Clear structure for different types of documentation
5. **Maintenance**: Easier to maintain and update documentation

### What Was Moved:
The following debugging and troubleshooting files were moved from `docs/` to `debug/documentation/`:

- `AUDIO_STATS_BUG_FIX.md`
- `AUDIO_STATS_DUPLICATION_FIX.md`
- `FAVORITE_BUTTON_STATE_FIX.md`
- `GRADE_BUTTONS_VISIBILITY_FIX.md`
- `JAVASCRIPT_ERROR_FIX.md`
- `VIETNAMESE_ENGLISH_DESCRIPTION_BUG_FIX.md`
- `WORD_SEARCH_AUTOCOMPLETE_IMPROVEMENTS.md`
- `INCORRECT_WORDS_DEBUG_GUIDE.md`
- `INCORRECT_WORDS_FIX_SUMMARY.md`
- `INCORRECT_ANSWER_TRACKING_FIX.md`
- `STATISTICS_INFLATION_FIX.md`
- `STUDY_PAGE_ARROW_NAVIGATION_FIX.md`
- `AUDIO_FEEDBACK_FIX.md`
- `DROPDOWN_FIX.md`
- `FLASHCARD_UPDATE_404_FIX.md`
- `FLASHCARD_UPDATE_FIX.md`
- `API_404_FIX_SUMMARY.md`

## 📋 Guidelines

### For Main Documentation (`docs/`):
- **Production features** and their documentation
- **User guides** and tutorials
- **System architecture** and design decisions
- **Development standards** and coding rules
- **Deployment** and configuration guides

### For Debug Documentation (`debug/`):
- **Bug fixes** and their solutions
- **Troubleshooting procedures** for common issues
- **Temporary debugging code** and test files
- **Investigation notes** and debugging steps
- **Performance analysis** and optimization notes

## 🔄 Workflow

### When Adding New Documentation:

1. **Determine the type**:
   - Production feature → `docs/`
   - Bug fix or debugging → `debug/documentation/`

2. **Follow naming conventions**:
   - Features: `FEATURE_NAME.md`
   - Bug fixes: `ISSUE_NAME_FIX.md`
   - Guides: `TOPIC_GUIDE.md`

3. **Update indexes**:
   - Add to `docs/INDEX.md` for main documentation
   - Add to `debug/documentation/INDEX.md` for debug documentation

### When Debugging:
1. **Create temporary files** in appropriate `debug/` subdirectories
2. **Document the process** in `debug/documentation/`
3. **Clean up temporary files** once issue is resolved
4. **Keep documentation** for future reference

## 🧹 Maintenance

### Regular Tasks:
- **Review debug files** monthly and archive old ones
- **Update indexes** when adding new documentation
- **Clean up temporary files** after issues are resolved
- **Verify links** in documentation are still valid

### Before Production Deployment:
- **Remove debugging code** from main application files
- **Verify no debug CSS/JS** is included in production
- **Check console.log statements** are removed
- **Test without debugging materials**

## 📞 Quick Reference

### Finding Documentation:
- **How to use a feature** → Check `docs/`
- **How to fix a bug** → Check `debug/documentation/`
- **Development guidelines** → Check `docs/`
- **Troubleshooting steps** → Check `debug/documentation/`

### Adding Documentation:
- **New feature docs** → Add to `docs/` and update `docs/INDEX.md`
- **Bug fix docs** → Add to `debug/documentation/` and update `debug/documentation/INDEX.md`
- **Temporary test files** → Add to appropriate `debug/` subdirectory

This organization ensures a clean, maintainable documentation structure that separates production documentation from debugging materials, making it easier for developers to find the information they need.
