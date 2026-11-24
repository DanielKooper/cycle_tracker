// cycle_tracker/webapp/script.js (обновлённая версия)

// Глобальные переменные
let currentDate = new Date();
let userData = null;
let cycles = [];
let userPremium = false; // Статус премиум пользователя
let partnerCycles = []; // Циклы партнёров

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', function() {
    initApp();
});

async function initApp() {
    const user = tg.initDataUnsafe?.user;
    
    if (user) {
        document.getElementById('username').textContent = user.first_name;
        userData = user;
        
        // Проверяем статус премиум
        await checkPremiumStatus();
        
        // Загружаем данные
        await loadCycles();
        await loadPartnerCycles();
        renderCalendar();
        updateStats();
        loadPartners();
        updateUIForPremium();
    }
}

// Проверка статуса премиум
async function checkPremiumStatus() {
    // Здесь должен быть API вызов к вашему серверу
    // Пока используем локальное хранилище для демонстрации
    const premiumStatus = localStorage.getItem('premium_status');
    userPremium = premiumStatus === 'true';
}

// Обновление UI в зависимости от статуса премиум
function updateUIForPremium() {
    if (!userPremium) {
        // Добавляем замки на премиум функции
        addLockToElement('advanced-stats');
        addLockToElement('partner-cycles-view');
        addLockToElement('ai-predictions');
        addLockToElement('export-data');
    }
}

function addLockToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const lock = document.createElement('div');
        lock.className = 'premium-lock';
        lock.innerHTML = '🔒';
        lock.onclick = () => showPremiumModal();
        element.appendChild(lock);
        element.style.position = 'relative';
    }
}

