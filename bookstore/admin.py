from django.contrib import admin
from .models import Book, Bookauthor, Creditlevel, Customer, Orderdetail, Orders,Procurement,Procurementdetail,Shortagerecord,Supplier,Supplierbook

# 注册所有模型
admin.site.register(Book)
admin.site.register(Bookauthor)
admin.site.register(Creditlevel)
admin.site.register(Customer)
admin.site.register(Orderdetail)
admin.site.register(Orders)
admin.site.register(Procurement)
admin.site.register(Procurementdetail)
admin.site.register(Shortagerecord)
admin.site.register(Supplier)
admin.site.register(Supplierbook)