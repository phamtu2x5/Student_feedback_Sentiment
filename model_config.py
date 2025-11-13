"""Configuration for PhoBERT Pair-ABSA Model"""

import unicodedata
import re

BASE_MODEL = "vinai/phobert-base"
MAX_LEN = 256
PRED_THRESHOLD = 0.60  
NUM_CLASSES = 4
DROPOUT = 0.3

MIN_SENT_PROB = 0.50  
MIN_MARGIN = 0.08 


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
            "ĐÁNH GIÁ phần liên quan GIẢNG VIÊN (giảng dạy, thái độ, hỗ trợ, chấm điểm, đúng giờ). Nếu câu không nhắc rõ đến GIẢNG VIÊN -> NONE. Mỗi aspect đánh giá độc lập (ví dụ: giảng viên đi dạy trễ nhưng mạng wifi tốt -> giảng viên NEGATIVE, cơ sở vật chất POSITIVE). NEGATIVE khi phàn nàn trễ, khó hiểu, thiếu hỗ trợ; POSITIVE khi được khen đúng giờ, nhiệt tình, dễ hiểu; không rõ -> NEUTRAL."
        ),
        "giang_day": (
            "ĐÁNH GIÁ GIẢNG DẠY của GIẢNG VIÊN. Nếu câu không nói về bài giảng, cách truyền đạt, phương pháp -> NONE. Mỗi aspect độc lập. NEGATIVE khi khó hiểu, quá nhanh/chậm, thiếu ví dụ; POSITIVE khi dễ hiểu, nhiều ví dụ, rõ ràng; không rõ -> NEUTRAL."
        ),
        "dung_gio": (
            "ĐÁNH GIÁ ĐÚNG GIỜ của GIẢNG VIÊN. Nếu câu không nhắc việc vào lớp, bắt đầu/kết thúc tiết -> NONE. Mỗi aspect độc lập. NEGATIVE khi trễ, bỏ tiết; POSITIVE khi đúng giờ, giữ lịch; không rõ -> NEUTRAL."
        ),
        "ho_tro": (
            "ĐÁNH GIÁ HỖ TRỢ/TƯ VẤN của GIẢNG VIÊN. Nếu câu không nhắc hỗ trợ, phản hồi, giải đáp -> NONE. Mỗi aspect độc lập. NEGATIVE khi chậm phản hồi, không giúp; POSITIVE khi nhiệt tình, phản hồi nhanh; không rõ -> NEUTRAL."
        ),
        "cham_diem": (
            "ĐÁNH GIÁ CHẤM ĐIỂM của GIẢNG VIÊN. Nếu câu không nói điểm, rubric, phúc khảo -> NONE. Mỗi aspect độc lập. NEGATIVE khi không công bằng, khó hiểu; POSITIVE khi minh bạch, công bằng; không rõ -> NEUTRAL."
        ),
        "thai_do": (
            "ĐÁNH GIÁ THÁI ĐỘ/TÁC PHONG của GIẢNG VIÊN. Nếu câu không nhắc thái độ, giao tiếp -> NONE. Mỗi aspect độc lập. NEGATIVE khi thô lỗ, thiếu tôn trọng; POSITIVE khi thân thiện, tôn trọng; không rõ -> NEUTRAL."
        ),
    },
    "chuong_trinh": {
        "_default": (
            "ĐÁNH GIÁ CHƯƠNG TRÌNH ĐÀO TẠO (môn học, tín chỉ, nội dung, lộ trình, lịch). Nếu câu không nhắc rõ đến chương trình -> NONE. Mỗi aspect đánh giá độc lập (ví dụ: lịch học dày nhưng giảng viên hỗ trợ tốt -> chương trình NEGATIVE, giảng viên POSITIVE). NEGATIVE khi quá tải, lạc hậu, trùng lặp; POSITIVE khi hợp lý, cập nhật, thực tế; không rõ -> NEUTRAL."
        ),
        "noi_dung": (
            "ĐÁNH GIÁ NỘI DUNG CHƯƠNG TRÌNH. Nếu câu không nói nội dung môn, học liệu, lộ trình -> NONE. Mỗi aspect độc lập. NEGATIVE khi lạc hậu, trùng lặp, thiếu thực tế; POSITIVE khi cập nhật, hữu ích; không rõ -> NEUTRAL."
        ),
        "lich_hoc": (
            "ĐÁNH GIÁ LỊCH HỌC/KẾ HOẠCH. Nếu câu không nhắc lịch, thời khóa biểu, xếp ca -> NONE. Mỗi aspect độc lập. NEGATIVE khi dồn dập, trùng lịch, đổi lịch liên tục; POSITIVE khi rõ ràng, hợp lý; không rõ -> NEUTRAL."
        ),
        "tin_chi": (
            "ĐÁNH GIÁ TÍN CHỈ/HỌC PHẦN. Nếu câu không nói tín chỉ, đăng ký học phần, tiên quyết -> NONE. Mỗi aspect độc lập. NEGATIVE khi bất hợp lý, khó đăng ký; POSITIVE khi phân bổ hợp lý, dễ đăng ký; không rõ -> NEUTRAL."
        ),
        "de_cuong": (
            "ĐÁNH GIÁ ĐỀ CƯƠNG/GIÁO TRÌNH. Nếu câu không nhắc đề cương, tài liệu, rubric -> NONE. Mỗi aspect độc lập. NEGATIVE khi thiếu rõ ràng, thiếu tài liệu; POSITIVE khi đầy đủ, minh bạch; không rõ -> NEUTRAL."
        ),
    },
    "co_so_vat_chat": {
        "_default": (
            "ĐÁNH GIÁ CƠ SỞ VẬT CHẤT (mạng, phòng học, phòng thí nghiệm, thiết bị, thư viện, gửi xe, vệ sinh, cổng đào tạo). Nếu câu không nhắc rõ đến cơ sở vật chất -> NONE. Mỗi aspect đánh giá độc lập (ví dụ: phòng học nóng nhưng thầy cô dạy dễ hiểu -> cơ sở vật chất NEGATIVE, giảng viên POSITIVE). NEGATIVE khi phàn nàn hỏng, thiếu, bẩn; POSITIVE khi khen đầy đủ, sạch, hiện đại; không rõ -> NEUTRAL."
        ),
        "mang": (
            "ĐÁNH GIÁ MẠNG/WI-FI. Nếu câu không nói mạng, wifi, internet -> NONE. Mỗi aspect độc lập. NEGATIVE khi chậm, rớt kết nối; POSITIVE khi nhanh, ổn định; không rõ -> NEUTRAL."
        ),
        "phong_hoc": (
            "ĐÁNH GIÁ PHÒNG HỌC. Nếu câu không nói phòng học, bàn ghế, điều hòa, tiếng ồn -> NONE. Mỗi aspect độc lập. NEGATIVE khi nóng, ồn, xuống cấp; POSITIVE khi mát, sạch, đủ tiện nghi; không rõ -> NEUTRAL."
        ),
        "phong_thi_nghiem": (
            "ĐÁNH GIÁ PHÒNG THÍ NGHIỆM/THỰC HÀNH. Nếu câu không nhắc lab, thiết bị thực hành -> NONE. Mỗi aspect độc lập. NEGATIVE khi thiếu máy, phần mềm lỗi; POSITIVE khi đầy đủ, hiện đại; không rõ -> NEUTRAL."
        ),
        "thiet_bi": (
            "ĐÁNH GIÁ THIẾT BỊ GIẢNG DẠY. Nếu câu không nói máy chiếu, micro, loa, TV -> NONE. Mỗi aspect độc lập. NEGATIVE khi hỏng, âm kém; POSITIVE khi hoạt động tốt, rõ ràng; không rõ -> NEUTRAL."
        ),
        "thu_vien": (
            "ĐÁNH GIÁ THƯ VIỆN. Nếu câu không nhắc thư viện, tài liệu, chỗ ngồi -> NONE. Mỗi aspect độc lập. NEGATIVE khi thiếu tài liệu, chật, ồn; POSITIVE khi phong phú, yên tĩnh; không rõ -> NEUTRAL."
        ),
        "giu_xe_ve_sinh": (
            "ĐÁNH GIÁ GIỮ XE/NHÀ VỆ SINH. Nếu câu không nói gửi xe hoặc nhà vệ sinh -> NONE. Mỗi aspect độc lập. NEGATIVE khi bẩn, đắt, mùi khó chịu; POSITIVE khi sạch, thuận tiện; không rõ -> NEUTRAL."
        ),
        "cong_quan_ly_dao_tao": (
            "ĐÁNH GIÁ CỔNG/TRANG QUẢN LÝ ĐÀO TẠO. Nếu câu không nhắc cổng đào tạo, đăng nhập, tra cứu -> NONE. Mỗi aspect độc lập. NEGATIVE khi quá tải, treo, khó dùng; POSITIVE khi ổn định, dễ dùng; không rõ -> NEUTRAL."
        ),
    },
    "khac": {
        "_default": (
            "ĐÁNH GIÁ NHÓM KHÁC (học phí, học bổng, hành chính, CLB, KTX, một cửa, đăng ký tín chỉ, điểm rèn luyện). Nếu câu không nhắc rõ đến nhóm này -> NONE. Mỗi aspect đánh giá độc lập (ví dụ: học phí tăng nhưng phòng học tốt -> nhóm khác NEGATIVE, cơ sở vật chất POSITIVE). NEGATIVE khi phàn nàn khó khăn, chậm trễ; POSITIVE khi khen rõ ràng, nhanh chóng; không rõ -> NEUTRAL."
        ),
        "hoc_phi": (
            "ĐÁNH GIÁ HỌC PHÍ. Nếu câu không nhắc học phí, mức thu, đóng tiền -> NONE. Mỗi aspect độc lập. NEGATIVE khi đắt, tăng, thiếu minh bạch; POSITIVE khi hợp lý, minh bạch; không rõ -> NEUTRAL."
        ),
        "hoc_bong": (
            "ĐÁNH GIÁ HỌC BỔNG. Nếu câu không nói tiêu chí, quy trình, kết quả học bổng -> NONE. Mỗi aspect độc lập. NEGATIVE khi khó, chậm, không rõ; POSITIVE khi dễ, minh bạch, kịp thời; không rõ -> NEUTRAL."
        ),
        "hanh_chinh": (
            "ĐÁNH GIÁ THỦ TỤC HÀNH CHÍNH/CTSV. Nếu câu không nhắc hồ sơ, giấy tờ, xử lý -> NONE. Mỗi aspect độc lập. NEGATIVE khi rườm rà, chậm, thiếu phản hồi; POSITIVE khi nhanh, rõ ràng; không rõ -> NEUTRAL."
        ),
        "clb": (
            "ĐÁNH GIÁ CLB/HOẠT ĐỘNG NGOẠI KHÓA. Nếu câu không nói CLB, sự kiện, hoạt động sinh viên -> NONE. Mỗi aspect độc lập. NEGATIVE khi ít hoạt động, thiếu hấp dẫn; POSITIVE khi sôi nổi, hữu ích; không rõ -> NEUTRAL."
        ),
        "ktx": (
            "ĐÁNH GIÁ KÝ TÚC XÁ. Nếu câu không nhắc phòng KTX, an ninh, điện nước -> NONE. Mỗi aspect độc lập. NEGATIVE khi chật, mất an ninh, thiếu điện nước; POSITIVE khi sạch, an toàn, đầy đủ; không rõ -> NEUTRAL."
        ),
        "mot_cua": (
            "ĐÁNH GIÁ VĂN PHÒNG MỘT CỬA. Nếu câu không nhắc một cửa, tiếp nhận, trả kết quả -> NONE. Mỗi aspect độc lập. NEGATIVE khi chờ lâu, đông, xử lý chậm; POSITIVE khi nhanh, rõ ràng; không rõ -> NEUTRAL."
        ),
        "dang_ky_tin": (
            "ĐÁNH GIÁ ĐĂNG KÝ TÍN CHỈ. Nếu câu không nói đăng ký môn, hệ thống đăng ký -> NONE. Mỗi aspect độc lập. NEGATIVE khi quá tải, lỗi, khó dùng; POSITIVE khi ổn định, dễ dùng; không rõ -> NEUTRAL."
        ),
        "diem_ren_luyen": (
            "ĐÁNH GIÁ ĐIỂM RÈN LUYỆN. Nếu câu không nhắc DRL, minh chứng, quy trình -> NONE. Mỗi aspect độc lập. NEGATIVE khi khó, không công bằng; POSITIVE khi rõ ràng, công bằng; không rõ -> NEUTRAL."
        ),
    },
}
SUBTOPIC_KW = {
    "giang_vien": {
        "dung_gio": _no_diacritics_set({
            "đi dạy","lên lớp","vào lớp","bắt đầu tiết","kết thúc tiết",
            "giảng viên","giáo viên","thầy giáo","cô giáo","thầy cô",
            "giảng viên đi dạy","giảng viên lên lớp","giảng viên vào lớp",
            "thầy đi dạy","cô đi dạy","thầy lên lớp","cô lên lớp"
        }),
        "cham_diem": _no_diacritics_set({
            "chấm điểm","thang điểm","điểm thi","điểm thành phần","điểm tổng kết","phúc khảo",
            "điểm giữa kỳ","điểm cuối kỳ","điểm nhóm","điểm cá nhân","điểm bonus",
            "điểm chuyên cần","điểm chuyên đề","rubric","grading",
            "giảng viên","giáo viên","thầy giáo","cô giáo",
            "giảng viên chấm điểm","thầy chấm điểm","cô chấm điểm","giáo viên chấm điểm",
            "thầy giáo chấm điểm","cô giáo chấm điểm"
        }),
        "ho_tro": _no_diacritics_set({
            "tư vấn học tập","giải đáp học tập","phản hồi học tập","cvht",
            "cố vấn học tập","hướng dẫn học tập","trao đổi học tập","hỏi đáp học tập",
            "tư vấn sinh viên","giải đáp sinh viên","phản hồi sinh viên",
            "cố vấn sinh viên","hướng dẫn sinh viên",
            "giảng viên","giáo viên","thầy giáo","cô giáo",
            "giảng viên tư vấn","giảng viên hướng dẫn","giảng viên giải đáp",
            "thầy tư vấn","cô tư vấn","thầy hướng dẫn","cô hướng dẫn",
            "thầy giáo tư vấn","cô giáo tư vấn"
        }),
        "thai_do": _no_diacritics_set({
            "thái độ","ứng xử","tác phong","phong thái","giao tiếp","cách nói",
            "ngữ điệu","hành vi","cử chỉ","cách cư xử","thái độ giảng viên",
            "phong cách","tương tác","thái độ lớp","ngôn ngữ cơ thể",
            "giảng viên","giáo viên","thầy giáo","cô giáo",
            "thái độ thầy","thái độ cô","thái độ giáo viên",
            "thầy giáo thái độ","cô giáo thái độ","giảng viên thái độ"
        }),
        "giang_day": _no_diacritics_set({
            "giảng dạy","truyền đạt","diễn đạt","ví dụ","bài giảng","slide","ghi chú",
            "ôn tập","bài học","phương pháp","thực hành","lý thuyết",
            "thảo luận","minh họa","slide giảng","slide bài","giải thích","phong cách giảng",
            "giảng viên","giáo viên","thầy giáo","cô giáo",
            "giảng viên giảng dạy","thầy giảng","cô giảng","giáo viên giảng dạy",
            "thầy giáo giảng dạy","cô giáo giảng dạy"
        }),
    },

    "chuong_trinh": {
        "lich_hoc": _no_diacritics_set({
            "lịch học","thời khóa biểu","thời khoá biểu","kế hoạch học tập","xếp lịch","trùng lịch",
            "đổi lịch","lịch thi","lịch học thêm","ca tối","online","offline","ca sáng",
            "ca chiều","học bù","thi dồn","thi liên tục","xếp ca","thời gian học","lịch kiểm tra"
        }),
        "tin_chi": _no_diacritics_set({
            "tín chỉ","học phần","tiên quyết","song hành","đăng ký học phần","nợ môn",
            "đủ tín","số tín","khối lượng học","điều kiện học phần","mã môn","tải học",
            "phân bổ học phần","lộ trình học","số học phần"
        }),
        "de_cuong": _no_diacritics_set({
            "đề cương","syllabus","giáo trình","tài liệu bắt buộc môn học","tài liệu tham khảo môn học",
            "mục tiêu học phần","kế hoạch môn","outline","kế hoạch giảng dạy","phân bổ điểm",
            "tài liệu học môn học","hướng dẫn môn học","phân phối chương trình","khung điểm môn học","thang đánh giá môn học"
        }),
        "noi_dung": _no_diacritics_set({
            "nội dung","thực tế","thực tiễn","lộ trình","khung chương trình",
            "cập nhật","định hướng nghề","kiến thức","module",
            "chuyên đề","cấu trúc môn","chương trình học","đề mục","môn học","học liệu"
        }),
    },

    "co_so_vat_chat": {
        "mang": _no_diacritics_set({
            "mạng wifi","wifi","wi-fi","wi fi","đăng nhập wifi", "ping wifi","băng thông wifi","wifi trường"
        }),
        "phong_hoc": _no_diacritics_set({
            "phòng học","ánh sáng","đèn phòng học","máy lạnh","điều hòa","điều hoà","quạt",
            "bàn ghế phòng học","ổ điện phòng học","ổ cắm phòng học","cách âm","sàn nhà","rèm cửa","trần nhà","bảng viết"
        }),
        "phong_thi_nghiem": _no_diacritics_set({
            "phòng thí nghiệm","phòng thực hành","lab","phòng lab","máy thực hành",
            "cài phần mềm","thiết bị thí nghiệm","dụng cụ lab","phòng máy","thiết bị lab"
        }),
        "thiet_bi": _no_diacritics_set({
            "máy chiếu","micro","mic","loa","âm thanh","tivi","cáp","hdmi","adapter",
            "thiết bị giảng dạy","máy quay","camera lớp","loa bluetooth","âm lượng",
            "đầu nối","bộ chia","thiết bị phòng học","tv phòng học"
        }),
        "thu_vien": _no_diacritics_set({
            "thư viện","mượn sách","trả sách","tài liệu số thư viện","ebook thư viện","chỗ ngồi thư viện",
            "bàn đọc","yên tĩnh thư viện","giờ mở cửa thư viện","mượn giáo trình","tra cứu sách","wifi thư viện",
            "tra cứu thư viện","kệ sách","tài nguyên số thư viện","khu đọc","mượn tài liệu thư viện","mượn thiết bị thư viện",
            "tài liệu thư viện","tài liệu mượn thư viện","sách thư viện"
        }),
        "giu_xe_ve_sinh": _no_diacritics_set({
            "bãi giữ xe","nhà giữ xe","gửi xe","thẻ xe","quẹt thẻ","phí gửi xe",
            "nhà vệ sinh","toilet","giấy vệ sinh","nước rửa tay",
            "ống nước nhà vệ sinh","cống thoát nhà vệ sinh","sàn nhà vệ sinh","wc nhà vệ sinh"
        }),
        "cong_quan_ly_dao_tao": _no_diacritics_set({
            "trang quản lý đào tạo","cổng đào tạo","hệ thống đào tạo","portal","cổng thông tin",
            "đăng nhập cổng đào tạo","quên mật khẩu","reset mật khẩu","quá tải","treo","tra cứu điểm",
            "web đào tạo","cổng sinh viên","hệ thống online","trang web đào tạo"
        }),
    },

    "khac": {
        "hoc_phi": _no_diacritics_set({
            "học phí","thu thêm","biên lai","miễn giảm","chính sách học phí","công khai học phí",
            "đóng tiền","nộp học phí","thu tiền","hoá đơn học phí","chính sách","phiếu thu","biên nhận",
            "đóng học","nộp lệ phí","phí học","thanh toán học phí","biên lai học phí","phiếu thu học phí"
        }),
        "hoc_bong": _no_diacritics_set({
            "học bổng","học bổng kkht","tiêu chí học bổng","điểm chuẩn học bổng",
            "nộp hồ sơ học bổng","kết quả học bổng","trễ hạn học bổng","xét học bổng",
            "điều kiện học bổng","quỹ học bổng","thông báo học bổng","hồ sơ học bổng","điểm xét"
        }),
        "hanh_chinh": _no_diacritics_set({
            "thủ tục hành chính","hành chính","giấy tờ hành chính","đóng dấu","xác nhận sinh viên","giấy xác nhận",
            "phòng ctsv","tiếp nhận hồ sơ hành chính","trả kết quả hành chính","xin giấy tờ hành chính","nộp hồ sơ hành chính","biểu mẫu hành chính",
            "phòng đào tạo hành chính","chứng nhận hành chính","xác minh hành chính","giấy phép hành chính","bản sao hành chính","văn thư hành chính"
        }),
        "clb": _no_diacritics_set({
            "câu lạc bộ","clb","tuyển thành viên","hoạt động clb","ngoại khóa","sự kiện","workshop",
            "đăng ký clb","đoàn hội","event","team","cuộc thi","hoạt động sv",
            "hoạt động ngoại khoá","nhóm sinh viên","sự kiện trường","đăng ký tham gia"
        }),
        "ktx": _no_diacritics_set({
            "ký túc xá","kí túc xá","ktx","ở ghép","phòng ktx","bảo vệ ktx","giờ giới nghiêm",
            "điện ktx","nước ktx","khu ở ktx","an ninh ktx","phòng chung ktx",
            "toà ktx","khu vực ở ktx","quản lý ktx"
        }),
        "mot_cua": _no_diacritics_set({
            "văn phòng một cửa","vp1c","phòng một cửa","nộp hồ sơ một cửa","số thứ tự","lấy giấy một cửa","trả giấy một cửa","trả kết quả một cửa",
            "hồ sơ một cửa","giấy tờ một cửa","số lượt một cửa","quầy tiếp nhận một cửa","một cửa"
        }),
        "dang_ky_tin": _no_diacritics_set({
            "đăng ký môn","đăng ký tín chỉ","đk tín","đk môn","server đăng ký",
            "xếp lịch tự động","lọc trùng lịch","hệ thống đăng ký",
            "đăng ký online","chọn môn","mở lớp","đóng lớp","sắp lịch","hệ thống đăng ký tín chỉ"
        }),
        "diem_ren_luyen": _no_diacritics_set({
            "điểm rèn luyện","drl","đánh giá rèn luyện","minh chứng drl","chấm drl",
            "minh chứng","điểm rl","bảng drl","đánh giá cá nhân","đánh giá tập thể"
        }),
    },
}

