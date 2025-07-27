# Audio Feedback Files

This directory contains audio files for study interface feedback:

## Files:
- `correct.mp3` - Success sound for correct answers (pleasant chime)
- `incorrect.mp3` - Feedback sound for incorrect answers (gentle error tone)

## Current Status:
⚠️ **PLACEHOLDER FILES** - The current files are text placeholders and need to be replaced with actual audio files.

## Audio File Requirements:

### Correct Answer Sound (`correct.mp3`):
- **Type**: Pleasant success sound (chime, ding, bell, or positive tone)
- **Duration**: 0.5-1.5 seconds
- **Volume**: Moderate level (not jarring)
- **Format**: MP3 (primary) with OGG fallback recommended
- **File Size**: < 50KB for fast loading
- **Examples**: Bell chime, success ding, positive notification sound

### Incorrect Answer Sound (`incorrect.mp3`):
- **Type**: Gentle error feedback (soft buzz, low tone, or neutral sound)
- **Duration**: 0.5-1.5 seconds
- **Volume**: Moderate level (not harsh or discouraging)
- **Format**: MP3 (primary) with OGG fallback recommended
- **File Size**: < 50KB for fast loading
- **Examples**: Soft buzz, low tone, gentle error sound (avoid harsh or negative sounds)

## Implementation Details:

### JavaScript Integration:
- Files are loaded via `new Audio('/static/audio/filename.mp3')`
- Volume set to 0.6 (60%) by default
- Includes error handling for failed loads
- Preloaded for instant playback

### User Controls:
- Toggle switch in study interface header
- Setting persisted in localStorage
- Enabled by default for new users

### Browser Compatibility:
- Primary: MP3 format (supported by all modern browsers)
- Fallback: OGG format can be added for older browsers
- Graceful degradation if audio fails to load

## How to Replace Placeholder Files:

1. **Find or Create Audio Files**:
   - Use royalty-free sound libraries (freesound.org, zapsplat.com)
   - Create custom sounds with audio editing software
   - Ensure files meet the requirements above

2. **Replace Files**:
   ```bash
   # Replace the placeholder files with actual audio
   cp your-correct-sound.mp3 static/audio/correct.mp3
   cp your-incorrect-sound.mp3 static/audio/incorrect.mp3
   ```

3. **Test Implementation**:
   - Load the study interface
   - Submit correct and incorrect answers
   - Verify sounds play at appropriate volume
   - Test the toggle switch functionality

## Recommended Sound Sources:
- **Freesound.org** - Free sound effects library
- **Zapsplat.com** - Professional sound effects (free account available)
- **Adobe Audition** - For creating custom sounds
- **Audacity** - Free audio editing software

## Fallback Behavior:
If audio files fail to load or play:
- Application continues to function normally
- Console warnings logged for debugging
- No user-facing errors
- Visual feedback remains primary interaction method
