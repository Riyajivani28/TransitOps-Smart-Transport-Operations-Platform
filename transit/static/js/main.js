// TransitOps - Main JavaScript file

document.addEventListener('DOMContentLoaded', () => {
    // Dynamic Active Navigation Classes helper
    const currentUrl = window.location.pathname;
    const navLinks = document.querySelectorAll('aside nav a');
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentUrl.startsWith(href) && href !== '/') {
            link.classList.add('bg-blue-600', 'text-white');
            link.classList.remove('text-slate-400');
        }
    });

    // Auto-dismiss Alerts/Messages
    const dismissButtons = document.querySelectorAll('[data-dismiss="alert"]');
    dismissButtons.forEach(button => {
        button.addEventListener('click', () => {
            const alertBox = button.closest('.alert-box');
            if (alertBox) {
                alertBox.classList.add('opacity-0', 'transition-opacity', 'duration-300');
                setTimeout(() => alertBox.remove(), 300);
            }
        });
    });
});
