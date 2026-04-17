/**
 * Chargebee Billing System - Combined Scripts
 * All JavaScript consolidated into a single file
 */

/* ============================================
   TOAST NOTIFICATION SYSTEM
   ============================================ */
function showToast(message, type = 'error') {
    const container = document.getElementById('toast-container');
    if (!container) {
        alert(message);
        return;
    }

    const toast = document.createElement('div');
    const isError = type === 'error';
    const isSuccess = type === 'success';

    toast.className = `transform transition-all duration-300 translate-y-[-1rem] opacity-0 flex items-center w-full max-w-sm p-4 space-x-3 bg-white shadow-lg pointer-events-auto rounded-md border-l-4`;

    if (isError) {
        toast.classList.add('border-red-500', 'text-red-700');
    } else if (isSuccess) {
        toast.classList.add('border-green-500', 'text-green-700');
    } else {
        toast.classList.add('border-blue-500', 'text-blue-700');
    }

    const icon = isError ? 'fa-circle-exclamation text-red-500' : isSuccess ? 'fa-check-circle text-green-500' : 'fa-info-circle text-blue-500';

    toast.innerHTML = `
        <div class="flex items-center gap-3 w-full">
            <i class="fas ${icon} text-lg"></i>
            <span class="text-sm font-medium flex-1 break-words">${message}</span>
            <button onclick="
                const t = this.closest('.border-l-4');
                t.classList.add('opacity-0', 'translate-x-[1rem]');
                setTimeout(() => t.remove(), 300);
            " class="text-gray-400 hover:text-gray-600 focus:outline-none">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.remove('opacity-0', 'translate-y-[-1rem]');
        toast.classList.add('opacity-100', 'translate-y-0');
    });

    setTimeout(() => {
        if (toast.parentElement) {
            toast.classList.remove('opacity-100', 'translate-y-0');
            toast.classList.add('opacity-0', 'translate-x-[1rem]');
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

/* ============================================
   CONFIRMATION MODAL SYSTEM
   ============================================ */
function showConfirm(message, onConfirm) {
    const overlay = document.createElement('div');
    overlay.className = 'fixed inset-0 z-[10000] flex items-center justify-center bg-black/50 backdrop-blur-sm opacity-0 transition-opacity duration-300';

    const formattedMessage = message.replace(/\n/g, '<br>');

    overlay.innerHTML = `
        <div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl max-w-sm w-full mx-4 transform scale-95 opacity-0 transition-all duration-300">
            <div class="p-6">
                <div class="flex items-center justify-center w-12 h-12 rounded-full bg-red-100 text-red-600 mb-4 mx-auto">
                    <i class="fas fa-exclamation-triangle text-xl"></i>
                </div>
                <h3 class="text-lg font-bold text-center text-slate-900 dark:text-white mb-2">Are you sure?</h3>
                <p class="text-sm text-center text-slate-500 dark:text-slate-400 mb-6">${formattedMessage}</p>
                <div class="flex gap-3">
                    <button id="confirm-cancel-btn" class="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-slate-50 dark:hover:bg-slate-600 rounded-lg text-sm font-semibold transition-colors">Cancel</button>
                    <button id="confirm-ok-btn" class="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold transition-colors shadow-sm">Confirm</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    const modal = overlay.querySelector('div.transform');

    requestAnimationFrame(() => {
        overlay.classList.remove('opacity-0');
        modal.classList.remove('scale-95', 'opacity-0');
    });

    const closeModal = () => {
        overlay.classList.add('opacity-0');
        modal.classList.add('scale-95', 'opacity-0');
        setTimeout(() => overlay.remove(), 300);
    };

    overlay.querySelector('#confirm-cancel-btn').addEventListener('click', closeModal);
    overlay.querySelector('#confirm-ok-btn').addEventListener('click', () => {
        closeModal();
        if (typeof onConfirm === 'function') onConfirm();
    });
}

/* ============================================
   THEME TOGGLE FUNCTIONALITY
   ============================================ */
