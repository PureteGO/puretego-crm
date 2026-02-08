/**
 * PURETEGO CRM - Reactive Dashboard
 * Gerencia a atualização automática de métricas e tarefas sem reload.
 */

class ReactiveDashboard {
    constructor(config) {
        this.userId = config.userId;
        this.role = config.role;
        this.pollInterval = config.pollInterval || 30000;
        this.lastUpdate = new Date();

        console.log('Reactive Dashboard Initialized for role:', this.role);
        this.startPolling();
    }

    startPolling() {
        setInterval(() => {
            this.refreshData();
        }, this.pollInterval);
    }

    async refreshData() {
        console.log('Refreshing dashboard data...');
        try {
            // 1. Atualizar Agenda (Tasks de hoje e amanhã)
            const agendaResponse = await fetch('/interactions/agenda');
            if (agendaResponse.ok) {
                const agenda = await agendaResponse.json();
                this.updateAgendaList('todayList', 'todayCount', agenda.today);
                this.updateAgendaList('upcomingList', 'upcomingCount', agenda.upcoming);
            }

            // 2. Atualizar Métricas específicas se houver endpoint
            const statsResponse = await fetch('/finance/receivables/summary');
            if (statsResponse.ok) {
                const stats = await statsResponse.json();
                this.updateGlobalStats(stats);
            }

        } catch (error) {
            console.error('Error refreshing dashboard:', error);
        }
    }

    updateAgendaList(listId, countId, tasks) {
        const list = document.getElementById(listId);
        const countBadge = document.getElementById(countId);
        if (!list || !countBadge) return;

        // Só atualiza se o número de itens mudou ou se for a primeira vez
        // Para simplificar agora, atualizamos sempre, mas uma comparação de hashes seria melhor
        countBadge.textContent = tasks.length;

        if (tasks.length === 0) {
            list.innerHTML = `<p class="text-muted text-center my-3">${translations.noTasksToday}</p>`;
            return;
        }

        let html = '';
        tasks.forEach(task => {
            const icon = task.is_call ? '<i class="bi bi-telephone"></i>' : '<i class="bi bi-geo-alt"></i>';
            const d = new Date(task.date);
            const dateStr = d.toLocaleDateString(undefined, { day: '2-digit', month: '2-digit' }) + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            html += `
                <a href="/clients/${task.client_id}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center animate__animated animate__fadeIn">
                    <div>
                        <span class="me-2 text-primary">${icon}</span>
                        <strong>${task.type_name}</strong>
                        <div class="small text-muted">${task.client_name}</div>
                    </div>
                    <span class="badge bg-light text-dark border">${dateStr}</span>
                </a>
            `;
        });
        list.innerHTML = html;
    }

    updateGlobalStats(data) {
        // Atualizar cards de métricas globais se existirem
        const elements = {
            'stat-awaiting-payment': data.awaiting_payment,
            'stat-pending-contracts': data.pending_contracts,
            'stat-won-amount': data.won_amount // Adicionado para consistência futura
        };

        for (const [id, value] of Object.entries(elements)) {
            const el = document.getElementById(id);
            if (el) {
                // Se for valor numérico, formatar como moeda ou apenas número
                if (id === 'stat-awaiting-payment' || id === 'stat-won-amount') {
                    // Aqui seria ideal ter uma função de formatação de moeda global no JS
                    el.textContent = value.toLocaleString();
                } else {
                    el.textContent = value;
                }
            }
        }
    }
}
