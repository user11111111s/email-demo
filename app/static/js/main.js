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
            // Enable select, disable text
            emailColumnSelect.required = true;
            emailColumnText.required = false;
            emailColumnText.value = '';

            parseCSV(file);
        } else {
            // Excel or other: Show Manual Input
            csvMode.style.display = 'none';
            excelMode.style.display = 'block';
            // Disable select, enable text
            emailColumnSelect.required = false;
            emailColumnText.required = true;

            // Clear previous select options if any? Not strictly necessary but good cleanup
            emailColumnSelect.innerHTML = '';
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
