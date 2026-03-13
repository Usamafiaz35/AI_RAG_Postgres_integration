// Financial RAG System Frontend JavaScript
// Handles API communication and UI interactions

class FinancialRAGSystem {
    constructor() {
        this.apiUrl = 'http://127.0.0.1:8000';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkApiConnection();
    }

    setupEventListeners() {
        // Submit button
        const submitBtn = document.getElementById('submitBtn');
        const queryInput = document.getElementById('queryInput');
        
        submitBtn.addEventListener('click', () => this.submitQuery());
        
        // Enter key support
        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.submitQuery();
            }
        });

        // Sample query chips
        const queryChips = document.querySelectorAll('.query-chip');
        queryChips.forEach(chip => {
            chip.addEventListener('click', () => {
                const query = chip.getAttribute('data-query');
                queryInput.value = query;
                this.submitQuery();
            });
        });

        // Auto-resize textarea
        queryInput.addEventListener('input', () => {
            queryInput.style.height = 'auto';
            queryInput.style.height = queryInput.scrollHeight + 'px';
        });
    }

    async checkApiConnection() {
        try {
            const response = await fetch(`${this.apiUrl}/docs`);
            if (response.ok) {
                console.log('API connection successful');
                this.updateConnectionStatus(true);
            } else {
                throw new Error('API not responding');
            }
        } catch (error) {
            console.warn('API connection failed:', error);
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(isConnected) {
        const header = document.querySelector('.header-content p');
        if (isConnected) {
            header.innerHTML = 'Ask questions about your financial data in natural language <span style="color: #28a745;">●</span>';
        } else {
            header.innerHTML = 'Ask questions about your financial data in natural language <span style="color: #dc3545;">●</span>';
            header.innerHTML += '<br><small style="color: #dc3545;">⚠️ Backend not connected. Please start the server.</small>';
        }
    }

    async submitQuery() {
        const queryInput = document.getElementById('queryInput');
        const query = queryInput.value.trim();

        if (!query) {
            this.showError('Please enter a question.');
            return;
        }

        // Show loading state
        this.showLoading();
        
        try {
            const response = await this.callAPI(query);
            
            if (response.ok) {
                this.showResults(response);
            } else {
                this.showError(response.error || 'An error occurred while processing your request.');
            }
        } catch (error) {
            console.error('API Error:', error);
            this.showError('Failed to connect to the server. Please check if the backend is running.');
        }
    }

    async callAPI(query) {
        const response = await fetch(`${this.apiUrl}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    showLoading() {
        this.hideAllSections();
        const loadingSection = document.getElementById('loadingSection');
        loadingSection.style.display = 'block';
        loadingSection.classList.add('fade-in');
    }

    showResults(response) {
        this.hideAllSections();
        
        const resultsSection = document.getElementById('resultsSection');
        const resultContent = document.getElementById('resultContent');
        
        // Build results HTML
        let html = `
            <div class="result-answer">
                <strong>Answer:</strong> ${response.answer}
            </div>
        `;

        // Add SQL query if available
        if (response.sql) {
            html += `
                <div class="result-sql-header">Generated SQL Query</div>
                <div class="result-sql">${this.formatSQL(response.sql)}</div>
            `;
        }

        // Add data table if available
        if (response.rows && response.rows.length > 0) {
            html += this.buildDataTable(response.rows);
        }

        resultContent.innerHTML = html;
        resultsSection.style.display = 'block';
        resultsSection.classList.add('slide-up');
    }

    showError(message) {
        this.hideAllSections();
        
        const errorSection = document.getElementById('errorSection');
        const errorMessage = document.getElementById('errorMessage');
        
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
        errorSection.classList.add('fade-in');
    }

    hideAllSections() {
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('loadingSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
    }

    formatSQL(sql) {
        // Basic SQL formatting
        return sql
            .replace(/\bSELECT\b/gi, '<span style="color: #3498db;">SELECT</span>')
            .replace(/\bFROM\b/gi, '<span style="color: #3498db;">FROM</span>')
            .replace(/\bWHERE\b/gi, '<span style="color: #3498db;">WHERE</span>')
            .replace(/\bAND\b/gi, '<span style="color: #3498db;">AND</span>')
            .replace(/\bOR\b/gi, '<span style="color: #3498db;">OR</span>')
            .replace(/\bORDER BY\b/gi, '<span style="color: #3498db;">ORDER BY</span>')
            .replace(/\bGROUP BY\b/gi, '<span style="color: #3498db;">GROUP BY</span>')
            .replace(/\bCOUNT\b/gi, '<span style="color: #e74c3c;">COUNT</span>')
            .replace(/\bSUM\b/gi, '<span style="color: #e74c3c;">SUM</span>')
            .replace(/\bAVG\b/gi, '<span style="color: #e74c3c;">AVG</span>')
            .replace(/\bMAX\b/gi, '<span style="color: #e74c3c;">MAX</span>')
            .replace(/\bMIN\b/gi, '<span style="color: #e74c3c;">MIN</span>');
    }

    buildDataTable(rows) {
        if (!rows || rows.length === 0) return '';

        const headers = Object.keys(rows[0]);
        
        let html = `
            <div class="result-data">
                <table class="result-table">
                    <thead>
                        <tr>
                            ${headers.map(header => `<th>${this.formatHeader(header)}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
        `;

        rows.forEach(row => {
            html += '<tr>';
            headers.forEach(header => {
                const value = row[header];
                html += `<td>${this.formatCellValue(value)}</td>`;
            });
            html += '</tr>';
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        return html;
    }

    formatHeader(header) {
        return header
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    formatCellValue(value) {
        if (value === null || value === undefined) {
            return '<em>N/A</em>';
        }
        
        // Format numbers with commas
        if (typeof value === 'number') {
            return value.toLocaleString();
        }
        
        // Format dates
        if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value)) {
            return new Date(value).toLocaleDateString();
        }
        
        return value;
    }
}

// Modal functions
function showAbout() {
    document.getElementById('aboutModal').style.display = 'flex';
}

function closeAbout() {
    document.getElementById('aboutModal').style.display = 'none';
}

function hideError() {
    document.getElementById('errorSection').style.display = 'none';
}

// Close modal when clicking outside
window.addEventListener('click', (event) => {
    const modal = document.getElementById('aboutModal');
    if (event.target === modal) {
        closeAbout();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (event) => {
    // Escape key to close modal
    if (event.key === 'Escape') {
        closeAbout();
        hideError();
    }
});

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FinancialRAGSystem();
    
    // Add some nice animations on load
    document.querySelector('.main-content').classList.add('fade-in');
    
    // Focus on input field
    setTimeout(() => {
        document.getElementById('queryInput').focus();
    }, 500);
});

// Service Worker registration for PWA capabilities (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
