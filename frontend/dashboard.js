document.addEventListener('DOMContentLoaded', () => {
    particlesJS('particles-js', {
        particles: {
            number: { value: 100, density: { enable: true, value_area: 800 } },
            color: { value: '#DAA520' },
            shape: { type: 'circle' },
            opacity: { value: 0.6, random: true },
            size: { value: 3, random: true },
            line_linked: { enable: true, distance: 150, color: '#8B4513', opacity: 0.3, width: 1 },
            move: { enable: true, speed: 5, direction: 'none', random: true, attract: { enable: true, rotateX: 600, rotateY: 1200 } }
        },
        interactivity: {
            detect_on: 'canvas',
            events: {
                onhover: { enable: true, mode: 'bubble' },
                onclick: { enable: true, mode: 'repulse' },
                resize: true
            },
            modes: {
                bubble: { distance: 300, size: 6, duration: 0.5 },
                repulse: { distance: 200, duration: 0.4 }
            }
        },
        retina_detect: true
    });

    const userId = localStorage.getItem('userId');
    if (!userId) {
        window.location.href = 'index.html';
        return;
    }

    const imageInput = document.getElementById('image-input');
    const weightSelect = document.getElementById('weight');
    const analyzeBtn = document.getElementById('analyze-btn');
    const preview = document.getElementById('preview');
    const result = document.getElementById('result');
    const foodLogs = document.getElementById('food-logs');
    const logoutBtn = document.getElementById('logout-btn');
    const searchLogs = document.getElementById('search-logs');
    const filterWeight = document.getElementById('filter-weight');

    function loadLogs() {
        fetch(`http://localhost:5000/api/food-logs?userId=${userId}`)
            .then(response => response.json())
            .then(logs => {
                foodLogs.innerHTML = '';
                let filteredLogs = logs.filter(log =>
                    log.foodName.toLowerCase().includes(searchLogs.value.toLowerCase()) &&
                    (filterWeight.value === 'all' || log.weight === parseInt(filterWeight.value))
                );

                filteredLogs.forEach(log => {
                    const li = document.createElement('li');
                    li.draggable = true;
                    li.innerHTML = `
                        <span><strong>${log.foodName}</strong> (${(log.confidence * 100).toFixed(2)}%) - ${log.weight}g</span>
                        <span>🌶️ ${log.nutrition.calories.toFixed(1)} kcal | 🍗 ${log.nutrition.protein.toFixed(1)}g | 🍚 ${log.nutrition.carbs.toFixed(1)}g | 🥑 ${log.nutrition.fat.toFixed(1)}g</span>
                        <button class="remove-log" data-id="${log.id}">Remove</button>
                    `;
                    foodLogs.appendChild(li);
                });

                $(foodLogs).sortable({
                    revert: true,
                    cursor: 'move',
                    update: function() {
                        console.log('Log order updated');
                    }
                });
                $(foodLogs).disableSelection();

                document.querySelectorAll('.remove-log').forEach(btn => {
                    btn.addEventListener('click', () => removeLog(btn.dataset.id));
                });
            })
            .catch(error => console.error('Error loading logs:', error));
    }

    imageInput.addEventListener('change', () => {
        const file = imageInput.files[0];
        if (file) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            preview.innerHTML = '';
            preview.appendChild(img);
            img.classList.add('animate-float');
        }
    });

    analyzeBtn.addEventListener('click', () => {
        const file = imageInput.files[0];
        if (!file) {
            result.innerHTML = '<p class="error-text">No dish to analyze!</p>';
            result.style.opacity = 1;
            setTimeout(() => result.style.opacity = 0, 3000);
            return;
        }

        const formData = new FormData();
        formData.append('image', file);
        formData.append('userId', userId);
        formData.append('weight', weightSelect.value);

        result.innerHTML = '<p class="loading-text">Tasting...</p>';
        result.style.opacity = 1;
        analyzeBtn.disabled = true;
        analyzeBtn.style.boxShadow = '0 0 25px #8B4513';

        fetch('http://localhost:5000/api/recognize', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            analyzeBtn.disabled = false;
            analyzeBtn.style.boxShadow = '0 0 15px #DAA520';
            if (data.error) {
                result.innerHTML = `<p class="error-text">${data.error}</p>`;
                result.style.opacity = 1;
                setTimeout(() => result.style.opacity = 0, 3000);
            } else {
                result.innerHTML = `
                    <h3>${data.foodName}</h3>
                    <p>Confidence: ${(data.confidence * 100).toFixed(2)}%</p>
                    <p>Calories:🌶️ ${data.nutrition.calories.toFixed(1)} kcal |Protien: 🍗 ${data.nutrition.protein.toFixed(1)}g |Carbs: 🍚 ${data.nutrition.carbs.toFixed(1)}g | Fat:🥑 ${data.nutrition.fat.toFixed(1)}g</p>
                     <div class="food-summary">
            <h4>🍽️ What is ${data.foodName.replace(/_/g, ' ')}?</h4>
            <p>${data.summary}</p>
        </div>
                `;
                result.style.opacity = 1;
                loadLogs();
                setTimeout(() => result.style.opacity = 1, 5000);
            }
        })
        .catch(error => {
            analyzeBtn.disabled = false;
            analyzeBtn.style.boxShadow = '0 0 15px #DAA520';
            result.innerHTML = '<p class="error-text">Analysis failed!</p>';
            result.style.opacity = 1;
            setTimeout(() => result.style.opacity = 0, 3000);
            console.error(error);
        });
    });

    logoutBtn.addEventListener('click', () => {
        logoutBtn.style.boxShadow = '0 0 25px #A52A2A';
        setTimeout(() => {
            localStorage.removeItem('userId');
            window.location.href = 'index.html';
        }, 300);
    });

    // Real-time Filtering
    searchLogs.addEventListener('input', loadLogs);
    filterWeight.addEventListener('change', loadLogs);

    // Initial Load
    loadLogs();
});