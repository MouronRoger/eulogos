/**
 * Main JavaScript for Eulogos application
 * Contains utility functions for the user interface and state management
 */

// Handle DOM-ready initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dark mode
    initDarkMode();
    
    // Initialize favorite and archive buttons
    initActionButtons();
    
    // Initialize author expanded state management
    initAuthorExpandedState();
});

/**
 * Initialize dark mode toggle
 */
function initDarkMode() {
    const darkModeToggle = document.getElementById('toggleDarkMode');
    
    if (darkModeToggle) {
        // Set initial state based on localStorage
        try {
            if (localStorage.getItem('darkMode') === 'true') {
                document.body.classList.add('dark');
            }
        } catch (e) {
            console.error('Error reading dark mode preference:', e);
        }
        
        // Add click handler
        darkModeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark');
            try {
                localStorage.setItem('darkMode', document.body.classList.contains('dark'));
            } catch (e) {
                console.error('Error saving dark mode preference:', e);
            }
        });
    }
}

/**
 * Toggle favorite button appearance
 * @param {HTMLElement} button - The button element to toggle
 */
function toggleFavoriteButton(button) {
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
    
    // For text list items, toggle SVG class
    const svg = button.querySelector('svg');
    if (svg) {
        svg.classList.toggle('text-yellow-500');
        svg.classList.toggle('text-gray-400');
    }
}

/**
 * Toggle archive button appearance and update endpoint
 * @param {HTMLElement} button - The button element
 * @param {boolean} isArchived - Whether the text is now archived
 * @param {string} path - The canonical path of the text
 */
function updateArchiveButton(button, isArchived, path) {
    if (!button) return;
    
    // Update the button's hx-post attribute
    button.setAttribute('hx-post', isArchived ? `/unarchive/${path}` : `/archive/${path}`);
    
    // Update the SVG styling
    const svg = button.querySelector('svg');
    if (svg) {
        if (isArchived) {
            svg.classList.add('text-red-500');
        } else {
            svg.classList.remove('text-red-500');
        }
    }
    
    // Update the title attribute
    button.setAttribute('title', isArchived ? 'Unarchive text' : 'Archive text');
}

/**
 * Initialize action buttons (favorite/archive) with HTMX handlers
 */
function initActionButtons() {
    // Find all favorite buttons with htmx attributes
    document.querySelectorAll('[hx-post^="/favorite/"]').forEach(button => {
        button.addEventListener('htmx:afterSwap', function(event) {
            try {
                // Parse the response
                const response = JSON.parse(event.detail.xhr.response);
                
                // Handle success/failure
                if (response && response.success) {
                    // Button was already toggled in the onclick handler
                    console.log('Favorite toggled successfully');
                } else {
                    // Revert the visual change if the server request failed
                    toggleFavoriteButton(button);
                    console.error('Failed to toggle favorite:', response?.message || 'Unknown error');
                }
            } catch (e) {
                console.error('Error processing favorite response:', e);
                // Revert the visual change if there was an error
                toggleFavoriteButton(button);
            }
        });
    });
    
    // Find all archive/unarchive buttons
    document.querySelectorAll('[hx-post^="/archive/"], [hx-post^="/unarchive/"]').forEach(button => {
        button.addEventListener('htmx:afterSwap', function(event) {
            try {
                const response = JSON.parse(event.detail.xhr.response);
                
                if (response && response.success) {
                    console.log(`Text ${response.archived ? 'archived' : 'unarchived'} successfully`);
                    
                    // Extract path from the endpoint
                    const endpoint = button.getAttribute('hx-post');
                    const path = endpoint.split('/').slice(2).join('/');
                    
                    // Update button appearance and toggle the endpoint
                    updateArchiveButton(button, response.archived, path);
                } else {
                    console.error('Failed to toggle archive status:', response?.message || 'Unknown error');
                }
            } catch (e) {
                console.error('Error processing archive response:', e);
            }
        });
    });
}

/**
 * Initialize author expanded state management for hierarchical browse
 */
function initAuthorExpandedState() {
    try {
        // Get stored expanded authors state
        let storedAuthors;
        try {
            storedAuthors = JSON.parse(localStorage.getItem('expandedAuthors') || '{}');
        } catch (parseError) {
            console.error('Error parsing expandedAuthors from localStorage:', parseError);
            storedAuthors = {};
            localStorage.setItem('expandedAuthors', '{}');
        }
        
        // Get current authors from the DOM
        const currentAuthors = new Set(
            Array.from(document.querySelectorAll('[data-author]'))
                .map(el => el.dataset.author)
                .filter(author => author) // Filter out any undefined/empty values
        );
        
        // Bail early if there are no authors (not on browse page)
        if (currentAuthors.size === 0) return;
        
        // Clean up storage for authors that no longer exist
        let needsUpdate = false;
        Object.keys(storedAuthors).forEach(author => {
            if (!currentAuthors.has(author)) {
                delete storedAuthors[author];
                needsUpdate = true;
            }
        });
        
        if (needsUpdate) {
            try {
                localStorage.setItem('expandedAuthors', JSON.stringify(storedAuthors));
            } catch (saveError) {
                console.error('Error saving expandedAuthors to localStorage:', saveError);
            }
        }
        
        // Expand first 3 authors by default if no saved state
        if (Object.keys(storedAuthors).length === 0 && currentAuthors.size > 0) {
            const initialExpanded = {};
            
            // Get first 3 authors
            const authorHeaders = document.querySelectorAll('[data-author]');
            for (let i = 0; i < Math.min(3, authorHeaders.length); i++) {
                const authorName = authorHeaders[i].dataset.author;
                if (authorName) {
                    initialExpanded[authorName] = true;
                }
            }
            
            // Save to localStorage
            try {
                localStorage.setItem('expandedAuthors', JSON.stringify(initialExpanded));
            } catch (saveError) {
                console.error('Error saving initial expandedAuthors to localStorage:', saveError);
            }
            
            // Update the stored state
            storedAuthors = initialExpanded;
        }
        
        // Apply the expanded state to DOM elements if not using Alpine.js
        // If using Alpine.js, this is handled by Alpine's x-data binding
        if (!window.Alpine) {
            Object.entries(storedAuthors).forEach(([author, isExpanded]) => {
                if (isExpanded) {
                    const authorElement = document.querySelector(`[data-author="${author}"]`);
                    if (authorElement) {
                        const content = authorElement.nextElementSibling;
                        if (content && content.classList.contains('hidden')) {
                            content.classList.remove('hidden');
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.error('Error initializing author expanded state:', e);
        // Reset expanded state if there's an error
        try {
            localStorage.setItem('expandedAuthors', '{}');
        } catch (storageError) {
            console.error('Could not reset expanded authors state:', storageError);
        }
    }
}