function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('themeIcon');
    const iconCollapsed = document.getElementById('themeIconCollapsed');
    const currentTheme = localStorage.getItem('theme') || 'light';

    if (currentTheme === 'light') {
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
        // Moon icon (SVG) for expanded
        if (icon) icon.innerHTML = '<path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/>';
        // Moon icon (FA) for collapsed
        if (iconCollapsed) {
            iconCollapsed.classList.remove('fa-sun');
            iconCollapsed.classList.add('fa-moon');
        }
    } else {
        html.classList.remove('dark');
        localStorage.setItem('theme', 'light');
        // Sun icon (SVG) for expanded
        if (icon) icon.innerHTML = '<path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"/>';
        // Sun icon (FA) for collapsed
        if (iconCollapsed) {
            iconCollapsed.classList.remove('fa-moon');
            iconCollapsed.classList.add('fa-sun');
        }
    }
}

// Apply saved theme on page load
(function () {
    const savedTheme = localStorage.getItem('theme') || 'light';
    const html = document.documentElement;
    const icon = document.getElementById('themeIcon');
    const iconCollapsed = document.getElementById('themeIconCollapsed');

    if (savedTheme === 'dark') {
        html.classList.add('dark');
        if (icon) {
            icon.innerHTML = '<path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/>';
        }
        if (iconCollapsed) {
            iconCollapsed.classList.remove('fa-sun');
            iconCollapsed.classList.add('fa-moon');
        }
    } else {
        html.classList.remove('dark');
        if (icon) {
            icon.innerHTML = '<path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"/>';
        }
        if (iconCollapsed) {
            iconCollapsed.classList.remove('fa-moon');
            iconCollapsed.classList.add('fa-sun');
        }
    }
})();


/* ============================================
   LOGIN PAGE FUNCTIONALITY
   ============================================ */
function togglePassword() {
    const passwordField = document.getElementById('passwordField');
    const eyeIcon = document.getElementById('eyeIcon');

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        // Eye with slash (hide)
        eyeIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path>';
    } else {
        passwordField.type = 'password';
        // Eye (show)
        eyeIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>';
    }
}

/* ============================================
   VERTICAL SLIDER FUNCTIONALITY - AUTOMATIC REVERSE WITH ARROWS
   ============================================ */
// Initialize automatic vertical slider with reverse animation if on login page
if (document.querySelector('.slider-container')) {
    const sliderContainer = document.querySelector('.slider-container');
    const slideRight = document.querySelector('.right-slide');
    const slideLeft = document.querySelector('.left-slide');
    const slidesLength = slideRight.querySelectorAll('div').length;
    const upArrow = document.querySelector('.slider-arrow-up');
    const downArrow = document.querySelector('.slider-arrow-down');

    let activeSlideIndex = 0;
    let direction = 1; // 1 for forward, -1 for reverse
    let autoSlideInterval;

    slideLeft.style.top = `-${(slidesLength - 1) * 100}vh`;

    const changeSlide = (manualDirection = null) => {
        const sliderHeight = sliderContainer.clientHeight;

        // If manual direction provided, use it; otherwise use auto direction
        if (manualDirection !== null) {
            activeSlideIndex += manualDirection;
            // Keep within bounds
            if (activeSlideIndex < 0) activeSlideIndex = 0;
            if (activeSlideIndex >= slidesLength) activeSlideIndex = slidesLength - 1;

            // Update direction based on position
            if (activeSlideIndex >= slidesLength - 1) {
                direction = -1;
            } else if (activeSlideIndex <= 0) {
                direction = 1;
            }
        } else {
            // Auto-advance
            activeSlideIndex += direction;

            // Reverse direction when reaching the end or beginning
            if (activeSlideIndex >= slidesLength - 1) {
                direction = -1; // Start going backwards
            } else if (activeSlideIndex <= 0) {
                direction = 1; // Start going forwards
            }
        }

        slideRight.style.transform = `translateY(-${activeSlideIndex * sliderHeight}px)`;
        slideLeft.style.transform = `translateY(${activeSlideIndex * sliderHeight}px)`;
    };

    // Start auto-advance
    const startAutoSlide = () => {
        if (autoSlideInterval) clearInterval(autoSlideInterval);
        autoSlideInterval = setInterval(() => changeSlide(), 3000);
    };

    // Arrow button handlers
    upArrow.addEventListener('click', () => {
        changeSlide(-1); // Go up (previous slide)
        startAutoSlide(); // Reset timer
    });

    downArrow.addEventListener('click', () => {
        changeSlide(1); // Go down (next slide)
        startAutoSlide(); // Reset timer
    });

    // Start automatic sliding
    startAutoSlide();

    // Pause on hover
    sliderContainer.addEventListener('mouseenter', () => {
        if (autoSlideInterval) clearInterval(autoSlideInterval);
    });

    // Resume on mouse leave
    sliderContainer.addEventListener('mouseleave', () => {
        startAutoSlide();
    });
}



