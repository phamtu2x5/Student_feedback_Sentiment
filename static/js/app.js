// Student Feedback Analysis - Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const feedbackForm = document.getElementById('feedbackForm');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const results = document.getElementById('results');
    const errorMessage = document.getElementById('errorMessage');
    const analyzeBtn = document.getElementById('analyzeBtn');

    // Form submission handler
    feedbackForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const feedbackText = document.getElementById('feedbackText').value.trim();
        
        if (!feedbackText) {
            showError('Vui lòng nhập feedback trước khi phân tích!');
            return;
        }

        // Show loading state
        showLoading();
        
        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: feedbackText })
            });

            const data = await response.json();

            if (response.ok) {
                displayResults(data, feedbackText);
            } else {
                showError(data.error || 'Có lỗi xảy ra khi phân tích feedback!');
            }
        } catch (error) {
            showError('Không thể kết nối đến server. Vui lòng thử lại!');
            console.error('Error:', error);
        } finally {
            hideLoading();
        }
    });

    // Show loading spinner
    function showLoading() {
        loadingSpinner.style.display = 'block';
        results.style.display = 'none';
        errorMessage.style.display = 'none';
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Đang phân tích...';
    }

    // Hide loading spinner
    function hideLoading() {
        loadingSpinner.style.display = 'none';
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-search me-2"></i>Phân Tích Feedback';
    }

    // Display results
    function displayResults(data, originalText) {
        const { sentiment, topic } = data;
        
        // Update sentiment result
        updateSentimentResult(sentiment);
        
        // Update topic result
        updateTopicResult(topic);
        
        // Show original text
        document.getElementById('originalText').textContent = originalText;
        
        // Show results with animation
        results.style.display = 'block';
        results.classList.add('fade-in');
        
        // Scroll to results
        results.scrollIntoView({ behavior: 'smooth' });
    }

    // Update sentiment result
    function updateSentimentResult(sentiment) {
        const sentimentResult = document.getElementById('sentimentResult');
        const sentimentIcon = document.getElementById('sentimentIcon');
        const sentimentDescription = document.getElementById('sentimentDescription');
        
        // Remove existing classes
        sentimentResult.className = 'mb-2';
        sentimentIcon.innerHTML = '';
        
        const sentimentConfig = getSentimentConfig(sentiment);
        
        // Update icon
        sentimentIcon.innerHTML = `<i class="fas ${sentimentConfig.icon} fa-3x ${sentimentConfig.colorClass}"></i>`;
        
        // Update text
        sentimentResult.textContent = sentimentConfig.label;
        sentimentResult.className += ` ${sentimentConfig.colorClass}`;
        
        // Update description
        sentimentDescription.textContent = sentimentConfig.description;
    }

    // Update topic result
    function updateTopicResult(topic) {
        const topicResult = document.getElementById('topicResult');
        const topicIcon = document.getElementById('topicIcon');
        const topicDescription = document.getElementById('topicDescription');
        
        // Remove existing classes
        topicResult.className = 'mb-2';
        topicIcon.innerHTML = '';
        
        const topicConfig = getTopicConfig(topic);
        
        // Update icon
        topicIcon.innerHTML = `<i class="fas ${topicConfig.icon} fa-3x ${topicConfig.colorClass}"></i>`;
        
        // Update text
        topicResult.textContent = topicConfig.label;
        topicResult.className += ` ${topicConfig.colorClass}`;
        
        // Update description
        topicDescription.textContent = topicConfig.description;
    }

    // Get sentiment configuration
    function getSentimentConfig(sentiment) {
        const configs = {
            'positive': {
                icon: 'fa-smile',
                label: 'Tích Cực',
                colorClass: 'sentiment-positive',
                description: 'Feedback thể hiện thái độ tích cực và hài lòng'
            },
            'neutral': {
                icon: 'fa-meh',
                label: 'Trung Tính',
                colorClass: 'sentiment-neutral',
                description: 'Feedback thể hiện thái độ trung lập, không rõ ràng'
            },
            'negative': {
                icon: 'fa-frown',
                label: 'Tiêu Cực',
                colorClass: 'sentiment-negative',
                description: 'Feedback thể hiện thái độ tiêu cực và không hài lòng'
            }
        };
        
        return configs[sentiment] || configs['neutral'];
    }

    // Get topic configuration
    function getTopicConfig(topic) {
        const configs = {
            'lecturer': {
                icon: 'fa-user-tie',
                label: 'Giảng Viên',
                colorClass: 'topic-lecturer',
                description: 'Feedback liên quan đến chất lượng giảng dạy của giảng viên'
            },
            'training_program': {
                icon: 'fa-graduation-cap',
                label: 'Chương Trình Đào Tạo',
                colorClass: 'topic-training_program',
                description: 'Feedback về nội dung và cấu trúc chương trình học'
            },
            'facility': {
                icon: 'fa-building',
                label: 'Cơ Sở Vật Chất',
                colorClass: 'topic-facility',
                description: 'Feedback về phòng học, thiết bị và cơ sở hạ tầng'
            },
            'others': {
                icon: 'fa-ellipsis-h',
                label: 'Khác',
                colorClass: 'topic-others',
                description: 'Feedback về các chủ đề khác không thuộc các danh mục trên'
            }
        };
        
        return configs[topic] || configs['others'];
    }

    // Show error message
    function showError(message) {
        document.getElementById('errorText').textContent = message;
        errorMessage.style.display = 'block';
        errorMessage.classList.add('fade-in');
        
        // Hide results if showing
        results.style.display = 'none';
        
        // Scroll to error
        errorMessage.scrollIntoView({ behavior: 'smooth' });
    }

    // Clear form function
    function clearForm() {
        document.getElementById('feedbackText').value = '';
        results.style.display = 'none';
        errorMessage.style.display = 'none';
        
        // Reset character counter
        const charCount = document.getElementById('charCount');
        if (charCount) {
            charCount.textContent = '0';
        }
        
        // Reset counter color
        const charCounter = document.querySelector('.form-text');
        if (charCounter) {
            charCounter.style.color = '#6c757d';
        }
    }

    // Add clear button functionality
    const clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.className = 'btn btn-outline-secondary mt-2';
    clearBtn.innerHTML = '<i class="fas fa-trash me-2"></i>Xóa Form';
    clearBtn.onclick = clearForm;
    
    feedbackForm.appendChild(clearBtn);

    // Add example feedbacks
    const exampleBtn = document.createElement('button');
    exampleBtn.type = 'button';
    exampleBtn.className = 'btn btn-outline-info mt-2 ms-2';
    exampleBtn.innerHTML = '<i class="fas fa-lightbulb me-2"></i>Ví Dụ';
    exampleBtn.onclick = showExamples;
    
    feedbackForm.appendChild(exampleBtn);

    // Show example feedbacks
    function showExamples() {
        const examples = [
            "Giảng viên giảng bài rất hay và dễ hiểu, sinh viên rất thích",
            "Phòng học quá nóng và không có điều hòa, rất khó chịu",
            "Chương trình học quá khó và không phù hợp với sinh viên",
            "Cơ sở vật chất rất hiện đại và đầy đủ tiện nghi",
            "Thầy cô rất nhiệt tình và hỗ trợ sinh viên học tập tốt"
        ];
        
        const randomExample = examples[Math.floor(Math.random() * examples.length)];
        document.getElementById('feedbackText').value = randomExample;
        
        // Trigger input event to update character counter
        const textarea = document.getElementById('feedbackText');
        textarea.dispatchEvent(new Event('input'));
        
        // Scroll to form
        feedbackForm.scrollIntoView({ behavior: 'smooth' });
    }

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl + Enter to submit form
        if (e.ctrlKey && e.key === 'Enter') {
            feedbackForm.dispatchEvent(new Event('submit'));
        }
        
        // Escape to clear form
        if (e.key === 'Escape') {
            clearForm();
        }
    });

    // Add character counter
    const textarea = document.getElementById('feedbackText');
    const charCounter = document.createElement('small');
    charCounter.className = 'form-text text-muted';
    charCounter.innerHTML = '<i class="fas fa-info-circle me-1"></i>Độ dài: <span id="charCount">0</span> ký tự';
    
    textarea.parentNode.appendChild(charCounter);
    
    textarea.addEventListener('input', function() {
        const count = this.value.length;
        document.getElementById('charCount').textContent = count;
        
        // Change color based on length
        if (count > 500) {
            charCounter.style.color = '#dc3545';
        } else if (count > 300) {
            charCounter.style.color = '#ffc107';
        } else {
            charCounter.style.color = '#6c757d';
        }
    });
});
