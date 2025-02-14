document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            document.getElementById('sidebar').classList.toggle('active');
        });
    }

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // Product management functions
    window.editProduct = function(id, name, brand, size, type, description, price, stock) {
        document.getElementById('edit_name').value = name;
        document.getElementById('edit_brand').value = brand;
        document.getElementById('edit_size').value = size;
        document.getElementById('edit_type').value = type;
        document.getElementById('edit_description').value = description;
        document.getElementById('edit_price').value = price;
        document.getElementById('edit_stock').value = stock;
        document.getElementById('editProductForm').action = `/inventory/edit/${id}`;
        new bootstrap.Modal(document.getElementById('editProductModal')).show();
    };

    window.deleteProduct = function(id) {
        if (confirm('Are you sure you want to delete this product?')) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/inventory/delete/${id}`;
            document.body.appendChild(form);
            form.submit();
        }
    };
}); 