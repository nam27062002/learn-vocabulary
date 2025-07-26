# Flashcard Update 404 Error Fix

## 🐛 **Problem Identified**

**Error**: HTTP 404 (Not Found) when trying to update flashcards in the deck detail interface.

**Specific Details**:
- **Endpoint**: `/api/update-flashcard/` returning 404
- **JavaScript Error**: `deck_detail.js:505` - "Error updating card: Error: HTTP 404: Not Found"
- **User Impact**: Users unable to edit and save flashcard changes
- **Root Cause**: JavaScript was using language-prefixed URLs (e.g., `/en/api/update-flashcard/`) but API endpoints were moved to be without language prefixes

## ✅ **Solution Applied**

### **1. Fixed Flashcard Update API Call**

**File**: `static/js/deck_detail.js` (lines 464-467)

**Before**:
```javascript
// Prepare request details with language prefix
const currentPath = window.location.pathname;
const languagePrefix = currentPath.split('/')[1]; // Get language code (en/vi)
const requestUrl = `/${languagePrefix}/api/update-flashcard/`;
```

**After**:
```javascript
// Prepare request details (API endpoints don't use language prefixes)
const requestUrl = `/api/update-flashcard/`;
```

### **2. Fixed Deck Name Update API Call**

**File**: `static/js/deck_detail.js` (lines 879-882)

**Before**:
```javascript
// Send update request (with language prefix)
const currentPath = window.location.pathname;
const languagePrefix = currentPath.split('/')[1]; // Get language code (en/vi)
fetch(`/${languagePrefix}/api/update-deck-name/`, {
```

**After**:
```javascript
// Send update request (API endpoints don't use language prefixes)
fetch(`/api/update-deck-name/`, {
```

### **3. Cleaned Up Unused Language Prefix Code**

**File**: `static/js/deck_detail.js` (lines 1039-1042)

**Before**:
```javascript
function fetchAudioForSingleCard(cardId) {
    const languagePrefix = window.location.pathname.split('/')[1];

    return fetch(`/api/fetch-audio-for-card/`, {
```

**After**:
```javascript
function fetchAudioForSingleCard(cardId) {
    return fetch(`/api/fetch-audio-for-card/`, {
```

## 🎯 **API Endpoints Verified**

### **Confirmed Working Endpoints**:
All these endpoints exist in `vocabulary/api_urls.py` and are accessible without language prefixes:

1. **✅ `/api/update-flashcard/`** - Updates flashcard content (FIXED)
2. **✅ `/api/update-deck-name/`** - Updates deck name (FIXED)
3. **✅ `/api/fetch-missing-audio/`** - Fetches audio for multiple cards (already working)
4. **✅ `/api/fetch-audio-for-card/`** - Fetches audio for single card (already working)

### **View Functions Verified**:
- **`api_update_flashcard`** (lines 1294-1385 in `vocabulary/views.py`) ✅
- **`api_update_deck_name`** (lines 1418-1454 in `vocabulary/views.py`) ✅
- **`api_fetch_missing_audio`** (lines 1458-1515 in `vocabulary/views.py`) ✅
- **`api_fetch_audio_for_card`** (lines 1519-1567 in `vocabulary/views.py`) ✅

## 🧪 **Testing Instructions**

### **Test 1: Flashcard Update Functionality**
1. **Navigate to a deck**: `http://127.0.0.1:8000/en/decks/{deck_id}/`
2. **Click "Edit" on any flashcard**
3. **Make changes** to word, phonetic, definitions, etc.
4. **Click "Save Changes"**
5. **Expected Result**: 
   - ✅ No 404 errors in browser console
   - ✅ Success message appears
   - ✅ Changes are saved and displayed immediately

### **Test 2: Deck Name Update Functionality**
1. **Navigate to a deck detail page**
2. **Click "Edit Deck Name"**
3. **Change the deck name**
4. **Click "Save Name"**
5. **Expected Result**:
   - ✅ No 404 errors in browser console
   - ✅ Deck name updates successfully
   - ✅ New name displays immediately

### **Test 3: Audio Fetching (Should Still Work)**
1. **Navigate to a deck with cards missing audio**
2. **Click "Fetch Missing Audio"**
3. **Expected Result**:
   - ✅ Audio fetching works normally
   - ✅ No 404 errors

### **Test 4: Browser Console Verification**
1. **Open Developer Tools (F12)**
2. **Go to Network tab**
3. **Perform flashcard updates**
4. **Check API calls**:
   - ✅ `/api/update-flashcard/` returns 200 status
   - ✅ `/api/update-deck-name/` returns 200 status
   - ✅ No calls to `/en/api/...` or `/vi/api/...`

## 📊 **Expected Results**

### ✅ **Fixed Issues**:
- **No more 404 errors** when updating flashcards
- **Deck name editing works** without errors
- **All API endpoints accessible** at correct URLs
- **Consistent URL structure** across all API calls

### ✅ **Maintained Functionality**:
- **Language switching still works** for page URLs
- **All existing features preserved**
- **Audio fetching continues to work**
- **No breaking changes** to user experience

## 🔧 **Files Modified**

1. **`static/js/deck_detail.js`**:
   - **Line 465**: Removed language prefix from flashcard update URL
   - **Line 880**: Removed language prefix from deck name update URL  
   - **Line 1039**: Cleaned up unused language prefix variable

## 🏗️ **System Architecture**

### **Current URL Structure**:
```
Page URLs (with language prefixes):
├── /en/decks/{id}/     ← Deck detail page
├── /vi/decks/{id}/     ← Vietnamese version
└── /en/study/          ← Study page

API URLs (without language prefixes):
├── /api/update-flashcard/     ← Flashcard updates
├── /api/update-deck-name/     ← Deck name updates
├── /api/fetch-missing-audio/  ← Audio fetching
└── /api/incorrect-words/count/ ← Incorrect words count
```

### **Benefits of This Fix**:
1. **Consistent API Architecture**: All API endpoints follow the same URL pattern
2. **No Language Conflicts**: API endpoints work regardless of current language
3. **Easier Maintenance**: Single URL structure for all API calls
4. **Better Performance**: No unnecessary language processing for JSON APIs

## 🚀 **Verification Checklist**

- [ ] Django server starts without errors
- [ ] Flashcard editing works in deck detail view
- [ ] Deck name editing works correctly
- [ ] No 404 errors in browser console
- [ ] API calls use correct URLs (without language prefixes)
- [ ] Language switching still works for pages
- [ ] Audio fetching functionality preserved
- [ ] All flashcard CRUD operations work normally

## 🎉 **Success Criteria**

✅ **All flashcard update operations work correctly**
✅ **No 404 errors when editing flashcards or deck names**
✅ **Consistent API URL structure across the application**
✅ **Language switching preserved for page navigation**
✅ **Core vocabulary learning functionality fully operational**

The fix ensures that users can edit their flashcards and deck names without encountering 404 errors, while maintaining the proper separation between localized page URLs and language-independent API endpoints.
