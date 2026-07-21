import keyboard
import speech_recognition as sr
from google import genai
import pyautogui
import pyperclip
import time
import os
import threading
import pyaudio
import struct
import math
from dotenv import load_dotenv
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import ctypes

load_dotenv()

# ─── Cấu hình ───────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
HOTKEY         = 'ctrl'   # Đổi phím tại đây nếu muốn
SAMPLE_RATE    = 44100
CHUNK          = 1024
FORMAT         = pyaudio.paInt16
CHANNELS       = 1
# Dùng gemini-2.0-flash: ổn định, hỗ trợ tiếng Việt tốt, dùng được với tất cả tài khoản
GEMINI_MODEL   = 'gemini-2.0-flash'
# ─────────────────────────────────────────────────────────────

if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    ai_client = None

# Biến trạng thái — dùng threading.Event để thread-safe
_recording     = threading.Event()
_processing    = threading.Event()

def rms(data):
    """Tính mức âm thanh (RMS) của một đoạn PCM 16-bit."""
    count  = len(data) // 2
    shorts = struct.unpack(f"{count}h", data)
    if count == 0:
        return 0
    mean_sq = sum(s * s for s in shorts) / count
    return int(math.sqrt(mean_sq))

def test_microphone():
    """Kiểm tra mic và in mức âm thanh ra terminal."""
    print("\n" + "="*50)
    print("🎤 KIỂM TRA MICROPHONE (3 giây)...")
    print("   Hãy nói vào mic để xem mức âm thanh.")
    print("="*50)

    p = pyaudio.PyAudio()

    # In danh sách thiết bị đầu vào
    print("\n📋 Danh sách thiết bị âm thanh đầu vào:")
    default_device = p.get_default_input_device_info()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info.get('maxInputChannels', 0) > 0:
            marker = " ◀ (ĐANG DÙNG)" if i == default_device['index'] else ""
            print(f"   [{i}] {info['name']}{marker}")

    print(f"\n✅ Sử dụng: {default_device['name']}")
    print("   Mức âm (0 = im lặng, >500 = có tiếng):")

    try:
        stream = p.open(format=FORMAT, channels=CHANNELS,
                        rate=SAMPLE_RATE, input=True,
                        frames_per_buffer=CHUNK)
        for _ in range(int(SAMPLE_RATE / CHUNK * 3)):
            data  = stream.read(CHUNK, exception_on_overflow=False)
            level = rms(data)
            bar   = "█" * (level // 50)
            print(f"\r   Level: {level:5d} |{bar:<20}|", end="", flush=True)
            time.sleep(0)
        stream.stop_stream()
        stream.close()
        print("\n✅ Microphone hoạt động tốt!\n")
    except Exception as e:
        print(f"\n❌ Lỗi microphone: {e}")
        print("   → Kiểm tra lại: Cài đặt > Quyền riêng tư > Microphone → BẬT\n")
    finally:
        p.terminate()

def record_and_transcribe():
    """Vòng lặp ghi âm chính, chạy trên thread riêng."""
    while True:
        # Chờ cho đến khi bắt đầu ghi âm
        _recording.wait()

        if _processing.is_set():
            # Đang xử lý câu trước, bỏ qua
            time.sleep(0.1)
            continue

        print("\n[🎙] Đang ghi âm... (Giữ phím)")
        p      = pyaudio.PyAudio()
        frames = []
        sample_width = p.get_sample_size(FORMAT)

        try:
            stream = p.open(format=FORMAT, channels=CHANNELS,
                            rate=SAMPLE_RATE, input=True,
                            frames_per_buffer=CHUNK)
        except Exception as e:
            print(f"[❌] Không mở được Microphone: {e}")
            _recording.clear()
            p.terminate()
            continue

        # Ghi âm cho đến khi nhả phím
        while _recording.is_set():
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            except Exception:
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

        if not frames:
            print("[⚠] Không có âm thanh. Thử lại!")
            continue

        # Tính mức âm trung bình để kiểm tra mic
        avg_level = sum(rms(f) for f in frames) / len(frames)
        print(f"[📊] Mức âm trung bình: {int(avg_level)} (cần > 100 để nhận diện tốt)")

        if avg_level < 50:
            print("[⚠] Âm thanh quá nhỏ. Kiểm tra lại microphone và thử nói to hơn.")
            continue

        # Xử lý trên thread riêng để không block hotkey
        raw_data = b''.join(frames)
        _processing.set()
        threading.Thread(
            target=transcribe_and_paste,
            args=(raw_data, sample_width),
            daemon=True
        ).start()

def transcribe_and_paste(raw_data, sample_width):
    """Nhận dạng giọng nói → chuẩn hóa AI → paste."""
    try:
        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(raw_data, SAMPLE_RATE, sample_width)

        print("[🔍] Đang nhận dạng giọng nói...")
        text = recognizer.recognize_google(audio_data, language="vi-VN")
        print(f"[✔] Bạn nói: \"{text}\"")

        if ai_client:
            print("[🤖] Đang chuẩn hóa câu chữ...")
            response = ai_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=(
                    f"Bạn là công cụ chỉnh sửa văn bản tiếng Việt. "
                    f"Chỉ sửa lỗi chính tả và dấu câu, giữ nguyên ý nghĩa và văn phong. "
                    f"TUYỆT ĐỐI không trả lời hay bình luận gì thêm. "
                    f"CHỈ trả về câu đã sửa: \"{text}\""
                )
            )
            output = response.text.strip()
        else:
            output = text  # Nếu không có Gemini key, dùng text thô

        print(f"[📋] Kết quả: \"{output}\"")

        # Paste vào app hiện tại
        old_clip = pyperclip.paste()
        pyperclip.copy(output)
        time.sleep(0.15)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.4)
        pyperclip.copy(old_clip)
        print("[✅] Đã dán thành công!")

    except sr.UnknownValueError:
        print("[⚠] Không nhận dạng được. Hãy nói rõ hơn và đảm bảo mic hoạt động.")
    except sr.RequestError as e:
        print(f"[❌] Lỗi kết nối Google STT: {e}")
    except Exception as e:
        print(f"[❌] Lỗi: {e}")
    finally:
        _processing.clear()

