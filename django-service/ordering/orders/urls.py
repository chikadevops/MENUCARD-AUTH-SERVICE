from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('categories/', views.CategoryList.as_view(), name='category-list'),
    path('order-items/<int:pk>/', views.OrderItemUpdate.as_view(), name='orderitem-update'),
    path('health/', views.health_check, name='health-check'),
]