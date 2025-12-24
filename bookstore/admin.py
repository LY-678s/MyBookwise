from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction, DatabaseError
from django.http import HttpResponseRedirect
from .models import (
    Book,
    Bookauthor,
    Creditlevel,
    Customer,
    Orderdetail,
    Orders,
    Procurement,
    Procurementdetail,
    Shortagerecord,
    Supplier,
    Supplierbook,
)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """图书：在列表页展示关键信息，并支持按书名/ISBN 搜索、按出版社筛选。"""

    list_display = ("isbn", "title", "publisher", "price", "stockqty", "minstocklimit")
    search_fields = ("isbn", "title", "keywords")
    list_filter = ("publisher",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """顾客：方便管理员按用户名/姓名/等级管理顾客账户。"""

    list_display = ("customerid", "username", "name", "email", "balance", "usedcredit", "totalspent", "levelid")
    search_fields = ("username", "name", "email")
    list_filter = ("levelid",)
    # 按累计消费排序（可选）
    ordering = ("-totalspent",)
    readonly_fields = ("usedcredit", "totalspent")  # 这些字段由系统自动计算，不允许手动修改


class OrderdetailInline(admin.TabularInline):
    """订单明细内联显示"""
    model = Orderdetail
    extra = 0  # 不显示空白行
    fields = ('isbn', 'quantity', 'unitprice', 'isshipped')
    readonly_fields = ('isbn', 'quantity', 'unitprice')  # 只允许修改发货状态
    can_delete = False  # 禁止删除明细（由触发器保护）
    
    def has_add_permission(self, request, obj=None):
        # 禁止在已存在的订单中添加明细（订单只能从客户端创建）
        return False


@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    """订单：查看订单号、顾客、金额和状态，并按日期与状态过滤。"""

    list_display = ("orderid", "orderno", "customerid", "orderdate", "totalamount", "actualpaid", "paymentstatus", "status")
    search_fields = ("orderno", "customerid__username", "customerid__name")
    list_filter = ("status", "paymentstatus", "orderdate")
    date_hierarchy = "orderdate"
    readonly_fields = ("totalamount", "actualpaid", "paymentstatus")  # 这些由系统计算，不可手动修改
    # 内嵌显示订单明细
    inlines = [OrderdetailInline]
    # 自定义批量动作
    actions = ["mark_as_shipped", "mark_as_completed", "mark_as_cancelled"]
    
    def has_add_permission(self, request):
        # 禁止在Admin后台创建订单（必须从客户端下单）
        return False

    def mark_as_placed(self, request, queryset):
        """将订单状态设为：0 = 已下单（未发货）"""
        total = queryset.count()
        usable_qs = queryset.exclude(status=4)
        updated = 0
        failed = []
        for order in usable_qs:
            try:
                order.status = 0
                order.save()
                updated += 1
            except Exception as e:
                failed.append((getattr(order, "orderno", order.pk), str(e)))
        skipped = total - updated
        self.message_user(request, f"已将 {updated} 个订单标记为【已下单】")
        if skipped:
            self.message_user(request, f"跳过 {skipped} 个已取消或更新失败的订单（不能修改状态）", level=messages.WARNING)
        for ordno, err in failed[:10]:
            self.message_user(request, f"订单 {ordno} 更新失败：{err}", level=messages.ERROR)

    mark_as_placed.short_description = "标记所选订单为：已下单（status=0）"

    def mark_as_shipped(self, request, queryset):
        """将订单状态设为：1 = 已发货"""
        total = queryset.count()
        usable_qs = queryset.exclude(status=4)
        try:
            updated = usable_qs.update(status=1)
            skipped = total - updated
            self.message_user(request, f"已将 {updated} 个订单标记为【已发货】")
            if skipped:
                self.message_user(request, f"跳过 {skipped} 个已取消的订单（不能修改状态）", level=messages.WARNING)
            return
        except DatabaseError as e:
            # 如果是触发器限制（1442），回退为逐条保存（不做库存校验）
            if getattr(e, "args", None) and e.args[0] == 1442:
                updated = 0
                failed = []
                for order in usable_qs:
                    try:
                        order.status = 1
                        order.save()
                        updated += 1
                    except Exception as ex:
                        failed.append((getattr(order, "orderno", order.pk), str(ex)))
                skipped = total - updated
                self.message_user(request, f"已将 {updated} 个订单标记为【已发货】（逐条回退）")
                if skipped:
                    self.message_user(request, f"跳过 {skipped} 个已取消或更新失败的订单", level=messages.WARNING)
                for ordno, err in failed[:10]:
                    self.message_user(request, f"订单 {ordno} 未更新：{err}", level=messages.ERROR)
                return
            # 其他数据库错误
            self.message_user(request, f"数据库错误，无法批量修改订单为已发货：{e}", level=messages.ERROR)
            return

    mark_as_shipped.short_description = "标记所选订单为：已发货（status=1）"

    def mark_as_completed(self, request, queryset):
        """将订单状态设为：2 = 已完成（逐条保存以触发信号）"""
        total = queryset.count()
        usable_qs = queryset.exclude(status=4)
        updated = 0
        failed = []
        
        # 逐条保存以触发Django信号（更新TotalSpent）
        for order in usable_qs:
            try:
                order.status = 2
                order.save()  # 触发信号
                updated += 1
            except Exception as ex:
                failed.append((getattr(order, "orderno", order.pk), str(ex)))
        
        skipped = total - updated
        self.message_user(request, f"已将 {updated} 个订单标记为【已完成】")
        if skipped:
            self.message_user(request, f"跳过 {skipped} 个已取消或更新失败的订单", level=messages.WARNING)
        for ordno, err in failed[:10]:
            self.message_user(request, f"订单 {ordno} 更新失败：{err}", level=messages.ERROR)

    mark_as_completed.short_description = "标记所选订单为：已完成（status=2）"

    def mark_as_cancelled(self, request, queryset):
        """将订单状态设为：4 = 已取消"""
        updated = 0
        failed = []
        for order in queryset:
            try:
                order.status = 4
                order.save()
                updated += 1
            except Exception as e:
                failed.append((getattr(order, "orderno", order.pk), str(e)))
        self.message_user(request, f"已将 {updated} 个订单标记为【已取消】")
        for ordno, err in failed[:10]:
            self.message_user(request, f"订单 {ordno} 标记取消失败：{err}", level=messages.ERROR)

    mark_as_cancelled.short_description = "标记所选订单为：已取消（status=4）"
    
    
    def save_model(self, request, obj, form, change):
        """
        在保存订单前进行校验：
        - 禁止把已取消订单改回其他状态（友好提示）
        """
        # 如果是修改，检查旧状态
        if change and obj.pk:
            try:
                old = Orders.objects.get(pk=obj.pk)
            except Orders.DoesNotExist:
                old = None
            if old and old.status == 4 and obj.status != 4:
                self.message_user(request, "已取消的订单不能再改为其他状态。", level=messages.ERROR)
                raise ValidationError("Cannot change order status from cancelled to another status")

        # 先保存对象（不包含 inlines）
        super().save_model(request, obj, form, change)

    

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """
        Wrap the entire admin changeform handling in an atomic transaction to ensure
        that save_model + save_related are executed atomically.
        """
        from django.db import transaction as _transaction
        try:
            with _transaction.atomic():
                return super().changeform_view(request, object_id, form_url, extra_context)
        except (ValidationError, DatabaseError) as e:
            # Show friendly message and redirect back to the form page (avoids raw DB error page)
            self.message_user(request, str(e), level=messages.ERROR)
            return HttpResponseRedirect(request.get_full_path())

    def add_view(self, request, form_url='', extra_context=None):
        """
        Wrap add_view to catch ValidationError/DatabaseError and show friendly message
        instead of Django error page.
        """
        try:
            return super().add_view(request, form_url, extra_context)
        except (ValidationError, DatabaseError) as e:
            self.message_user(request, str(e), level=messages.ERROR)
            return HttpResponseRedirect(request.get_full_path())
    
# 订单明细已通过OrderdetailInline嵌入到订单页面中显示，不再单独注册
# @admin.register(Orderdetail)
class OrderdetailAdmin(admin.ModelAdmin):
    """订单明细：查看每个订单中购买了哪些书。"""

    list_display = ("detailid", "orderid", "isbn", "quantity", "unitprice", "isshipped")
    list_filter = ("isshipped", "orderid")
    search_fields = ("orderid__orderno", "isbn__title", "isbn__isbn")
    # 自定义批量动作：发货管理
    actions = ["mark_as_shipped","mark_as_nonshipped"]

    # 禁用删除权限
    def has_delete_permission(self, request, obj=None):
        return False
    def mark_as_shipped(self, request, queryset):
        """
        批量将选中的订单明细标记为已发货。
        约定：isshipped 字段含义：0=未发货，1=已发货。
        """
        updated = queryset.update(isshipped=1)
        self.message_user(request, f"已将 {updated} 条订单明细标记为已发货")

    def mark_as_nonshipped(self, request, queryset):
        """
        批量将选中的订单明细标记为未发货。
        约定：isshipped 字段含义：0=未发货，1=已发货。
        """
        updated = queryset.update(isshipped=0)
        self.message_user(request, f"已将 {updated} 条订单明细更改为未发货")

    mark_as_shipped.short_description = "标记所选订单明细为：已发货（isshipped=1）"
    mark_as_nonshipped.short_description = "标记所选订单明细为：未发货（isshipped=0）"

    def save_model(self, request, obj, form, change):
        """
        在保存单条 Orderdetail 前检查对应书籍的库存是否足够（更早反馈）。
        如果库存不足，给出友好提示并阻止保存。
        """
        from .models import Book, Orderdetail as OrderdetailModel
        from django.db.models import Sum
        # 计算该订单对这本书的总需求量（包含正在保存的这条）
        order = obj.orderid
        isbn = obj.isbn
        # 汇总除了当前 (如果是修改) 之外的已有数量
        existing_qs = OrderdetailModel.objects.filter(orderid=order, isbn=isbn)
        if change and obj.pk:
            existing_qs = existing_qs.exclude(pk=obj.pk)
        total_required = existing_qs.aggregate(total=Sum('quantity'))['total'] or 0
        total_required += obj.quantity or 0

        try:
            book = Book.objects.get(pk=isbn.pk if hasattr(isbn, 'pk') else isbn)
        except Book.DoesNotExist:
            msg = f"图书（ISBN={isbn}）不存在，无法保存订单明细。"
            raise ValidationError(msg)

        # 允许库存低于最小安全库存（minstocklimit），但不允许出现负库存
        remaining = book.stockqty - total_required
        if remaining < 0:
            msg = f"图书《{book.title}》(ISBN={book.isbn}) 库存不足，当前库存 {book.stockqty}，需要 {total_required}。请调整数量或补货。"
            raise ValidationError(msg)
        # 如果剩余库存小于最小库存限制，给出警告（但允许保存），并按照原逻辑生成缺货记录/采购单
        if remaining < (book.minstocklimit or 0):
            warn_msg = f"注意：图书《{book.title}》(ISBN={book.isbn}) 剩余库存 {remaining} 已低于最小库存限制 {book.minstocklimit}，将触发缺货补货流程。"
            self.message_user(request, warn_msg, level=messages.WARNING)

        # 库存充足则继续保存（捕获底层数据库错误并友好提示）
        try:
            super().save_model(request, obj, form, change)
        except DatabaseError as e:
            raise ValidationError(f"保存订单明细失败，数据库操作错误：{e}")

    def _check_stock_for_orderdetail(self, orderdetail_obj):
        """
        在保存单条 Orderdetail 前检查对应图书库存是否充足（考虑同一订单内其它明细）。
        返回 (True, None) 如果充足，或者 (False, "错误消息") 如果不足。
        """
        from .models import Book, Orderdetail
        from django.db.models import Sum

        order = orderdetail_obj.orderid
        if order is None:
            return True, None

        # 统一使用 isbn_id（主键）作为键，避免对象/主键混用导致聚合错误
        isbn_id = getattr(orderdetail_obj, "isbn_id", None)
        if isbn_id is None:
            # 尝试从关联对象取主键（如果对象存在）
            isbn_field = getattr(orderdetail_obj, "isbn", None)
            isbn_id = getattr(isbn_field, "pk", isbn_field)

        # 计算该订单内除当前记录外同 ISBN 的已存在数量（仅本订单）
        qs = Orderdetail.objects.filter(orderid=order, isbn_id=isbn_id)
        if orderdetail_obj.pk:
            qs = qs.exclude(pk=orderdetail_obj.pk)
        existing_qty = qs.aggregate(total=Sum('quantity'))['total'] or 0

        # qty_needed 指的是“本次订单对该 ISBN 的需求量”
        total_needed = existing_qty + (orderdetail_obj.quantity or 0)

        try:
            book = Book.objects.get(pk=isbn_id)
        except Book.DoesNotExist:
            # 不抛出异常，返回友好提示由调用方显示
            return False, f"图书（ISBN={isbn_id}）不存在，无法完成库存检查。"

        if book.stockqty < total_needed:
            return False, f"图书《{book.title}》(ISBN={book.isbn}) 库存不足，当前库存 {book.stockqty}，本订单需要 {total_needed}。"
        return True, None

    def save_model(self, request, obj, form, change):
        """
        在保存单条订单明细前进行库存检查，并把整个 changeform 包到事务中以保证原子性。
        """
        ok, err = self._check_stock_for_orderdetail(obj)
        if not ok:
            raise ValidationError(err)

        # 包裹到事务中以保证原子性
        with transaction.atomic():
            super().save_model(request, obj, form, change)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """
        将 changeform 操作包在事务里，确保保存 orderdetail 及相关 inlines 原子提交。
        """
        try:
            with transaction.atomic():
                return super().changeform_view(request, object_id, form_url, extra_context)
        except (ValidationError, DatabaseError) as e:
            self.message_user(request, str(e), level=messages.ERROR)
            return HttpResponseRedirect(request.get_full_path())

    def add_view(self, request, form_url='', extra_context=None):
        try:
            return super().add_view(request, form_url, extra_context)
        except (ValidationError, DatabaseError) as e:
            self.message_user(request, str(e), level=messages.ERROR)
            return HttpResponseRedirect(request.get_full_path())


class ProcurementdetailInline(admin.TabularInline):
    """采购明细内联显示"""
    model = Procurementdetail
    extra = 0
    fields = ('isbn', 'quantity', 'supplyprice', 'receivedqty')
    readonly_fields = ('isbn', 'quantity', 'supplyprice')  # 只允许修改已到货数量


@admin.register(Procurement)
class ProcurementAdmin(admin.ModelAdmin):
    """采购单：用于记录补货采购，用日期和状态筛选。"""

    list_display = ("procid", "procno", "supplierid", "createdate", "status")
    search_fields = ("procno", "supplierid__suppliername")
    list_filter = ("status", "createdate", "supplierid")
    date_hierarchy = "createdate"
    # 内嵌显示采购明细
    inlines = [ProcurementdetailInline]
    # 批量修改采购单状态
    actions = ["mark_status_0", "mark_status_1", "mark_status_2", "mark_status_3"]

    def _update_status(self, request, queryset, value, label):
        updated = queryset.update(status=value)
        self.message_user(request, f"已将 {updated} 个采购单标记为【{label}】（status={value}）")

    def mark_status_0(self, request, queryset):
        """将采购单状态设为：0（根据设计文档的语义自行解释，例如：新建/待处理）"""
        self._update_status(request, queryset, 0, "采购中")

    def mark_status_1(self, request, queryset):
        """将采购单状态设为：1"""
        self._update_status(request, queryset, 1, "已到货入库")
    
    def mark_status_2(self, request, queryset):
        """将采购单状态设为：1"""
        self._update_status(request, queryset, 2, "已取消")

    mark_status_0.short_description = "标记所选采购单为：采购中（status=0）"
    mark_status_1.short_description = "标记所选采购单为：已到货入库（status=1）"
    mark_status_2.short_description = "标记所选采购单为：已取消（status=2）"

# 采购明细已通过ProcurementdetailInline嵌入到采购单页面中显示，不再单独注册
# @admin.register(Procurementdetail)
class ProcurementdetailAdmin(admin.ModelAdmin):
    """采购明细：展示每次采购了哪些书、多少数量。"""

    list_display = ("detailid", "procid", "isbn", "quantity", "supplyprice", "receivedqty")
    list_filter = ("procid", "isbn")
    search_fields = ("procid__procno", "isbn__title", "isbn__isbn")


@admin.register(Shortagerecord)
class ShortagerecordAdmin(admin.ModelAdmin):
    """缺货记录：帮助管理员发现需要补货的书。"""

    list_display = ("recordid", "recordno", "isbn", "quantity", "regdate", "status")
    list_filter = ("status", "regdate", "sourcetype")
    search_fields = ("recordno", "isbn__title", "isbn__isbn")
    date_hierarchy = "regdate"
    # 批量修改缺货记录状态：0=未处理，1=已处理，2=已生成采购单，3=已取消（建议语义）
    actions = ["mark_unhandled", "mark_processed", "mark_generated", "mark_cancelled"]

    def _update_status(self, request, queryset, value, label):
        updated = queryset.update(status=value)
        self.message_user(request, f"已将 {updated} 条缺货记录标记为【{label}】（status={value}）")

    def mark_unhandled(self, request, queryset):
        """标记为：未处理（status=0）"""
        self._update_status(request, queryset, 0, "未处理")

    def mark_processed(self, request, queryset):
        """标记为：已处理（status=1）"""
        self._update_status(request, queryset, 1, "已处理")

    def mark_generated(self, request, queryset):
        """标记为：已生成采购单（status=2）"""
        self._update_status(request, queryset, 2, "已生成采购单")

    def mark_cancelled(self, request, queryset):
        """标记为：已取消（status=3）"""
        self._update_status(request, queryset, 3, "已取消")
    mark_unhandled.short_description = "标记所选缺货记录为：未处理（status=0）"
    mark_processed.short_description = "标记所选缺货记录为：已处理（status=1）"
    mark_generated.short_description = "标记所选缺货记录为：已生成采购单（status=2）"
    mark_cancelled.short_description = "标记所选缺货记录为：已取消（status=3）"

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """供应商信息管理。"""

    list_display = ("supplierid", "suppliercode", "suppliername", "supplylocation", "isactive")
    search_fields = ("suppliercode", "suppliername", "supplylocation")
    list_filter = ("isactive",)
    # 批量启用 / 停用供应商
    actions = ["activate_suppliers", "deactivate_suppliers"]

    def activate_suppliers(self, request, queryset):
        """启用所选供应商（isactive=1）"""
        updated = queryset.update(isactive=1)
        self.message_user(request, f"已启用 {updated} 个供应商（isactive=1）")

    def deactivate_suppliers(self, request, queryset):
        """停用所选供应商（isactive=0）"""
        updated = queryset.update(isactive=0)
        self.message_user(request, f"已停用 {updated} 个供应商（isactive=0）")

    activate_suppliers.short_description = "启用所选供应商（isactive=1）"
    deactivate_suppliers.short_description = "停用所选供应商（isactive=0）"    

@admin.register(Bookauthor)
class BookauthorAdmin(admin.ModelAdmin):
    """图书作者关系管理。"""

    list_display = ("id", "isbn", "authorname", "authororder")
    search_fields = ("authorname", "isbn__title", "isbn__isbn")


@admin.register(Creditlevel)
class CreditlevelAdmin(admin.ModelAdmin):
    """会员等级与折扣。"""

    list_display = ("levelid", "discountrate", "canusecredit", "creditlimit")


@admin.register(Supplierbook)
class SupplierbookAdmin(admin.ModelAdmin):
    """供应商与图书的对应关系：看某个供应商能提供哪些书。"""

    list_display = ("supplierid", "isbn", "supplyprice", "lastsupplydate")
    list_filter = ("supplierid", "isbn")
    search_fields = ("supplierid__suppliername", "isbn__title", "isbn__isbn")

    def get_object(self, request, object_id, from_field=None):
        """
        自定义对象查找逻辑。
        由于数据库是联合主键 (supplierid, isbn)，但 Django 使用 supplierid 作为主键，
        当存在多条记录时，返回第一条以避免 admin 报错。
        """
        queryset = self.get_queryset(request)
        model = queryset.model
        field = model._meta.pk if from_field is None else model._meta.get_field(from_field)

        try:
            obj = queryset.get(**{field.name: object_id})
            return obj
        except model.MultipleObjectsReturned:
            return queryset.filter(**{field.name: object_id}).first()
        except model.DoesNotExist:
            return None