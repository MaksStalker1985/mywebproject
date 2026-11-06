from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("products/", views.ProductListView.as_view(), name="products"),
    path("products/new/", views.ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/", views.ProductUpdateView.as_view(), name="product_edit"),
    path("products/<int:pk>/delete/", views.ProductDeleteView.as_view(), name="product_delete"),
    path("forum/", views.CategoryListView.as_view(), name="categories"),
    path("forum/new/", views.CategoryCreateView.as_view(), name="category_create"),
    path("forum/<int:pk>/", views.CategoryUpdateView.as_view(), name="category_edit"),
    path("forum/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),
    path("topics/", views.TopicListView.as_view(), name="topics"),
    path("topics/<int:pk>/toggle/<str:field>/", views.TopicToggleView.as_view(), name="topic_toggle"),
    path("topics/<int:pk>/delete/", views.TopicDeleteView.as_view(), name="topic_delete"),
    path("messages/", views.MessageListView.as_view(), name="messages"),
    path("messages/<int:pk>/toggle/", views.MessageToggleView.as_view(), name="message_toggle"),
    path("orders/", views.OrderListView.as_view(), name="orders"),
    path("orders/<int:pk>/refund/", views.OrderRefundView.as_view(), name="order_refund"),
    path("pages/", views.PageListView.as_view(), name="pages"),
    path("pages/new/", views.PageCreateView.as_view(), name="page_create"),
    path("pages/<int:pk>/", views.PageUpdateView.as_view(), name="page_edit"),
    path("pages/<int:pk>/delete/", views.PageDeleteView.as_view(), name="page_delete"),
    path("users/", views.UserListView.as_view(), name="users"),
    path("users/<int:pk>/role/", views.UserRoleView.as_view(), name="user_role"),
    path("users/<int:pk>/avatar/delete/", views.UserAvatarDeleteView.as_view(), name="user_avatar_delete"),
    path("groups/", views.RoleListView.as_view(), name="roles"),
    path("groups/new/", views.RoleCreateView.as_view(), name="role_create"),
    path("groups/<int:pk>/", views.RoleUpdateView.as_view(), name="role_edit"),
    path("groups/<int:pk>/delete/", views.RoleDeleteView.as_view(), name="role_delete"),
]
