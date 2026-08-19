/* TechTrend E-Commerce Frontend Core JavaScript Module */

const TechTrend = {
  
  // Toast Notification System
  showToast(message, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    
    const iconMap = {
      success: 'bi-check-circle-fill',
      error: 'bi-exclamation-triangle-fill',
      warning: 'bi-exclamation-circle-fill',
      info: 'bi-info-circle-fill'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <i class="bi ${iconMap[type] || 'bi-bell-fill'}"></i>
      <span>${message}</span>
    `;
    
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  // Cart Operations
  async addToCart(productId, quantity = 1) {
    try {
      const res = await fetch('/api/cart/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, quantity: quantity })
      });
      const data = await res.json();
      
      if (res.status === 401 && data.redirect_url) {
        this.showToast(data.message, 'warning');
        setTimeout(() => window.location.href = data.redirect_url, 1200);
        return;
      }
      
      if (data.success) {
        this.showToast(data.message, 'success');
        this.updateCartBadge(data.total_items_count);
      } else {
        this.showToast(data.message, 'error');
      }
    } catch (err) {
      this.showToast('Failed to add item to cart.', 'error');
    }
  },

  async updateCartQuantity(itemId, newQty) {
    try {
      const res = await fetch('/api/cart/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId, quantity: newQty })
      });
      const data = await res.json();
      if (data.success) {
        location.reload();
      } else {
        this.showToast(data.message, 'error');
      }
    } catch (err) {
      this.showToast('Error updating cart.', 'error');
    }
  },

  async removeCartItem(itemId) {
    if (!confirm('Are you sure you want to remove this item from your cart?')) return;
    try {
      const res = await fetch('/api/cart/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast(data.message, 'success');
        location.reload();
      }
    } catch (err) {
      this.showToast('Error removing cart item.', 'error');
    }
  },

  updateCartBadge(count) {
    const badge = document.getElementById('navCartBadge');
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    }
  },

  // Wishlist Operations
  async toggleWishlist(productId, btnElement) {
    try {
      const isRemove = btnElement && btnElement.classList.contains('active');
      const endpoint = isRemove ? '/api/wishlist/remove' : '/api/wishlist/add';
      
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId })
      });
      const data = await res.json();
      
      if (res.status === 401 && data.redirect_url) {
        this.showToast(data.message, 'warning');
        setTimeout(() => window.location.href = data.redirect_url, 1200);
        return;
      }

      if (data.success) {
        this.showToast(data.message, 'success');
        if (btnElement) {
          btnElement.classList.toggle('active');
          const icon = btnElement.querySelector('i');
          if (icon) {
            icon.className = isRemove ? 'bi bi-heart' : 'bi bi-heart-fill';
          }
        }
      }
    } catch (err) {
      this.showToast('Wishlist action failed.', 'error');
    }
  },

  async moveToCart(productId) {
    try {
      const res = await fetch('/api/wishlist/move-to-cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast(data.message, 'success');
        location.reload();
      } else {
        this.showToast(data.message, 'error');
      }
    } catch (err) {
      this.showToast('Failed to move item to cart.', 'error');
    }
  },

  // Auto-complete Search Init
  initSearchAutocomplete() {
    const searchInput = document.getElementById('searchInput');
    const autoBox = document.getElementById('searchAutocomplete');
    if (!searchInput || !autoBox) return;

    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      const query = e.target.value.trim();
      if (query.length < 2) {
        autoBox.classList.remove('active');
        autoBox.innerHTML = '';
        return;
      }

      debounceTimer = setTimeout(async () => {
        try {
          const res = await fetch(`/api/products/search?q=${encodeURIComponent(query)}`);
          const items = await res.json();
          if (items.length === 0) {
            autoBox.innerHTML = '<div style="padding: 1rem; color: var(--text-dim); text-align: center;">No products found</div>';
          } else {
            autoBox.innerHTML = items.map(item => `
              <a href="/product/${item.id}" class="search-item">
                <img src="${item.image}" alt="${item.name}">
                <div>
                  <div style="font-weight: 700; color: var(--text-main); font-size: 0.9rem;">${item.name}</div>
                  <div style="font-size: 0.8rem; color: var(--color-accent);">₹${item.discounted_price.toLocaleString('en-IN')} <span style="color: var(--text-dim); text-decoration: line-through; margin-left: 6px;">₹${item.price.toLocaleString('en-IN')}</span></div>
                </div>
              </a>
            `).join('');
          }
          autoBox.classList.add('active');
        } catch (err) {
          console.error(err);
        }
      }, 250);
    });

    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && !autoBox.contains(e.target)) {
        autoBox.classList.remove('active');
      }
    });
  },

  // User Dropdown Toggle
  initUserDropdown() {
    const btn = document.getElementById('userMenuBtn');
    const list = document.getElementById('userMenuList');
    if (!btn || !list) return;

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      list.classList.toggle('show');
    });

    document.addEventListener('click', () => {
      list.classList.remove('show');
    });
  }
};

document.addEventListener('DOMContentLoaded', () => {
  TechTrend.initSearchAutocomplete();
  TechTrend.initUserDropdown();
  
  // Refresh cart badge on load
  fetch('/api/cart')
    .then(r => r.json())
    .then(data => {
      if (data.total_items_count !== undefined) {
        TechTrend.updateCartBadge(data.total_items_count);
      }
    })
    .catch(() => {});
});
