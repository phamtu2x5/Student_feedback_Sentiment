"""Configuration for PhoBERT Pair-ABSA Model"""

import unicodedata
import re

BASE_MODEL = "vinai/phobert-base"
MAX_LEN = 256
PRED_THRESHOLD = 0.50  
NUM_CLASSES = 4
DROPOUT = 0.3

MIN_SENT_PROB = 0.40  
MIN_MARGIN = 0.03 


ASPECTS_VI = ["giang_vien", "chuong_trinh", "co_so_vat_chat", "khac"]
ASPECTS_EN = ["lecturer", "training_program", "facility", "others"]

ASPECT_MAPPING = {
    "giang_vien": "lecturer",
    "chuong_trinh": "training_program", 
    "co_so_vat_chat": "facility",
    "khac": "others"
}

ASPECT_REVERSE_MAPPING = {v: k for k, v in ASPECT_MAPPING.items()}

LABEL_MAP = {
    0: "none",
    1: "negative",
    2: "neutral", 
    3: "positive"
}

def _norm_store(s: str) -> str:
    """Chuẩn hoá để lưu/dedup (giữ dấu)"""
    s = unicodedata.normalize("NFC", str(s)).strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _norm_match(s: str) -> str:
    """Chuẩn hoá để match keyword (bỏ dấu + lower)"""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")

def _no_diacritics_set(kws: set) -> set:
    """Build keyword set có & không dấu"""
    return kws | {_norm_match(k) for k in kws}

