document.addEventListener('DOMContentLoaded', () => {
    particlesJS('particles-js', {
        particles: {
            number: { value: 80, density: { enable: true, value_area: 800 } },
            color: { value: '#ff007a' },
            shape: { type: 'circle' },
            opacity: { value: 0.5, random: true },
            size: { value: 3, random: true },
            line_linked: { enable: true, distance: 150, color: '#b0b0ff', opacity: 0.4, width: 1 },
            move: { enable: true, speed: 4, direction: 'none', random: true, attract: { enable: true, rotateX: 600, rotateY: 1200 } }
        },
        interactivity: {
            detect_on: 'canvas',
            events: {
                onhover: { enable: true, mode: 'grab' },
                onclick: { enable: true, mode: 'repulse' },
                resize: true
            },
            modes: {
                grab: { distance: 200, line_linked: { opacity: 0.5 } },
                repulse: { distance: 150, duration: 0.4 }
            }
        },
        retina_detect: true
    });

    const authForm = document.getElementById('auth-form');
    const authBtn = document.getElementById('auth-btn');
    const toggleAuth = document.getElementById('toggle-auth');
    const formTitle = document.getElementById('form-title');
    const authError = document.getElementById('auth-error');
    let isLogin = true;

    authForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();

        if (!username || !password) {
            authError.textContent = 'Enter your credentials, explorer!';
            return;
        }

        authBtn.disabled = true;
        authBtn.textContent = 'Launching...';

        const endpoint = isLogin ? '/api/login' : '/api/register';
        fetch(`http://localhost:5000${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            authBtn.disabled = false;
            authBtn.textContent = isLogin ? 'Launch' : 'Forge';
            if (data.error) {
                authError.textContent = data.error;
            } else {
                localStorage.setItem('userId', data.userId);
                window.location.href = 'dashboard.html';
            }
        })
        .catch(error => {
            authBtn.disabled = false;
            authBtn.textContent = isLogin ? 'Launch' : 'Forge';
            authError.textContent = 'Cosmic error detected!';
            console.error(error);
        });
    });

    window.toggleForm = () => {
        isLogin = !isLogin;
        formTitle.textContent = isLogin ? 'Enter the Verse' : 'Forge Your Path';
        authBtn.textContent = isLogin ? 'Launch' : 'Forge';
        toggleAuth.innerHTML = isLogin 
            ? `New Explorer? <a href="#" onclick="toggleForm()">Forge Your Path</a>`
            : `Returning? <a href="#" onclick="toggleForm()">Enter the Verse</a>`;
        authError.textContent = '';
    };
});