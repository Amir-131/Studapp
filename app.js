document.addEventListener('DOMContentLoaded', function() {
    const contentContainer = document.getElementById('content-container');
    const navigationButtons = document.querySelectorAll('.sidebar-icon[data-page]');
    
    // Function to load content
    async function loadContent(url) {
        // Prüfen, ob es sich um eine externe URL handelt
        if (url.startsWith('http')) {
            window.open(url, '_blank');
            return;
        }
        
        // Spezielle Aktionen für bestimmte Seiten
        if (url === 'moreapps' || url === 'logout') {
            // Diese werden vom zusätzlichen Script in index.html behandelt
            return;
        }
        
        try {
            console.log('Loading content from:', url);
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const content = await response.text();
            contentContainer.innerHTML = content;
            
            // Execute any scripts that were loaded with the new content
            const scripts = contentContainer.querySelectorAll('script');
            scripts.forEach(script => {
                const newScript = document.createElement('script');
                if (script.src) {
                    newScript.src = script.src;
                } else {
                    newScript.textContent = script.textContent;
                }
                document.body.appendChild(newScript);
                script.remove();
            });
        } catch (error) {
            console.error('Error loading content:', error);
            contentContainer.innerHTML = '<div class="p-6"><h2>Fehler beim Laden der Inhalte</h2><p>Bitte versuche es später erneut.</p></div>';
        }
    }
    
    // Set up navigation event listeners
    navigationButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active button styling
            navigationButtons.forEach(btn => btn.classList.remove('active-icon'));
            this.classList.add('active-icon');
            
            // Load the corresponding content
            const pageUrl = this.getAttribute('data-page');
            loadContent(pageUrl);
        });
    });
    
    // Load initial content (Startseite by default)
    // Check if there's a homeButton with data-page attribute
    const homeButton = document.getElementById('homeButton');
    if (homeButton && homeButton.getAttribute('data-page')) {
        loadContent(homeButton.getAttribute('data-page'));
    } else {
        loadContent('Startseite.html');
    }
});