ASPECT_PROMPTS = {
    "giang_vien": {
        "_default": (
            "ĐÁNH GIÁ phần liên quan GIẢNG VIÊN (giảng dạy, thái độ, hỗ trợ, chấm điểm, đúng giờ). "
            "QUAN TRỌNG: Một câu có thể chứa NHIỀU aspects khác nhau cùng lúc. "
            "Chỉ chọn NONE nếu phần này HOÀN TOÀN KHÔNG liên quan đến giảng viên hoặc MƠ HỒ. "
            "Nếu câu có đề cập đến giảng viên (dù chỉ một phần), hãy đánh giá sentiment. "
            "Chỉ khi nội dung RÕ RÀNG mới quyết định âm/trung/dương."
        ),
        "giang_day": (
            "ĐÁNH GIÁ GIẢNG DẠY của GIẢNG VIÊN (truyền đạt, ví dụ, dễ hiểu, tốc độ). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "dung_gio": (
            "ĐÁNH GIÁ TÍNH ĐÚNG GIỜ/LÊN LỚP của GIẢNG VIÊN. "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "ho_tro": (
            "ĐÁNH GIÁ MỨC HỖ TRỢ/TƯ VẤN của GIẢNG VIÊN cho sinh viên (phản hồi, giải đáp). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "cham_diem": (
            "ĐÁNH GIÁ CÁCH CHẤM ĐIỂM của GIẢNG VIÊN (công bằng, minh bạch, rubric). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "thai_do": (
            "ĐÁNH GIÁ THÁI ĐỘ của GIẢNG VIÊN (tôn trọng, thân thiện, khắt khe). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
    },

    "chuong_trinh": {
        "_default": (
            "ĐÁNH GIÁ CHƯƠNG TRÌNH ĐÀO TẠO (môn học, tín chỉ, nội dung, lộ trình, lịch/kế hoạch). "
            "QUAN TRỌNG: Một câu có thể chứa NHIỀU aspects khác nhau cùng lúc. "
            "Chỉ chọn NONE nếu phần này HOÀN TOÀN KHÔNG liên quan đến chương trình hoặc MƠ HỒ. "
            "Nếu câu có đề cập đến chương trình (dù chỉ một phần), hãy đánh giá sentiment."
        ),
        "noi_dung": (
            "ĐÁNH GIÁ NỘI DUNG CTĐT (mới/cập nhật, thực tiễn, trùng lặp, lộ trình). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "lich_hoc": (
            "ĐÁNH GIÁ LỊCH HỌC/KẾ HOẠCH (phân bổ, dồn dập, trùng lịch, đổi lịch). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "tin_chi": (
            "ĐÁNH GIÁ TÍN CHỈ/HỌC PHẦN (phân bổ, tiên quyết, nợ môn). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "de_cuong": (
            "ĐÁNH GIÁ ĐỀ CƯƠNG/GIÁO TRÌNH/SYLLABUS (mục tiêu, tài liệu, rubric). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
    },

    "co_so_vat_chat": {
        "_default": (
            "ĐÁNH GIÁ CƠ SỞ VẬT CHẤT (mạng/Wi-Fi, phòng học, phòng thí nghiệm, thiết bị, thư viện, gửi xe, vệ sinh, cổng đào tạo). "
            "QUAN TRỌNG: Một câu có thể chứa NHIỀU aspects khác nhau cùng lúc. "
            "Chỉ chọn NONE nếu phần này HOÀN TOÀN KHÔNG liên quan đến cơ sở vật chất hoặc MƠ HỒ. "
            "Nếu câu có đề cập đến cơ sở vật chất (dù chỉ một phần), hãy đánh giá sentiment."
        ),
        "mang": (
            "ĐÁNH GIÁ MẠNG/Wi-Fi (tốc độ, ổn định, đăng nhập). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "phong_hoc": (
            "ĐÁNH GIÁ PHÒNG HỌC (ánh sáng, nhiệt độ, sạch sẽ, bàn ghế, ổ điện, tiếng ồn). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "phong_thi_nghiem": (
            "ĐÁNH GIÁ PHÒNG THÍ NGHIỆM/THỰC HÀNH (máy, cấu hình, phần mềm, lab). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "thiet_bi": (
            "ĐÁNH GIÁ THIẾT BỊ GIẢNG DẠY (máy chiếu, micro/loa, TV/tivi, cáp/HDMI). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "thu_vien": (
            "ĐÁNH GIÁ THƯ VIỆN (tài liệu, chỗ ngồi, không gian, giờ mở cửa). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "giu_xe_ve_sinh": (
            "ĐÁNH GIÁ GIỮ XE/ NHÀ VỆ SINH (bãi xe, phí, vệ sinh, giấy, mùi). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "cong_quan_ly_dao_tao": (
            "ĐÁNH GIÁ CỔNG/ TRANG QUẢN LÝ ĐÀO TẠO (đăng nhập, quá tải, tra cứu). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
    },

    "khac": {
        "_default": (
            "ĐÁNH GIÁ NHÓM KHÁC (học phí, học bổng, thủ tục hành chính, CLB, KTX, một cửa, đăng ký tín chỉ, điểm rèn luyện). "
            "QUAN TRỌNG: Một câu có thể chứa NHIỀU aspects khác nhau cùng lúc. "
            "Chỉ chọn NONE nếu phần này HOÀN TOÀN KHÔNG liên quan đến nhóm khác hoặc MƠ HỒ. "
            "Nếu câu có đề cập đến nhóm khác (dù chỉ một phần), hãy đánh giá sentiment."
        ),
        "hoc_phi": (
            "ĐÁNH GIÁ HỌC PHÍ (mức thu, tăng/giảm, minh bạch, miễn giảm). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "hoc_bong": (
            "ĐÁNH GIÁ HỌC BỔNG (tiêu chí, quy trình, thời hạn, công bố). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "hanh_chinh": (
            "ĐÁNH GIÁ THỦ TỤC HÀNH CHÍNH/CTSV (giấy tờ, xử lý, phản hồi). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "clb": (
            "ĐÁNH GIÁ CLB/ NGOẠI KHÓA (tuyển, hoạt động, sự kiện, truyền thông). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "ktx": (
            "ĐÁNH GIÁ KÝ TÚC XÁ (phòng ở, an ninh, điện nước, giờ giấc). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "mot_cua": (
            "ĐÁNH GIÁ VĂN PHÒNG MỘT CỬA (tiếp nhận, số thứ tự, trả kết quả). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "dang_ky_tin": (
            "ĐÁNH GIÁ ĐĂNG KÝ TÍN CHỈ (quá tải, dễ dùng, xếp lịch). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
        "diem_ren_luyen": (
            "ĐÁNH GIÁ ĐIỂM RÈN LUYỆN (tiêu chí, minh chứng, quy trình). "
            "Một câu có thể có nhiều aspects. Nếu KHÔNG liên quan → NONE."
        ),
    },
}

PROMPTS_EN_DEFAULT = {
    "lecturer": ASPECT_PROMPTS["giang_vien"]["_default"],
    "training_program": ASPECT_PROMPTS["chuong_trinh"]["_default"],
    "facility": ASPECT_PROMPTS["co_so_vat_chat"]["_default"],
    "others": ASPECT_PROMPTS["khac"]["_default"]
}
SUBTOPIC_KW = {
    "giang_vien": {
        "dung_gio": _no_diacritics_set({
            "đi dạy ","lên lớp","vào lớp","bắt đầu tiết","kết thúc tiết","giảng viên","cô","thầy","giáo viên","gv"
        }),
        "cham_diem": _no_diacritics_set({
            "chấm điểm","thang điểm","điểm thi","điểm thành phần","điểm tổng kết","phúc khảo",
            "điểm giữa kỳ","điểm cuối kỳ","điểm nhóm","điểm cá nhân","điểm bonus",
            "điểm chuyên cần","điểm chuyên cần","điểm chuyên đề","rubric","grading","giảng viên","cô","thầy","giáo viên","gv"
        }),
        "ho_tro": _no_diacritics_set({
            "tư vấn","giải đáp","phản hồi","cvht",
            "cố vấn","hướng dẫn","trao đổi","hỏi đáp","giảng viên","cô","thầy","giáo viên","gv"
        }),
        "thai_do": _no_diacritics_set({
            "thái độ","ứng xử","tác phong","phong thái","giao tiếp","cách nói",
            "ngữ điệu","hành vi","cử chỉ","cách cư xử","thái độ giảng viên",
            "phong cách","tương tác","thái độ lớp","ngôn ngữ cơ thể",
            "giảng viên","cô","thầy","giáo viên","gv"
        }),
        "giang_day": _no_diacritics_set({
            "giảng dạy","truyền đạt","diễn đạt","ví dụ","bài giảng","slide","ghi chú",
            "ôn tập","bài học","phương pháp","thực hành","lý thuyết",
            "thảo luận","minh họa","slide giảng","slide bài","giải thích","phong cách giảng",
            "giảng viên","cô","thầy","giáo viên","gv"
        }),
    },

    "chuong_trinh": {
        "lich_hoc": _no_diacritics_set({
            "lịch học","thời khóa biểu","thời khoá biểu","kế hoạch học","xếp lịch","trùng lịch",
            "đổi lịch","lịch thi","lịch học thêm","ca tối","online","offline","ca sáng",
            "ca chiều","học bù","thi dồn","thi liên tục","xếp ca","thời gian học","lịch kiểm tra"
        }),
        "tin_chi": _no_diacritics_set({
            "tín chỉ","học phần","tiên quyết","song hành","đăng ký học phần","nợ môn",
            "đủ tín","số tín","khối lượng học","điều kiện học phần","mã môn","tải học",
            "đăng ký tín","phân bổ học phần","lộ trình học","số học phần"
        }),
        "de_cuong": _no_diacritics_set({
            "đề cương","syllabus","giáo trình","tài liệu bắt buộc","tài liệu tham khảo",
            "mục tiêu học phần","kế hoạch môn","outline","kế hoạch giảng dạy","phân bổ điểm",
            "tài liệu học","hướng dẫn môn","phân phối chương","khung điểm","thang đánh giá"
        }),
        "noi_dung": _no_diacritics_set({
            "nội dung","thực tế","thực tiễn","lộ trình","khung chương trình",
            "cập nhật","định hướng nghề","kiến thức","module",
            "chuyên đề","cấu trúc môn","chương trình học","đề mục","môn học","học liệu"
        }),
    },

    "co_so_vat_chat": {
        "mang": _no_diacritics_set({
            "mạng","wifi","wi-fi","wi fi","đăng nhập wifi", "ping","băng thông","wifi trường"
        }),
        "phong_hoc": _no_diacritics_set({
            "phòng học","ánh sáng","đèn","máy lạnh","điều hòa","điều hoà","quạt",
            "bàn ghế","ổ điện","ổ cắm","cách âm","sàn nhà","rèm cửa","trần nhà","bảng viết"
        }),
        "phong_thi_nghiem": _no_diacritics_set({
            "phòng thí nghiệm","phòng thực hành","lab","phòng lab","máy thực hành",
            "cài phần mềm","thiết bị thí nghiệm","dụng cụ lab","phòng máy","thiết bị lab"
        }),
        "thiet_bi": _no_diacritics_set({
            "máy chiếu","micro","mic","loa","âm thanh","tv","tivi","cáp","hdmi","adapter",
            "thiết bị giảng dạy","máy quay","camera lớp","loa bluetooth","âm lượng",
            "loa","đầu nối","bộ chia"
        }),
        "thu_vien": _no_diacritics_set({
            "thư viện","mượn sách","trả sách","tài liệu số","ebook","chỗ ngồi",
            "bàn đọc","yên tĩnh","giờ mở cửa","mượn giáo trình","tra cứu sách","wifi thư viện",
            "tra cứu","kệ sách","tài nguyên số","khu đọc","mượn tài liệu","mượn thiết bị",
            "tài liệu thư viện","tài liệu mượn","sách thư viện"
        }),
        "giu_xe_ve_sinh": _no_diacritics_set({
            "bãi giữ xe","nhà giữ xe","gửi xe","thẻ xe","quẹt thẻ","phí gửi xe",
            "nhà vệ sinh","wc","toilet","giấy vệ sinh","nước rửa tay","nhà vệ sinh",
            "ống nước","cống thoát","sàn"
        }),
        "cong_quan_ly_dao_tao": _no_diacritics_set({
            "trang quản lý đào tạo","cổng đào tạo","hệ thống đào tạo","portal","cổng thông tin",
            "đăng nhập","quên mật khẩu","reset mật khẩu","quá tải","treo","tra cứu điểm",
            "web đào tạo","cổng sinh viên","hệ thống online","điểm số","trang web"
        }),
    },

    "khac": {
        "hoc_phi": _no_diacritics_set({
            "học phí","thu thêm","biên lai","miễn giảm","chính sách học phí","công khai học phí",
            "đóng tiền","nộp học phí","thu tiền","hoá đơn","chính sách","phiếu thu","biên nhận",
            "đóng học","nộp lệ phí","phí học","thanh toán học phí"
        }),
        "hoc_bong": _no_diacritics_set({
            "học bổng","học bổng kkht","tiêu chí học bổng","điểm chuẩn học bổng",
            "nộp hồ sơ học bổng","kết quả học bổng","trễ hạn học bổng","xét học bổng",
            "điều kiện học bổng","quỹ học bổng","thông báo học bổng","hồ sơ học bổng","điểm xét"
        }),
        "hanh_chinh": _no_diacritics_set({
            "thủ tục","hành chính","giấy tờ","đóng dấu","xác nhận sinh viên","giấy xác nhận",
            "phòng ctsv","tiếp nhận hồ sơ","trả kết quả","xin giấy","nộp hồ sơ","biểu mẫu",
            "phòng đào tạo","chứng nhận","xác minh","giấy phép","bản sao","văn thư"
        }),
        "clb": _no_diacritics_set({
            "câu lạc bộ","clb","tuyển thành viên","hoạt động clb","ngoại khóa","sự kiện","workshop",
            "đăng ký clb","đoàn hội","event","chương trình","team","cuộc thi","hoạt động sv",
            "hoạt động ngoại khoá","nhóm sinh viên","sự kiện trường","đăng ký tham gia"
        }),
        "ktx": _no_diacritics_set({
            "ký túc xá","kí túc xá","ktx","ở ghép","phòng ở","bảo vệ","giờ giới nghiêm",
            "điện","nước","phòng ktx","khu ở","ktx","an ninh","phòng chung",
            "toà ktx","khu vực ở","quản lý ktx"
        }),
        "mot_cua": _no_diacritics_set({
            "văn phòng một cửa","vp1c","nộp hồ sơ","số thứ tự","lấy giấy","trả giấy","trả kết quả",
            "văn phòng","phòng một cửa","hồ sơ","giấy tờ","số lượt","quầy tiếp nhận"
        }),
        "dang_ky_tin": _no_diacritics_set({
            "đăng ký","đăng ký môn","đăng ký tín chỉ","đk tín","đk môn","server",
            "xếp lịch tự động","lọc trùng lịch","hệ thống",
            "đăng ký online","chọn môn","mở lớp","đóng lớp","sắp lịch"
        }),
        "diem_ren_luyen": _no_diacritics_set({
            "điểm rèn luyện","drl","đánh giá rèn luyện","minh chứng drl","chấm drl",
            "minh chứng","điểm rl","bảng drl","đánh giá cá nhân","đánh giá tập thể"
        }),
    },
}

_VI_LETTER = re.compile(r"[A-Za-zÀ-ỹĐđ]")

def _pick_subprompt(aspect_vi: str, sentence: str) -> str:
    """Chọn subprompt dựa trên keywords trong câu"""
    s_norm = _norm_match(str(sentence))
    for sub, kws in SUBTOPIC_KW.get(aspect_vi, {}).items():
        if any(k in s_norm for k in kws):
            return ASPECT_PROMPTS[aspect_vi].get(sub, ASPECT_PROMPTS[aspect_vi]["_default"])
    return ASPECT_PROMPTS[aspect_vi]["_default"]

def get_prompt(aspect_en: str, sentence: str = "", use_subprompt: bool = False) -> str:
    """Lấy prompt cho aspect"""
    if use_subprompt and sentence:
        aspect_vi = ASPECT_REVERSE_MAPPING.get(aspect_en, "khac")
        return _pick_subprompt(aspect_vi, sentence)
    return PROMPTS_EN_DEFAULT.get(aspect_en, "")

def check_keywords(text: str, aspect_vi: str) -> bool:
    """Kiểm tra text có chứa keywords của aspect không"""
    text_norm = _norm_match(text)
    for sub, kws in SUBTOPIC_KW.get(aspect_vi, {}).items():
        if any(k in text_norm for k in kws):
            return True
    return False

def _is_garbage(txt: str) -> bool:
    """Kiểm tra text có phải garbage không (quá ngắn hoặc không phải tiếng Việt)"""
    t = str(txt).strip()
    if len(t) < 4:
        return True
    if len(t.split()) < 2:
        return True
    letters = sum(1 for ch in t if _VI_LETTER.match(ch))
    return (letters / max(1, len(t))) < 0.4

def _aspect_has_kw(aspect_vi: str, s_norm: str) -> bool:
    """Kiểm tra aspect có keyword trong sentence không"""
    for kws in SUBTOPIC_KW.get(aspect_vi, {}).values():
        if any(k in s_norm for k in kws):
            return True
    return False

def _has_any_kw(s_norm: str) -> bool:
    """Kiểm tra sentence có keyword của bất kỳ aspect nào không"""
    for aspect_vi in ASPECTS_VI:
        if _aspect_has_kw(aspect_vi, s_norm):
            return True
    return False

