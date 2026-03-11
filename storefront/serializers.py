from rest_framework import serializers
from .models import Store, Product, Review

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['id', 'title', 'blurb', 'owner']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'content', 'price', 'inventory', 'store']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'title', 'content', 'rating', 'date_written', 'product', 'verified']
