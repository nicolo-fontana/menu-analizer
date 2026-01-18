// Configurazione API
const API_URL = 'http://localhost:8000';
let selectedFile = null;

// Inizializzazione
$(document).ready(function() {
    initializeEventListeners();
});

function initializeEventListeners() {
    // Click su bottone selezione file
    $('#selectFileBtn').on('click', function() {
        $('#fileInput').click();
    });

    // Selezione file
    $('#fileInput').on('change', function(e) {
        handleFileSelect(e.target.files[0]);
    });

    // Drag & Drop
    $('.upload-box').on('dragover', function(e) {
        e.preventDefault();
        $(this).addClass('dragover');
    });

    $('.upload-box').on('dragleave', function() {
        $(this).removeClass('dragover');
    });

    $('.upload-box').on('drop', function(e) {
        e.preventDefault();
        $(this).removeClass('dragover');
        const file = e.originalEvent.dataTransfer.files[0];
        handleFileSelect(file);
    });

    // Click su bottone upload
    $('#uploadBtn').on('click', function() {
        uploadMenu();
    });

    // Click su bottone annulla
    $('#cancelBtn').on('click', function() {
        resetUpload();
    });

    // Click su nuovo upload
    $('#newUploadBtn').on('click', function() {
        resetToUpload();
    });

    // Click su riprova
    $('#retryBtn').on('click', function() {
        resetToUpload();
    });
}

function handleFileSelect(file) {
    if (!file) return;

    // Validazione tipo file
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
        showError('Tipo di file non supportato. Usa PNG o JPG.');
        return;
    }

    // Validazione dimensione (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showError('File troppo grande. Dimensione massima: 10MB');
        return;
    }

    selectedFile = file;

    // Mostra anteprima
    const reader = new FileReader();
    reader.onload = function(e) {
        $('#previewImage').attr('src', e.target.result);
        $('#fileName').text(file.name);
        $('#filePreview').fadeIn();
        $('#selectFileBtn').hide();
    };
    reader.readAsDataURL(file);
}

function resetUpload() {
    selectedFile = null;
    $('#fileInput').val('');
    $('#filePreview').fadeOut(function() {
        $('#selectFileBtn').fadeIn();
    });
}

function resetToUpload() {
    selectedFile = null;
    $('#fileInput').val('');
    $('#filePreview').hide();
    $('#selectFileBtn').show();
    
    $('#loadingSection').hide();
    $('#resultsSection').hide();
    $('#errorSection').hide();
    $('#uploadSection').fadeIn();
}

async function uploadMenu() {
    if (!selectedFile) return;

    // Mostra loading
    $('#uploadSection').hide();
    $('#loadingSection').fadeIn();

    // Prepara FormData
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        // Chiamata API
        const response = await fetch(`${API_URL}/api/process-menu`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Errore durante l\'analisi del menu');
        }

        const result = await response.json();

        // Mostra risultati
        displayResults(result.data);
        
    } catch (error) {
        console.error('Errore:', error);
        showError(error.message || 'Errore di connessione al server');
    }
}

function displayResults(menuData) {
    $('#loadingSection').hide();
    
    // Informazioni menu
    let menuInfoHtml = '<p><strong>Totale piatti:</strong> ' + menuData.piatti.length + '</p>';
    menuInfoHtml += '<p><strong>Totale bevande:</strong> ' + menuData.bevande.length + '</p>';
    if (menuData.prezzo_coperto) {
        menuInfoHtml += '<p><strong>Coperto:</strong> €' + menuData.prezzo_coperto.toFixed(2) + '</p>';
    }
    $('#menuInfo').html(menuInfoHtml);

    // Renderizza piatti
    if (menuData.piatti && menuData.piatti.length > 0) {
        const piattiHtml = menuData.piatti.map(piatto => createPiattoCard(piatto)).join('');
        $('#piattiGrid').html(piattiHtml);
    }

    // Renderizza bevande
    if (menuData.bevande && menuData.bevande.length > 0) {
        $('#bevandeHeader').show();
        const bevandeHtml = menuData.bevande.map(bevanda => createBevandaCard(bevanda)).join('');
        $('#bevandeList').html(bevandeHtml);
    } else {
        $('#bevandeHeader').hide();
        $('#bevandeList').empty();
    }

    // Mostra sezione risultati
    $('#resultsSection').fadeIn();
}

function createPiattoCard(piatto) {
    const imageHtml = piatto.image_url 
        ? `<img src="${piatto.image_url}" alt="${piatto.nome}" onerror="this.parentElement.innerHTML='🍽️'">` 
        : '🍽️';
    
    const descrizioneHtml = piatto.descrizione 
        ? `<p class="piatto-descrizione">${piatto.descrizione}</p>` 
        : '';

    return `
        <div class="piatto-card">
            <div class="piatto-image">
                ${imageHtml}
            </div>
            <div class="piatto-content">
                <span class="piatto-categoria">${piatto.categoria}</span>
                <div class="piatto-header">
                    <h3 class="piatto-nome">${piatto.nome}</h3>
                    <span class="piatto-prezzo">€${piatto.prezzo.toFixed(2)}</span>
                </div>
                ${descrizioneHtml}
            </div>
        </div>
    `;
}

function createBevandaCard(bevanda) {
    const descrizioneHtml = bevanda.descrizione 
        ? `<p class="bevanda-descrizione">${bevanda.descrizione}</p>` 
        : '';

    return `
        <div class="bevanda-card">
            <div class="bevanda-header">
                <span class="bevanda-nome">🥤 ${bevanda.nome}</span>
                <span class="bevanda-prezzo">€${bevanda.prezzo.toFixed(2)}</span>
            </div>
            ${descrizioneHtml}
        </div>
    `;
}

function showError(message) {
    $('#uploadSection').hide();
    $('#loadingSection').hide();
    $('#resultsSection').hide();
    
    $('#errorMessage').text(message);
    $('#errorSection').fadeIn();
}