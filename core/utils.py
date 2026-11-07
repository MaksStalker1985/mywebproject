def client_ip(request):
    """IP посетителя. За nginx (сокет unix) REMOTE_ADDR пустой — адрес передаётся заголовком X-Real-IP,
    который nginx всегда перезаписывает (proxy_params), поэтому подделать его клиент не может."""
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR", "")
