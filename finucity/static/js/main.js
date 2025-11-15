document.addEventListener('DOMContentLoaded', function() {
    // Mobile Menu Toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    
    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            mobileMenuBtn.innerHTML = navLinks.classList.contains('active') ? 
                '<i class="fas fa-times"></i>' : '<i class="fas fa-bars"></i>';
        });
    }
    
    // Navbar Scroll Effect
    const navbar = document.getElementById('navbar');
    
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }
    
    // FAQ accordion
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        
        if (question) {
            question.addEventListener('click', () => {
                item.classList.toggle('active');
            });
        }
    });
    
    // Animate elements when they come into view
    const fadeElements = document.querySelectorAll('.fade-in');
    
    const fadeInObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.2
    });
    
    fadeElements.forEach(element => {
        fadeInObserver.observe(element);
    });
    
    // Daily tip rotation
    const tips = [
        "Start your tax planning early in the financial year to maximize deductions under Section 80C.",
        "Consider ELSS mutual funds for tax savings with potentially higher returns and a shorter lock-in period.",
        "Claiming HRA? Keep rent receipts and ensure your rental agreement is properly executed.",
        "Self-employed? Track business expenses diligently throughout the year for better tax optimization.",
        "Remember that health insurance premiums provide tax benefits under Section 80D.",
        "Filing ITR is mandatory even if your income is below taxable limit if you have foreign assets.",
        "GST registered businesses should reconcile their GSTR-1 and GSTR-3B returns to avoid discrepancies."
    ];
    
    const dailyTip = document.getElementById('dailyTip');
    if (dailyTip) {
        // Show random tip or rotate tips every few seconds
        const randomTip = tips[Math.floor(Math.random() * tips.length)];
        dailyTip.textContent = randomTip;
        
        // Rotate tips every 10 seconds
        let tipIndex = 0;
        setInterval(() => {
            tipIndex = (tipIndex + 1) % tips.length;
            dailyTip.style.opacity = 0;
            
            setTimeout(() => {
                dailyTip.textContent = tips[tipIndex];
                dailyTip.style.opacity = 1;
            }, 500);
        }, 10000);
    }
    
    // Fetch stats from API
    const fetchStats = async () => {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            const userCount = document.getElementById('userCount');
            const queryCount = document.getElementById('queryCount');
            
            if (userCount && data.users) {
                userCount.textContent = `${data.users}+`;
            }
            
            if (queryCount && data.queries) {
                queryCount.textContent = `${data.queries}+`;
            }
        } catch (error) {
            console.log('Could not fetch stats');
        }
    };
    
    // Try to fetch stats but don't break the page if it fails
    fetchStats().catch(() => {});
});