# Debug & Troubleshooting Directory

This directory contains all debugging materials, troubleshooting guides, and temporary test code for the vocabulary learning application.

## 📁 Directory Structure

```
debug/
├── README.md                    # This file
├── documentation/               # Debugging and troubleshooting documentation
│   ├── AUDIO_STATS_BUG_FIX.md
│   ├── AUDIO_STATS_DUPLICATION_FIX.md
│   ├── FAVORITE_BUTTON_STATE_FIX.md
│   ├── GRADE_BUTTONS_VISIBILITY_FIX.md
│   ├── JAVASCRIPT_ERROR_FIX.md
│   ├── VIETNAMESE_ENGLISH_DESCRIPTION_BUG_FIX.md
│   ├── WORD_SEARCH_AUTOCOMPLETE_IMPROVEMENTS.md
│   ├── INCORRECT_WORDS_DEBUG_GUIDE.md
│   ├── INCORRECT_WORDS_FIX_SUMMARY.md
│   ├── INCORRECT_ANSWER_TRACKING_FIX.md
│   ├── STATISTICS_INFLATION_FIX.md
│   ├── STUDY_PAGE_ARROW_NAVIGATION_FIX.md
│   ├── AUDIO_FEEDBACK_FIX.md
│   ├── DROPDOWN_FIX.md
│   ├── FLASHCARD_UPDATE_404_FIX.md
│   ├── FLASHCARD_UPDATE_FIX.md
│   └── API_404_FIX_SUMMARY.md
├── css/                        # Temporary CSS debugging styles
├── js/                         # Temporary JavaScript debugging code
└── templates/                  # Temporary template debugging files
```

## 🎯 Purpose

This directory serves to:

1. **Organize debugging materials** - Keep all troubleshooting documentation in one place
2. **Separate concerns** - Prevent debugging code from mixing with production code
3. **Maintain clean codebase** - Keep the main application files clean and organized
4. **Historical reference** - Preserve debugging steps and solutions for future reference
5. **Team collaboration** - Provide clear documentation for debugging processes

## 📋 Guidelines

### For Debugging Documentation (`documentation/`)
- **Bug fix guides** - Step-by-step solutions for resolved issues
- **Troubleshooting procedures** - Diagnostic steps for common problems
- **Testing instructions** - How to verify fixes and test functionality
- **Root cause analysis** - Technical explanations of why issues occurred

### For Temporary Code (`css/`, `js/`, `templates/`)
- **Debugging styles** - CSS for highlighting elements during debugging
- **Console logging** - JavaScript with extensive logging for troubleshooting
- **Test templates** - Modified templates for testing specific functionality
- **Experimental code** - Code snippets for testing potential solutions

## 🔄 Workflow

### When Debugging:
1. **Create debugging files** in appropriate subdirectories
2. **Document the process** in the `documentation/` folder
3. **Test thoroughly** using debugging materials
4. **Clean up** temporary code once issue is resolved
5. **Archive documentation** for future reference

### When Issue is Resolved:
1. **Remove debugging code** from main application files
2. **Clean up temporary files** in `css/`, `js/`, `templates/`
3. **Keep documentation** for historical reference
4. **Update main docs** if permanent changes were made

## 📚 Documentation Categories

### Bug Fixes
- Audio-related issues (stats, feedback, fetching)
- UI/UX problems (buttons, visibility, navigation)
- JavaScript errors and functionality issues
- API and backend problems

### Feature Debugging
- Study interface improvements
- Search functionality enhancements
- User interaction debugging
- Performance optimization

### System Issues
- Localization and internationalization
- Database and model problems
- Template rendering issues
- Static file and asset problems

## 🚫 What NOT to Include

- **Production code** - Keep main application files clean
- **User data** - Never include real user information in debug files
- **Sensitive information** - API keys, passwords, or configuration secrets
- **Large files** - Avoid storing large images or data files here

## 🧹 Maintenance

### Regular Cleanup:
- **Monthly review** of temporary files
- **Archive old documentation** that's no longer relevant
- **Remove outdated debugging code**
- **Update this README** when structure changes

### Before Production Deployment:
- **Verify no debugging code** remains in main application
- **Check console.log statements** are removed
- **Confirm debug CSS** is not included in production
- **Test without debugging materials**

## 📞 Contact

If you have questions about debugging procedures or need help with troubleshooting, refer to the documentation in this directory or consult the main project documentation in the `docs/` folder.

---

**Remember**: This directory is for debugging and troubleshooting only. Keep production code clean and organized in the main application directories.
