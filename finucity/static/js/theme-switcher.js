// Enhanced Theme Switcher for Finucity
document.addEventListener('DOMContentLoaded', function() {
    const themeToggleContainer = document.getElementById('themeToggleContainer');
    const body = document.body;

    // Define all available themes
    const themes = [
        'theme-default',
        'theme-light-wine',
        'theme-dark-charcoal',
        'theme-burnt-copper-sea-mist',
        'theme-coffee-ecru'
    ];

    // Theme names for display
    const themeNames = {
        'theme-default': 'Olive & Orange',
        'theme-light-wine': 'Wine & Gold',
        'theme-dark-charcoal': 'Charcoal & Almond',
        'theme-burnt-copper-sea-mist': 'Burnt Copper & Sea Mist',
        'theme-coffee-ecru': 'Coffee & Ecru'
    };

    let currentThemeIndex = 0;
    const savedTheme = localStorage.getItem('finucity-theme');

    // Initialize with saved theme or default
    if (savedTheme && themes.includes(savedTheme)) {
        applyTheme(savedTheme);
        currentThemeIndex = themes.indexOf(savedTheme);
    } else {
        applyTheme(themes[0]);
    }

    // Create theme selector dropdown if the container exists
    if (themeToggleContainer) {
        const parent = themeToggleContainer.parentNode;
        
        // Create new theme selector
        const themeSelector = document.createElement('div');
        themeSelector.className = 'theme-selector';
        
        const currentTheme = document.createElement('div');
        currentTheme.className = 'current-theme';
        currentTheme.innerHTML = `<i class="fas fa-palette"></i> <span>${themeNames[themes[currentThemeIndex]]}</span>`;
        
        const themeDropdown = document.createElement('div');
        themeDropdown.className = 'theme-dropdown';
        
        themes.forEach((theme, index) => {
            const themeOption = document.createElement('div');
            themeOption.className = `theme-option ${theme === savedTheme ? 'active' : ''}`;
            themeOption.innerHTML = themeNames[theme];
            themeOption.dataset.theme = theme;
            
            themeOption.addEventListener('click', () => {
                applyTheme(theme);
                currentThemeIndex = index;
                
                // Update active state
                document.querySelectorAll('.theme-option').forEach(option => {
                    option.classList.remove('active');
                });
                themeOption.classList.add('active');
                
                // Update current theme display
                currentTheme.innerHTML = `<i class="fas fa-palette"></i> <span>${themeNames[theme]}</span>`;
                
                // Close dropdown
                themeDropdown.classList.remove('show');
            });
            
            themeDropdown.appendChild(themeOption);
        });
        
        themeSelector.appendChild(currentTheme);
        themeSelector.appendChild(themeDropdown);
        
        // Replace old theme toggle with new selector
        parent.replaceChild(themeSelector, themeToggleContainer);
        
        // Toggle dropdown
        currentTheme.addEventListener('click', (e) => {
            e.stopPropagation();
            themeDropdown.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            themeDropdown.classList.remove('show');
        });
    }

    function applyTheme(themeName) {
        // Remove all theme classes
        themes.forEach(theme => {
            body.classList.remove(theme);
        });
        
        // Add selected theme class
        body.classList.add(themeName);
        
        // Save preference
        localStorage.setItem('finucity-theme', themeName);
        
        // Fix home button contrast for specific themes
        const homeBtn = document.querySelector('.home-btn');
        if (homeBtn) {
            if (themeName === 'theme-default' || themeName === 'theme-burnt-copper-sea-mist' || themeName === 'theme-coffee-ecru') {
                homeBtn.style.color = '#fff';  // Ensure text is visible
            } else {
                homeBtn.style.color = '';  // Reset to theme default
            }
        }
        
        // Update logo appearance based on theme
        updateLogoForTheme(themeName);
    }
    
    function updateLogoForTheme(themeName) {
        const logo = document.querySelector('.logo img');
        if (logo) {
            // If using alternate logo versions for different themes
            // logo.src = `/static/images/logo-${themeName.replace('theme-', '')}.png`;
            
            // Adjust logo brightness/contrast if needed
            if (themeName === 'theme-dark-charcoal') {
                logo.style.filter = 'brightness(1.2)';
            } else {
                logo.style.filter = '';
            }
        }
    }
});