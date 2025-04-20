/**
 * Main JavaScript for Eulogos application
 * Contains utility functions for the user interface
 */

// Handle dark mode toggle
document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('toggleDarkMode');
    
    if (darkModeToggle) {
        // Set initial state based on localStorage
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark');
        }
        
        // Add click handler
        darkModeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark');
            localStorage.setItem('darkMode', document.body.classList.contains('dark'));
        });
    }
    
    // Initialize favorite buttons
    initFavoriteButtons();
});

/**
 * Initialize favorite button handlers
 */
function initFavoriteButtons() {
    // Find all favorite buttons with htmx attributes
    document.querySelectorAll('[hx-post^="/favorite/"]').forEach(button => {
        button.addEventListener('htmx:afterSwap', function(event) {
            // Get the response
            const response = JSON.parse(event.detail.xhr.response);
            
            // Handle success/failure
            if (response && response.success) {
                // Button was already toggled in the onclick handler
                console.log('Favorite toggled successfully');
            } else {
                // Revert the visual change if the server request failed
                toggleFavButton(button);
                console.error('Failed to toggle favorite');
            }
        });
    });
}

/**
 * Toggle favorite button appearance
 * @param {HTMLElement} button - The button element to toggle (optional)
 */
function toggleFavButton(button) {
    // If no button is provided, use the one from the reader page
    button = button || document.getElementById('favButton');
    
    if (!button) return;
    
    // Toggle classes
    if (button.classList.contains('bg-blue-700')) {
        button.classList.remove('bg-blue-700', 'hover:bg-blue-800');
        button.classList.add('bg-yellow-500', 'hover:bg-yellow-600');
    } else {
        button.classList.remove('bg-yellow-500', 'hover:bg-yellow-600');
        button.classList.add('bg-blue-700', 'hover:bg-blue-800');
    }
} 