/* ============================================
   DASHBOARD FUNCTIONALITY
   ============================================ */
// Toggle Recent Invoices Panel
function toggleRecentInvoices() {
    const panel = document.getElementById('recentInvoicesPanel');
    const icon = document.getElementById('toggleIcon');

    if (panel.style.maxHeight === '0px' || panel.style.maxHeight === '') {
        panel.style.maxHeight = panel.scrollHeight + 'px';
        icon.style.transform = 'rotate(180deg)';
    } else {
        panel.style.maxHeight = '0px';
        icon.style.transform = 'rotate(0deg)';
    }
}

// Recent Invoices Panel is closed by default.




/* ============================================
   INVOICE FORM FUNCTIONALITY
   ============================================ */
let items = [];
let products = [];
let invoiceFormInitialized = false;

// Add a new line item
function addItem() {
    items.push({ id: Date.now(), productId: "", quantity: 1, price: 0 });
    renderTable();
}


// Remove a line item
function removeItem(id) {
    items = items.filter(i => i.id !== id);
    renderTable();
}

// Update item properties
function updateItem(id, field, value) {
    const item = items.find(i => i.id === id);
    if (field === 'productId') {
        // Check if this product already exists in another line item
        if (value) {
            const existingItem = items.find(i => i.id !== id && i.productId == value);
            if (existingItem) {
                // Merge quantity into the existing row
                const product = products.find(p => p.id == value);
                let newQty = existingItem.quantity + item.quantity;
                if (product && newQty > product.stock) {
                    showToast(`Only ${product.stock} units of "${product.name}" are available in stock. Quantity set to max.`, 'error');
                    newQty = product.stock;
                }
                existingItem.quantity = newQty;
                // Remove the current (duplicate) row
                items = items.filter(i => i.id !== id);
                renderTable();
                return;
            }
        }
        item.productId = value;
        const product = products.find(p => p.id == value);
        if (product) {
            item.price = product.price;
            // If new product has less stock than current quantity, limit it
            if (item.quantity > product.stock) {
                item.quantity = product.stock > 0 ? product.stock : 1;
            }
        }
    } else if (field === 'quantity') {
        const product = products.find(p => p.id == item.productId);
        let newQty = parseInt(value) || 0;

        if (product) {
            // Calculate remaining stock: total stock minus what OTHER rows are using
            const othersAllocated = getAllocatedQty(item.productId, item.id);
            const availableForThisRow = product.stock - othersAllocated;
            if (newQty > availableForThisRow) {
                showToast(`Only ${availableForThisRow} units of "${product.name}" are available in stock.`, 'error');
                newQty = availableForThisRow;
            }
        }

        item.quantity = newQty;
    }
    renderTable();
}

// Calculate total allocated quantity for a product across all line items, excluding a specific item
function getAllocatedQty(productId, excludeItemId) {
    let allocated = 0;
    items.forEach(i => {
        if (i.productId == productId && i.id !== excludeItemId) {
            allocated += i.quantity;
        }
    });
    return allocated;
}

// Adjust quantity by +1 or -1 via stepper buttons
function adjustQty(id, delta) {
    const item = items.find(i => i.id === id);
    if (!item) return;
    const newQty = Math.max(1, item.quantity + delta);
    updateItem(id, 'quantity', newQty);
}

