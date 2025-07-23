# Study Random Words Feature

## Tổng quan
Đã thêm tính năng "Study Random Words" vào ứng dụng học từ vựng, cho phép người dùng học từ ngẫu nhiên từ toàn bộ cơ sở dữ liệu từ vựng của họ thay vì chỉ học theo bộ thẻ cụ thể.

## Tính năng mới

### 1. Study Mode Selection
- **Radio buttons** để chọn chế độ học:
  - "Normal Study (by Decks)" - Chế độ học bình thường theo bộ thẻ
  - "Study Random Words" - Chế độ học từ ngẫu nhiên

### 2. Conditional Interface Display
- **Normal Study Mode**: Hiển thị giao diện chọn bộ thẻ như trước
- **Random Study Mode**: Ẩn giao diện chọn bộ thẻ, hiển thị:
  - Input field để nhập số lượng từ muốn học (1-100)
  - Hiển thị tổng số từ có sẵn trong database
  - Button "Start Study" riêng cho random mode

### 3. Backend Logic

#### API Endpoint: `api_next_question`
- **Parameters mới**:
  - `study_mode`: 'decks' hoặc 'random'
  - `word_count`: Số lượng từ muốn học (cho random mode)
  - `seen_card_ids[]`: Danh sách ID của các thẻ đã học trong session

#### Logic xử lý:
- **Normal Study**: Sử dụng `_get_next_card_enhanced()` với deck_ids
- **Random Study**: 
  - Lọc ra các thẻ chưa được học trong session hiện tại
  - Chọn ngẫu nhiên từ toàn bộ vocabulary database
  - Không lặp lại từ trong cùng một session

### 4. Frontend Implementation

#### Template Changes (`study.html`):
- Thêm study mode selection với radio buttons
- Tách riêng giao diện cho deck study và random study
- Hiển thị tổng số từ có sẵn

#### JavaScript Changes (`study.js`):
- Xử lý study mode selection
- Tracking seen card IDs cho random mode
- Conditional API calls dựa trên study mode
- UI state management cho các giao diện khác nhau

### 5. User Experience Features

#### Visual Feedback:
- Clear indication về study mode đang được chọn
- Hiển thị số lượng từ có sẵn cho random study
- Smooth transitions giữa các giao diện

#### Edge Case Handling:
- **Empty database**: Hiển thị thông báo "No cards due"
- **Requesting more words than available**: Tự động sử dụng tất cả từ có sẵn
- **No decks selected**: Validation cho normal study mode

#### Integration:
- **Spaced Repetition**: Random study vẫn sử dụng hệ thống spaced repetition
- **Study Modes**: Hỗ trợ đầy đủ multiple choice, typing, dictation
- **Progress Tracking**: Theo dõi tiến độ và thống kê như bình thường
- **Statistics**: Cập nhật thống kê học tập

## Files đã được sửa đổi

### Backend:
- `vocabulary/views.py`: 
  - Cập nhật `study_page()` để truyền `total_words_available`
  - Cập nhật `api_next_question()` để hỗ trợ random study mode

### Frontend:
- `vocabulary/templates/vocabulary/study.html`: 
  - Thêm study mode selection UI
  - Tách riêng giao diện cho deck và random study
- `static/js/study.js`: 
  - Xử lý study mode selection
  - Tracking seen cards cho random mode
  - Conditional API calls
- `staticfiles/js/study.js`: Cập nhật tương tự

### Localization:
- `locale/vi/LC_MESSAGES/django.po`: Thêm text labels tiếng Việt
- `locale/en/LC_MESSAGES/django.po`: Thêm text labels tiếng Anh

## Cách sử dụng

### Normal Study Mode:
1. Chọn "Normal Study (by Decks)"
2. Chọn một hoặc nhiều bộ thẻ
3. Click "Start Study"

### Random Study Mode:
1. Chọn "Study Random Words"
2. Nhập số lượng từ muốn học (1-100)
3. Click "Start Study"

## Technical Details

### Random Selection Algorithm:
```python
# Lọc thẻ chưa được học trong session
available_cards = Flashcard.objects.filter(user=request.user).exclude(id__in=seen_card_ids)

# Chọn ngẫu nhiên
card = available_cards.order_by('?').first()
```

### Session Management:
- `seenCardIds` array để track các thẻ đã học
- Reset khi bắt đầu session mới
- Không lặp lại từ trong cùng session

### API Parameters:
```
GET /api/next_question/?study_mode=random&word_count=10&seen_card_ids[]=1&seen_card_ids[]=2
```

## Benefits

1. **Variety**: Học từ toàn bộ vocabulary thay vì chỉ một bộ thẻ
2. **Flexibility**: Người dùng có thể chọn số lượng từ muốn học
3. **No Repetition**: Không lặp lại từ trong cùng session
4. **Seamless Integration**: Hoạt động với tất cả tính năng hiện có
5. **User Control**: Người dùng có thể chọn chế độ học phù hợp

## Future Enhancements

1. **Smart Random**: Ưu tiên từ khó hoặc từ chưa học lâu
2. **Session History**: Lưu lịch sử các session random study
3. **Custom Filters**: Cho phép lọc theo difficulty, part of speech
4. **Progress Tracking**: Thống kê riêng cho random study mode 