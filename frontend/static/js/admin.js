/* Admin Dashboard JavaScript Controller */

const AdminApp = {

  showModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.add('active');
  },

  closeModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.remove('active');
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

  async deleteProduct(productId) {
    if (!confirm('Are you sure you want to deactivate this product?')) return;
    try {
      const res = await fetch('/admin/api/products/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId })
      });
      const data = await res.json();
      if (data.success) {
        TechTrend.showToast(data.message, 'success');
        setTimeout(() => location.reload(), 600);
      }
    } catch (err) {
      TechTrend.showToast('Delete failed.', 'error');
    }
  },

  async saveProductForm() {
    const payload = {
      product_id: document.getElementById('prodId').value || null,
      category_id: document.getElementById('prodCategory').value,
      name: document.getElementById('prodName').value.trim(),
      slug: document.getElementById('prodSlug').value.trim(),
      short_description: document.getElementById('prodShortDesc').value.trim(),
      description: document.getElementById('prodDesc').value.trim(),
      specifications: document.getElementById('prodSpecs').value.trim(),
      price: document.getElementById('prodPrice').value,
      discount_percent: document.getElementById('prodDiscount').value,
      stock: document.getElementById('prodStock').value,
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
        setTimeout(() => location.reload(), 600);
      } else {
        TechTrend.showToast(data.message, 'error');
      }
    } catch (err) {
      TechTrend.showToast('Error saving product.', 'error');
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
  }
};
