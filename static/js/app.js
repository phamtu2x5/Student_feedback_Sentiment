// Student Feedback Analysis - Optimized JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const elements = {
        form: document.getElementById('feedbackForm'),
        textarea: document.getElementById('feedbackText'),
        loadingSpinner: document.getElementById('loadingSpinner'),
        results: document.getElementById('results'),
        errorMessage: document.getElementById('errorMessage'),
        analyzeBtn: document.getElementById('analyzeBtn'),
        originalText: document.getElementById('originalText'),
        errorText: document.getElementById('errorText'),
        sentimentResult: document.getElementById('sentimentResult'),
        sentimentIcon: document.getElementById('sentimentIcon'),
        sentimentDescription: document.getElementById('sentimentDescription'),
        topicResult: document.getElementById('topicResult'),
        topicIcon: document.getElementById('topicIcon'),
        topicDescription: document.getElementById('topicDescription')
    };

    // Configuration Objects
    const sentimentConfigs = {
        positive: {
            icon: 'fa-smile',
            label: 'Tích Cực',
            colorClass: 'sentiment-positive',
            description: 'Feedback thể hiện thái độ tích cực và hài lòng'
        },
        neutral: {
            icon: 'fa-meh',
            label: 'Trung Tính',
            colorClass: 'sentiment-neutral',
            description: 'Feedback thể hiện thái độ trung lập, không rõ ràng'
        },
        negative: {
            icon: 'fa-frown',
            label: 'Tiêu Cực',
            colorClass: 'sentiment-negative',
            description: 'Feedback thể hiện thái độ tiêu cực và không hài lòng'
        }
    };

    const topicConfigs = {
        lecturer: {
            icon: 'fa-user-tie',
            label: 'Giảng Viên',
            colorClass: 'topic-lecturer',
            description: 'Feedback liên quan đến chất lượng giảng dạy của giảng viên'
        },
        training_program: {
            icon: 'fa-graduation-cap',
            label: 'Chương Trình Đào Tạo',
            colorClass: 'topic-training_program',
            description: 'Feedback về nội dung và cấu trúc chương trình học'
        },
        facility: {
            icon: 'fa-building',
            label: 'Cơ Sở Vật Chất',
            colorClass: 'topic-facility',
            description: 'Feedback về phòng học, thiết bị và cơ sở hạ tầng'
        },
        others: {
            icon: 'fa-ellipsis-h',
            label: 'Khác',
            colorClass: 'topic-others',
            description: 'Feedback về các chủ đề khác không thuộc các danh mục trên'
        }
    };

    const examples = [
        "Giảng viên giảng bài rất hay và dễ hiểu, sinh viên rất thích",
        "Thầy cô rất nhiệt tình và hỗ trợ sinh viên học tập tốt",
        "Giảng viên có kiến thức sâu rộng và phương pháp dạy hiệu quả",
        "Thầy cô rất tận tâm và luôn sẵn sàng giải đáp thắc mắc",
        "Phong cách giảng dạy của giảng viên rất thu hút và dễ hiểu",
        "Chương trình học rất phù hợp và bổ ích cho sinh viên",
        "Nội dung môn học rất thực tế và có tính ứng dụng cao",
        "Cấu trúc chương trình học rất logic và dễ theo dõi",
        "Môn học này giúp sinh viên phát triển kỹ năng tốt",
        "Chương trình đào tạo rất toàn diện và chất lượng",
        "Cơ sở vật chất rất hiện đại và đầy đủ tiện nghi",
        "Phòng học rộng rãi, thoáng mát và có đầy đủ thiết bị",
        "Thư viện rất đẹp và có nhiều tài liệu hữu ích",
        "Khuôn viên trường rất đẹp và môi trường học tập tốt",
        "Phòng thực hành được trang bị đầy đủ và hiện đại",
        "Giảng viên giảng bài quá nhanh và khó hiểu",
        "Thầy cô không nhiệt tình và ít quan tâm đến sinh viên",
        "Phương pháp dạy của giảng viên rất nhàm chán",
        "Giảng viên không sẵn sàng giải đáp thắc mắc của sinh viên",
        "Thầy cô có thái độ không tốt với sinh viên",
        "Chương trình học quá khó và không phù hợp với sinh viên",
        "Nội dung môn học quá lý thuyết và thiếu thực hành",
        "Cấu trúc chương trình rối rắm và khó theo dõi",
        "Môn học này không có tính ứng dụng thực tế",
        "Chương trình đào tạo quá nặng và áp lực",
        "Phòng học quá nóng và không có điều hòa, rất khó chịu",
        "Cơ sở vật chất cũ kỹ và thiếu thiết bị cần thiết",
        "Thư viện quá nhỏ và thiếu chỗ ngồi",
        "Khuôn viên trường không được bảo trì tốt",
        "Phòng thực hành thiếu thiết bị và không đảm bảo an toàn",
        "Môn học này có nội dung bình thường, không có gì đặc biệt",
        "Giảng viên dạy ổn, không có gì nổi bật",
        "Chương trình học có thể chấp nhận được"
    ];

    // Utility Functions
    const utils = {
        showLoading() {
            elements.loadingSpinner.style.display = 'block';
            elements.results.style.display = 'none';
            elements.errorMessage.style.display = 'none';
            elements.analyzeBtn.disabled = true;
            elements.analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Đang phân tích...';
        },

        hideLoading() {
            elements.loadingSpinner.style.display = 'none';
            elements.analyzeBtn.disabled = false;
            elements.analyzeBtn.innerHTML = '<i class="fas fa-search me-2"></i>Phân Tích Feedback';
        },

        showError(message) {
            elements.errorText.textContent = message;
            elements.errorMessage.style.display = 'block';
            elements.errorMessage.classList.add('fade-in');
            elements.results.style.display = 'none';
            elements.errorMessage.scrollIntoView({ behavior: 'smooth' });
        },

        clearForm() {
            elements.textarea.value = '';
            elements.results.style.display = 'none';
            elements.errorMessage.style.display = 'none';
            
            const charCount = document.getElementById('charCount');
            const charCounter = document.querySelector('.form-text');
            
            if (charCount) charCount.textContent = '0';
            if (charCounter) charCounter.style.color = '#6c757d';
        },

        updateResult(type, value) {
            const configs = type === 'sentiment' ? sentimentConfigs : topicConfigs;
            const config = configs[value] || configs[type === 'sentiment' ? 'neutral' : 'others'];
            
            const resultEl = elements[`${type}Result`];
            const iconEl = elements[`${type}Icon`];
            const descEl = elements[`${type}Description`];
            
            resultEl.className = `mb-2 ${config.colorClass}`;
            iconEl.innerHTML = `<i class="fas ${config.icon} fa-3x ${config.colorClass}"></i>`;
            resultEl.textContent = config.label;
            descEl.textContent = config.description;
        },

        scrollToResults() {
            setTimeout(() => {
                const resultsRect = elements.results.getBoundingClientRect();
                const windowHeight = window.innerHeight;
                const scrollOffset = window.scrollY + resultsRect.top - (windowHeight * 0.1);
                
                window.scrollTo({
                    top: Math.max(0, scrollOffset),
                    behavior: 'smooth'
                });
            }, 100);
        },

        updateCharCounter() {
            const count = elements.textarea.value.length;
            const charCount = document.getElementById('charCount');
            const charCounter = document.querySelector('.form-text');
            
            if (charCount) charCount.textContent = count;
            if (charCounter) {
                charCounter.style.color = count > 500 ? '#dc3545' : 
                                        count > 300 ? '#ffc107' : '#6c757d';
            }
        }
    };

    // Main Functions
    async function handleFormSubmit(e) {
        e.preventDefault();
        
        const feedbackText = elements.textarea.value.trim();
        
        if (!feedbackText) {
            utils.showError('Vui lòng nhập feedback trước khi phân tích!');
            return;
        }

        utils.showLoading();
        
        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: feedbackText })
            });

            const data = await response.json();

            if (response.ok) {
                utils.updateResult('sentiment', data.sentiment);
                utils.updateResult('topic', data.topic);
                elements.originalText.textContent = feedbackText;
                elements.results.style.display = 'block';
                elements.results.classList.add('fade-in');
                utils.scrollToResults();
            } else {
                utils.showError(data.error || 'Có lỗi xảy ra khi phân tích feedback!');
            }
        } catch (error) {
            utils.showError('Không thể kết nối đến server. Vui lòng thử lại!');
            console.error('Error:', error);
        } finally {
            utils.hideLoading();
        }
    }

    function showExamples() {
        const randomExample = examples[Math.floor(Math.random() * examples.length)];
        elements.textarea.value = randomExample;
        elements.textarea.dispatchEvent(new Event('input'));
        elements.form.scrollIntoView({ behavior: 'smooth' });
    }

    // Event Listeners
    elements.form.addEventListener('submit', handleFormSubmit);
    elements.textarea.addEventListener('input', utils.updateCharCounter);

    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            elements.form.dispatchEvent(new Event('submit'));
        } else if (e.key === 'Escape') {
            utils.clearForm();
        }
    });

    // Dynamic Button Creation
    function createButton(text, icon, className, onClick) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = className;
        btn.innerHTML = `<i class="fas ${icon} me-2"></i>${text}`;
        btn.onclick = onClick;
        return btn;
    }

    // Add buttons container
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'd-flex justify-content-center gap-2 mt-3';
    
    buttonContainer.appendChild(createButton('Xóa Form', 'fa-trash', 'btn btn-outline-secondary', utils.clearForm));
    buttonContainer.appendChild(createButton('Ví Dụ', 'fa-lightbulb', 'btn btn-outline-info', showExamples));
    
    elements.form.appendChild(buttonContainer);

    // Add character counter
    const charCounter = document.createElement('small');
    charCounter.className = 'form-text text-muted';
    charCounter.innerHTML = '<i class="fas fa-info-circle me-1"></i>Độ dài: <span id="charCount">0</span> ký tự';
    elements.textarea.parentNode.appendChild(charCounter);
});