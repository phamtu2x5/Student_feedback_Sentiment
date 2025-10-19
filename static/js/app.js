// Student Feedback Analysis - Optimized JavaScript

// ===== Global Utilities =====
const Utils = {
    // Smooth scrolling with automatic offset calculation
    scrollToSection(el, extraOffset = 0) {
        if (!el) return;
        const fixed = document.querySelector('.navbar.fixed-top, header.sticky-top, .sticky-top, .fixed-top');
        const base = fixed ? Math.max(0, fixed.getBoundingClientRect().height + 8) : 56;
        const offset = Math.max(0, base + extraOffset);
        const rect = el.getBoundingClientRect();
        const top = window.pageYOffset + rect.top - offset;
        window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
    },

    // Auto-hide alerts functionality
    initAutoHideAlerts() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                alert.classList.add('fade-out');
                setTimeout(() => alert.remove(), 500);
            }, 2000);
        });
    }
};

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
        positive: { icon: 'fa-smile', label: 'Tích Cực', colorClass: 'sentiment-positive', description: 'Feedback thể hiện thái độ tích cực và hài lòng' },
        neutral:  { icon: 'fa-meh',   label: 'Trung Tính', colorClass: 'sentiment-neutral',  description: 'Feedback thể hiện thái độ trung lập, không rõ ràng' },
        negative: { icon: 'fa-frown', label: 'Tiêu Cực',  colorClass: 'sentiment-negative', description: 'Feedback thể hiện thái độ tiêu cực và không hài lòng' }
    };

    const topicConfigs = {
        lecturer:         { icon: 'fa-user-tie',       label: 'Giảng Viên',           colorClass: 'topic-lecturer',         description: 'Feedback liên quan đến chất lượng giảng dạy của giảng viên' },
        training_program: { icon: 'fa-graduation-cap', label: 'Chương Trình Đào Tạo', colorClass: 'topic-training_program', description: 'Feedback về nội dung và cấu trúc chương trình học' },
        facility:         { icon: 'fa-building',       label: 'Cơ Sở Vật Chất',       colorClass: 'topic-facility',         description: 'Feedback về phòng học, thiết bị và cơ sở hạ tầng' },
        others:           { icon: 'fa-ellipsis-h',     label: 'Khác',                  colorClass: 'topic-others',           description: 'Feedback về các chủ đề khác không thuộc các danh mục trên' }
    };

    const examples = [
        "Giảng viên giảng bài rất hay và dễ hiểu, sinh viên rất thích",
        "Thầy cô rất nhiệt tình và hỗ trợ sinh viên học tập tốt",
        "Chương trình học rất phù hợp và bổ ích cho sinh viên",
        "Cơ sở vật chất rất hiện đại và đầy đủ tiện nghi",
        "Giảng viên giảng bài quá nhanh và khó hiểu",
        "Chương trình học quá khó và không phù hợp với sinh viên",
        "Phòng học quá nóng và không có điều hòa, rất khó chịu",
        "Môn học này có nội dung bình thường, không có gì đặc biệt"
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
            this.updateCharCounter();
            
            // Cuộn lên form giống như khi nhấn "Ví Dụ"
            const formElement = elements.form;
            const formRect = formElement.getBoundingClientRect();
            const scrollTop = window.pageYOffset + formRect.top - 120; // Cùng vị trí như "Ví Dụ"
            
            window.scrollTo({
                top: scrollTop,
                behavior: 'smooth'
            });
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
            Utils.scrollToSection(elements.results, 105);
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
                
                // Clear the textarea after successful analysis
                elements.textarea.value = '';
                utils.updateCharCounter();
                
                // Reload feedback history after successful analysis
                loadFeedbackHistory(1);
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
        
        // Cuộn trực tiếp với vị trí cao hơn
        const formElement = elements.form;
        const formRect = formElement.getBoundingClientRect();
        const scrollTop = window.pageYOffset + formRect.top - 120; // Tăng lên 120px để cuộn cao hơn
        
        window.scrollTo({
            top: scrollTop,
            behavior: 'smooth'
        });
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

    // Add utility buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'd-flex justify-content-center gap-2 mt-3';
    const clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.className = 'btn btn-outline-secondary';
    clearBtn.innerHTML = '<i class="fas fa-trash me-2"></i>Xóa Form';
    clearBtn.onclick = () => utils.clearForm();
    const exampleBtn = document.createElement('button');
    exampleBtn.type = 'button';
    exampleBtn.className = 'btn btn-outline-info';
    exampleBtn.innerHTML = '<i class="fas fa-lightbulb me-2"></i>Ví Dụ';
    exampleBtn.onclick = showExamples;
    buttonContainer.appendChild(clearBtn);
    buttonContainer.appendChild(exampleBtn);
    elements.form.appendChild(buttonContainer);

    // Add character counter
    const charCounter = document.createElement('small');
    charCounter.className = 'form-text text-muted';
    charCounter.innerHTML = '<i class="fas fa-info-circle me-1"></i>Độ dài: <span id="charCount">0</span> ký tự';
    elements.textarea.parentNode.appendChild(charCounter);

    // Load feedback history
    loadFeedbackHistory();
    
    // Initialize auto-hide alerts
    Utils.initAutoHideAlerts();
});

