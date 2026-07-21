# myvoice - AI Voice Assistant for Windows

`myvoice` là một ứng dụng "Push-to-talk" trên Windows giúp bạn có thể nói chuyện trực tiếp với AI thay vì phải chat. Thay vì chỉ nhập văn bản bằng giọng nói (như chức năng dictation), `myvoice` sẽ lắng nghe giọng nói của bạn, gửi cho AI (Google Gemini), và AI sẽ tự động gõ câu trả lời vào ứng dụng mà bạn đang sử dụng.

## Tính năng
- **Push-to-talk**: Giữ phím `Ctrl`, nói, và nhả phím để kết thúc. Không cần phải click chuột hay thao tác phức tạp.
- **Auto-type**: AI tự động dán (paste) câu trả lời của mình thẳng vào bất kì ô text nào bạn đang trỏ chuột tới (Zalo, Word, trình duyệt, Code Editor...).
- Sử dụng Google Web Speech API (nhận dạng giọng nói miễn phí) & Gemini 1.5 Flash (Xử lý AI siêu tốc).

## Cài đặt

1. Đảm bảo bạn đã cài đặt Python (phiên bản 3.8+).
2. Clone repository này về máy:
   ```bash
   git clone https://github.com/anhtuan161/myvoice.git
   cd myvoice
   ```
3. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
4. Tạo một file tên là `.env` (copy từ file `.env.example`) và điền API Key của Google Gemini vào:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   *(Bạn có thể lấy API Key miễn phí tại [Google AI Studio](https://aistudio.google.com/app/apikey))*

## Cách sử dụng

1. Chạy ứng dụng từ Terminal/Command Prompt (chạy với quyền Administrator nếu phím tắt không hoạt động):
   ```bash
   python main.py
   ```
2. Mở một ứng dụng bất kỳ (ví dụ: Notepad, Zalo, trình duyệt) và đặt con trỏ chuột vào vị trí gõ văn bản.
3. Nhấn và GIỮ phím `Ctrl` trên bàn phím.
4. Nói câu hỏi của bạn (ví dụ: "Viết cho tôi một hàm Python tính giai thừa").
5. Nhả phím `Ctrl` ra. Đợi vài giây, câu trả lời của AI sẽ tự động được gõ vào màn hình.

## Đóng góp
Dự án được tạo bởi [anhtuan161](https://github.com/anhtuan161). Mọi đóng góp xin vui lòng tạo Pull Request!
