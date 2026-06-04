const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileNameDisplay = document.getElementById('file-name');
const outputNameInput = document.getElementById('output-name-input');
const convertBtn = document.getElementById('convert-btn');
const progressBar = document.getElementById('progress-bar');
const progressFill = document.getElementById('progress-fill');
const statusDiv = document.getElementById('status');
const openFolderBtn = document.getElementById('open-folder-btn');
const supportLink = document.getElementById('support-link');

let selectedFile = null;

// Click on drop zone triggers file selection
dropZone.addEventListener('click', () => fileInput.click());

// Drag-and-drop events
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
    if (files.length) handleFile(files[0]);
});

// File input change (when using the browse dialog)
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleFile(e.target.files[0]);
});

function handleFile(file) {
    selectedFile = file;
    fileNameDisplay.textContent = file.name;

    // Set output name to the file name without extension
    const stem = file.name.replace(/\.[^/.]+$/, "");
    outputNameInput.value = stem;
    outputNameInput.disabled = false;
    convertBtn.disabled = false;
    statusDiv.textContent = '';
    openFolderBtn.classList.add('hidden');
}

// Convert button
convertBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    convertBtn.disabled = true;
    progressBar.classList.remove('hidden');
    progressFill.style.width = '0%';
    statusDiv.textContent = 'Converting...';

    // Read the file as base64
    const reader = new FileReader();
    reader.onload = async function() {
        const b64 = reader.result.split(',')[1];  // remove "data:...;base64,"

        try {
            // Animate progress while waiting
            let progress = 0;
            const interval = setInterval(() => {
                progress = Math.min(progress + Math.random() * 20, 90);
                progressFill.style.width = progress + '%';
            }, 300);

            // Call the Python function exposed by Eel
            const result = await eel.convert_file(
                b64,
                selectedFile.name,
                outputNameInput.value.trim()
            )();

            clearInterval(interval);

            if (result.success) {
                progressFill.style.width = '100%';
                statusDiv.textContent = '✅ ' + result.message;
                // Save the PDF path for the "Open Folder" button
                window.lastPdfPath = result.file_path;
                openFolderBtn.classList.remove('hidden');
                supportLink.classList.remove('hidden');
              
            } else {
                statusDiv.textContent = '❌ ' + result.message;
                progressFill.style.width = '0%';
            }
        } catch (err) {
            statusDiv.textContent = '❌ Error: ' + err.message;
            progressFill.style.width = '0%';
        } finally {
            convertBtn.disabled = false;
            setTimeout(() => progressBar.classList.add('hidden'), 1000);
        }
    };
    reader.readAsDataURL(selectedFile);
});

// Open the folder containing the converted PDF
function openFolder() {
    if (window.lastPdfPath) {
        eel.open_file_explorer(window.lastPdfPath);
    }
}

