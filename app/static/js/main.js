// File Upload & Drag-and-Drop Logic

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileInfo = document.getElementById('file-info');
const fileNameText = document.getElementById('file-name-text');
const columnSelection = document.getElementById('column-selection');
const csvMode = document.getElementById('csv-mode');
const excelMode = document.getElementById('excel-mode');
const previewTable = document.getElementById('preview-table');
const emailColumnSelect = document.getElementById('email-column-select');
const emailColumnText = document.getElementById('email-column-text');
const nameColumnSelect = document.getElementById('name-column-select');
const dobColumnSelect = document.getElementById('dob-column-select');

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
        fileNameText.textContent = `Selected: ${file.name}`;
        fileInfo.style.display = 'flex';
        columnSelection.style.display = 'block';

        if (file.name.endsWith('.csv')) {
            csvMode.style.display = 'block';
            excelMode.style.display = 'none';
            // Enable CSV inputs, disable Excel text
            emailColumnSelect.required = true;
            emailColumnText.required = false;
            emailColumnText.value = '';

            parseCSV(file);
        } else {
            // Excel or other: Show Manual Input
            csvMode.style.display = 'none';
            excelMode.style.display = 'block';
            // Disable CSV inputs, enable Excel text
            emailColumnSelect.required = false;
            emailColumnText.required = true;

            // Clear previous values
            emailColumnSelect.value = '';
            nameColumnSelect.value = '';
            dobColumnSelect.value = '';
        }
    }
}

function clearFileSelection() {
    fileInput.value = '';
    fileInfo.style.display = 'none';
    columnSelection.style.display = 'none';
    csvMode.style.display = 'none';
    excelMode.style.display = 'none';
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
    // Auto-fill Email input
    const emailHeader = headers.find(h => h.toLowerCase().includes('email'));
    if (emailHeader) {
        emailColumnSelect.value = emailHeader;
    }

    // Auto-fill Name input (optional)
    const nameHeader = headers.find(h => h.toLowerCase().includes('name'));
    if (nameHeader) {
        nameColumnSelect.value = nameHeader;
    }

    // Auto-fill DOB input (optional)
    const dobHeader = headers.find(h => {
        const lower = h.toLowerCase();
        return lower.includes('dob') || lower.includes('birth') || lower.includes('birthday');
    });
    if (dobHeader) {
        dobColumnSelect.value = dobHeader;
    }

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
