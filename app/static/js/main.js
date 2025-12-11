// File Upload & Drag-and-Drop Logic

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileNameDisplay = document.getElementById('file-name');
const csvPreview = document.getElementById('csv-preview');
const previewTable = document.getElementById('preview-table');
const emailColumnSelect = document.getElementById('email-column-select');

if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(fileInput);
        }
    });
}

function handleFileSelect(input) {
    const file = input.files[0];
    if (file) {
        fileNameDisplay.textContent = `Selected: ${file.name}`;

        // Simple CSV parse for preview using PapaParse (added in template)
        if (file.name.endsWith('.csv')) {
            parseCSV(file);
        } else {
            // Excel is harder to parse client-side without big libraries.
            // For now, just show the name.
            fileNameDisplay.textContent += " (Preview not available for .xlsx, please ensure 'Email' column exists)";
            csvPreview.style.display = 'none';
        }
    }
}

function parseCSV(file) {
    Papa.parse(file, {
        preview: 5, // Only first 5 lines
        header: true,
        complete: function (results) {
            console.log(results);
            if (results.data && results.data.length > 0) {
                renderPreview(results.data, results.meta.fields);
            }
        }
    });
}

function renderPreview(data, headers) {
    csvPreview.style.display = 'block';

    // Populate Select
    emailColumnSelect.innerHTML = '';
    headers.forEach(header => {
        const option = document.createElement('option');
        option.value = header;
        option.textContent = header;
        // Auto-select if contains "email"
        if (header.toLowerCase().includes('email')) {
            option.selected = true;
        }
        emailColumnSelect.appendChild(option);
    });

    // Populate Table
    let tableHtml = '<thead><tr>';
    headers.forEach(h => tableHtml += `<th style="padding: 0.5rem; border: 1px solid var(--border); background: var(--glass);">${h}</th>`);
    tableHtml += '</tr></thead><tbody>';

    data.forEach(row => {
        tableHtml += '<tr>';
        headers.forEach(h => {
            tableHtml += `<td style="padding: 0.5rem; border: 1px solid var(--border);">${row[h] || ''}</td>`;
        });
        tableHtml += '</tr>';
    });
    tableHtml += '</tbody>';

    previewTable.innerHTML = tableHtml;
}
