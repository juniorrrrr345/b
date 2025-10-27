// Scripts JavaScript pour la boutique

// Mise à jour du compteur de panier
function updateCartCount() {
    fetch('/api/cart_count')
        .then(response => response.json())
        .then(data => {
            const cartCount = document.getElementById('cart-count');
            if (cartCount) {
                cartCount.textContent = data.count;
            }
        })
        .catch(error => console.error('Erreur:', error));
}

// Ajouter au panier
function addToCart(productId, quantity = 1) {
    return fetch('/add_to_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount();
            showNotification('Produit ajouté au panier !', 'success');
        } else {
            showNotification('Erreur: ' + data.message, 'error');
        }
        return data;
    })
    .catch(error => {
        console.error('Erreur:', error);
        showNotification('Une erreur est survenue', 'error');
        throw error;
    });
}

// Mettre à jour le panier
function updateCart(productId, quantity) {
    return fetch('/update_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount();
        } else {
            showNotification('Erreur: ' + data.message, 'error');
        }
        return data;
    })
    .catch(error => {
        console.error('Erreur:', error);
        showNotification('Une erreur est survenue', 'error');
        throw error;
    });
}

// Supprimer du panier
function removeFromCart(productId) {
    return updateCart(productId, 0);
}

// Afficher une notification
function showNotification(message, type = 'info') {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Ajouter au DOM
    document.body.appendChild(notification);
    
    // Supprimer automatiquement après 5 secondes
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Animation du bouton "Ajouter au panier"
function animateAddToCart(button) {
    const originalContent = button.innerHTML;
    const originalClass = button.className;
    
    button.innerHTML = '<i class="fas fa-check"></i> Ajouté !';
    button.className = button.className.replace('btn-primary', 'btn-success');
    button.disabled = true;
    
    setTimeout(() => {
        button.innerHTML = originalContent;
        button.className = originalClass;
        button.disabled = false;
    }, 2000);
}

// Recherche en temps réel
function initSearch() {
    const searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const products = document.querySelectorAll('.product-item');
            
            products.forEach(product => {
                const name = product.dataset.name || '';
                const description = product.dataset.description || '';
                
                if (name.includes(searchTerm) || description.includes(searchTerm)) {
                    product.style.display = 'block';
                } else {
                    product.style.display = 'none';
                }
            });
        });
    }
}

// Tri des produits
function initSorting() {
    document.querySelectorAll('[data-sort]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const sortBy = this.dataset.sort;
            const container = document.getElementById('products-container');
            if (!container) return;
            
            const products = Array.from(container.children);
            
            products.sort((a, b) => {
                switch(sortBy) {
                    case 'name':
                        return (a.dataset.name || '').localeCompare(b.dataset.name || '');
                    case 'name-desc':
                        return (b.dataset.name || '').localeCompare(a.dataset.name || '');
                    case 'price':
                        return parseFloat(a.dataset.price || 0) - parseFloat(b.dataset.price || 0);
                    case 'price-desc':
                        return parseFloat(b.dataset.price || 0) - parseFloat(a.dataset.price || 0);
                    default:
                        return 0;
                }
            });
            
            // Réorganiser les éléments
            products.forEach(product => container.appendChild(product));
        });
    });
}

// Validation de formulaire
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }
    });
    
    return isValid;
}

// Formatage des prix
function formatPrice(price) {
    return parseFloat(price).toFixed(2) + ' €';
}

// Calcul du total du panier
function calculateCartTotal() {
    let subtotal = 0;
    
    document.querySelectorAll('.cart-item').forEach(item => {
        const quantity = parseInt(item.querySelector('.quantity-input')?.value || 0);
        const price = parseFloat(item.querySelector('.item-price')?.textContent || 0);
        const total = quantity * price;
        
        const totalElement = item.querySelector('.item-total');
        if (totalElement) {
            totalElement.textContent = formatPrice(total);
        }
        
        subtotal += total;
    });
    
    const subtotalElement = document.getElementById('subtotal');
    if (subtotalElement) {
        subtotalElement.textContent = formatPrice(subtotal);
    }
    
    const shipping = subtotal >= 50 ? 0 : 9.99;
    const total = subtotal + shipping;
    
    const totalElement = document.getElementById('total');
    if (totalElement) {
        totalElement.textContent = formatPrice(total);
    }
    
    // Mettre à jour l'affichage de la livraison
    const shippingElement = document.getElementById('shipping');
    if (shippingElement) {
        if (subtotal >= 50) {
            shippingElement.innerHTML = '<span class="text-success">Gratuite</span>';
        } else {
            shippingElement.innerHTML = '9.99 €';
        }
    }
    
    return { subtotal, shipping, total };
}

// Initialisation des événements du panier
function initCartEvents() {
    // Mise à jour de la quantité
    document.querySelectorAll('.quantity-input').forEach(input => {
        input.addEventListener('change', function() {
            const productId = this.closest('.cart-item')?.dataset.productId;
            const quantity = parseInt(this.value);
            
            if (productId) {
                updateCart(productId, quantity).then(() => {
                    calculateCartTotal();
                });
            }
        });
    });
    
    // Suppression d'un article
    document.querySelectorAll('.remove-item').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.closest('.cart-item')?.dataset.productId;
            
            if (productId && confirm('Êtes-vous sûr de vouloir supprimer cet article du panier ?')) {
                removeFromCart(productId).then(() => {
                    const cartItem = this.closest('.cart-item');
                    if (cartItem) {
                        cartItem.remove();
                    }
                    
                    // Recharger la page si le panier est vide
                    if (document.querySelectorAll('.cart-item').length === 0) {
                        location.reload();
                    } else {
                        calculateCartTotal();
                    }
                });
            }
        });
    });
}

// Initialisation générale
document.addEventListener('DOMContentLoaded', function() {
    // Mettre à jour le compteur de panier
    updateCartCount();
    
    // Initialiser la recherche
    initSearch();
    
    // Initialiser le tri
    initSorting();
    
    // Initialiser les événements du panier
    initCartEvents();
    
    // Calculer le total du panier si on est sur la page panier
    if (document.querySelector('.cart-item')) {
        calculateCartTotal();
    }
    
    // Initialiser les boutons "Ajouter au panier"
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const quantityInput = this.closest('.product-actions')?.querySelector('input[type="number"]');
            const quantity = quantityInput ? parseInt(quantityInput.value) : 1;
            
            if (productId) {
                addToCart(productId, quantity).then(() => {
                    animateAddToCart(this);
                });
            }
        });
    });
    
    // Auto-dismiss des alertes
    setTimeout(() => {
        document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Fonctions utilitaires
window.BoutiqueUtils = {
    updateCartCount,
    addToCart,
    updateCart,
    removeFromCart,
    showNotification,
    animateAddToCart,
    validateForm,
    formatPrice,
    calculateCartTotal
};