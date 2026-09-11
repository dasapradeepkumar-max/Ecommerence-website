/* E-Commerce Admin Dashboard Controller */

const AdminApp = {
  currentPage: 1,
  currentLimit: 10,
  searchTimer: null,
  pendingDeleteId: null,

  init() {
    this.bindEvents();
    this.loadProducts(1);
  },

  bindEvents() {
    // Real-time price calculation listeners
    const priceInput = document.getElementById('prodPrice');
    const discountInput = document.getElementById('prodDiscount');
    if (priceInput) priceInput.addEventListener('input', () => this.calculateFinalPrice());
    if (discountInput) discountInput.addEventListener('input', () => this.calculateFinalPrice());

    // Search input debouncer
    const searchInput = document.getElementById('adminSearchInput');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        clearTimeout(this.searchTimer);
        this.searchTimer = setTimeout(() => this.loadProducts(1), 300);
      });
    }

    // Filter selects
    ['filterCategory', 'filterStatus', 'filterStock', 'filterSort', 'filterLimit'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('change', () => this.loadProducts(1));
    });

    // Image URL live preview
    const imgUrlInput = document.getElementById('prodImage');
    if (imgUrlInput) {
      imgUrlInput.addEventListener('input', () => this.updateImagePreview(imgUrlInput.value));
    }
  },

  toggleSidebar() {
    const sidebar = document.querySelector('.admin-sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (sidebar) sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('active');
  },

  showModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.add('active');
  },

  closeModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.remove('active');
  },

  // Calculate and display live final price in Add/Edit modal
  calculateFinalPrice() {
    const priceEl = document.getElementById('prodPrice');
    const discountEl = document.getElementById('prodDiscount');
    const displayEl = document.getElementById('prodFinalPricePreview');
    
    if (!priceEl || !displayEl) return;
    
    const price = parseFloat(priceEl.value) || 0;
    const discount = parseFloat(discountEl ? discountEl.value : 0) || 0;
    const finalPrice = Math.max(0, price * (1 - discount / 100));

    if (price > 0) {
      const formattedOriginal = price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      const formattedFinal = finalPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      displayEl.innerHTML = `₹${formattedOriginal} - ${discount}% = <span style="color: var(--color-success); font-weight: 800; font-size: 1.05rem;">₹${formattedFinal}</span>`;
    } else {
      displayEl.innerHTML = `<span style="color: var(--text-dim);">₹0.00</span>`;
    }
  },

  updateImagePreview(url) {
    const previewContainer = document.getElementById('prodImagePreviewContainer');
    const imgEl = document.getElementById('prodImagePreview');
    if (!previewContainer || !imgEl) return;

    if (url && url.trim()) {
      imgEl.src = url.trim();
      previewContainer.style.display = 'block';
    } else {
      previewContainer.style.display = 'none';
    }
  },

  async uploadImageFile(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    
    const formData = new FormData();
    formData.append('image', file);

    const statusMsg = document.getElementById('uploadStatusMsg');
    if (statusMsg) statusMsg.textContent = 'Uploading image...';

    try {
      const res = await fetch('/admin/api/products/upload-image', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById('prodImage').value = data.image_url;
        this.updateImagePreview(data.image_url);
        if (statusMsg) statusMsg.textContent = 'Uploaded successfully!';
        TechTrend.showToast('Image uploaded successfully!', 'success');
      } else {
        if (statusMsg) statusMsg.textContent = data.message || 'Upload failed.';
        TechTrend.showToast(data.message || 'Image upload failed.', 'error');
      }
    } catch (err) {
      if (statusMsg) statusMsg.textContent = 'Upload error.';
      TechTrend.showToast('Error uploading image file.', 'error');
    }
  },

  clearSearch() {
    const searchInput = document.getElementById('adminSearchInput');
    if (searchInput) {
      searchInput.value = '';
      this.loadProducts(1);
    }
  },

  // Fetch product catalog asynchronously
  async loadProducts(page = 1) {
    this.currentPage = page;
    const limitEl = document.getElementById('filterLimit');
    this.currentLimit = limitEl ? parseInt(limitEl.value) || 10 : 10;

    const categoryId = document.getElementById('filterCategory')?.value || 'all';
    const status = document.getElementById('filterStatus')?.value || 'all';
    const stockStatus = document.getElementById('filterStock')?.value || 'all';
    const sortBy = document.getElementById('filterSort')?.value || 'newest';
    const search = document.getElementById('adminSearchInput')?.value.trim() || '';

    const tbody = document.getElementById('productsTableBody');
    if (tbody) {
      tbody.innerHTML = `
        <tr class="skeleton-tr">
          <td colspan="10">
            <div class="skeleton-box" style="margin-bottom: 8px;"></div>
            <div class="skeleton-box" style="margin-bottom: 8px; opacity: 0.7;"></div>
            <div class="skeleton-box" style="opacity: 0.4;"></div>
          </td>
        </tr>
      `;
    }

    const params = new URLSearchParams({
      page: page,
      limit: this.currentLimit,
      category_id: categoryId === 'all' ? '' : categoryId,
      status: status,
      stock_status: stockStatus,
      sort_by: sortBy,
      search: search
    });

    try {
      const res = await fetch(`/admin/api/products?${params.toString()}`);
      const data = await res.json();
      if (data.success) {
        this.renderProductsTable(data.products);
        this.renderPagination(data);
      } else {
        TechTrend.showToast(data.message || 'Failed to load products.', 'error');
      }
    } catch (err) {
      console.error('Error fetching products:', err);
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="10" style="text-align: center; padding: 2rem; color: var(--color-danger);">
              <i class="bi bi-exclamation-octagon" style="font-size: 2rem; display: block; margin-bottom: 0.5rem;"></i>
              Failed to load product catalog. Please try refreshing.
            </td>
          </tr>
        `;
      }
    }
  },

  renderProductsTable(products) {
    const tbody = document.getElementById('productsTableBody');
    if (!tbody) return;

    if (!products || products.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="10" style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
            <i class="bi bi-box-seam" style="font-size: 2.5rem; color: var(--text-dim); display: block; margin-bottom: 0.75rem;"></i>
            <div style="font-weight: 700; font-size: 1.1rem; color: var(--text-main); margin-bottom: 0.25rem;">No products found</div>
            <p style="font-size: 0.85rem; margin-bottom: 1rem;">Try adjusting your search query or filter selections.</p>
            <button class="btn btn-outline btn-sm" onclick="AdminApp.openAddModal()">+ Add New Product</button>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = products.map(p => {
      const origPrice = parseFloat(p.price || 0);
      const disc = parseFloat(p.discount_percent || 0);
      const finalPrice = parseFloat(p.discounted_price || origPrice * (1 - disc / 100));

      const origFormatted = origPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      const finalFormatted = finalPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

      // Stock status badge
      let stockBadgeClass = 'badge-instock';
      let stockText = `${p.stock} in stock`;
      if (p.stock <= 0) {
        stockBadgeClass = 'badge-outstock';
        stockText = 'Out of Stock';
      } else if (p.stock <= 10) {
        stockBadgeClass = 'badge-lowstock';
        stockText = `Low (${p.stock})`;
      }

      // Active status badge
      const activeBadgeClass = p.is_active ? 'badge-active' : 'badge-inactive';
      const activeText = p.is_active ? 'Active' : 'Inactive';

      const imageSrc = p.primary_image || 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80';

      return `
        <tr>
          <td>
            <img src="${imageSrc}" alt="${p.name}" class="prod-thumb" onclick="AdminApp.openViewModal(${p.id})" title="Click to view details">
          </td>
          <td>
            <div style="font-weight: 700; color: var(--text-main); font-size: 0.92rem; max-width: 220px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${p.name}</div>
            <div style="font-size: 0.75rem; color: var(--text-dim);">#${p.id} &bull; ${p.slug || ''}</div>
          </td>
          <td><span style="font-weight: 600; color: var(--text-muted); font-size: 0.85rem;">${p.category_name || '-'}</span></td>
          <td style="white-space: nowrap;">₹${origFormatted}</td>
          <td>
            ${disc > 0 ? `<span style="color: var(--color-accent); font-weight: 800; background: rgba(99, 102, 241, 0.1); padding: 0.15rem 0.4rem; border-radius: 4px;">${disc}% OFF</span>` : `<span style="color: var(--text-dim);">0%</span>`}
          </td>
          <td style="font-weight: 800; color: var(--color-success); white-space: nowrap;">₹${finalFormatted}</td>
          <td><span class="badge ${stockBadgeClass}">${stockText}</span></td>
          <td>
            <span class="badge ${activeBadgeClass}" style="cursor: pointer;" onclick="AdminApp.toggleStatus(${p.id}, ${!p.is_active})" title="Click to toggle Active status">
              ${activeText}
            </span>
          </td>
          <td style="font-size: 0.8rem; color: var(--text-dim); white-space: nowrap;">${p.created_date || '-'}</td>
          <td>
            <div class="action-btn-group">
              <button class="btn-icon btn-icon-view" title="View Product Details" onclick="AdminApp.openViewModal(${p.id})">
                <i class="bi bi-eye"></i>
              </button>
              <button class="btn-icon" title="Edit Product" onclick="AdminApp.openEditModal(${p.id})">
                <i class="bi bi-pencil-square"></i>
              </button>
              <button class="btn-icon btn-icon-danger" title="Delete Product" onclick="AdminApp.openDeleteConfirmModal(${p.id}, '${p.name.replace(/'/g, "\\'")}')">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  renderPagination(data) {
    const infoEl = document.getElementById('paginationInfo');
    const controlsEl = document.getElementById('paginationControls');
    if (!infoEl || !controlsEl) return;

    const total = data.total || 0;
    const page = data.page || 1;
    const limit = data.limit || 10;
    const totalPages = data.total_pages || 1;

    const start = total === 0 ? 0 : (page - 1) * limit + 1;
    const end = Math.min(total, page * limit);

    infoEl.textContent = `Showing ${start} to ${end} of ${total} products`;

    let btnsHtml = '';

    // Previous Button
    btnsHtml += `
      <button class="page-btn" ${page <= 1 ? 'disabled' : ''} onclick="AdminApp.loadProducts(${page - 1})">
        <i class="bi bi-chevron-left"></i> Prev
      </button>
    `;

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= page - 1 && i <= page + 1)) {
        btnsHtml += `
          <button class="page-btn ${i === page ? 'active' : ''}" onclick="AdminApp.loadProducts(${i})">
            ${i}
          </button>
        `;
      } else if (i === page - 2 || i === page + 2) {
        btnsHtml += `<span style="color: var(--text-dim); padding: 0 0.2rem;">...</span>`;
      }
    }

    // Next Button
    btnsHtml += `
      <button class="page-btn" ${page >= totalPages ? 'disabled' : ''} onclick="AdminApp.loadProducts(${page + 1})">
        Next <i class="bi bi-chevron-right"></i>
      </button>
    `;

    controlsEl.innerHTML = btnsHtml;
  },

  // Open Add Product Modal
  openAddModal() {
    document.getElementById('prodModalTitle').textContent = 'Add New Product';
    document.getElementById('prodId').value = '';
    document.getElementById('prodName').value = '';
    document.getElementById('prodSlug').value = '';
    document.getElementById('prodPrice').value = '';
    document.getElementById('prodDiscount').value = '0';
    document.getElementById('prodStock').value = '10';
    document.getElementById('prodShortDesc').value = '';
    document.getElementById('prodDesc').value = '';
    document.getElementById('prodSpecs').value = '';
    document.getElementById('prodImage').value = 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80';
    document.getElementById('prodStatusActive').checked = true;
    document.getElementById('prodFeatured').checked = false;
    document.getElementById('prodTrending').checked = false;

    this.calculateFinalPrice();
    this.updateImagePreview(document.getElementById('prodImage').value);
    this.showModal('modalProduct');
  },

  // Open Edit Product Modal
  async openEditModal(productId) {
    try {
      const res = await fetch(`/admin/api/products/${productId}`);
      const data = await res.json();
      if (!data.success || !data.product) {
        TechTrend.showToast('Could not fetch product details.', 'error');
        return;
      }

      const p = data.product;
      document.getElementById('prodModalTitle').textContent = `Edit Product #${p.id}`;
      document.getElementById('prodId').value = p.id;
      document.getElementById('prodCategory').value = p.category_id;
      document.getElementById('prodName').value = p.name || '';
      document.getElementById('prodSlug').value = p.slug || '';
      document.getElementById('prodPrice').value = p.price || 0;
      document.getElementById('prodDiscount').value = p.discount_percent || 0;
      document.getElementById('prodStock').value = p.stock !== undefined ? p.stock : 10;
      document.getElementById('prodShortDesc').value = p.short_description || '';
      document.getElementById('prodDesc').value = p.description || '';
      document.getElementById('prodSpecs').value = p.specifications || '';
      
      const primaryImg = p.primary_image || (p.images && p.images[0] ? p.images[0].image_url : '');
      document.getElementById('prodImage').value = primaryImg;

      if (p.is_active) {
        document.getElementById('prodStatusActive').checked = true;
      } else {
        document.getElementById('prodStatusInactive').checked = true;
      }

      document.getElementById('prodFeatured').checked = !!p.is_featured;
      document.getElementById('prodTrending').checked = !!p.is_trending;

      this.calculateFinalPrice();
      this.updateImagePreview(primaryImg);
      this.showModal('modalProduct');
    } catch (err) {
      TechTrend.showToast('Error opening edit dialog.', 'error');
    }
  },

  // View Product Modal
  async openViewModal(productId) {
    try {
      const res = await fetch(`/admin/api/products/${productId}`);
      const data = await res.json();
      if (!data.success || !data.product) {
        TechTrend.showToast('Product detail not available.', 'error');
        return;
      }

      const p = data.product;
      const origPrice = parseFloat(p.price || 0);
      const disc = parseFloat(p.discount_percent || 0);
      const finalPrice = parseFloat(p.discounted_price || origPrice * (1 - disc / 100));

      const origFormatted = origPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      const finalFormatted = finalPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

      const imageSrc = p.primary_image || (p.images && p.images[0] ? p.images[0].image_url : 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80');

      const modalBody = document.getElementById('viewModalBody');
      if (modalBody) {
        modalBody.innerHTML = `
          <div style="display: grid; grid-template-columns: minmax(180px, 240px) 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
            <div>
              <img src="${imageSrc}" alt="${p.name}" style="width: 100%; border-radius: var(--radius-md); border: 1px solid var(--border-light); object-fit: cover; max-height: 240px;">
            </div>
            <div>
              <div style="font-size: 0.78rem; font-weight: 700; color: var(--color-brand); text-transform: uppercase; margin-bottom: 0.2rem;">${p.category_name || 'Category'}</div>
              <h2 style="font-size: 1.3rem; font-weight: 800; margin-bottom: 0.5rem; color: var(--text-main);">${p.name}</h2>
              <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 1rem;">${p.short_description || 'No short description provided.'}</p>

              <!-- Price Box -->
              <div style="background: var(--bg-input); border-radius: var(--radius-md); padding: 0.85rem 1rem; margin-bottom: 1rem;">
                <div style="font-size: 0.75rem; color: var(--text-dim); font-weight: 700;">PRICING BREAKDOWN</div>
                <div style="display: flex; align-items: baseline; gap: 0.75rem; margin-top: 0.3rem;">
                  <span style="font-size: 1.4rem; font-weight: 800; color: var(--color-success);">₹${finalFormatted}</span>
                  ${disc > 0 ? `<span style="text-decoration: line-through; color: var(--text-dim); font-size: 0.95rem;">₹${origFormatted}</span>` : ''}
                  ${disc > 0 ? `<span style="color: var(--color-accent); font-weight: 800; font-size: 0.82rem; background: rgba(99, 102, 241, 0.15); padding: 0.1rem 0.5rem; border-radius: 12px;">${disc}% OFF</span>` : ''}
                </div>
              </div>

              <!-- Inventory & Status -->
              <div style="display: flex; flex-wrap: wrap; gap: 0.75rem;">
                <div>
                  <span style="font-size: 0.75rem; color: var(--text-dim); display: block;">STOCK QUANTITY</span>
                  <span style="font-weight: 800; font-size: 1rem;">${p.stock} units</span>
                </div>
                <div style="border-left: 1px solid var(--border-light); padding-left: 0.75rem;">
                  <span style="font-size: 0.75rem; color: var(--text-dim); display: block;">STATUS</span>
                  <span class="badge ${p.is_active ? 'badge-active' : 'badge-inactive'}">${p.is_active ? 'Active' : 'Inactive'}</span>
                </div>
                <div style="border-left: 1px solid var(--border-light); padding-left: 0.75rem;">
                  <span style="font-size: 0.75rem; color: var(--text-dim); display: block;">RATING</span>
                  <span style="font-weight: 700; color: #fbbf24;">★ ${p.avg_rating || 0} (${p.review_count || 0} reviews)</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Tabs or Accordion for Full Description & Specifications -->
          <div style="border-top: 1px solid var(--border-light); padding-top: 1rem;">
            <h4 style="font-size: 0.9rem; font-weight: 800; color: var(--text-main); margin-bottom: 0.4rem;">FULL DESCRIPTION</h4>
            <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.6; white-space: pre-line; margin-bottom: 1rem;">${p.description || 'N/A'}</p>

            <h4 style="font-size: 0.9rem; font-weight: 800; color: var(--text-main); margin-bottom: 0.4rem;">SPECIFICATIONS</h4>
            <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.6; white-space: pre-line;">${p.specifications || 'N/A'}</p>
          </div>
        `;
      }

      this.showModal('modalViewProduct');
    } catch (err) {
      TechTrend.showToast('Error displaying product view.', 'error');
    }
  },

  // Delete Confirmation Modal
  openDeleteConfirmModal(productId, productName) {
    this.pendingDeleteId = productId;
    const nameEl = document.getElementById('deleteProdName');
    if (nameEl) nameEl.textContent = productName;
    this.showModal('modalDeleteConfirm');
  },

  async confirmDelete(permanent = false) {
    if (!this.pendingDeleteId) return;

    try {
      const res = await fetch('/admin/api/products/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: this.pendingDeleteId, permanent: permanent })
      });
      const data = await res.json();
      if (data.success) {
        TechTrend.showToast(data.message, 'success');
        this.closeModal('modalDeleteConfirm');
        this.loadProducts(this.currentPage);
      } else {
        TechTrend.showToast(data.message || 'Delete operation failed.', 'error');
      }
    } catch (err) {
      TechTrend.showToast('Delete request error.', 'error');
    } finally {
      this.pendingDeleteId = null;
    }
  },

  async toggleStatus(productId, newStatus) {
    try {
      const res = await fetch('/admin/api/products/toggle-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, is_active: newStatus })
      });
      const data = await res.json();
      if (data.success) {
        TechTrend.showToast(data.message, 'success');
        this.loadProducts(this.currentPage);
      } else {
        TechTrend.showToast(data.message || 'Status toggle failed.', 'error');
      }
    } catch (err) {
      TechTrend.showToast('Status update request failed.', 'error');
    }
  },

  // Save Product Form Handler
  async saveProductForm() {
    const name = document.getElementById('prodName').value.trim();
    const categoryId = document.getElementById('prodCategory').value;
    const priceVal = parseFloat(document.getElementById('prodPrice').value);
    const discVal = parseFloat(document.getElementById('prodDiscount').value) || 0;
    const stockVal = parseInt(document.getElementById('prodStock').value);

    // Client-side validations
    if (!name) {
      TechTrend.showToast('Please enter a product name.', 'error');
      return;
    }
    if (isNaN(priceVal) || priceVal < 0) {
      TechTrend.showToast('Please enter a valid non-negative original price.', 'error');
      return;
    }
    if (isNaN(discVal) || discVal < 0 || discVal > 100) {
      TechTrend.showToast('Discount percentage must be between 0% and 100%.', 'error');
      return;
    }
    if (isNaN(stockVal) || stockVal < 0) {
      TechTrend.showToast('Please enter a valid stock quantity.', 'error');
      return;
    }

    const payload = {
      product_id: document.getElementById('prodId').value || null,
      category_id: categoryId,
      name: name,
      slug: document.getElementById('prodSlug').value.trim(),
      price: priceVal,
      discount_percent: discVal,
      stock: stockVal,
      is_active: document.getElementById('prodStatusActive').checked ? 1 : 0,
      short_description: document.getElementById('prodShortDesc').value.trim(),
      description: document.getElementById('prodDesc').value.trim(),
      specifications: document.getElementById('prodSpecs').value.trim(),
      is_featured: document.getElementById('prodFeatured').checked,
      is_trending: document.getElementById('prodTrending').checked,
      image_urls: [document.getElementById('prodImage').value.trim()]
    };

    try {
      const res = await fetch('/admin/api/products/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        TechTrend.showToast(data.message, 'success');
        this.closeModal('modalProduct');
        this.loadProducts(this.currentPage);
      } else {
        TechTrend.showToast(data.message || 'Error saving product.', 'error');
      }
    } catch (err) {
      TechTrend.showToast('Request failed. Could not save product.', 'error');
    }
  },

  async updateOrderStatus(orderId, newStatus) {
    try {
      const res = await fetch('/admin/api/orders/update-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order_id: orderId, status: newStatus })
      });
      const data = await res.json();
      if (data.success) {
        TechTrend.showToast(data.message, 'success');
      } else {
        TechTrend.showToast(data.message, 'error');
      }
    } catch (err) {
      TechTrend.showToast('Failed to update status.', 'error');
    }
  },

  async saveCouponForm() {
    const payload = {
      coupon_id: document.getElementById('couponId').value || null,
      code: document.getElementById('couponCode').value.trim(),
      discount_type: document.getElementById('couponType').value,
      discount_value: document.getElementById('couponVal').value,
      min_order_amount: document.getElementById('couponMin').value,
      max_discount: document.getElementById('couponMax').value || null,
      is_active: document.getElementById('couponActive').checked
    };

    try {
      const res = await fetch('/admin/api/coupons/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        TechTrend.showToast(data.message, 'success');
        setTimeout(() => location.reload(), 600);
      } else {
        TechTrend.showToast(data.message, 'error');
      }
    } catch (err) {
      TechTrend.showToast('Error saving coupon.', 'error');
    }
  },

  async openCustomerDetailModal(userId) {
    const modalBody = document.getElementById('customerModalBody');
    if (modalBody) {
      modalBody.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
          <div class="skeleton-box" style="height: 30px; margin-bottom: 1rem; width: 60%; margin-left: auto; margin-right: auto;"></div>
          <div class="skeleton-box" style="height: 120px; margin-bottom: 1rem;"></div>
          <div class="skeleton-box" style="height: 200px;"></div>
        </div>
      `;
    }
    this.showModal('modalCustomerDetail');

    try {
      const res = await fetch(`/admin/api/customers/${userId}`);
      const data = await res.json();
      if (!data.success || !data.customer) {
        TechTrend.showToast(data.message || 'Could not fetch customer details.', 'error');
        this.closeModal('modalCustomerDetail');
        return;
      }

      const c = data.customer;
      const u = c.user || {};
      const addresses = c.addresses || [];
      const loginHistory = c.login_history || [];
      const orders = c.orders || [];

      const userCode = u.user_code || `USR-${String(u.id).padStart(6, '0')}`;
      const fullName = u.full_name || 'New Customer';
      const email = u.email || 'N/A';
      const phone = u.phone || 'N/A';
      const isComplete = !!u.is_profile_complete;
      const loginCount = c.login_count || u.login_count || loginHistory.length || 1;
      const lastLogin = u.last_login || (loginHistory[0] ? loginHistory[0].login_at : 'N/A');
      const registeredOn = u.created_at || 'N/A';
      const totalSpent = parseFloat(c.total_spent || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

      let defaultAddressStr = 'No address on file';
      if (addresses.length > 0) {
        const addr = addresses.find(a => a.is_default) || addresses[0];
        defaultAddressStr = `${addr.address_line || ''}, ${addr.city || ''}, ${addr.state || ''} - ${addr.pincode || ''}`;
      }

      // Login history HTML
      let loginLogsHtml = '';
      if (loginHistory.length === 0) {
        loginLogsHtml = `
          <tr>
            <td colspan="3" style="text-align: center; padding: 1rem; color: var(--text-dim);">No login activity logged yet.</td>
          </tr>
        `;
      } else {
        loginLogsHtml = loginHistory.map((log, idx) => `
          <tr>
            <td style="font-weight: 700; color: var(--text-dim); width: 40px;">#${loginHistory.length - idx}</td>
            <td style="font-weight: 700; color: var(--text-main); white-space: nowrap;"><i class="bi bi-clock-history" style="color: var(--color-brand);"></i> ${log.login_at || 'N/A'}</td>
            <td style="font-size: 0.8rem; color: var(--text-dim);">${log.ip_address || '127.0.0.1'} ${log.user_agent ? `&bull; ${log.user_agent.substring(0, 45)}...` : ''}</td>
          </tr>
        `).join('');
      }

      // Orders HTML
      let ordersHtml = '';
      if (orders.length === 0) {
        ordersHtml = `
          <tr>
            <td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-dim);">
              <i class="bi bi-bag-x" style="font-size: 2rem; display: block; margin-bottom: 0.5rem;"></i>
              No orders placed by this customer yet.
            </td>
          </tr>
        `;
      } else {
        ordersHtml = orders.map(ord => {
          const ordAmount = parseFloat(ord.total_amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
          const itemsSummary = (ord.order_items || []).map(it => `${it.name} (x${it.quantity})`).join(', ');

          let statusBadge = 'badge-active';
          if (ord.status === 'Delivered') statusBadge = 'badge-instock';
          else if (ord.status === 'Cancelled') statusBadge = 'badge-inactive';
          else if (ord.status === 'Shipped' || ord.status === 'Out for Delivery') statusBadge = 'badge-lowstock';

          return `
            <tr>
              <td style="font-weight: 800; color: var(--color-accent); white-space: nowrap;">${ord.order_number}</td>
              <td style="font-size: 0.82rem; color: var(--text-muted); white-space: nowrap;"><i class="bi bi-calendar3"></i> ${ord.created_at || 'N/A'}</td>
              <td style="font-size: 0.85rem; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${itemsSummary}">${itemsSummary || 'Items'}</td>
              <td style="font-weight: 800; color: var(--color-success); white-space: nowrap;">₹${ordAmount}</td>
              <td style="font-size: 0.82rem; white-space: nowrap;">${ord.payment_method || 'N/A'} (${ord.payment_status || 'SUCCESS'})</td>
              <td><span class="badge ${statusBadge}">${ord.status}</span></td>
            </tr>
          `;
        }).join('');
      }

      if (modalBody) {
        modalBody.innerHTML = `
          <!-- Customer Header Profile Box -->
          <div style="background: var(--bg-input); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 1.25rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem;">
              <div>
                <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.3rem;">
                  <span class="badge" style="background: rgba(99,102,241,0.2); color: var(--color-brand); font-weight: 800; font-size: 0.9rem; padding: 0.3rem 0.6rem;">
                    <i class="bi bi-person-vcard"></i> ${userCode}
                  </span>
                  <span class="badge ${isComplete ? 'badge-active' : 'badge-warning'}">
                    ${isComplete ? 'Profile Complete' : 'Profile Pending'}
                  </span>
                </div>
                <h2 style="font-size: 1.4rem; font-weight: 800; margin: 0; color: var(--text-main);">${fullName}</h2>
              </div>

              <!-- Quick Metrics Badges -->
              <div style="display: flex; gap: 0.6rem; flex-wrap: wrap;">
                <div style="background: var(--bg-card); border: 1px solid var(--border-light); padding: 0.5rem 0.8rem; border-radius: var(--radius-md); text-align: center;">
                  <div style="font-size: 0.7rem; font-weight: 700; color: var(--text-dim);">TOTAL LOGINS</div>
                  <div style="font-size: 1.1rem; font-weight: 800; color: var(--color-brand);">${loginCount}</div>
                </div>
                <div style="background: var(--bg-card); border: 1px solid var(--border-light); padding: 0.5rem 0.8rem; border-radius: var(--radius-md); text-align: center;">
                  <div style="font-size: 0.7rem; font-weight: 700; color: var(--text-dim);">TOTAL ORDERS</div>
                  <div style="font-size: 1.1rem; font-weight: 800; color: var(--color-accent);">${c.total_orders || orders.length}</div>
                </div>
                <div style="background: var(--bg-card); border: 1px solid var(--border-light); padding: 0.5rem 0.8rem; border-radius: var(--radius-md); text-align: center;">
                  <div style="font-size: 0.7rem; font-weight: 700; color: var(--text-dim);">TOTAL SPENT</div>
                  <div style="font-size: 1.1rem; font-weight: 800; color: var(--color-success);">₹${totalSpent}</div>
                </div>
              </div>
            </div>

            <!-- Customer Details Grid -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; border-top: 1px solid var(--border-light); padding-top: 0.85rem; font-size: 0.85rem;">
              <div>
                <span style="font-size: 0.72rem; color: var(--text-dim); font-weight: 700; display: block;">EMAIL ADDRESS</span>
                <span style="font-weight: 600; color: var(--text-main);"><i class="bi bi-envelope" style="color: var(--text-dim);"></i> ${email}</span>
              </div>
              <div>
                <span style="font-size: 0.72rem; color: var(--text-dim); font-weight: 700; display: block;">PHONE NUMBER</span>
                <span style="font-weight: 600; color: var(--text-main);"><i class="bi bi-telephone" style="color: var(--text-dim);"></i> ${phone}</span>
              </div>
              <div>
                <span style="font-size: 0.72rem; color: var(--text-dim); font-weight: 700; display: block;">REGISTERED ON</span>
                <span style="color: var(--text-muted);">${registeredOn}</span>
              </div>
              <div>
                <span style="font-size: 0.72rem; color: var(--text-dim); font-weight: 700; display: block;">LAST LOGIN TIME</span>
                <span style="color: var(--color-brand); font-weight: 700;">${lastLogin}</span>
              </div>
            </div>

            <div style="margin-top: 0.75rem; font-size: 0.83rem;">
              <span style="font-size: 0.72rem; color: var(--text-dim); font-weight: 700; display: block;">DEFAULT DELIVERY ADDRESS</span>
              <span style="color: var(--text-muted);"><i class="bi bi-geo-alt" style="color: var(--color-accent);"></i> ${defaultAddressStr}</span>
            </div>
          </div>

          <!-- Section 1: Complete Login Activity History -->
          <div style="margin-bottom: 1.75rem;">
            <h4 style="font-size: 1rem; font-weight: 800; color: var(--text-main); margin-bottom: 0.75rem; display: flex; align-items: center; justify-content: space-between;">
              <span><i class="bi bi-activity" style="color: var(--color-success);"></i> Login Activity History</span>
              <span style="font-size: 0.8rem; font-weight: 700; color: var(--text-dim);">Total Logins: ${loginCount}</span>
            </h4>
            <div style="max-height: 180px; overflow-y: auto; border: 1px solid var(--border-light); border-radius: var(--radius-md);">
              <table class="admin-table" style="font-size: 0.85rem;">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Login Date & Time</th>
                    <th>IP / Device Info</th>
                  </tr>
                </thead>
                <tbody>
                  ${loginLogsHtml}
                </tbody>
              </table>
            </div>
          </div>

          <!-- Section 2: Customer Orders History -->
          <div>
            <h4 style="font-size: 1rem; font-weight: 800; color: var(--text-main); margin-bottom: 0.75rem; display: flex; align-items: center; justify-content: space-between;">
              <span><i class="bi bi-box-seam" style="color: var(--color-accent);"></i> All Customer Orders (${orders.length})</span>
              <span style="font-size: 0.8rem; font-weight: 700; color: var(--color-success);">Total Completed Spent: ₹${totalSpent}</span>
            </h4>
            <div style="max-height: 240px; overflow-y: auto; border: 1px solid var(--border-light); border-radius: var(--radius-md);">
              <table class="admin-table" style="font-size: 0.85rem;">
                <thead>
                  <tr>
                    <th>Order ID</th>
                    <th>Order Date & Time</th>
                    <th>Products</th>
                    <th>Amount</th>
                    <th>Payment</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  ${ordersHtml}
                </tbody>
              </table>
            </div>
          </div>
        `;
      }
    } catch (err) {
      console.error("Error opening customer detail:", err);
      TechTrend.showToast('Error loading customer activity details.', 'error');
    }
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  AdminApp.init();
});