_VI_LETTER = re.compile(r"[A-Za-zÀ-ỹĐđ]")

def _is_garbage(txt: str) -> bool:
    """
    Kiểm tra text có phải garbage (quá ngắn hoặc không phải tiếng Việt) để bỏ qua.
    """
    t = str(txt).strip()
    if len(t) < 4:
        return True
    if len(t.split()) < 2:
        return True
    letters = sum(1 for ch in t if _VI_LETTER.match(ch))
    return (letters / max(1, len(t))) < 0.4

def _aspect_has_kw(aspect_vi: str, s_norm: str) -> bool:
    """Kiểm tra aspect có keyword trong sentence không (chỉ keywords >= 3 ký tự)"""
    for kws in SUBTOPIC_KW.get(aspect_vi, {}).values():
        for kw in kws:
            kw_norm = _norm_match(kw)
            # Chỉ match với keywords >= 3 ký tự để tránh false positive
            if len(kw_norm) >= 3 and kw_norm in s_norm:
                return True
    return False

def _pick_subprompt(aspect: str, sentence: str) -> str:
    s = _norm_match(str(sentence))
    for sub, kws in SUBTOPIC_KW.get(aspect, {}).items():
        # Chỉ match với keywords >= 3 ký tự
        for kw in kws:
            kw_norm = _norm_match(kw)
            if len(kw_norm) >= 3 and kw_norm in s:
                return ASPECT_PROMPTS[aspect].get(sub, ASPECT_PROMPTS[aspect]["_default"])
    return ASPECT_PROMPTS[aspect]["_default"]



def _has_any_kw(s_norm: str) -> bool:
    """Kiểm tra sentence có keyword của bất kỳ aspect nào không"""
    for aspect_vi in ASPECTS_VI:
        if _aspect_has_kw(aspect_vi, s_norm):
            return True
    return False


def get_prompt(aspect_en: str, sentence: str = "", use_subprompt: bool = False) -> str:
    """
    Lấy prompt cho aspect (dùng subprompt nếu cần).
    """
    aspect_vi = ASPECT_REVERSE_MAPPING.get(aspect_en, "khac")
    if use_subprompt and sentence:
        return _pick_subprompt(aspect_vi, sentence)
    aspect_prompts = ASPECT_PROMPTS.get(aspect_vi, {})
    return aspect_prompts.get("_default", "")

