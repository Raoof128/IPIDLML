/**
 * IPI-Shield Dashboard JavaScript
 * Handles API interactions and UI updates
 */

const API_BASE = '';

// DOM Elements
const contentInput = document.getElementById('content-input');
const contentType = document.getElementById('content-type');
const sanitizationMode = document.getElementById('sanitization-mode');
const analyzeBtn = document.getElementById('analyze-btn');
const promptInput = document.getElementById('prompt-input');
const proxyBtn = document.getElementById('proxy-btn');

// Score displays
const riskScoreEl = document.getElementById('risk-score');
const safetyScoreEl = document.getElementById('safety-score');
const riskCategoryEl = document.getElementById('risk-category');
const actionBadgeEl = document.getElementById('recommended-action');
const flaggedSegmentsEl = document.getElementById('flagged-segments');
const sanitizedOutputEl = document.getElementById('sanitized-output');
const proxyResponseEl = document.getElementById('proxy-response');

/**
 * Analyze content for prompt injection
 */
async function analyzeContent() {
    const content = contentInput.value.trim();
    if (!content) {
        showNotification('Please enter content to analyze', 'warning');
        return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';

    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: content,
                content_type: contentType.value
            })
        });

        if (!response.ok) throw new Error('Analysis failed');

        const result = await response.json();
        updateScores(result);
        updateFlaggedSegments(result.flagged_segments);
        updateDetectionBreakdown(result.detection_breakdown);

        // Also run sanitization
        await sanitizeContent(content);

    } catch (error) {
        console.error('Analysis error:', error);
        showNotification('Analysis failed. Please try again.', 'error');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Content';
    }
}

/**
 * Sanitize content
 */
async function sanitizeContent(content) {
    try {
        const response = await fetch(`${API_BASE}/sanitize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: content,
                mode: sanitizationMode.value
            })
        });

        if (!response.ok) throw new Error('Sanitization failed');

        const result = await response.json();
        updateSanitizedOutput(result);

    } catch (error) {
        console.error('Sanitization error:', error);
    }
}

/**
 * Test LLM proxy
 */
async function testProxy() {
    const prompt = promptInput.value.trim();
    if (!prompt) {
        showNotification('Please enter a prompt', 'warning');
        return;
    }

    proxyBtn.disabled = true;
    proxyBtn.textContent = 'Processing...';

    try {
        const response = await fetch(`${API_BASE}/proxy_llm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: prompt,
                sanitization_mode: sanitizationMode.value
            })
        });

        if (!response.ok) throw new Error('Proxy request failed');

        const result = await response.json();
        updateProxyResponse(result);

    } catch (error) {
        console.error('Proxy error:', error);
        showNotification('Proxy request failed', 'error');
    } finally {
        proxyBtn.disabled = false;
        proxyBtn.textContent = 'Send Through Proxy';
    }
}

/**
 * Update score displays
 */
function updateScores(result) {
    const riskScore = result.injection_score;
    const safetyScore = result.safety_score;

    // Update risk score circle
    const riskValue = riskScoreEl.querySelector('.score-value');
    riskValue.textContent = Math.round(riskScore);
    riskScoreEl.style.background = `conic-gradient(${getScoreColor(riskScore)} ${riskScore}%, var(--bg-secondary) ${riskScore}%)`;

    // Update safety score circle
    const safetyValue = safetyScoreEl.querySelector('.score-value');
    safetyValue.textContent = Math.round(safetyScore);
    safetyScoreEl.style.background = `conic-gradient(${getScoreColor(100 - safetyScore)} ${100 - safetyScore}%, var(--bg-secondary) ${100 - safetyScore}%)`;

    // Update category and action
    riskCategoryEl.textContent = result.risk_category;
    riskCategoryEl.style.color = getCategoryColor(result.risk_category);

    actionBadgeEl.textContent = result.recommended_action;
    actionBadgeEl.style.background = getActionColor(result.recommended_action);
}

/**
 * Update flagged segments display
 */
function updateFlaggedSegments(segments) {
    if (!segments || segments.length === 0) {
        flaggedSegmentsEl.innerHTML = '<div class="empty-state">No suspicious patterns detected ✓</div>';
        return;
    }

    flaggedSegmentsEl.innerHTML = segments.map(seg => `
        <div class="flagged-item ${getSeverityClass(seg.confidence)}">
            <div class="flagged-text">"${escapeHtml(seg.text)}"</div>
            <div class="flagged-meta">
                <span>📍 Pattern: ${seg.pattern_type}</span>
                <span>⚡ Confidence: ${(seg.confidence * 100).toFixed(0)}%</span>
                <span>💡 ${seg.reason}</span>
            </div>
        </div>
    `).join('');
}

