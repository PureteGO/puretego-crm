/**
 * PURETEGO CRM - Reactive Dashboard Logic
 * Handles real-time polling for tasks and metrics
 */

class ReactiveDashboard {
    constructor(options = {}) {
        this.pollInterval = options.pollInterval || 30000; // 30 seconds
        this.userId = options.userId;
        this.role = options.role;
        this.intervalId = null;
        
        this.init();
    }

    init() {
        console.log(`[Dashboard] Initializing reactive mode for role: ${this.role}`);
        this.updateTasks();
        this.startPolling();
    }

    startPolling() {
        this.intervalId = setInterval(() => {
            this.updateTasks();
            this.updateMetrics();
        }, this.pollInterval);
    }

    stopPolling() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
    }

    async updateTasks() {
        try {
            const response = await fetch('/api/tasks/summary');
            const data = await response.json();
            
            if (data.success) {
                this.renderTaskLists(data);
                this.updateGlobalCounters(data);
            }
        } catch (error) {
            console.error('[Dashboard] Error fetching tasks:', error);
        }
    }

    updateGlobalCounters(data) {
        // Update overdue badge in navbar/dashboard if exists
        const overdueBadge = document.getElementById('overdue-tasks-count');
        if (overdueBadge) {
            overdueBadge.textContent = data.overdue_count;
            overdueBadge.parentElement.style.display = data.overdue_count > 0 ? 'inline-block' : 'none';
        }
        
        // Update specific dashboard widgets
        const totalPendingEl = document.getElementById('total-pending-tasks');
        if (totalPendingEl) totalPendingEl.textContent = data.total_pending;
    }

    renderTaskLists(data) {
        const container = document.getElementById('workflow-tasks-container');
        if (!container) return;

        if (data.tasks.length === 0) {
            container.innerHTML = `<div class="p-4 text-center text-muted">🎉 Nenhuma tarefa pendente!</div>`;
            return;
        }

        let html = '<div class="list-group list-group-flush">';
        data.tasks.forEach(task => {
            const isOverdue = new Date(task.due_date) < new Date();
            const badgeClass = isOverdue ? 'bg-danger' : 'bg-primary';
            
            html += `
                <div class="list-group-item list-group-item-action border-start border-4 ${isOverdue ? 'border-danger' : 'border-primary'}">
                    <div class="d-flex w-100 justify-content-between align-items-center">
                        <h6 class="mb-1 fw-bold">${task.title}</h6>
                        <span class="badge ${badgeClass}">${this.formatDate(task.due_date)}</span>
                    </div>
                    <p class="mb-1 small text-secondary">${task.description}</p>
                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <small class="text-muted"><i class="bi bi-tag"></i> ${task.type}</small>
                        <button class="btn btn-sm btn-outline-success py-0" onclick="completeDashboardTask(${task.id})">
                            <i class="bi bi-check2"></i> Concluir
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    }

    async updateMetrics() {
        // Here we could poll for other metrics if needed
        // For now, task synchronization is the priority
    }

    formatDate(dateStr) {
        const d = new Date(dateStr);
        return d.toLocaleDateString(undefined, { day: '2-digit', month: '2-digit' });
    }
}

// Global helper for completing tasks from the dashboard
async function completeDashboardTask(taskId) {
    if (!confirm('Deseja marcar esta tarefa como concluída?')) return;
    
    try {
        const response = await fetch(`/tasks/${taskId}/complete`, { 
            method: 'POST',
            headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content') }
        });
        const data = await response.json();
        if (data.success) {
            // Task completed successfully, refresh dashboard data
            if (window.dashboardInstance) {
                window.dashboardInstance.updateTasks();
            }
        }
    } catch (error) {
        console.error('Error completing task:', error);
    }
}