// Render the invoice items table
function renderTable() {
    const tbody = document.getElementById('itemsBody');
    if (!tbody) return; // Exit if not on invoice page

    tbody.innerHTML = '';
    let total = 0;

    // Calculate total allocated quantities per product (across all rows)
    const totalAllocated = {};
    items.forEach(i => {
        if (i.productId) {
            totalAllocated[i.productId] = (totalAllocated[i.productId] || 0) + i.quantity;
        }
    });

    items.forEach(item => {
        const product = products.find(p => p.id == item.productId);
        const gstRate = product ? product.gst : 0;
        const taxable = item.price * item.quantity;
        const tax = (taxable * gstRate) / 100;
        const rowTotal = taxable + tax;
        total += rowTotal;

        // For this row, calculate the max qty allowed (stock minus what OTHER rows use)
        const othersAllocated = product ? getAllocatedQty(product.id, item.id) : 0;
        const remainingForRow = product ? product.stock - othersAllocated : 0;

        const tr = document.createElement('tr');
        tr.className = `border-b border-gray-200 ${product && product.stock <= 0 ? 'bg-red-50' : ''}`;
        tr.innerHTML = `
            <td class="px-2 py-1.5">
                <select onchange="updateItem(${item.id}, 'productId', this.value)" class="border border-gray-300 px-2 py-1 w-full text-sm ${product && product.stock <= 0 ? 'text-red-600 font-bold' : ''}">
                    <option value="">Select...</option>
                    ${products.map(p => {
            const usedByAll = totalAllocated[p.id] || 0;
            const remaining = p.stock - usedByAll;
            const isOutOfStock = p.stock <= 0;
            const displayStock = isOutOfStock ? '(OUT OF STOCK)' : `(${remaining} in stock)`;
            return `
                        <option value="${p.id}" ${p.id == item.productId ? 'selected' : ''} ${isOutOfStock ? 'class="text-red-500 font-bold"' : ''}>
                            ${p.name} ${displayStock}
                        </option>
                        `;
        }).join('')}
                </select>
                ${product && product.stock <= 0 ? '<div class="text-[10px] text-red-600 font-bold mt-0.5">⚠️ THIS PRODUCT IS CURRENTLY OUT OF STOCK</div>' : ''}
            </td>
            <td class="px-2 py-1.5 text-right text-sm">
                ₹${item.price}
                ${gstRate > 0 ? `<span class="text-xs text-gray-500"> (+${gstRate}%)</span>` : ''}
            </td>
            <td class="px-2 py-1.5 text-right">
                <div class="custom-number-wrapper" style="margin-left: auto;">
                    <button type="button" onclick="adjustQty(${item.id}, -1)" 
                        ${product && product.stock <= 0 ? 'disabled' : ''} 
                        class="number-btn number-btn-minus" title="Decrease">
                        <i class="fas fa-minus"></i>
                    </button>
                    <input type="number" min="1" max="${product ? remainingForRow : ''}" value="${item.quantity}" 
                        ${product && product.stock <= 0 ? 'disabled' : ''} 
                        onchange="updateItem(${item.id}, 'quantity', this.value)" data-no-custom
                        class="custom-number-input" style="min-width:36px; width:36px;">
                    <button type="button" onclick="adjustQty(${item.id}, 1)" 
                        ${product && product.stock <= 0 ? 'disabled' : ''} 
                        class="number-btn number-btn-plus" title="Increase">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            </td>
            <td class="px-2 py-1.5 text-right font-bold text-sm">
                ₹${rowTotal.toFixed(2)}
                ${tax > 0 ? `<div class="text-xs text-gray-500 font-normal">Tax: ₹${tax.toFixed(2)}</div>` : ''}
            </td>
            <td class="px-2 py-1.5 text-center">
                <button type="button" onclick="removeItem(${item.id})" class="text-red-600 hover:text-red-800 text-sm p-1 rounded hover:bg-red-50" title="Remove Item">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById('grandTotal').textContent = '₹' + total.toFixed(2);
}

// Load existing invoice data into the form for editing
function loadInvoiceForEdit(invoice) {
    // Populate simple fields
    if (document.getElementById('customer')) {
        document.getElementById('customer').value = invoice.customer || "";
    }
    if (document.getElementById('dispatch_through')) {
        document.getElementById('dispatch_through').value = invoice.dispatch_through || "";
    }
    if (document.getElementById('due_date')) {
        document.getElementById('due_date').value = invoice.due_date || "";
    }
    if (document.getElementById('payment_note')) {
        document.getElementById('payment_note').value = invoice.payment_note || "";
    }
    if (document.getElementById('document_note')) {
        document.getElementById('document_note').value = invoice.document_note || "";
    }

    // Populate Items
    // Reset items first (even though strict init does it, allow re-entry)
    items = [];

    if (invoice.items && Array.isArray(invoice.items)) {
        invoice.items.forEach(item => {
            // Mapping from API structure to internal structure
            // API: { product: ID, quantity: N, price: N.NN }
            // Internal: { id: timestamp, productId: ID, quantity: N, price: N.NN }
            items.push({
                id: Date.now() + Math.random(), // Unique ID
                productId: item.product,
                quantity: item.quantity,
                price: parseFloat(item.price)
            });
        });
        renderTable();
    }
}

// Submit invoice to API (Create or Update)
async function submitInvoice(e, csrfToken, invoiceId = null) {
    e.preventDefault();
    const customerId = document.getElementById('customer').value;

    if (!customerId || items.length === 0) {
        showToast("Please select customer and add items.", 'error');
        return;
    }

    // Aggregate validation: Check total requested quantity per product
    const aggregateQuantities = new Map();
    for (const item of items) {
        const qty = parseInt(item.quantity) || 0;
        aggregateQuantities.set(item.productId, (aggregateQuantities.get(item.productId) || 0) + qty);
    }

    for (const [productId, totalQty] of aggregateQuantities) {
        const product = products.find(p => p.id == productId);
        if (product) {
            // Note: For existing invoices, we need to be careful.
            //Ideally backend handles "net change" validation.
            // Frontend validation might be overly strict if it doesn't account for already allocated stock.
            // However, since we are doing a full replace, checking against current stock IS correct 
            // IF we assume current stock does NOT include the items we are about to delete.
            // BUT current stock DOES include them (they are deducted).
            // So if I have 10 items in invoice, and stock is 0. I edit to 10 items.
            // Frontend sees stock 0, request 10 -> FAIL.
            // FIX: We should rely on backend validation for edits OR strictly calculate net change here.

            // Allow submission if editing, let backend handle complex net-stock validation
            if (!invoiceId) {
                if (product.stock <= 0) {
                    showToast(`"${product.name}" is out of stock. Please remove it to continue.`, 'error');
                    return;
                }
                if (totalQty > product.stock) {
                    showToast(`Total quantity for "${product.name}" (${totalQty}) exceeds available stock (${product.stock}).`, 'error');
                    return;
                }
            }
        }
    }

    const payload = {
        customer: customerId,
        items: items.map(i => ({ product: i.productId, quantity: i.quantity, price: i.price })),
        dispatch_through: document.getElementById('dispatch_through').value,
        due_date: document.getElementById('due_date').value || null,
        payment_note: document.getElementById('payment_note').value,
        document_note: document.getElementById('document_note').value
    };

    const url = invoiceId ? `/api/invoices/${invoiceId}/` : '/api/invoices/';
    const method = invoiceId ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const data = await response.json();
            window.location.href = `/invoices/${data.id}/`;
        } else {
            let errorMsg = "Unknown error";
            try {
                const errData = await response.json();
                errorMsg = JSON.stringify(errData);
            } catch (e) {
                // Not JSON, probably 500 HTML
                errorMsg = `Server error (${response.status})`;
            }
            showToast("Error saving invoice: " + errorMsg, 'error');
        }
    } catch (error) {
        console.error('Fetch error:', error);
        showToast("Network error: " + error.message, 'error');
    }
}

// Initialize products data (to be called from template)
function initializeProducts(productsData) {
    // Prevent double initialization
    if (invoiceFormInitialized) {
        console.warn('Invoice form already initialized, skipping duplicate initialization');
        return;
    }

    // Strict Reset: Ensure we start with a fresh form on every load
    items = [];
    products = productsData;

    // Add exactly one empty starting item
    addItem();

    invoiceFormInitialized = true;
}


/* ============================================
   REPORTS PAGE FUNCTIONALITY
   ============================================ */
// Toggle Outstanding Invoices Panel
function toggleOutstanding() {
    const panel = document.getElementById('outstandingPanel');
    const icon = document.getElementById('outstandingIcon');

    if (panel.style.maxHeight === '0px' || panel.style.maxHeight === '') {
        panel.style.maxHeight = '300px';
        icon.style.transform = 'rotate(180deg)';
    } else {
        panel.style.maxHeight = '0px';
        icon.style.transform = 'rotate(0deg)';
    }
}

// Toggle Top Customers Panel
function toggleTopCustomers() {
    const panel = document.getElementById('customersPanel');
    const icon = document.getElementById('customersIcon');

    if (panel.style.maxHeight === '0px' || panel.style.maxHeight === '') {
        panel.style.maxHeight = '300px';
        icon.style.transform = 'rotate(180deg)';
    } else {
        panel.style.maxHeight = '0px';
        icon.style.transform = 'rotate(0deg)';
    }
}

// Reports panels are closed by default.

/* ============================================
   DYNAMIC AJAX SEARCH
   ============================================ */
document.addEventListener('DOMContentLoaded', () => {
    const searchInputs = document.querySelectorAll('input[data-ajax-search]');

    searchInputs.forEach(input => {
        let debounceTimer;
        const form = input.closest('form');

        // Prevent full form submission on Enter
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
            });
        }

        input.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const query = e.target.value;
                const url = new URL(window.location.href);
                url.searchParams.set(input.name || 'q', query);

                // Find a submit button icon in the same form to show a spinner
                let searchIcon = null;
                if (form) {
                    searchIcon = form.querySelector('button[type="submit"] i.fa-search');
                    if (searchIcon) {
                        searchIcon.className = 'fas fa-spinner fa-spin text-xs mr-1';
                    }
                }

                fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');

                        const newContainer = doc.getElementById('ajax-list-container');
                        const oldContainer = document.getElementById('ajax-list-container');

                        if (newContainer && oldContainer) {
                            oldContainer.innerHTML = newContainer.innerHTML;
                            // Re-initialize custom number inputs for the new results
                            initCustomNumberInputs();
                        }

                        if (searchIcon) {
                            searchIcon.className = 'fas fa-search text-xs mr-1';
                        }
                    })
                    .catch(error => {
                        console.error('AJAX Search Error:', error);
                        if (searchIcon) {
                            searchIcon.className = 'fas fa-search text-xs mr-1';
                        }
                    });
            }, 300); // 300ms debounce
        });
    });
});


/* ============================================
   GLOBAL CUSTOM NUMBER INPUT INITIALIZATION
   ============================================ */
function initCustomNumberInputs() {
    const numberInputs = document.querySelectorAll('input[type="number"]:not(.custom-number-input):not([data-no-custom])');

    numberInputs.forEach(input => {
        // Prevent double wrapping
        if (input.parentElement.classList.contains('custom-number-wrapper')) return;

        // Wrap input
        const wrapper = document.createElement('div');
        wrapper.className = 'custom-number-wrapper';
        if (input.className.includes('w-full')) wrapper.classList.add('w-full');

        input.parentNode.insertBefore(wrapper, input);

        // Add Minus Button
        const minusBtn = document.createElement('button');
        minusBtn.type = 'button';
        minusBtn.className = 'number-btn number-btn-minus';
        minusBtn.innerHTML = '<i class="fas fa-minus"></i>';

        // Add Plus Button
        const plusBtn = document.createElement('button');
        plusBtn.type = 'button';
        plusBtn.className = 'number-btn number-btn-plus';
        plusBtn.innerHTML = '<i class="fas fa-plus"></i>';

        // Setup Input
        input.classList.add('custom-number-input');

        // Layout: [Minus] [Input] [Plus]
        wrapper.appendChild(minusBtn);
        wrapper.appendChild(input);
        wrapper.appendChild(plusBtn);

        // Event Listeners
        const step = parseFloat(input.getAttribute('step')) || 1;
        const min = input.hasAttribute('min') ? parseFloat(input.getAttribute('min')) : null;
        const max = input.hasAttribute('max') ? parseFloat(input.getAttribute('max')) : null;

        const handleStep = (delta) => {
            const currentVal = parseFloat(input.value) || 0;
            let newVal = currentVal + (delta * step);

            // Respect bounds
            if (min !== null && newVal < min) newVal = min;
            if (max !== null && newVal > max) newVal = max;

            // Fix decimal precision if step is a float
            if (step % 1 !== 0) {
                const precision = step.toString().split(".")[1].length;
                newVal = parseFloat(newVal.toFixed(precision));
            }

            input.value = newVal;

            // Trigger standard events so other scripts react
            input.dispatchEvent(new Event('change', { bubbles: true }));
            input.dispatchEvent(new Event('input', { bubbles: true }));
        };

        minusBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleStep(-1);
        };

        plusBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleStep(1);
        };
    });
}

// Initial call
document.addEventListener('DOMContentLoaded', initCustomNumberInputs);
