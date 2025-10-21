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
    
    // Initialize time filter
    initTimeFilter();
    
    // Initialize analysis mode toggle
    initAnalysisModeToggle();
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
        // Get filter parameters
        const filterParams = getTimeFilterParams();
        const queryParams = new URLSearchParams({
            page: page,
            per_page: itemsPerPage,
            ...filterParams
        });
        
        const response = await fetch(`/api/feedback-history?${queryParams.toString()}`);
        const data = await response.json();
        if (response.ok) {
            displayFeedbackHistory(data.feedbacks);
            displayPagination(data, page);
            updateFeedbackCount(data.total);
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
        const date = feedback.created_at; // Thời gian đã được format từ server
        html += `
            <div class="card mb-3 border-start border-4 border-${getSentimentColor(feedback.sentiment)}">
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-12">
                            <p class="card-text">${feedback.text}</p>
                            <small class="text-muted">
                                <i class="fas fa-clock me-1"></i>${date}
                            </small>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-6">
                            <div class="d-flex align-items-center">
                                <span class="badge bg-${getSentimentColor(feedback.sentiment)} me-2">
                                    <i class="fas ${sentimentConfig.icon} me-1"></i>
                                    ${sentimentConfig.label}
                                </span>
                                <small class="text-muted">Tin cậy: ${(feedback.sentiment_confidence * 100).toFixed(1)}%</small>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="d-flex align-items-center">
                                <span class="badge bg-secondary me-2">
                                    <i class="fas ${topicConfig.icon} me-1"></i>
                                    ${topicConfig.label}
                                </span>
                                <small class="text-muted">Tin cậy: ${(feedback.topic_confidence * 100).toFixed(1)}%</small>
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
    
    // Giới hạn hiển thị tối đa 5 trang
    const maxPages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
    let endPage = Math.min(data.pages, startPage + maxPages - 1);
    
    // Điều chỉnh nếu gần cuối danh sách
    if (endPage - startPage + 1 < maxPages) {
        startPage = Math.max(1, endPage - maxPages + 1);
    }
    
    let html = '<nav><ul class="pagination pagination-sm">';
    if (data.has_prev) {
        html += `<li class="page-item">
                   <a class="page-link" href="javascript:void(0)" onclick="loadFeedbackHistory(${currentPage - 1}, true); return false;">Trước</a>
                 </li>`;
    }
    
    // Hiển thị dấu "..." nếu cần
    if (startPage > 1) {
        html += `<li class="page-item">
                   <a class="page-link" href="javascript:void(0)" onclick="loadFeedbackHistory(1, true); return false;">1</a>
                 </li>`;
        if (startPage > 2) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const active = i === currentPage ? 'active' : '';
        html += `<li class="page-item ${active}">
                   <a class="page-link" href="javascript:void(0)" onclick="loadFeedbackHistory(${i}, true); return false;">${i}</a>
                 </li>`;
    }
    
    // Hiển thị dấu "..." nếu cần
    if (endPage < data.pages) {
        if (endPage < data.pages - 1) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
        html += `<li class="page-item">
                   <a class="page-link" href="javascript:void(0)" onclick="loadFeedbackHistory(${data.pages}, true); return false;">${data.pages}</a>
                 </li>`;
    }
    
    if (data.has_next) {
        html += `<li class="page-item">
                   <a class="page-link" href="javascript:void(0)" onclick="loadFeedbackHistory(${currentPage + 1}, true); return false;">Sau</a>
                 </li>`;
    }
    html += '</ul></nav>';
    
    // Thêm phần nhập số trang cụ thể
    html += `
        <div class="d-flex align-items-center justify-content-center" style="margin-left: 20px; margin-top: -3px;">
            <span class="me-2 text-muted" style="font-size: 0.875rem; line-height: 2.2;">Đến:</span>
            <input type="number" id="pageInput" class="form-control form-control-sm me-2" 
                   style="width: 80px; height: 38px; font-size: 0.875rem; text-align: center; line-height: 1;" min="1" max="${data.pages}" value="${currentPage}">
            <button class="btn btn-outline-secondary btn-sm" onclick="goToPage()" style="height: 38px; width: 38px; padding: 0; display: flex; align-items: center; justify-content: center;">
                <i class="fas fa-arrow-right" style="font-size: 0.875rem;"></i>
            </button>
        </div>
    `;
    
    historyPagination.innerHTML = html;
}

function goToPage() {
    const pageInput = document.getElementById('pageInput');
    const page = parseInt(pageInput.value);
    
    // Lấy tổng số trang từ pagination data
    const paginationNav = document.querySelector('.pagination');
    if (!paginationNav) return;
    
    // Tìm số trang lớn nhất từ pagination
    const pageLinks = paginationNav.querySelectorAll('.page-link');
    let maxPage = 1;
    pageLinks.forEach(link => {
        const pageNum = parseInt(link.textContent);
        if (!isNaN(pageNum) && pageNum > maxPage) {
            maxPage = pageNum;
        }
    });
    
    if (page && page > 0 && page <= maxPage) {
        loadFeedbackHistory(page, true);
    } else if (page > maxPage) {
        showAlert(`Trang tối đa là ${maxPage}`, 'warning');
        pageInput.value = maxPage; // Reset về trang tối đa
    } else {
        showAlert('Vui lòng nhập số trang hợp lệ', 'warning');
    }
}

// Thêm event listener cho Enter key
document.addEventListener('keypress', function(e) {
    if (e.target.id === 'pageInput' && e.key === 'Enter') {
        goToPage();
    }
});

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

// Time Filter Functions
function initTimeFilter() {
    const timeFilterInputs = document.querySelectorAll('input[name="timeFilter"]');
    const customDateRange = document.getElementById('customDateRange');
    const filterInfo = document.getElementById('filterInfo');
    
    // Set default end date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('endDate').value = today;
    
    // Ensure date picker is hidden by default
    customDateRange.style.setProperty('display', 'none', 'important');
    
    timeFilterInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.value === 'custom') {
                customDateRange.style.setProperty('display', 'flex', 'important');
                updateFilterInfo();
            } else {
                customDateRange.style.setProperty('display', 'none', 'important');
                updateFilterInfo();
                loadFeedbackHistory(1, true); // Reload with new filter
            }
        });
    });
    
    // Date change handlers
    document.getElementById('startDate').addEventListener('change', function() {
        if (document.querySelector('input[name="timeFilter"]:checked').value === 'custom') {
            updateFilterInfo();
            loadFeedbackHistory(1, true);
        }
    });
    
    document.getElementById('endDate').addEventListener('change', function() {
        if (document.querySelector('input[name="timeFilter"]:checked').value === 'custom') {
            updateFilterInfo();
            loadFeedbackHistory(1, true);
        }
    });
}

function updateFilterInfo() {
    const selectedFilter = document.querySelector('input[name="timeFilter"]:checked');
    const filterInfo = document.getElementById('filterInfo');
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    let infoText = '';
    switch(selectedFilter.value) {
        case 'all':
            infoText = 'Hiển thị tất cả feedback';
            break;
        case 'today':
            infoText = 'Hiển thị feedback trong ngày hôm nay';
            break;
        case 'week':
            infoText = 'Hiển thị feedback trong 7 ngày qua';
            break;
        case 'month':
            infoText = 'Hiển thị feedback trong 30 ngày qua';
            break;
        case 'custom':
            if (startDate && endDate) {
                const start = new Date(startDate).toLocaleDateString('vi-VN');
                const end = new Date(endDate).toLocaleDateString('vi-VN');
                infoText = `Hiển thị feedback từ ${start} đến ${end}`;
            } else {
                infoText = 'Vui lòng chọn khoảng thời gian';
            }
            break;
    }
    filterInfo.textContent = infoText;
}

function getTimeFilterParams() {
    const selectedFilter = document.querySelector('input[name="timeFilter"]:checked');
    const params = {
        time_filter: selectedFilter.value
    };
    
    if (selectedFilter.value === 'custom') {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (startDate) params.start_date = startDate;
        if (endDate) params.end_date = endDate;
    }
    
    return params;
}

function updateFeedbackCount(total) {
    const feedbackCount = document.getElementById('feedbackCount');
    if (feedbackCount) {
        feedbackCount.textContent = total;
        
        // Cập nhật màu sắc badge dựa trên số lượng - sử dụng màu tối để dễ nhìn
        feedbackCount.className = 'badge bg-dark text-white ms-2 rounded-pill px-3 py-1';
        if (total === 0) {
            feedbackCount.className = 'badge bg-secondary text-white ms-2 rounded-pill px-3 py-1';
        } else if (total < 5) {
            feedbackCount.className = 'badge bg-dark text-white ms-2 rounded-pill px-3 py-1';
        } else if (total < 20) {
            feedbackCount.className = 'badge bg-dark text-white ms-2 rounded-pill px-3 py-1';
        } else {
            feedbackCount.className = 'badge bg-dark text-white ms-2 rounded-pill px-3 py-1';
        }
    }
}

// ===== CSV Analysis Functions =====
function initAnalysisModeToggle() {
    const singleModeInput = document.getElementById('singleMode');
    const csvModeInput = document.getElementById('csvMode');
    const singleForm = document.getElementById('singleFeedbackForm');
    const csvForm = document.getElementById('csvUploadForm');
    
    // Show single form by default
    singleForm.style.display = 'block';
    csvForm.style.display = 'none';
    
    singleModeInput.addEventListener('change', function() {
        if (this.checked) {
            singleForm.style.display = 'block';
            csvForm.style.display = 'none';
        }
    });
    
    csvModeInput.addEventListener('change', function() {
        if (this.checked) {
            singleForm.style.display = 'none';
            csvForm.style.display = 'block';
        }
    });
    
    // Handle CSV form submission
    document.getElementById('csvForm').addEventListener('submit', handleCsvUpload);
    
    // Handle CSV template download
    document.getElementById('downloadTemplate').addEventListener('click', downloadCsvTemplate);
}

async function handleCsvUpload(event) {
    event.preventDefault();
    
    const csvFile = document.getElementById('csvFile').files[0];
    const analyzeBtn = document.getElementById('analyzeCsvBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const results = document.getElementById('results');
    
    if (!csvFile) {
        showAlert('Vui lòng chọn file CSV', 'warning');
        return;
    }
    
    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (csvFile.size > maxSize) {
        showAlert('File quá lớn. Kích thước tối đa là 10MB.', 'danger');
        return;
    }
    
    // Validate file type
    if (!csvFile.name.toLowerCase().endsWith('.csv')) {
        showAlert('Vui lòng chọn file có định dạng .csv', 'danger');
        return;
    }
    
    // Show loading
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Đang phân tích...';
    loadingSpinner.style.display = 'block';
    results.style.display = 'none';
    
    const formData = new FormData();
    formData.append('csvFile', csvFile);
    
    try {
        const response = await fetch('/analyze-csv', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showCsvResults(data);
            showAlert(data.message, 'success');
            // Reload feedback history with small delay to ensure database is updated
            setTimeout(() => {
                loadFeedbackHistory(1, true);
            }, 500);
        } else {
            showAlert(data.error || 'Có lỗi xảy ra khi xử lý file CSV', 'danger');
        }
    } catch (error) {
        console.error('CSV upload error:', error);
        showAlert('Có lỗi xảy ra khi upload file CSV', 'danger');
    } finally {
        // Hide loading and clear CSV file
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-chart-bar me-2"></i>Phân Tích File CSV';
        loadingSpinner.style.display = 'none';
        
        // Clear CSV file in all cases (success or error)
        document.getElementById('csvFile').value = '';
    }
}

function showCsvResults(data) {
    const results = document.getElementById('results');
    
    let html = `
        <div class="card shadow-lg mb-3">
            <div class="card-header bg-secondary text-white">
                <h4 class="card-title mb-0">
                    <i class="fas fa-check-circle me-2"></i>
                    Kết quả phân tích CSV
                </h4>
            </div>
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-md-4">
                        <div class="text-center">
                            <h5 class="text-success">${data.processed_count}</h5>
                            <small class="text-muted">Thành công</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center">
                            <h5 class="text-danger">${data.error_count}</h5>
                            <small class="text-muted">Lỗi</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center">
                            <h5 class="text-secondary">${data.total_rows}</h5>
                            <small class="text-muted">Tổng cộng</small>
                        </div>
                    </div>
                </div>
                
                <div class="table-responsive">
                    <table class="table table-sm" id="csvResultsTable">
                        <thead>
                            <tr>
                                <th>Dòng</th>
                                <th>Feedback</th>
                                <th>Sentiment</th>
                                <th>Topic</th>
                                <th>Tin cậy</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    // Chỉ hiển thị 10 dòng đầu tiên
    const displayResults = data.results.slice(0, 10);
    
    displayResults.forEach(result => {
        if (result.success) {
            const sentimentConfig = getSentimentConfig(result.sentiment);
            const topicConfig = getTopicConfig(result.topic);
            
            html += `
                <tr>
                    <td>${result.row}</td>
                    <td>${result.text}</td>
                    <td>
                        <span class="badge bg-${getSentimentColor(result.sentiment)}">
                            <i class="fas fa-${sentimentConfig.icon} me-1"></i>
                            ${sentimentConfig.label}
                        </span>
                    </td>
                    <td>
                        <span class="badge bg-secondary">
                            <i class="fas fa-${topicConfig.icon} me-1"></i>
                            ${topicConfig.label}
                        </span>
                    </td>
                    <td>
                        <small class="text-muted">
                            S: ${result.sentiment_confidence}%<br>
                            T: ${result.topic_confidence}%
                        </small>
                    </td>
                </tr>
            `;
        } else {
            html += `
                <tr class="table-danger">
                    <td>${result.row}</td>
                    <td>${result.text}</td>
                    <td colspan="3">
                        <small class="text-danger">
                            <i class="fas fa-exclamation-triangle me-1"></i>
                            ${result.error}
                        </small>
                    </td>
                </tr>
            `;
        }
    });
    
    html += `
        </tbody>
    </table>
</div>
</div>

${data.total_rows > 10 ? `
    <div class="alert alert-info mb-0 d-flex align-items-center custom-alert-left">
        <i class="fas fa-info-circle me-2"></i>
        Chỉ hiển thị 10 dòng đầu tiên trong tổng số ${data.total_rows} dòng
    </div>
` : ''}
`;





    
    results.innerHTML = html;
    results.style.display = 'block';
    
    // Scroll to results with better positioning
    setTimeout(() => {
        // Điều chỉnh vị trí cuộn dựa trên số dòng
        const blockPosition = data.total_rows > 10 ? 'start' : 'center';
        results.scrollIntoView({ behavior: 'smooth', block: blockPosition });
    }, 100);
}

function downloadCsvTemplate(event) {
    event.preventDefault();
    
    const csvContent = `feedback
"Giảng viên rất nhiệt tình và giảng bài dễ hiểu"
"Chương trình học có nhiều kiến thức bổ ích"
"Cơ sở vật chất hiện đại và tiện nghi"
"Thời gian học hợp lý và không quá căng thẳng"
"Tài liệu học tập đầy đủ và chất lượng"`;
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', 'feedback_template.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}
