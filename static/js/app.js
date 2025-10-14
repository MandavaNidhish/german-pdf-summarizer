// Enhanced Frontend JavaScript for PDF Parsing Application
// Fixed timing issues, improved error handling, and better user experience

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('searchForm');
    const downloadBtn = document.getElementById('downloadBtn');
    const companyInput = document.getElementById('companyName');
    let latestFilename = '';
    let isProcessing = false;

    // Form submit handler with improved error handling
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (isProcessing) {
            showError('Ein Verarbeitungsvorgang läuft bereits. Bitte warten...');
            return;
        }

        clearError();
        clearResults();

        if (!validateInput()) return;

        const companyName = companyInput.value.trim();

        try {
            isProcessing = true;
            setButtonLoading(true);
            showStatusSection('Suche nach Unternehmen wird gestartet...');

            // Add longer timeout for processing
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes

            const response = await fetch('/api/process-company', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ company: companyName }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP Error: ${response.status}`);
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Unbekannter Fehler aufgetreten');
            }

            latestFilename = result.filename;

            // Update UI with results
            updateStatusSection('Verarbeitung erfolgreich abgeschlossen!');
            populateCompanyInfo(result);
            populateSummary(result);
            populateStatistics(result);
            showResultsSection();

        } catch (error) {
            console.error('Processing error:', error);

            if (error.name === 'AbortError') {
                showError('Die Verarbeitung dauerte zu lange und wurde abgebrochen. Bitte versuchen Sie es erneut.');
            } else if (error.message.includes('Failed to fetch')) {
                showError('Verbindungsfehler. Bitte überprüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.');
            } else {
                showError(error.message || 'Ein unerwarteter Fehler ist aufgetreten');
            }

            updateStatusSection('Verarbeitung fehlgeschlagen', false);

        } finally {
            isProcessing = false;
            setButtonLoading(false);
        }
    });

    // Download button handler
    downloadBtn.addEventListener('click', () => {
        if (!latestFilename) {
            showError('Keine Datei zum Download verfügbar');
            return;
        }

        try {
            window.location.href = `/download/${latestFilename}`;
        } catch (error) {
            showError('Download fehlgeschlagen. Bitte versuchen Sie es erneut.');
        }
    });

    // Input validation with real-time feedback
    companyInput.addEventListener('input', (e) => {
        const value = e.target.value.trim();
        const submitBtn = document.getElementById('searchBtn');

        if (value.length >= 3) {
            submitBtn.disabled = false;
            companyInput.classList.remove('error');
        } else {
            submitBtn.disabled = true;
            if (value.length > 0) {
                companyInput.classList.add('error');
            }
        }
    });

    function validateInput() {
        const input = companyInput.value.trim();

        if (!input) {
            showError('Bitte geben Sie einen Firmennamen ein.');
            companyInput.focus();
            return false;
        }

        if (input.length < 3) {
            showError('Firmennamen müssen mindestens 3 Zeichen lang sein.');
            companyInput.focus();
            return false;
        }

        if (input.length > 200) {
            showError('Firmennamen dürfen maximal 200 Zeichen lang sein.');
            companyInput.focus();
            return false;
        }

        // Check for suspicious characters
        const suspiciousPattern = /[<>"\'{}]/;
        if (suspiciousPattern.test(input)) {
            showError('Firmennamen dürfen keine Sonderzeichen wie <, >, ", \', { oder } enthalten.');
            companyInput.focus();
            return false;
        }

        return true;
    }

    function showError(message) {
        const errorElement = document.getElementById('errorMessage');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.add('show');

            // Auto-hide error after 10 seconds
            setTimeout(() => {
                clearError();
            }, 10000);
        }

        // Also log to console for debugging
        console.error('User Error:', message);
    }

    function clearError() {
        const errorElement = document.getElementById('errorMessage');
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.classList.remove('show');
        }
    }

    function clearResults() {
        const resultsSection = document.getElementById('resultsSection');
        const statusSection = document.getElementById('statusSection');

        if (resultsSection) {
            resultsSection.style.display = 'none';
        }

        if (statusSection) {
            statusSection.style.display = 'none';
        }
    }

    function setButtonLoading(isLoading) {
        const btn = document.getElementById('searchBtn');
        const btnText = btn.querySelector('.btn-text');
        const btnIcon = btn.querySelector('.btn-icon');

        btn.disabled = isLoading;

        if (isLoading) {
            btn.classList.add('loading');
            btnText.textContent = 'Verarbeitung läuft...';
            if (btnIcon) {
                btnIcon.innerHTML = '⏳';
            }
        } else {
            btn.classList.remove('loading');
            btnText.textContent = 'Suchen & Verarbeiten';
            if (btnIcon) {
                btnIcon.innerHTML = '🔍';
            }
        }
    }

    function showStatusSection(message) {
        const statusSection = document.getElementById('statusSection');
        const statusList = document.getElementById('statusList');

        if (statusSection && statusList) {
            statusList.innerHTML = `<li class="status-item processing">
                <span class="status-icon">⏳</span>
                <span class="status-text">${message}</span>
            </li>`;
            statusSection.style.display = 'block';
        }
    }

    function updateStatusSection(message, success = true) {
        const statusList = document.getElementById('statusList');

        if (statusList) {
            const icon = success ? '✅' : '❌';
            const className = success ? 'completed' : 'failed';

            statusList.innerHTML = `<li class="status-item ${className}">
                <span class="status-icon">${icon}</span>
                <span class="status-text">${message}</span>
            </li>`;
        }
    }

    function populateCompanyInfo(result) {
        // Company name
        const companyNameEl = document.getElementById('companyName_result');
        if (companyNameEl) {
            companyNameEl.textContent = result.company_name || 'Unbekannt';
        }

        // File info
        const fileSizeEl = document.getElementById('fileSize');
        const fileNameEl = document.getElementById('fileName');

        if (fileSizeEl) {
            fileSizeEl.textContent = result.file_size || 'Unbekannt';
        }

        if (fileNameEl) {
            fileNameEl.textContent = result.filename || 'Unbekannt';
        }

        // Download button
        if (downloadBtn && result.filename) {
            downloadBtn.style.display = 'inline-block';
        }
    }

    function populateSummary(result) {
        const summaryEl = document.getElementById('summaryContent');

        if (summaryEl && result.summary) {
            // Format the summary with proper line breaks
            const formattedSummary = result.summary
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>');

            summaryEl.innerHTML = `<p>${formattedSummary}</p>`;
        }

        // Additional extracted info
        if (result.extracted_info) {
            populateExtractedInfo(result.extracted_info);
        }
    }

    function populateExtractedInfo(extractedInfo) {
        const container = document.getElementById('extractedInfo');
        if (!container) return;

        let html = '<h3>Extrahierte Informationen</h3><ul>';

        if (extractedInfo.organization) {
            html += `<li><strong>Organisation:</strong> ${extractedInfo.organization}</li>`;
        }

        if (extractedInfo.reference_number) {
            html += `<li><strong>Referenznummer:</strong> ${extractedInfo.reference_number}</li>`;
        }

        if (extractedInfo.location) {
            html += `<li><strong>Ort:</strong> ${extractedInfo.location}</li>`;
        }

        if (extractedInfo.important_dates) {
            html += `<li><strong>Wichtige Daten:</strong> ${extractedInfo.important_dates.join(', ')}</li>`;
        }

        if (extractedInfo.persons) {
            html += `<li><strong>Personen:</strong> ${extractedInfo.persons.join(', ')}</li>`;
        }

        html += '</ul>';
        container.innerHTML = html;
    }

    function populateStatistics(result) {
        const stats = result.processing_stats || {};

        // Processing time
        const timeEl = document.getElementById('processingTime');
        if (timeEl) {
            timeEl.textContent = `${stats.total_time || 0} Sekunden`;
        }

        // Quality score
        const qualityEl = document.getElementById('qualityScore');
        if (qualityEl) {
            const score = stats.quality_score || 0;
            qualityEl.textContent = `${score}%`;
            qualityEl.className = score >= 80 ? 'high-quality' : score >= 60 ? 'medium-quality' : 'low-quality';
        }

        // Word count
        const wordCountEl = document.getElementById('wordCount');
        if (wordCountEl) {
            wordCountEl.textContent = `${stats.word_count || 0} Wörter`;
        }

        // Extraction method
        const methodEl = document.getElementById('extractionMethod');
        if (methodEl) {
            methodEl.textContent = stats.extraction_method || 'Unbekannt';
        }
    }

    function showResultsSection() {
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'block';
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
    }

    // Initialize form state
    const submitBtn = document.getElementById('searchBtn');
    if (submitBtn && companyInput.value.trim().length < 3) {
        submitBtn.disabled = true;
    }

    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+Enter to submit form
        if (e.ctrlKey && e.key === 'Enter' && !isProcessing) {
            e.preventDefault();
            searchForm.dispatchEvent(new Event('submit'));
        }

        // Escape to clear error
        if (e.key === 'Escape') {
            clearError();
        }
    });

    console.log('PDF Parsing Frontend initialized successfully');
});
