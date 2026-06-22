from .models import Customer


def current_customer(request):
    """导航栏等全局模板从数据库读取顾客姓名，避免 session 缓存乱码或过期数据。"""
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return {"current_customer_name": None}
    name = (
        Customer.objects.filter(customerid=customer_id)
        .values_list("name", flat=True)
        .first()
    )
    return {"current_customer_name": name}
