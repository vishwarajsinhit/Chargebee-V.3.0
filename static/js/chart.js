/**
 * Chargebee Billing System - Chart Visualizations
 * Consolidated Chart.js logic for Dashboard and Admin Panel
 */

/* ============================================
   DASHBOARD CHARTS
   ============================================ */
function initializeDashboardCharts(revenueLabels, revenueData, paidCount, unpaidCount) {
    if (!document.getElementById('revenueChart')) return;

    // Revenue Trend Chart (Bar)
    const revenueCtx = document.getElementById('revenueChart').getContext('2d');
    new Chart(revenueCtx, {
        type: 'bar',
        data: {
            labels: revenueLabels,
            datasets: [{
                label: 'Revenue (₹)',
                data: revenueData,
                backgroundColor: 'rgba(37, 99, 235, 0.7)',
                borderColor: 'rgba(37, 99, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function (value) {
                            return '₹' + value.toLocaleString();
                        },
                        font: { size: 10 }
                    }
                },
                x: {
                    ticks: { font: { size: 10 } }
                }
            }
        }
    });

    // Invoice Status Chart (Doughnut)
    if (document.getElementById('statusChart')) {
        const statusCtx = document.getElementById('statusChart').getContext('2d');
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['Paid', 'Unpaid'],
                datasets: [{
                    data: [paidCount, unpaidCount],
                    backgroundColor: [
                        'rgba(34, 197, 94, 0.7)',
                        'rgba(234, 88, 12, 0.7)'
                    ],
                    borderColor: [
                        'rgba(34, 197, 94, 1)',
                        'rgba(234, 88, 12, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            font: { size: 10 },
                            padding: 8
                        }
                    }
                }
            }
        });
    }
}

/* ============================================
   ADMIN PANEL CHARTS
   ============================================ */
function initializeAdminPanelCharts(data) {
    // 1. Invoice Trend Line Chart
    if (document.getElementById('invoiceTrendChart')) {
        const trendCtx = document.getElementById('invoiceTrendChart').getContext('2d');
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: data.monthlyLabels,
                datasets: [{
                    label: 'Total Invoices',
                    data: data.monthlyInvoices,
                    borderColor: '#4F46E5', // Indigo-600
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#4F46E5',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }, {
                    label: 'Paid Invoices',
                    data: data.monthlyPaid,
                    borderColor: '#10B981', // Emerald-500
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#10B981',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } }
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#f3f4f6' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 2. Top Products Doughnut Chart
    if (document.getElementById('topProductsChart')) {
        const topProductsCtx = document.getElementById('topProductsChart').getContext('2d');
        new Chart(topProductsCtx, {
            type: 'doughnut',
            data: {
                labels: data.topProductNames,
                datasets: [{
                    data: data.topProductSales,
                    backgroundColor: [
                        '#3B82F6', // Blue-500
                        '#10B981', // Emerald-500
                        '#F59E0B', // Amber-500
                        '#8B5CF6', // Violet-500
                        '#EC4899'  // Pink-500
                    ],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 12, usePointStyle: true, font: { size: 10 } } }
                }
            }
        });
    }

    // 3. Customer Activity Doughnut Chart
    if (document.getElementById('customerActivityChart')) {
        const customerActivityCtx = document.getElementById('customerActivityChart').getContext('2d');
        new Chart(customerActivityCtx, {
            type: 'doughnut',
            data: {
                labels: ['Active (7 days)', 'Inactive'],
                datasets: [{
                    data: [data.activeCustomers, data.totalCustomers - data.activeCustomers],
                    backgroundColor: [
                        '#0EA5E9', // Sky-500
                        '#CBD5E1'  // Slate-300
                    ],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 12, usePointStyle: true, font: { size: 10 } } }
                }
            }
        });
    }

    // 4. Top Customers Horizontal Bar Chart
    if (document.getElementById('topCustomersChart')) {
        const topCustomersCtx = document.getElementById('topCustomersChart').getContext('2d');
        new Chart(topCustomersCtx, {
            type: 'bar',
            data: {
                labels: data.topCustomerNames,
                datasets: [{
                    label: 'Revenue',
                    data: data.topCustomerRevenue,
                    backgroundColor: [
                        '#3B82F6', // Blue-500
                        '#10B981', // Emerald-500
                        '#F59E0B', // Amber-500
                        '#8B5CF6', // Violet-500
                        '#EC4899'  // Pink-500
                    ],
                    borderRadius: 4,
                    barPercentage: 0.6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: '#f3f4f6' },
                        ticks: {
                            callback: function (value) {
                                return '₹' + value.toLocaleString();
                            },
                            font: { size: 10 }
                        }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } }
                    }
                }
            }
        });
    }
}