// Модальное окно премиум
function showPremiumModal() {
    const modal = document.createElement('div');
    modal.className = 'modal premium-modal';
    modal.innerHTML = `
        <div class="modal-content premium-content">
            <h2>⭐ Премиум функции</h2>
            <p>Разблокируйте все возможности за Telegram Stars!</p>
            
            <div class="premium-features">
                <div class="feature-item">
                    <span>📊 Расширенная статистика</span>
                    <span class="price">50 ⭐</span>
                </div>
                <div class="feature-item">
                    <span>👥 Просмотр циклов партнёров</span>
                    <span class="price">100 ⭐</span>
                </div>
                <div class="feature-item">
                    <span>🤖 AI прогнозы</span>
                    <span class="price">75 ⭐</span>
                </div>
                <div class="feature-item">
                    <span>📥 Экспорт данных</span>
                    <span class="price">30 ⭐</span>
                </div>
                <div class="feature-item">
                    <span>💎 Все функции навсегда</span>
                    <span class="price">200 ⭐</span>
                </div>
            </div>
            
            <button class="btn-primary" onclick="buyPremium('all')">
                Купить всё за 200 ⭐
            </button>
            <button class="btn-secondary" onclick="closePremiumModal()">
                Позже
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'block';
}

function closePremiumModal() {
    const modal = document.querySelector('.premium-modal');
    if (modal) {
        modal.remove();
    }
}

// Покупка премиум
async function buyPremium(packageType) {
    const prices = {
        'stats': 50,
        'partners': 100,
        'ai': 75,
        'export': 30,
        'all': 200
    };
    
    const price = prices[packageType];
    
    try {
        // Используем Telegram Stars API
        const invoice = await tg.openInvoice({
            title: `Премиум пакет: ${packageType}`,
            description: `Разблокировка функций за ${price} звёзд`,
            payload: JSON.stringify({
                type: 'premium',
                package: packageType,
                user_id: userData.id
            }),
            currency: 'XTR', // Telegram Stars
            prices: [{
                label: 'Premium Access',
                amount: price * 100 // В копейках/центах
            }]
        });
        
        if (invoice.status === 'paid') {
            await activatePremium(packageType);
            tg.showPopup({
                title: 'Успешно! 🎉',
                message: 'Премиум функции активированы!',
                buttons: [{type: 'ok'}]
            });
            closePremiumModal();
            updateUIForPremium();
        }
    } catch (error) {
        console.error('Ошибка покупки:', error);
        tg.showPopup({
            title: 'Ошибка',
            message: 'Не удалось完成 покупку. Попробуйте позже.',
            buttons: [{type: 'ok'}]
        });
    }
}

// Активация премиум
async function activatePremium(packageType) {
    // Здесь должен быть API вызов к вашему серверу
    localStorage.setItem('premium_status', 'true');
    localStorage.setItem(`premium_${packageType}`, 'true');
    userPremium = true;
}

// Расширенная статистика (премиум)
function showAdvancedStats() {
    if (!userPremium) {
        showPremiumModal();
        return;
    }
    
    switchView('advanced-stats-view');
    renderAdvancedCharts();
}

function renderAdvancedCharts() {
    // Здесь можно использовать Chart.js или другую библиотеку
    const canvas = document.getElementById('advanced-chart');
    if (!canvas) return;
    
    // Пример данных для графика
    const ctx = canvas.getContext('2d');
    
    // График длины циклов
    const cycleLengths = cycles.map(c => c.period_length || 5);
    const labels = cycles.map((c, i) => `Цикл ${i + 1}`);
    
    // Простая визуализация
    canvas.width = 400;
    canvas.height = 200;
    
    const maxVal = Math.max(...cycleLengths);
    const barWidth = 40;
    const spacing = 20;
    
    cycleLengths.forEach((length, i) => {
        const x = i * (barWidth + spacing) + 20;
        const height = (length / maxVal) * 150;
        const y = 180 - height;
        
        ctx.fillStyle = '#667eea';
        ctx.fillRect(x, y, barWidth, height);
        
        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.fillText(length, x + 10, y - 5);
    });
}

// Просмотр циклов партнёров (премиум)
function showPartnerCycles() {
    if (!userPremium) {
        showPremiumModal();
        return;
    }
    
    switchView('partner-cycles-view');
    renderPartnerCycles();
}

function renderPartnerCycles() {
    const container = document.getElementById('partner-cycles-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (partnerCycles.length === 0) {
        container.innerHTML = '<p>Нет данных о партнёрах</p>';
        return;
    }
    
    partnerCycles.forEach(partner => {
        const card = document.createElement('div');
        card.className = 'partner-cycle-card';
        card.innerHTML = `
            <h4>${partner.username}</h4>
            <p>Последний цикл: ${formatDate(partner.last_cycle_start)}</p>
            <p>Средняя длина: ${partner.avg_cycle_length} дней</p>
            <div class="mini-calendar">
                ${renderMiniCalendar(partner.cycles)}
            </div>
        `;
        container.appendChild(card);
    });
}

function renderMiniCalendar(cycles) {
    // Упрощённый календарь для партнёра
    let html = '<div class="mini-cal-days">';
    for (let i = 0; i < 30; i++) {
        const hasPeriod = cycles.some(c => {
            const start = new Date(c.start_date);
            const end = new Date(start);
            end.setDate(end.getDate() + (c.period_length || 5));
            const today = new Date();
            today.setDate(today.getDate() - (29 - i));
            return today >= start && today <= end;
        });
        
        html += `<div class="mini-day ${hasPeriod ? 'period' : ''}"></div>`;
    }
    html += '</div>';
    return html;
}

// AI прогнозы (премиум)
function showAIPredictions() {
    if (!userPremium) {
        showPremiumModal();
        return;
    }
    
    switchView('ai-predictions-view');
    generateAIPredictions();
}

function generateAIPredictions() {
    // Здесь должен быть вызов к AI API
    const predictions = {
        next_period: predictNextPeriod(),
        fertile_window: calculateFertileWindow(),
        mood_forecast: predictMood(),
        symptoms_prediction: predictSymptoms()
    };
    
    const container = document.getElementById('ai-predictions-container');
    if (!container) return;
    
    container.innerHTML = `
        <div class="prediction-card">
            <h3>📅 Следующий период</h3>
            <p>${formatDate(predictions.next_period)}</p>
            <p>Вероятность: 85%</p>
        </div>
        
        <div class="prediction-card">
            <h3>🌸 Окно фертильности</h3>
            <p>${formatDate(predictions.fertile_window.start)} - ${formatDate(predictions.fertile_window.end)}</p>
        </div>
        
        <div class="prediction-card">
            <h3>😊 Прогноз настроения</h3>
            <p>${predictions.mood_forecast}</p>
        </div>
        
        <div class="prediction-card">
            <h3>⚠️ Возможные симптомы</h3>
            <ul>
                ${predictions.symptoms_prediction.map(s => `<li>${s}</li>`).join('')}
            </ul>
        </div>
    `;
}

function calculateFertileWindow() {
    if (cycles.length === 0) return null;
    
    const nextPeriod = predictNextPeriod();
    if (!nextPeriod) return null;
    
    const ovulationDay = new Date(nextPeriod);
    ovulationDay.setDate(ovulationDay.getDate() - 14);
    
    const windowStart = new Date(ovulationDay);
    windowStart.setDate(windowStart.getDate() - 5);
    
    const windowEnd = new Date(ovulationDay);
    windowEnd.setDate(windowEnd.getDate() + 1);
    
    return {
        start: windowStart,
        end: windowEnd
    };
}

function predictMood() {
    const moods = ['Хорошее', 'Нормальное', 'Энергичное', 'Спокойное'];
    return moods[Math.floor(Math.random() * moods.length)];
}

function predictSymptoms() {
    const allSymptoms = ['Судороги', 'Головная боль', 'Усталость', 'Вздутие', 'Перепады настроения'];
    return allSymptoms.slice(0, Math.floor(Math.random() * 3) + 1);
}

// Экспорт данных (премиум)
function exportData() {
    if (!userPremium) {
        showPremiumModal();
        return;
    }
    
    const data = {
        user: userData,
        cycles: cycles,
        export_date: new Date().toISOString()
    };
    
    const dataStr = JSON.stringify(data, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `cycle_data_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    tg.showPopup({
        title: 'Экспорт завершён',
        message: 'Данные сохранены в файл',
        buttons: [{type: 'ok'}]
    });
}

// Обновлённые функции навигации
function showStats() {
    if (event.target.classList.contains('premium-feature')) {
        showPremiumModal();
        return;
    }
    switchView('stats-view');
    updateStats();
}

function showPartners() {
    if (event.target.classList.contains('premium-feature')) {
        showPremiumModal();
        return;
    }
    switchView('partners-view');
}

// Форматирование даты
function formatDate(date) {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString('ru-RU');
}

// Загрузка циклов партнёров
async function loadPartnerCycles() {
    // Здесь должен быть API вызов
    partnerCycles = [
        {
            username: 'Анна',
            last_cycle_start: '2026-11-15',
            avg_cycle_length: 28,
            cycles: [
                {start_date: '2026-11-15', period_length: 5},
                {start_date: '2026-10-18', period_length: 6}
            ]
        }
    ];
}

// Остальные функции остаются без изменений...