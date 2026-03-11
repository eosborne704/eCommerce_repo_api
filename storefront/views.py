from django.db import models
import secrets
from datetime import datetime, timedelta
from hashlib import sha1
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.core.mail import EmailMessage
from django.utils import timezone
from .models import Product, Store, Review, ResetToken, Purchase
from .forms import ProductsForm, StoreForm, ReviewForm

# REST Framework imports
from rest_framework.decorators import api_view, renderer_classes, authentication_classes, permission_classes
from rest_framework_xml.renderers import XMLRenderer
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import StoreSerializer, ProductSerializer, ReviewSerializer
from django.http import JsonResponse
from rest_framework import status

# API Views
@api_view(['GET'])
@renderer_classes([XMLRenderer])
def view_stores(request):
    serializer = StoreSerializer(Store.objects.all(), many=True)
    return Response(data=serializer.data)

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def add_store(request):
    if request.user.id == int(request.data.get('owner')):
        serializer = StoreSerializer(data=request.data)
        if serializer.is_valid():
            store_obj = serializer.save()
            # Tweet about new store (integration step)
            return JsonResponse(data=serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse({'ID mismatch': 'User ID and store ID not matching'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@renderer_classes([XMLRenderer])
def view_products(request):
    serializer = ProductSerializer(Product.objects.all(), many=True)
    return Response(data=serializer.data)

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def add_product_api(request):
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        product_obj = serializer.save()
        # Tweet about new product (integration step)
        return JsonResponse(data=serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@renderer_classes([XMLRenderer])
def view_reviews(request):
    serializer = ReviewSerializer(Review.objects.all(), many=True)
    return Response(data=serializer.data)

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def add_review_api(request):
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        review_obj = serializer.save()
        return JsonResponse(data=serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@login_required
def edit_product_details(request, pk):
    product = get_object_or_404(Product, pk=pk)
    store = product.store
    # Only allow the owner (vendor) to edit products in their store
    if not (request.user.is_authenticated and store.owner == request.user):
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        form = ProductsForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect("view_product", pk=product.pk)
    else:
        form = ProductsForm(instance=product)
    return render(request, "storefront/edit_product_details.html", {"form": form, "product": product})

@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    store = product.store
    # Only allow the owner (vendor) to delete products in their store
    if not (request.user.is_authenticated and store.owner == request.user):
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        product.delete()
        return redirect("view_store", pk=store.pk)
    return render(request, "storefront/delete_product.html", {"product": product})

@login_required
def delete_store(request, pk):
    store = get_object_or_404(Store, pk=pk)
    # Only allow the owner (vendor) to delete their store
    if not (request.user.is_authenticated and store.owner == request.user):
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        store.delete()
        return redirect("all_stores")
    return render(request, "storefront/delete_store.html", {"store": store})
from django.db import models
import secrets
from datetime import datetime, timedelta
from hashlib import sha1
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.core.mail import EmailMessage
from django.utils import timezone
from .models import Product, Store, Review, ResetToken, Purchase
from .forms import ProductsForm, StoreForm, ReviewForm


def logout_view(request):
    logout(request)
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirect all users to stores page immediately
            return redirect('all_stores')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def verify_username(username):
    """
    Checks if username exists in database.
    """
    return not User.objects.filter(username=username).exists()


def verify_password(password):
    """
    Checks if password is at least 8.
    """
    return len(password) >= 8



def register_user(request):
    """
    Allows users to register themselves
    as either a Vendor or Buyer.
    """
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pword = request.POST.get('password')
        confirm_pword = request.POST.get('confirm_password')
        role = request.POST.get('role')
        valid_roles = ['Vendor', 'Buyer']
        if role not in valid_roles:
            return render(request, 'register.html', {
                'error': 'Invalid role selected.',
                'username': uname,
                'email': email,
                'role': role
            })
        if User.objects.filter(username=uname).exists():
            return render(request, 'register.html', {
                'error': 'Username already taken. Please choose another.',
                'username': uname,
                'email': email,
                'role': role
            })
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {
                'error': 'Email already registered. Please use a different email.',
                'username': uname,
                'email': email,
                'role': role
            })
        if pword != confirm_pword:
            return render(request, 'register.html', {
                'error': 'Passwords do not match. Please make sure you have entered the right password both times.',
                'username': uname,
                'email': email,
                'role': role
            })
        # Always ensure both groups exist
        vendor_group, _ = Group.objects.get_or_create(name='Vendor')
        buyer_group, _ = Group.objects.get_or_create(name='Buyer')
        user = User.objects.create_user(username=uname, password=pword)
        if role == 'Vendor':
            user.groups.add(vendor_group)
        elif role == 'Buyer':
            user.groups.add(buyer_group)
        user.save()
        # Confirm correct group assignment
        if not user.groups.filter(name=role).exists():
            return render(request, 'register.html', {
                'error': f'{role} registration failed.',
                'username': uname,
                'role': role
            })
        login(request, user)
        return redirect('home')
    return render(request, 'register.html')


def change_user_password(username, new_password):
    # Retrieve a specific user by their username
    user = User.objects.get(username=username)

    # Use the set_password() method to change their password
    user.set_password(new_password)

    # Save the changes to the database
    user.save()


@login_required
def welcome_view(request):
    """
    Renders the welcome page
    """
    stores = Store.objects.all()
    return render(request, 'welcome.html', {"stores": stores})


def all_stores(request):
    """
    Displays all presently-created stores
    """
    is_vendor = False
    stores = Store.objects.all()
    if request.user.is_authenticated:
        is_vendor = request.user.groups.filter(name='Vendor').exists()
        if is_vendor:
            stores = Store.objects.filter(owner=request.user)
    context = {
        "stores": stores,
        "store_display": "All Stores",
        "is_vendor": is_vendor,
    }
    return render(request, "storefront/all_stores.html", context)
def view_product_page(request):
    """
    Show product page if user permitted.
    """
    user = request.user
    if user.has_perm('eCommerce.view_product'):
        product_name = request.POST['product']
        product = Product.objects.get(name=product_name)
        return render(request, 'product_page.html', {'product': product})


def change_product_price(request):
    """
    Change product price if permitted.
    """
    user = request.user
    if user.has_perm('eCommerce.change_product'):
        product = request.POST.get('product')
        new_price = request.POST.get('new_price')
        Product.objects.filter(name=product).update(price=new_price)
        return HttpResponseRedirect(reverse('eCommerce:products'))


@login_required
def create_store(request):
    """
    Allows vendor to create a new store
    """
    if request.method == "POST":
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save(commit=False)
            store.owner = request.user
            store.save()
            return redirect("all_stores")
    else:
        form = StoreForm()
    return render(request, "storefront/create_store.html", {"form": form})


def view_store(request, pk):
    """
    Allows vendor or buyer to view a
    specific store
    """
    store = get_object_or_404(Store, pk=pk)
    is_vendor = False
    if request.user.is_authenticated:
        is_vendor = request.user.groups.filter(name='Vendor').exists()
    return render(request, "storefront/view_store.html", {"store": store, "is_vendor": is_vendor})


@login_required
def edit_store_details(request, pk):
    """
    View to edit store details
    """
    store = get_object_or_404(Store, pk=pk)
    # Only allow the owner (vendor) to edit their store
    if not (request.user.is_authenticated and store.owner == request.user):
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            return redirect("all_stores")
    else:
        form = StoreForm(instance=store)
    return render(request, "storefront/create_store.html", {"form": form})


@login_required
def delete_store(request, pk):
    """
    View to delete a product
    """
    store = get_object_or_400(Store, pk=pk)
    store.delete()


def all_products(request, store_id):
    """
    Show all products for a store.
    """
    store = get_object_or_404(Store, pk=store_id)
    products = Product.objects.filter(store=store)

    context = {
        "products": products,
        "store": store,
    }

    return render(request, "storefront/all_products.html", context)


@login_required
def add_product(request, store_id):
    """
    View to add a new product
    """
    store = get_object_or_404(Store, pk=store_id)
    # Only allow the owner (vendor) to add products to their store
    if not (request.user.is_authenticated and store.owner == request.user):
        return HttpResponse("Unauthorized", status=403)
    if request.method == "POST":
        form = ProductsForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            if not store:
                return render(request, "storefront/add_product.html", {"form": form, "store": store, "error": "Store not found. Cannot save product."})
            product.store = store
            product.save()
            if not product.store:
                return render(request, "storefront/add_product.html", {"form": form, "store": store, "error": "Product not linked to a store. Cannot save."})
            return redirect("view_product", pk=product.pk)
    else:
        form = ProductsForm()
    return render(request, "storefront/add_product.html", {"form": form, "store": store})


def get_rating_phrase_and_color(rating):
    if rating >= 4.5:
        return "Overwhelmingly positive!", "#50C878"  # emerald green
    elif rating >= 4.0:
        return "Very Positive!", "#66FF66"  # slightly brighter green
    elif rating >= 3.5:
        return "Fairly Positive!", "#99FF00"  # lime green
    elif rating >= 3.0:
        return "Decent", "#FFFF00"  # yellow
    elif rating >= 2.5:
        return "Fairly Negative", "#FFD700"  # orange-yellow
    elif rating >= 2.0:
        return "Very Negative", "#FF4500"  # orange-red
    elif rating >= 1.0:
        return "Overwhelmingly negative", "#B22222"  # slightly darker red
    elif rating > 0:
        return "Unusable", "#000000"  # black
    else:
        return "No ratings yet", "#888888"

def view_product(request, pk):
    """
    Show details for a product.
    """
    product = get_object_or_404(Product, pk=pk)
    store = product.store
    reviews = Review.objects.filter(product=product)
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    phrase, color = get_rating_phrase_and_color(avg_rating)
    # Annotate each review with phrase and color
    annotated_reviews = []
    for review in reviews:
        r_phrase, r_color = get_rating_phrase_and_color(review.rating)
        annotated_reviews.append({
            'review': review,
            'phrase': r_phrase,
            'color': r_color,
        })
    is_buyer = False
    if request.user.is_authenticated:
        is_buyer = request.user.groups.filter(name='Buyer').exists()
    return render(request, "storefront/view_product.html", {
        "product": product,
        "store": store,
        "reviews": annotated_reviews,
        "avg_rating": avg_rating,
        "avg_phrase": phrase,
        "avg_color": color,
        "is_buyer": is_buyer,
    })


@login_required
def edit_product_details(request, pk):
    """
    View to edit product details
    """
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductsForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect("view_product", pk=product.pk)

    else:
        form = ProductsForm(instance=product)
    return render(request, "storefront/add_product.html", {"form": form})


@login_required
def delete_product(request, pk):
    """
    View to delete a product
    """
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect("all_products", store_id=product.store.pk)


def all_reviews(request, product_id):
    """
    Allows user to view all reviews for a product
    """
    product = get_object_or_404(Product, pk=product_id)
    reviews = Review.objects.filter(product=product)
    context = {
        "reviews": reviews,
        "product": product,
        "page_title": f"Reviews for {product.title}",
    }
    return render(request, "storefront/all_reviews.html", context)


def view_review(request, pk):
    """
    Allows user to view a specific review
    """
    review = get_object_or_404(Review, pk=pk)
    return render(request, "storefront/view_review.html", {"review": review})


@login_required
def write_review(request, product_id):
    """
    Allows buyers to write a review
    Tags them as verified if they've bought the product
    """
    product = get_object_or_404(Product, pk=product_id)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            # Check if user has bought the product
            user_has_bought = Purchase.objects.filter(user=request.user, product=product).exists()
            review.verified = user_has_bought
            review.save()
            return redirect("all_reviews", product_id=product.pk)
    else:
        form = ReviewForm()
    return render(request, "storefront/write_review.html", {"form": form, "product": product})


@login_required
def edit_review(request, pk):
    """
    Allows buyers to edit the content of their review
    """
    review = get_object_or_404(Review, pk=pk)
    product = review.product
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.save()
            return redirect("all_reviews", product_id=product.pk)
    else:
        form = ReviewForm(instance=review)
    return render(request, "storefront/edit_review.html", {"form": form, "product": product})


@login_required
def delete_review(request, pk):
    """
    Allows buyers to delete their reviews
    """
    review = get_object_or_404(Review, pk=pk)
    product = review.product
    if request.method == "POST":
        review.delete()
        return redirect("all_reviews", product_id=product.pk)
    return render(request, "storefront/delete_review.html", {"review": review, "product": product})


def send_password_reset(request):
    """
    Send password reset email to user.
    """
    user_email = request.POST.get('email')
    try:
        user = User.objects.get(email=user_email)
        # Create a secure random token
        token_value = secrets.token_urlsafe(32)

        # Save token to database (expires in 1 hour)
        ResetToken.objects.create(
            user=user,
            token=token_value,
            expiry_date=timezone.now() + timezone.timedelta(hours=1)
        )

        # Build and send email
        reset_url = f"http://127.0.0.1:8000/reset-password/{token_value}/"
        email = EmailMessage(
            "Password Reset",
            f"Hello {user.username}, click here to reset: {reset_url}",
            "noreply@yourstore.com",
            [user_email]
        )
        email.send()
        return HttpResponse("Check your console for the reset link!")
    except User.DoesNotExist:
        return HttpResponse("Email not found.")


@require_POST
@login_required
def add_item_to_cart(request):
    """
    Add an item to user cart.
    """
    # Only allow buyers to add to cart
    if not request.user.groups.filter(name='Buyer').exists():
        return HttpResponse("Only buyers can add items to cart.")
    session = request.session
    item_name = request.POST.get('item') # The product name from your form
    quantity = int(request.POST.get('quantity', 1))

    # Find the product in the database
    try:
        product = Product.objects.get(title=item_name)
    except Product.DoesNotExist:
        return render(request, "product_not_found.html", status=404)

    # Check if enough inventory is available
    if product.inventory < quantity:
        return HttpResponse("Not enough inventory in stock.")

    # Subtract purchased quantity from inventory
    product.inventory -= quantity
    product.save()

    # Update cart in session
    if 'cart' in session:
        session['cart'][item_name] = quantity
    else:
        session['cart'] = {item_name: quantity}
    session.modified = True
    return redirect('show_user_cart')

@require_POST
@login_required
def empty_cart(request):
    """
    Remove all items from the user's cart.
    """
    # Only allow buyers to empty cart
    if not request.user.groups.filter(name='Buyer').exists():
        return HttpResponse("Only buyers can empty cart.")
    if 'cart' in request.session:
        del request.session['cart']
        request.session.modified = True
    return redirect('show_user_cart')

total = 0
@login_required
def show_user_cart(request):
    """
    Display the current user's shopping cart.
    """
    # Only allow buyers to view cart
    if not request.user.groups.filter(name='Buyer').exists():
        return HttpResponse("Only buyers can view cart.")
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for item, quantity in cart.items():
        try:
            product = Product.objects.get(title=item)
            cart_items.append({'product': product, 'quantity': quantity})
            total += product.price * quantity
        except Product.DoesNotExist:
            continue
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})


@login_required
def checkout_view(request):
    """
    Checks out cart items
    """
    cart = request.session.get('cart', {})
    user = request.user
    for item, quantity in cart.items():
        try:
            product = Product.objects.get(title=item)
            Purchase.objects.create(user=user, product=product, quantity=quantity)
        except Product.DoesNotExist:
            continue
    if 'cart' in request.session:
        del request.session['cart']
        request.session.modified = True
    return render(request, 'storefront/checkout_complete.html')


def retreive_products(request):
    """
    Get all products in user cart.
    """
    products = []
    session = request.session
    if 'cart' in session:
        for data in session['cart'].items():
            name, quantity = data
            product = Product.objects.get(name=name)
            products.append({product, quantity})
    return products


def build_email(user, reset_url):
    """
    Builds reset email
    """
    subject = "Password Reset"
    user_email = user.email
    domain_email = "example@domain.com"
    body = f"Hi {user.username},\nHere is your link to reset your password: {reset_url}"
    email = EmailMessage(subject, body, domain_email, [user_email])
    return email


def generate_reset_url(user):
    """
    Produces reset url
    """
    domain = "http://127.0.0.1:8000/"
    app_name = "grabmore"
    url = f"{domain}{app_name}/reset_password/"
    token = str(secrets.token_urlsafe(16))
    expiry_date = datetime.now() + timedelta(minutes=5)
    reset_token = ResetToken.objects.create(user=user,
    token=sha1(token.encode()).hexdigest(),
    expiry_date=expiry_date)
    url += f"{token}/"
    return url