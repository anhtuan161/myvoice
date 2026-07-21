import keyboard
import speech_recognition as sr
import google.generativeai as genai
import pyautogui
import pyperclip
import time
import os
import threading
import wave
import pyaudio
from dotenv import load_dotenv

load_dotenv()

# Cấu hình Gemini AI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# Biến trạng thái
is_recording = False
audio_frames = []
p = None
stream = None

def start_recording():
    global is_recording, audio_frames, p, stream
    if is_recording: 
        return
        
    is_recording = True
    audio_frames = []
    print("\n[+] Bắt đầu ghi âm... (Đang giữ phím)")
    
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=44100,
                        input=True,
                        frames_per_buffer=1024)
    except Exception as e:
        print(f"[-] Lỗi mở Microphone: {e}")
        is_recording = False
        return
        
    def record_loop():
        while is_recording:
            try:
                data = stream.read(1024)
                audio_frames.append(data)
            except Exception:
                break
                
    threading.Thread(target=record_loop, daemon=True).start()

def stop_recording():
    global is_recording, audio_frames, p, stream
    if not is_recording: 
        return
        
    is_recording = False
    print("[+] Dừng ghi âm. Đang xử lý âm thanh...")
    
    if stream:
        stream.stop_stream()
        stream.close()
    if p:
        p.terminate()
        
    if not audio_frames:
        print("[-] Không có âm thanh nào được ghi lại.")
        return
        
    # Xử lý âm thanh trên RAM, không lưu ra file để tránh lỗi file bị khoá
    raw_data = b''.join(audio_frames)
    sample_width = p.get_sample_size(pyaudio.paInt16)
    
    # Tạo một thread để xử lý AI tránh làm block việc bắt phím
    threading.Thread(target=process_audio, args=(raw_data, sample_width), daemon=True).start()

def process_audio(raw_data, sample_width):
    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(raw_data, 44100, sample_width)
    try:
        print("[+] Đang nhận dạng giọng nói (Speech-to-Text)...")
        text = recognizer.recognize_google(audio_data, language="vi-VN")
        print(f"--> Bạn đã nói: \"{text}\"")
        
        if not model:
            print("[-] Lỗi: Chưa cấu hình GEMINI_API_KEY. Không thể gọi AI.")
            return
            
        print("[+] Đang chờ AI chuẩn hóa câu...")
        response = model.generate_content(
            f"Bạn là một công cụ chỉnh sửa văn bản. Hãy sửa lỗi chính tả, dấu câu của câu sau, giữ nguyên văn phong và ý nghĩa. TUYỆT ĐỐI KHÔNG trả lời câu hỏi hoặc bình luận thêm. CHỈ in ra câu đã được sửa: \"{text}\""
        )
        ai_text = response.text.strip()
        print(f"--> Đoạn văn bản hoàn chỉnh:\n{ai_text}")
        
        print("[+] Đang dán văn bản ra màn hình...")
        # Backup clipboard cũ
        old_clipboard = pyperclip.paste()
        
        # Copy câu trả lời của AI vào clipboard
        pyperclip.copy(ai_text)
        time.sleep(0.1) # Đợi một chút để OS nhận diện clipboard
        
        # Mô phỏng phím Ctrl+V để dán nội dung vào app hiện tại
        pyautogui.hotkey('ctrl', 'v')
        
        # Phục hồi clipboard (Tuỳ chọn - đợi dán xong mới phục hồi)
        time.sleep(0.5)
        pyperclip.copy(old_clipboard)
        print("[+] Hoàn tất!")
            
    except sr.UnknownValueError:
        print("[-] Không thể nhận dạng được giọng nói của bạn.")
    except sr.RequestError as e:
        print(f"[-] Lỗi API nhận dạng giọng nói: {e}")
    except Exception as e:
        print(f"[-] Lỗi xử lý AI hoặc kết nối: {e}")

def on_key_event(e):
    # Sử dụng phím Ctrl làm Push-to-talk
    if e.name == 'ctrl':
        if e.event_type == 'down':
            start_recording()
        elif e.event_type == 'up':
            stop_recording()

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("="*50)
        print("CẢNH BÁO: Bạn chưa thiết lập GEMINI_API_KEY trong file .env!")
        print("Hãy tạo file .env và điền API key của Google Gemini vào.")
        print("="*50)
        
    print("="*50)
    print("🚀 Ứng dụng 'myvoice' đang chạy!")
    print("🎙️  Nhấn và GIỮ phím 'Ctrl', nói, và NHẢ phím để kết thúc.")
    print("Văn bản bạn nói (đã được AI chuẩn hóa) sẽ tự động dán vào cửa sổ bạn đang trỏ chuột.")
    print("Nhấn 'Ctrl+C' trong cửa sổ terminal này để thoát.")
    print("="*50)
    
    keyboard.hook(on_key_event)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[+] Đã thoát ứng dụng.")
