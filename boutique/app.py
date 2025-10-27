#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boutique E-commerce - Application Flask
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre-cle-secrete-ici'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boutique.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modèles de base de données
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50), nullable=False)
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    shipping_address = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

# Routes principales
@app.route('/')
def index():
    """Page d'accueil avec les produits"""
    products = Product.query.filter_by(is_active=True).limit(8).all()
    return render_template('index.html', products=products)

@app.route('/products')
def products():
    """Page de tous les produits"""
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = Product.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(Product.name.contains(search))
    
    products = query.all()
    categories = db.session.query(Product.category.distinct()).all()
    
    return render_template('products.html', products=products, categories=categories, 
                         current_category=category, search_term=search)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Page de détail d'un produit"""
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    """Page du panier"""
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product:
            item_total = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """Ajouter un produit au panier"""
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)
    
    product = Product.query.get_or_404(product_id)
    
    if product.stock < quantity:
        return jsonify({'success': False, 'message': 'Stock insuffisant'})
    
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart
    
    return jsonify({'success': True, 'message': 'Produit ajouté au panier'})

@app.route('/update_cart', methods=['POST'])
def update_cart():
    """Mettre à jour le panier"""
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 0)
    
    cart = session.get('cart', {})
    
    if quantity <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = quantity
    
    session['cart'] = cart
    return jsonify({'success': True})

@app.route('/checkout')
def checkout():
    """Page de commande"""
    if 'user_id' not in session:
        flash('Vous devez être connecté pour passer commande', 'error')
        return redirect(url_for('login'))
    
    cart = session.get('cart', {})
    if not cart:
        flash('Votre panier est vide', 'error')
        return redirect(url_for('cart'))
    
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product:
            item_total = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/place_order', methods=['POST'])
def place_order():
    """Passer la commande"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non connecté'})
    
    cart = session.get('cart', {})
    if not cart:
        return jsonify({'success': False, 'message': 'Panier vide'})
    
    shipping_address = request.json.get('shipping_address')
    if not shipping_address:
        return jsonify({'success': False, 'message': 'Adresse de livraison requise'})
    
    # Calculer le total
    total = 0
    order_items = []
    
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product and product.stock >= quantity:
            item_total = product.price * quantity
            total += item_total
            order_items.append({
                'product': product,
                'quantity': quantity,
                'price': product.price
            })
        else:
            return jsonify({'success': False, 'message': f'Stock insuffisant pour {product.name}'})
    
    # Créer la commande
    order = Order(
        user_id=session['user_id'],
        total_amount=total,
        shipping_address=shipping_address
    )
    db.session.add(order)
    db.session.flush()
    
    # Créer les items de commande
    for item in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item['product'].id,
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(order_item)
        
        # Mettre à jour le stock
        item['product'].stock -= item['quantity']
    
    db.session.commit()
    
    # Vider le panier
    session.pop('cart', None)
    
    return jsonify({'success': True, 'message': 'Commande passée avec succès', 'order_id': order.id})

# Authentification
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Connexion"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Connexion réussie', 'success')
            return redirect(url_for('index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Cette adresse email existe déjà', 'error')
            return render_template('register.html')
        
        # Créer l'utilisateur
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Compte créé avec succès', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    flash('Déconnexion réussie', 'success')
    return redirect(url_for('index'))

# Administration
@app.route('/admin')
def admin():
    """Panneau d'administration"""
    if not session.get('is_admin'):
        flash('Accès non autorisé', 'error')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('admin.html', products=products, orders=orders)

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    """Ajouter un produit (admin)"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Non autorisé'})
    
    data = request.json
    product = Product(
        name=data['name'],
        description=data['description'],
        price=float(data['price']),
        image_url=data.get('image_url', ''),
        category=data['category'],
        stock=int(data['stock'])
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Produit ajouté'})

@app.route('/admin/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    """Modifier un produit (admin)"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Non autorisé'})
    
    product = Product.query.get_or_404(product_id)
    data = request.json
    
    product.name = data['name']
    product.description = data['description']
    product.price = float(data['price'])
    product.image_url = data.get('image_url', '')
    product.category = data['category']
    product.stock = int(data['stock'])
    product.is_active = data.get('is_active', True)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Produit modifié'})

@app.route('/admin/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Supprimer un produit (admin)"""
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Non autorisé'})
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Produit supprimé'})

# API pour les données
@app.route('/api/products')
def api_products():
    """API pour récupérer les produits"""
    products = Product.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.price,
        'image_url': p.image_url,
        'category': p.category,
        'stock': p.stock
    } for p in products])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Créer un admin par défaut
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@boutique.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        
        # Ajouter des produits d'exemple
        if not Product.query.first():
            sample_products = [
                Product(name='Laptop Gaming', description='Ordinateur portable gaming haute performance', 
                       price=1299.99, category='Informatique', stock=5, 
                       image_url='https://via.placeholder.com/300x200?text=Laptop'),
                Product(name='Smartphone', description='Smartphone dernière génération', 
                       price=699.99, category='Mobile', stock=10,
                       image_url='https://via.placeholder.com/300x200?text=Smartphone'),
                Product(name='Casque Audio', description='Casque audio professionnel', 
                       price=199.99, category='Audio', stock=15,
                       image_url='https://via.placeholder.com/300x200?text=Casque'),
                Product(name='Montre Connectée', description='Montre intelligente avec capteurs', 
                       price=299.99, category='Wearable', stock=8,
                       image_url='https://via.placeholder.com/300x200?text=Montre'),
            ]
            
            for product in sample_products:
                db.session.add(product)
            
            db.session.commit()
    
    app.run(host='0.0.0.0', port=5000, debug=True)