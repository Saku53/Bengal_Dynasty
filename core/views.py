from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Category, Product, Cart, CartItem, Favorite, Order, OrderItem, OrderStatus
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate

def frontpage(request):
    # Show some featured products on the front page (optional)
    products = Product.objects.all()[:8]
    return render(request, "core/frontpage.html", {'products': products})

def get_descendant_ids(category):
    ids = [category.id]
    for child in category.children.all():
        ids += get_descendant_ids(child)
    return ids

def product_list(request):
    # -- CHANGE: now using category_slug, not category_id --
    category_slug = request.GET.get('category')
    query = request.GET.get('q', '')
    categories = Category.objects.filter(parent__isnull=True)  # All top-level categories
    products = Product.objects.all()
    selected_category = None

    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        # Include descendants if using nested categories, else just filter by slug
        descendant_ids = get_descendant_ids(selected_category)
        products = products.filter(category_id__in=descendant_ids)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    user_fav_ids = []
    if request.user.is_authenticated:
        user_fav_ids = request.user.favorites.values_list('product_id', flat=True)
    return render(request, 'core/product_list.html', {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
        'query': query,
        'user_fav_ids': user_fav_ids,
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    user_fav = False
    if request.user.is_authenticated:
        user_fav = Favorite.objects.filter(user=request.user, product=product).exists()
    return render(request, 'core/product_detail.html', {'product': product, 'user_fav': user_fav})

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > product.stock:
        messages.error(request, "Not enough stock available.")
        return redirect('product_detail', pk=pk)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    item.quantity += quantity
    item.save()
    product.stock -= quantity
    product.save()
    messages.success(request, "Added to cart!")
    return redirect('cart_detail')

@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product')
    total = sum(item.product.price * item.quantity for item in items)
    return render(request, 'core/cart_detail.html', {
        'cart': cart,
        'items': items,
        'total': total,
    })

@login_required
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    if action == 'increase' and item.quantity < item.product.stock:
        item.quantity += 1
        item.product.stock -= 1
        item.product.save()
        item.save()
    elif action == 'decrease' and item.quantity > 1:
        item.quantity -= 1
        item.product.stock += 1
        item.product.save()
        item.save()
    elif action == 'remove':
        item.product.stock += item.quantity
        item.product.save()
        item.delete()
    return redirect('cart_detail')

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.select_related('product')
    total = sum(item.product.price * item.quantity for item in items)
    if request.method == "POST":
        order = Order.objects.create(user=request.user, total_price=total, is_paid=True)
        for item in items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
        OrderStatus.objects.create(order=order, payment_confirmed=True)
        cart.items.all().delete()
        messages.success(request, "Payment successful! Your order has been placed.")
        return redirect('user_profile')
    return render(request, 'core/checkout.html', {'cart': cart, 'items': items, 'total': total})

@login_required
def add_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Favorite.objects.get_or_create(user=request.user, product=product)
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

@login_required
def remove_favorite(request, product_id):
    Favorite.objects.filter(user=request.user, product_id=product_id).delete()
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user)
    return render(request, 'core/favorite_list.html', {'favorites': favorites, 'active_page': 'favorites'})

@login_required
def user_profile(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/user_profile.html', {'user': request.user, 'orders': orders, 'active_page': 'dashboard'})

def profile_info(request):
    return render(request, 'core/profile_info.html', {"active_page": "profile_info"})

def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    print(orders)  # Debug print to see what orders are being returned
    return render(request, 'core/order_history.html', {
        'orders': orders,
        'active_page': 'order_history'
    })
def change_password(request):
    return render(request, 'core/change_password.html', {"active_page": "change_password"})

@login_required
def edit_profile(request):
    if request.method == "POST":
        user = request.user
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        errors = []

        if not email:
            errors.append("Email is required.")

        if not errors:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile_info")
        else:
            return render(request, 'core/edit_profile.html', {
                "errors": errors,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "active_page": "edit_profile",
            })
    else:
        return render(request, 'core/edit_profile.html', {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
            "active_page": "edit_profile",
        })

def not_authenticated(request):
    return render(request, 'core/not_authenticated.html')

def logout_view(request):
    logout(request)
    return redirect('login')  # or use redirect('/') if you want to go to home after logout

def signup(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        errors = []

        if not username or not email or not password1 or not password2:
            errors.append("All fields are required.")
        if password1 != password2:
            errors.append("Passwords do not match.")
        if User.objects.filter(username=username).exists():
            errors.append("Username already taken.")
        if User.objects.filter(email=email).exists():
            errors.append("Email already registered.")
        if len(password1) < 6:
            errors.append("Password must be at least 6 characters.")

        if errors:
            return render(request, "registration/signup.html", {
                "errors": errors,
                "username": username,
                "email": email,
            })
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        login(request, user)
        messages.success(request, "Account created successfully!")
        return redirect("product_list")

    return render(request, "registration/signup.html")