document.addEventListener('DOMContentLoaded', function() {
    anime({
        targets: '.login-form',
        translateY: [50, 0],
        opacity: [0, 1],
        easing: 'easeOutExpo',
        duration: 1200,
        delay: 300
    });

    anime({
        targets: '.login-form input, .login-form button',
        translateX: [-50, 0],
        opacity: [0, 1],
        easing: 'easeOutExpo',
        duration: 800,
        delay: anime.stagger(100, {start: 600})
    });
});