// ===== Feedback History Functions =====
let currentPage = 1;
const itemsPerPage = 5;

async function loadFeedbackHistory(page = 1, shouldScroll = false) {
    const historyLoading = document.getElementById('historyLoading');
    const historyContent = document.getElementById('historyContent');
    const historyPagination = document.getElementById('historyPagination');
    const feedbackHistorySection = document.getElementById('feedbackHistory');

    historyLoading.style.display = 'block';
    historyContent.style.opacity = '0.5';
    historyPagination.style.opacity = '0.5';
    try {
        const response = await fetch(`/api/feedback-history?page=${page}&per_page=${itemsPerPage}`);
        const data = await response.json();
        if (response.ok) {
            displayFeedbackHistory(data.feedbacks);
            displayPagination(data, page);
            if (shouldScroll && feedbackHistorySection) {
                // Pagination cuộn thấp xuống một chút
                Utils.scrollToSection(feedbackHistorySection, -40);
            }
        } else {
            historyContent.innerHTML = '<p class="text-muted text-center">Không thể tải lịch sử feedback.</p>';
        }
    } catch (error) {
        console.error('Error loading feedback history:', error);
        historyContent.innerHTML = '<p class="text-muted text-center">Có lỗi xảy ra khi tải lịch sử.</p>';
    } finally {
        historyLoading.style.display = 'none';
        historyContent.style.opacity = '1';
        historyPagination.style.opacity = '1';
        currentPage = page;
    }
}

function displayFeedbackHistory(feedbacks) {
    const historyContent = document.getElementById('historyContent');
    if (!feedbacks || feedbacks.length === 0) {
        historyContent.innerHTML = '<p class="text-muted text-center">Chưa có feedback nào. Hãy phân tích feedback đầu tiên!</p>';
        return;
    }
    let html = '';
    feedbacks.forEach(feedback => {
        const sentimentConfig = getSentimentConfig(feedback.sentiment);
        const topicConfig = getTopicConfig(feedback.topic);
        const date = new Date(feedback.created_at).toLocaleString('vi-VN');
        html += `
            <div class="card mb-3 border-start border-4 border-${getSentimentColor(feedback.sentiment)}">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-8">
                            <p class="card-text">${feedback.text}</p>
                            <small class="text-muted">
                                <i class="fas fa-clock me-1"></i>${date}
                            </small>
                        </div>
                        <div class="col-md-4 text-end">
                            <div class="mb-2">
                                <span class="badge bg-${getSentimentColor(feedback.sentiment)} me-2">
                                    <i class="fas ${sentimentConfig.icon} me-1"></i>
                                    ${sentimentConfig.label}
                                </span>
                                <span class="badge bg-secondary">
                                    <i class="fas ${topicConfig.icon} me-1"></i>
                                    ${topicConfig.label}
                                </span>
                            </div>
                            <div class="small text-muted">
                                <div>Tin cậy: ${(feedback.sentiment_confidence * 100).toFixed(1)}%</div>
                                <div>Chủ đề: ${(feedback.topic_confidence * 100).toFixed(1)}%</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    historyContent.innerHTML = html;
}

function displayPagination(data, currentPage) {
    const historyPagination = document.getElementById('historyPagination');
    if (!data || data.pages <= 1) {
        historyPagination.innerHTML = '';
        return;
    }
    let html = '<nav><ul class="pagination pagination-sm">';
    if (data.has_prev) {
        html += `<li class="page-item">
                   <a class="page-link" href="javascript:void(0)" onclick="loadFeedbackHistory(${currentPage - 1}, true); return false;">Trước</a>
                 </li>`;
    }
    for (let i = 1; i <= data.pages; i++) {
        const active = i === currentPage ? 'active' : '';
        html += `<li class="page-item ${active}">
                   <a class="page-link" href="javascript:void(0)" onclick="loadFeedbackHistory(${i}, true); return false;">${i}</a>
                 </li>`;
    }
    if (data.has_next) {
        html += `<li class="page-item">
                   <a class="page-link" href="javascript:void(0)" onclick="loadFeedbackHistory(${currentPage + 1}, true); return false;">Sau</a>
                 </li>`;
    }
    html += '</ul></nav>';
    historyPagination.innerHTML = html;
}

function getSentimentConfig(sentiment) {
    const configs = {
        positive: { icon: 'fa-smile', label: 'Tích Cực' },
        neutral:  { icon: 'fa-meh',   label: 'Trung Tính' },
        negative: { icon: 'fa-frown', label: 'Tiêu Cực' }
    };
    return configs[sentiment] || configs.neutral;
}

function getTopicConfig(topic) {
    const configs = {
        lecturer: { icon: 'fa-user-tie',       label: 'Giảng Viên' },
        training_program: { icon: 'fa-graduation-cap', label: 'Chương Trình' },
        facility: { icon: 'fa-building',       label: 'Cơ Sở Vật Chất' },
        others:   { icon: 'fa-ellipsis-h',     label: 'Khác' }
    };
    return configs[topic] || configs.others;
}

function getSentimentColor(sentiment) {
    const colors = { positive: 'success', neutral: 'warning', negative: 'danger' };
    return colors[sentiment] || 'secondary';
}
