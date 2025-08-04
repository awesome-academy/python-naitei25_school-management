/* Bootstrap 5.3.0 - Minimal JavaScript for admin panel */

(function() {
    'use strict';

    // Dropdown functionality
    function initDropdowns() {
        const dropdownToggles = document.querySelectorAll('[data-bs-toggle="dropdown"]');
        
        dropdownToggles.forEach(function(toggle) {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const dropdownMenu = this.nextElementSibling;
                if (!dropdownMenu || !dropdownMenu.classList.contains('dropdown-menu')) {
                    return;
                }
                
                // Close other dropdowns
                document.querySelectorAll('.dropdown-menu.show').forEach(function(menu) {
                    if (menu !== dropdownMenu) {
                        menu.classList.remove('show');
                    }
                });
                
                // Toggle current dropdown
                dropdownMenu.classList.toggle('show');
            });
        });
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', function() {
            document.querySelectorAll('.dropdown-menu.show').forEach(function(menu) {
                menu.classList.remove('show');
            });
        });
    }

    // Alert dismiss functionality
    function initAlerts() {
        const alertDismissBtns = document.querySelectorAll('[data-bs-dismiss="alert"]');
        
        alertDismissBtns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                const alert = this.closest('.alert');
                if (alert) {
                    alert.style.opacity = '0';
                    setTimeout(function() {
                        alert.remove();
                    }, 150);
                }
            });
        });
    }

    // Auto-hide alerts after 5 seconds
    function autoHideAlerts() {
        const alerts = document.querySelectorAll('.alert:not(.alert-dismissible)');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                if (alert.parentNode) {
                    alert.style.opacity = '0';
                    setTimeout(function() {
                        if (alert.parentNode) {
                            alert.remove();
                        }
                    }, 150);
                }
            }, 5000);
        });
    }

    // Form validation helpers
    function initFormValidation() {
        const forms = document.querySelectorAll('form[data-bs-validation]');
        
        forms.forEach(function(form) {
            form.addEventListener('submit', function(e) {
                const requiredFields = form.querySelectorAll('[required]');
                let isValid = true;
                
                requiredFields.forEach(function(field) {
                    if (!field.value.trim()) {
                        field.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        field.classList.remove('is-invalid');
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                }
            });
        });
    }

    // Initialize when DOM is ready
    function init() {
        initDropdowns();
        initAlerts();
        autoHideAlerts();
        initFormValidation();
    }

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose Bootstrap object for compatibility
    window.bootstrap = {
        Alert: {
            getOrCreateInstance: function(element) {
                return {
                    close: function() {
                        element.style.opacity = '0';
                        setTimeout(function() {
                            element.remove();
                        }, 150);
                    }
                };
            }
        },
        Dropdown: {
            getOrCreateInstance: function(element) {
                return {
                    toggle: function() {
                        const menu = element.nextElementSibling;
                        if (menu && menu.classList.contains('dropdown-menu')) {
                            menu.classList.toggle('show');
                        }
                    }
                };
            }
        }
    };
})();