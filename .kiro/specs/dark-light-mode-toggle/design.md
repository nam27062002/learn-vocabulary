# Design Document

## Overview

This design document outlines the implementation of a dark mode and light mode toggle feature for the LearnEnglish vocabulary learning application. The solution will provide users with the ability to switch between dark and light themes seamlessly, with their preference persisted across browser sessions. The design leverages CSS custom properties (variables) for maintainable theming and integrates smoothly with the existing Tailwind CSS and custom CSS architecture.

## Architecture

### Theme System Architecture

The theme system will be built using a layered approach:

1. **CSS Custom Properties Layer**: Define theme colors using CSS variables in the `:root` selector
2. **Theme Detection Layer**: JavaScript logic to detect system preference and user choice
3. **Theme Application Layer**: CSS classes and JavaScript functions to apply themes
4. **Persistence Layer**: localStorage to save user preferences
5. **UI Control Layer**: Toggle button component for theme switching

### Integration with Existing System

The current application uses:
- **Tailwind CSS**: For utility-first styling with dark mode support
- **Custom CSS**: Main.css and study.css with existing color schemes
- **CSS Variables**: Already partially implemented in base.html
- **Django Templates**: Base template system for consistent UI

The theme system will extend the existing CSS variable system and integrate with Tailwind's dark mode utilities.

## Components and Interfaces

### 1. Theme Toggle Button Component

**Location**: Navigation bar (desktop and mobile)
**Appearance**: 
- Icon-based toggle (sun/moon icons)
- Positioned in the top navigation near language selector
- Tooltip showing current mode and action

**States**:
- Light mode: Moon icon (🌙) - "Switch to dark mode"
- Dark mode: Sun icon (☀️) - "Switch to light mode"

### 2. CSS Theme Variables

**Enhanced CSS Custom Properties**:
```css
:root {
  /* Light Mode (default) */
  --theme-bg-primary: #ffffff;
  --theme-bg-secondary: #f3f4f6;
  --theme-bg-tertiary: #e5e7eb;
  --theme-text-primary: #1f2937;
  --theme-text-secondary: #6b7280;
  --theme-text-muted: #9ca3af;
  --theme-border: #e5e7eb;
  --theme-shadow: rgba(0, 0, 0, 0.1);
  
  /* Interactive elements */
  --theme-button-bg: #6366f1;
  --theme-button-hover: #4f46e5;
  --theme-input-bg: #ffffff;
  --theme-input-border: #d1d5db;
}

[data-theme="dark"] {
  /* Dark Mode */
  --theme-bg-primary: #111827;
  --theme-bg-secondary: #1f2937;
  --theme-bg-tertiary: #374151;
  --theme-text-primary: #f9fafb;
  --theme-text-secondary: #d1d5db;
  --theme-text-muted: #9ca3af;
  --theme-border: #374151;
  --theme-shadow: rgba(0, 0, 0, 0.3);
  
  /* Interactive elements */
  --theme-button-bg: #6366f1;
  --theme-button-hover: #4f46e5;
  --theme-input-bg: #1f2937;
  --theme-input-border: #4b5563;
}
```

### 3. JavaScript Theme Manager

**Core Functions**:
- `initializeTheme()`: Set initial theme based on localStorage or system preference
- `toggleTheme()`: Switch between light and dark modes
- `applyTheme(theme)`: Apply theme to DOM and update UI elements
- `saveThemePreference(theme)`: Save preference to localStorage
- `getSystemTheme()`: Detect system color scheme preference

**Theme Detection Logic**:
1. Check localStorage for saved preference
2. If no preference, use system preference (`prefers-color-scheme`)
3. Default to light mode if system preference unavailable

### 4. Theme-Aware Components

**Navigation Bar**: Update toggle button icon and tooltip
**Cards and Modals**: Inherit theme colors from CSS variables
**Form Elements**: Apply appropriate background and border colors
**Study Interface**: Maintain readability in both themes
**Statistics Charts**: Adapt colors for theme contrast

## Data Models

### LocalStorage Schema

```javascript
{
  "theme": "light" | "dark" | null
}
```

**Key**: `learnEnglish_theme`
**Values**: 
- `"light"`: User explicitly chose light mode
- `"dark"`: User explicitly chose dark mode
- `null`: No preference set, use system default

### CSS Class Structure

```css
/* Theme application classes */
.theme-light { /* Light mode styles */ }
.theme-dark { /* Dark mode styles */ }

/* Component-specific theme classes */
.card-themed { /* Uses CSS variables for theming */ }
.button-themed { /* Uses CSS variables for theming */ }
.input-themed { /* Uses CSS variables for theming */ }
```

## Error Handling

### JavaScript Error Scenarios

1. **localStorage Access Denied**: Fallback to session-only theme switching
2. **CSS Variable Support**: Graceful degradation for older browsers
3. **Theme Application Failure**: Retry mechanism with fallback to light mode

### CSS Fallbacks

1. **CSS Variables Not Supported**: Provide fallback color values
2. **Dark Mode Media Query Not Supported**: Default to light mode
3. **Transition Failures**: Ensure immediate theme application

### User Experience Considerations

1. **Theme Switching Delay**: Implement smooth transitions (0.3s)
2. **Flash of Wrong Theme**: Apply theme before content renders
3. **Accessibility**: Maintain contrast ratios in both themes

## Testing Strategy

### Unit Tests

1. **Theme Manager Functions**: Test all JavaScript theme functions
2. **LocalStorage Operations**: Test save/load theme preferences
3. **CSS Variable Application**: Verify theme variables are applied correctly

### Integration Tests

1. **Theme Persistence**: Verify theme persists across page reloads
2. **System Theme Detection**: Test automatic theme detection
3. **Component Theming**: Ensure all UI components respect theme

### Visual Tests

1. **Contrast Ratios**: Verify WCAG AA compliance (4.5:1 minimum)
2. **Component Appearance**: Test all components in both themes
3. **Transition Smoothness**: Verify smooth theme switching animations

### Cross-Browser Tests

1. **CSS Variable Support**: Test in modern browsers
2. **Dark Mode Media Query**: Test system preference detection
3. **LocalStorage Functionality**: Verify persistence across browsers

### Accessibility Tests

1. **Screen Reader Compatibility**: Test toggle button announcements
2. **Keyboard Navigation**: Ensure toggle is keyboard accessible
3. **High Contrast Mode**: Test compatibility with system high contrast

### Mobile Tests

1. **Touch Interaction**: Test toggle button on mobile devices
2. **Responsive Design**: Verify theme works across screen sizes
3. **Performance**: Test theme switching performance on mobile

## Implementation Phases

### Phase 1: Core Theme System
- Implement CSS custom properties
- Create JavaScript theme manager
- Add theme toggle button to navigation

### Phase 2: Component Integration
- Update existing components to use theme variables
- Ensure Tailwind dark mode compatibility
- Test theme switching across all pages

### Phase 3: Polish and Optimization
- Add smooth transitions
- Implement accessibility features
- Optimize performance and add error handling

### Phase 4: Testing and Deployment
- Comprehensive testing across browsers and devices
- User acceptance testing
- Production deployment with monitoring