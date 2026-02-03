/* ========================================
   PREMIUM ADVANCED INTERACTIONS
   Ultra-premium JavaScript enhancements
   ======================================== */

(function() {
    'use strict';

    // ==================== SCROLL PROGRESS BAR ====================
    function initScrollProgress() {
        const scrollProgress = document.getElementById('scrollProgress');
        if (!scrollProgress) return;

        function updateScrollProgress() {
            const windowHeight = window.innerHeight;
            const documentHeight = document.documentElement.scrollHeight - windowHeight;
            const scrolled = window.scrollY;
            const progress = (scrolled / documentHeight) * 100;
            
            scrollProgress.style.transform = `scaleX(${progress / 100})`;
        }

        window.addEventListener('scroll', updateScrollProgress, { passive: true });
        updateScrollProgress();
    }

    // ==================== FLOATING PARTICLES SYSTEM ====================
    function initFloatingParticles() {
        const heroSection = document.querySelector('.hero-premium');
        if (!heroSection) return;

        const particlesContainer = document.createElement('div');
        particlesContainer.className = 'floating-particles';
        heroSection.appendChild(particlesContainer);

        const particleCount = window.innerWidth > 768 ? 30 : 15;

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            
            // Random positioning
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 15 + 's';
            particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
            
            // Random size
            const size = Math.random() * 3 + 2;
            particle.style.width = size + 'px';
            particle.style.height = size + 'px';
            
            particlesContainer.appendChild(particle);
        }
    }

    // ==================== SPOTLIGHT CURSOR EFFECT ====================
    function initSpotlightEffect() {
        const spotlightContainers = document.querySelectorAll('.spotlight-container');
        
        spotlightContainers.forEach(container => {
            const spotlight = document.createElement('div');
            spotlight.className = 'spotlight';
            container.appendChild(spotlight);
            
            container.addEventListener('mousemove', (e) => {
                const rect = container.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                spotlight.style.transform = `translate(${x - 300}px, ${y - 300}px)`;
            });
            
            container.addEventListener('mouseleave', () => {
                spotlight.style.transform = 'translate(-1000px, -1000px)';
            });
        });
    }

    // ==================== REVEAL ON SCROLL ANIMATIONS ====================
    function initRevealAnimations() {
        const revealElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
        
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    revealObserver.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
        });
        
        revealElements.forEach(el => revealObserver.observe(el));
    }

    // ==================== MAGNETIC BUTTON EFFECT ====================
    function initMagneticButtons() {
        const magneticButtons = document.querySelectorAll('.btn-magnetic');
        
        magneticButtons.forEach(button => {
            button.addEventListener('mousemove', (e) => {
                const rect = button.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                
                const moveX = x * 0.3;
                const moveY = y * 0.3;
                
                button.style.transform = `translate(${moveX}px, ${moveY}px) scale(1.05)`;
            });
            
            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translate(0, 0) scale(1)';
            });
        });
    }

    // ==================== 3D CARD TILT EFFECT ====================
    function init3DCards() {
        const cards3D = document.querySelectorAll('.card-3d');
        
        cards3D.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = ((y - centerY) / centerY) * -5;
                const rotateY = ((x - centerX) / centerX) * 5;
                
                card.style.transform = `
                    perspective(1000px)
                    rotateX(${rotateX}deg)
                    rotateY(${rotateY}deg)
                    translateY(-8px)
                    scale(1.02)
                `;
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0) scale(1)';
            });
        });
    }

    // ==================== SMOOTH PARALLAX SCROLLING ====================
    function initParallaxEffect() {
        const parallaxElements = document.querySelectorAll('[data-parallax]');
        
        function updateParallax() {
            const scrolled = window.pageYOffset;
            
            parallaxElements.forEach(element => {
                const speed = element.dataset.parallax || 0.5;
                const yPos = -(scrolled * speed);
                element.style.transform = `translateY(${yPos}px)`;
            });
        }
        
        if (parallaxElements.length > 0) {
            window.addEventListener('scroll', updateParallax, { passive: true });
            updateParallax();
        }
    }

    // ==================== ENHANCED RIPPLE EFFECT ====================
    function initEnhancedRipple() {
        const rippleButtons = document.querySelectorAll('.btn-premium, .cta-button');
        
        rippleButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                const ripple = document.createElement('span');
                ripple.className = 'ripple-effect';
                
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = x + 'px';
                ripple.style.top = y + 'px';
                
                this.appendChild(ripple);
                
                setTimeout(() => ripple.remove(), 600);
            });
        });
    }

    // ==================== STAGGER ANIMATION ====================
    function initStaggerAnimation() {
        const staggerContainers = document.querySelectorAll('[data-stagger]');
        
        const staggerObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const items = entry.target.querySelectorAll('.stagger-item');
                    items.forEach((item, index) => {
                        setTimeout(() => {
                            item.style.animationPlayState = 'running';
                        }, index * 100);
                    });
                    staggerObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.2 });
        
        staggerContainers.forEach(container => {
            const items = container.querySelectorAll('.stagger-item');
            items.forEach(item => {
                item.style.animationPlayState = 'paused';
            });
            staggerObserver.observe(container);
        });
    }

    // ==================== GLOW ON HOVER ENHANCEMENT ====================
    function initGlowEffects() {
        const glowElements = document.querySelectorAll('.glow-on-hover');
        
        glowElements.forEach(element => {
            element.addEventListener('mousemove', (e) => {
                const rect = element.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;
                
                element.style.setProperty('--mouse-x', x + '%');
                element.style.setProperty('--mouse-y', y + '%');
            });
        });
    }

    // ==================== LAZY LOAD IMAGES WITH BLUR ====================
    function initLazyLoadImages() {
        const lazyImages = document.querySelectorAll('img[data-src]');
        
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.add('loaded');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    }

    // ==================== ADVANCED NAVBAR BEHAVIOR ====================
    function initAdvancedNavbar() {
        const navbar = document.getElementById('navbar');
        if (!navbar) return;

        let lastScrollTop = 0;
        let scrollTimeout;
        let isScrolling = false;

        window.addEventListener('scroll', () => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            clearTimeout(scrollTimeout);
            isScrolling = true;

            // Add scrolled class
            if (scrollTop > 100) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }

            // Hide on scroll down, show on scroll up
            if (scrollTop > lastScrollTop && scrollTop > 300) {
                navbar.style.transform = 'translateY(-100%)';
            } else {
                navbar.style.transform = 'translateY(0)';
            }

            lastScrollTop = scrollTop;

            // Show navbar when scrolling stops
            scrollTimeout = setTimeout(() => {
                isScrolling = false;
                navbar.style.transform = 'translateY(0)';
            }, 150);
        }, { passive: true });
    }

    // ==================== SMOOTH SCROLL ANCHOR LINKS ====================
    function initSmoothScroll() {
        const scrollLinks = document.querySelectorAll('a[href^="#"]');
        
        scrollLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                if (href === '#' || href === '#!') return;
                
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    const offsetTop = target.offsetTop - 100;
                    
                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }

    // ==================== COUNT UP ANIMATION FOR STATS ====================
    function initCountUpAnimation() {
        const countElements = document.querySelectorAll('[data-count]');
        
        const countObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    const target = parseInt(element.dataset.count);
                    const duration = 2000;
                    const increment = target / (duration / 16);
                    let current = 0;
                    
                    const timer = setInterval(() => {
                        current += increment;
                        if (current >= target) {
                            element.textContent = target.toLocaleString();
                            clearInterval(timer);
                        } else {
                            element.textContent = Math.floor(current).toLocaleString();
                        }
                    }, 16);
                    
                    countObserver.unobserve(element);
                }
            });
        }, { threshold: 0.5 });
        
        countElements.forEach(el => countObserver.observe(el));
    }

    // ==================== TYPING ANIMATION ====================
    function initTypingAnimation() {
        const typingElements = document.querySelectorAll('[data-typing]');
        
        typingElements.forEach(element => {
            const text = element.dataset.typing;
            element.textContent = '';
            let index = 0;
            
            const typeChar = () => {
                if (index < text.length) {
                    element.textContent += text.charAt(index);
                    index++;
                    setTimeout(typeChar, 100);
                }
            };
            
            const observer = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting) {
                    typeChar();
                    observer.disconnect();
                }
            });
            
            observer.observe(element);
        });
    }

    // ==================== INITIALIZE ALL EFFECTS ====================
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        // Initialize all effects
        initScrollProgress();
        initFloatingParticles();
        initSpotlightEffect();
        initRevealAnimations();
        initMagneticButtons();
        init3DCards();
        initParallaxEffect();
        initEnhancedRipple();
        initStaggerAnimation();
        initGlowEffects();
        initLazyLoadImages();
        initAdvancedNavbar();
        initSmoothScroll();
        initCountUpAnimation();
        initTypingAnimation();

        console.log('🎨 Premium Advanced Effects Initialized');
    }

    // Start initialization
    init();

    // ==================== PERFORMANCE MONITORING ====================
    if ('performance' in window) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                if (perfData) {
                    console.log('⚡ Page Load Time:', Math.round(perfData.loadEventEnd), 'ms');
                }
            }, 0);
        });
    }

})();

// ==================== RIPPLE EFFECT STYLES (INJECTED) ====================
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    .btn-premium, .cta-button {
        position: relative;
        overflow: hidden;
    }
    
    .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.5);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(rippleStyle);