def on_key_down():
    if not _recording.is_set():
        _recording.set()

def on_key_up():
    _recording.clear()

def set_mic_max_volume():
    """Đặt âm lượng microphone mặc định lên 100%."""
    try:
        devices = AudioUtilities.GetMicrophone()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(1.0, None)  # 1.0 = 100%
        print("[🔊] Microphone đã được đặt lên 100%.")
    except Exception as e:
        print(f"[⚠] Không thể điều chỉnh âm lượng mic: {e}")

if __name__ == "__main__":
    print("="*50)
    print("🚀 myvoice — AI Dictation for Windows")
    print("="*50)

    if not GEMINI_API_KEY:
        print("⚠️  CẢNH BÁO: Chưa có GEMINI_API_KEY trong file .env!")
        print("   Ứng dụng vẫn chạy nhưng KHÔNG chuẩn hóa câu chữ bằng AI.")
        print("   Tạo key miễn phí tại: https://aistudio.google.com/app/apikey\n")

    # Đặt mic lên 100% ngay khi khởi động
    set_mic_max_volume()

    # Kiểm tra mic ngay khi khởi động
    test_microphone()

    print("="*50)
    print(f"🎙️  Giữ phím [{HOTKEY.upper()}] để nói, nhả phím để kết thúc.")
    print("   Nhấn Ctrl+C trong cửa sổ này để thoát.")
    print("="*50 + "\n")

    # Thread ghi âm chạy nền liên tục
    threading.Thread(target=record_and_transcribe, daemon=True).start()

    # Bắt sự kiện phím — dùng on_press/on_release thay vì hook để tránh lặp key
    keyboard.on_press_key(HOTKEY,   lambda _: on_key_down(), suppress=False)
    keyboard.on_release_key(HOTKEY, lambda _: on_key_up(),   suppress=False)

    try:
        keyboard.wait()   # Chờ vô hạn, không dùng while True + sleep
    except KeyboardInterrupt:
        print("\n[+] Đã thoát ứng dụng.")
