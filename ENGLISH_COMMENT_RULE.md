# English Comment Rule

## Rule: All Code Comments Must Be in English

All comments in the codebase must be written in English. Vietnamese comments are not allowed.

### Requirements:

1. **All comments must be in English** - No Vietnamese text in comments
2. **Use clear and descriptive English** - Comments should be understandable to English-speaking developers
3. **Follow standard commenting conventions** - Use appropriate comment styles for the programming language
4. **Maintain consistency** - All team members must follow this rule

### Implementation Guidelines:

- Use clear, concise English for all comments
- Follow proper English grammar and spelling
- Use technical terminology appropriately
- Keep comments up-to-date with code changes
- Use meaningful variable and function names to reduce the need for excessive comments

### Comment Examples:

**Good (English):**
```python
# Check if user has permission to access this resource
if user.has_permission('read', resource):
    # Process the request and return data
    return process_request(request)
```

**Not Allowed (Vietnamese):**
```python
# Kiểm tra quyền truy cập của người dùng
if user.has_permission('read', resource):
    # Xử lý yêu cầu và trả về dữ liệu
    return process_request(request)
```

### Benefits:

- Improves code readability for international teams
- Facilitates code review and collaboration
- Ensures consistency across the codebase
- Makes the code more maintainable and professional

**Note:** This rule applies to all programming languages and frameworks used in the project. 