/**
 * Update detection breakdown bars
 */
function updateDetectionBreakdown(breakdown) {
    if (!breakdown) return;

    const container = document.getElementById('detection-breakdown');
    const items = container.querySelectorAll('.bar-item');

    const scores = [
        breakdown.pattern_score || 0,
        breakdown.bert_score || 0,
        breakdown.embedding_score || 0,
        breakdown.anomaly_score || 0
    ];

    items.forEach((item, index) => {
        const fill = item.querySelector('.bar-fill');
        const value = item.querySelector('.bar-value');
        fill.style.width = `${scores[index]}%`;
        value.textContent = `${Math.round(scores[index])}%`;
    });
}

/**
 * Update sanitized output display
 */
function updateSanitizedOutput(result) {
    let content = result.sanitized_content;

    // Highlight filtered segments
    content = content.replace(/\[FILTERED[^\]]*\]/g, '<span class="filtered">$&</span>');
    content = content.replace(/\[BLOCKED\]/g, '<span class="filtered">$&</span>');

    sanitizedOutputEl.innerHTML = `
        <div style="margin-bottom: 12px; color: var(--text-muted); font-size: 12px;">
            Mode: ${result.mode} | Segments Modified: ${result.segments_modified} | 
            Risk: ${result.original_risk_score?.toFixed(1) || '?'} → ${result.post_sanitization_risk_score?.toFixed(1) || '?'}
        </div>
        <div>${content}</div>
    `;
}

/**
 * Update proxy response display
 */
function updateProxyResponse(result) {
    proxyResponseEl.innerHTML = `
        <div style="margin-bottom: 16px;">
            <span style="color: ${result.injection_detected ? 'var(--danger)' : 'var(--success)'}">
                ${result.injection_detected ? '⚠️ Injection Detected' : '✅ Clean'}
            </span>
            <span style="margin-left: 16px; color: var(--text-muted);">
                Risk: ${result.injection_score?.toFixed(1) || 0}/100 | Action: ${result.sanitization_action}
            </span>
        </div>
        ${result.was_sanitized ? `
            <div style="background: var(--bg-card); padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                <div style="color: var(--warning); font-size: 12px; margin-bottom: 8px;">Original:</div>
                <div style="font-size: 13px;">${escapeHtml(result.original_prompt)}</div>
            </div>
            <div style="background: var(--bg-card); padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                <div style="color: var(--success); font-size: 12px; margin-bottom: 8px;">Sanitized:</div>
                <div style="font-size: 13px;">${escapeHtml(result.sanitized_prompt)}</div>
            </div>
        ` : ''}
        <div style="background: var(--bg-card); padding: 16px; border-radius: 8px; border-left: 3px solid var(--accent-primary);">
            <div style="color: var(--accent-secondary); font-size: 12px; margin-bottom: 8px;">LLM Response:</div>
            <div style="white-space: pre-wrap;">${escapeHtml(result.llm_response)}</div>
        </div>
        <div style="margin-top: 12px; font-size: 11px; color: var(--text-muted);">
            Compliance: ${result.compliance_tags?.join(', ') || 'N/A'}
        </div>
    `;
}

// Helper functions
function getScoreColor(score) {
    if (score >= 80) return 'var(--critical)';
    if (score >= 60) return 'var(--danger)';
    if (score >= 40) return 'var(--warning)';
    return 'var(--success)';
}

function getCategoryColor(category) {
    const colors = {
        'Critical': 'var(--critical)',
        'High': 'var(--danger)',
        'Medium': 'var(--warning)',
        'Low': 'var(--success)'
    };
    return colors[category] || 'var(--text-primary)';
}

function getActionColor(action) {
    const colors = {
        'BLOCK': 'rgba(220, 38, 38, 0.3)',
        'PASS_WITH_WARNINGS': 'rgba(245, 158, 11, 0.3)',
        'PASS': 'rgba(16, 185, 129, 0.3)'
    };
    return colors[action] || 'var(--bg-secondary)';
}

function getSeverityClass(confidence) {
    if (confidence >= 0.8) return 'critical';
    if (confidence >= 0.6) return 'medium';
    return 'low';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Could be enhanced with toast notifications
}

// Event Listeners
analyzeBtn.addEventListener('click', analyzeContent);
proxyBtn.addEventListener('click', testProxy);

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        if (document.activeElement === contentInput) {
            analyzeContent();
        } else if (document.activeElement === promptInput) {
            testProxy();
        }
    }
});

// Initialize
console.log('🛡️ IPI-Shield Dashboard loaded');
