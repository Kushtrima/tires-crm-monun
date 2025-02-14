function editProduct(id, name, brand, size, type, description, price, stock) {
    // Set values in edit modal
    document.getElementById('edit_name').value = name || '';
    document.getElementById('edit_brand').value = brand || '';
    document.getElementById('edit_size').value = size || '';
    document.getElementById('edit_type').value = type || '';
    document.getElementById('edit_description').value = description || '';
    document.getElementById('edit_price').value = price || 0;
    document.getElementById('edit_stock').value = stock || 0;
    
    // Set form action
    const form = document.getElementById('editProductForm');
    form.action = `/inventory/edit/${id}`;
    
    // Show modal
    const modal = document.getElementById('editProductModal');
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function addSaleItem(type) {
    // ... rest of the function ...
} 