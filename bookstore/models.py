# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Book(models.Model):
    isbn = models.CharField(db_column='ISBN', primary_key=True, max_length=20)  # Field name made lowercase.
    title = models.CharField(db_column='Title', max_length=100)  # Field name made lowercase.
    publisher = models.CharField(db_column='Publisher', max_length=100, blank=True, null=True)  # Field name made lowercase.
    price = models.DecimalField(db_column='Price', max_digits=10, decimal_places=2)  # Field name made lowercase.
    keywords = models.CharField(db_column='Keywords', max_length=200, blank=True, null=True)  # Field name made lowercase.
    coverimage = models.TextField(db_column='CoverImage', blank=True, null=True)  # Field name made lowercase.
    stockqty = models.IntegerField(db_column='StockQty')  # Field name made lowercase.
    location = models.CharField(db_column='Location', max_length=50, blank=True, null=True)  # Field name made lowercase.
    minstocklimit = models.IntegerField(db_column='MinStockLimit')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'book'
        verbose_name = '图书'
        verbose_name_plural = '图书'

    def __str__(self):
        return f"{self.title} ({self.isbn})"


class Bookauthor(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    isbn = models.ForeignKey(Book, models.DO_NOTHING, db_column='ISBN')  # Field name made lowercase.
    authorname = models.CharField(db_column='AuthorName', max_length=50)  # Field name made lowercase.
    authororder = models.IntegerField(db_column='AuthorOrder')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'bookauthor'
        verbose_name = '图书作者'
        verbose_name_plural = '图书作者'

    def __str__(self):
        return f"{self.authorname} ({self.isbn.title})"


class Creditlevel(models.Model):
    levelid = models.IntegerField(db_column='LevelID', primary_key=True)  # Field name made lowercase.
    discountrate = models.DecimalField(db_column='DiscountRate', max_digits=3, decimal_places=2)  # Field name made lowercase.
    canusecredit = models.IntegerField(db_column='CanUseCredit')  # 是否可使用信用支付
    creditlimit = models.DecimalField(db_column='CreditLimit', max_digits=10, decimal_places=2)  # 信用额度上限

    class Meta:
        managed = False
        db_table = 'creditlevel'
        verbose_name = '信用等级'
        verbose_name_plural = '信用等级'

    def __str__(self):
        return f"等级{self.levelid} ({self.discountrate*100:.0f}折)"


class Customer(models.Model):
    customerid = models.AutoField(db_column='CustomerID', primary_key=True)  # Field name made lowercase.
    username = models.CharField(db_column='Username', unique=True, max_length=50)  # Field name made lowercase.
    password = models.CharField(db_column='Password', max_length=50)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=50)  # Field name made lowercase.
    address = models.CharField(db_column='Address', max_length=200, blank=True, null=True)  # Field name made lowercase.
    email = models.CharField(db_column='Email', unique=True, max_length=100, blank=True, null=True)  # Field name made lowercase.
    balance = models.DecimalField(db_column='Balance', max_digits=10, decimal_places=2)  # 账户余额（最低为0）
    levelid = models.ForeignKey(Creditlevel, models.DO_NOTHING, db_column='LevelID')  # Field name made lowercase.
    creditlimit = models.DecimalField(db_column='CreditLimit', max_digits=10, decimal_places=2)  # 信用额度上限
    usedcredit = models.DecimalField(db_column='UsedCredit', max_digits=10, decimal_places=2, default=0)  # 已使用信用额度
    totalspent = models.DecimalField(db_column='TotalSpent', max_digits=12, decimal_places=2)  # 累计消费（从余额支付的总额）
    registerdate = models.DateTimeField(db_column='RegisterDate')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'customer'
        verbose_name = '客户'
        verbose_name_plural = '客户'

    def __str__(self):
        return f"{self.username} ({self.name})"


class Orderdetail(models.Model):
    detailid = models.AutoField(db_column='DetailID', primary_key=True)  # Field name made lowercase.
    orderid = models.ForeignKey('Orders', models.DO_NOTHING, db_column='OrderID')  # Field name made lowercase.
    isbn = models.ForeignKey(Book, models.DO_NOTHING, db_column='ISBN')  # Field name made lowercase.
    quantity = models.IntegerField(db_column='Quantity')  # Field name made lowercase.
    unitprice = models.DecimalField(db_column='UnitPrice', max_digits=10, decimal_places=2)  # Field name made lowercase.
    isshipped = models.IntegerField(db_column='IsShipped')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'orderdetail'
        verbose_name = '订单明细'
        verbose_name_plural = '订单明细'

    def __str__(self):
        return f"{self.orderid.orderno} - {self.isbn.title} x{self.quantity}"


class Orders(models.Model):
    orderid = models.AutoField(db_column='OrderID', primary_key=True)  # Field name made lowercase.
    orderno = models.CharField(db_column='OrderNo', unique=True, max_length=30)  # Field name made lowercase.
    orderdate = models.DateTimeField(db_column='OrderDate')  # Field name made lowercase.
    customerid = models.ForeignKey(Customer, models.DO_NOTHING, db_column='CustomerID')  # Field name made lowercase.
    shipaddress = models.CharField(db_column='ShipAddress', max_length=200)  # Field name made lowercase.
    totalamount = models.DecimalField(db_column='TotalAmount', max_digits=10, decimal_places=2, blank=True, null=True)  # 应付金额（折扣后）
    actualpaid = models.DecimalField(db_column='ActualPaid', max_digits=10, decimal_places=2, default=0)  # 实际已付金额
    paymentstatus = models.IntegerField(db_column='PaymentStatus', default=0)  # 付款状态: 0=未付款, 1=已付款, 2=已退款
    status = models.IntegerField(db_column='Status')  # 订单状态

    class Meta:
        managed = False
        db_table = 'orders'
        verbose_name = '订单'
        verbose_name_plural = '订单'

    def __str__(self):
        return self.orderno


class Procurement(models.Model):
    procid = models.AutoField(db_column='ProcID', primary_key=True)  # Field name made lowercase.
    procno = models.CharField(db_column='ProcNo', unique=True, max_length=30)  # Field name made lowercase.
    supplierid = models.ForeignKey('Supplier', models.DO_NOTHING, db_column='SupplierID')  # Field name made lowercase.
    recordid = models.ForeignKey('Shortagerecord', models.DO_NOTHING, db_column='RecordID', blank=True, null=True)  # Field name made lowercase.
    createdate = models.DateTimeField(db_column='CreateDate')  # Field name made lowercase.
    updatedate = models.DateTimeField(db_column='UpdateDate', auto_now=True)  # 最后更新时间
    status = models.IntegerField(db_column='Status')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'procurement'
        verbose_name = '采购单'
        verbose_name_plural = '采购单'

    def __str__(self):
        return self.procno


class Procurementdetail(models.Model):
    detailid = models.AutoField(db_column='DetailID', primary_key=True)  # Field name made lowercase.
    procid = models.ForeignKey(Procurement, models.DO_NOTHING, db_column='ProcID')  # Field name made lowercase.
    isbn = models.ForeignKey(Book, models.DO_NOTHING, db_column='ISBN')  # Field name made lowercase.
    shortagerecordid = models.ForeignKey('Shortagerecord', models.DO_NOTHING, db_column='ShortageRecordID', blank=True, null=True)  # 关联缺货记录
    quantity = models.IntegerField(db_column='Quantity')  # 采购数量
    supplyprice = models.DecimalField(db_column='SupplyPrice', max_digits=10, decimal_places=2)  # 供货单价
    totalprice = models.DecimalField(db_column='TotalPrice', max_digits=10, decimal_places=2)  # 总价
    isreceived = models.IntegerField(db_column='IsReceived', default=0)  # 是否已到货

    class Meta:
        managed = False
        db_table = 'procurementdetail'
        verbose_name = '采购明细'
        verbose_name_plural = '采购明细'

    def __str__(self):
        return f"{self.procid.procno} - {self.isbn.title} x{self.quantity}"


class Shortagerecord(models.Model):
    recordid = models.AutoField(db_column='RecordID', primary_key=True)  # Field name made lowercase.
    recordno = models.CharField(db_column='RecordNo', unique=True, max_length=30)  # Field name made lowercase.
    isbn = models.ForeignKey(Book, models.DO_NOTHING, db_column='ISBN')  # Field name made lowercase.
    quantity = models.IntegerField(db_column='Quantity')  # Field name made lowercase.
    regdate = models.DateTimeField(db_column='RegDate')  # Field name made lowercase.
    sourcetype = models.IntegerField(db_column='SourceType')  # Field name made lowercase.
    customerid = models.ForeignKey(Customer, models.DO_NOTHING, db_column='CustomerID', blank=True, null=True)  # Field name made lowercase.
    status = models.IntegerField(db_column='Status')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'shortagerecord'
        verbose_name = '缺货记录'
        verbose_name_plural = '缺货记录'

    def __str__(self):
        return self.recordno


class Supplier(models.Model):
    supplierid = models.AutoField(db_column='SupplierID', primary_key=True)  # Field name made lowercase.
    suppliercode = models.CharField(db_column='SupplierCode', unique=True, max_length=20)  # Field name made lowercase.
    suppliername = models.CharField(db_column='SupplierName', max_length=100)  # Field name made lowercase.
    supplylocation = models.CharField(db_column='SupplyLocation', max_length=100)  # Field name made lowercase.
    contactinfo = models.CharField(db_column='ContactInfo', max_length=200, blank=True, null=True)  # Field name made lowercase.
    isactive = models.IntegerField(db_column='IsActive')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'supplier'
        verbose_name = '供应商'
        verbose_name_plural = '供应商'

    def __str__(self):
        return f"{self.suppliername} ({self.suppliercode})"


class SupplierbookManager(models.Manager):
    """自定义 Manager 来处理联合主键的查找"""
    def get(self, **kwargs):
        # 如果使用 supplierid 查找，需要同时提供 isbn
        if 'supplierid' in kwargs and 'isbn' not in kwargs:
            raise ValueError("Supplierbook requires both supplierid and isbn to uniquely identify a record")
        return super().get(**kwargs)


class Supplierbook(models.Model):
    # 注意：数据库中是联合主键 (supplierid, isbn)
    # Django 不支持联合主键，所以我们使用 supplierid 作为主键（仅用于 Django admin）
    # 实际查询时会使用 unique_together 约束
    supplierid = models.ForeignKey(Supplier, models.DO_NOTHING, db_column='SupplierID', primary_key=True)  # Field name made lowercase.
    isbn = models.ForeignKey(Book, models.DO_NOTHING, db_column='ISBN')  # Field name made lowercase.
    supplyprice = models.DecimalField(db_column='SupplyPrice', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    lastsupplydate = models.DateTimeField(db_column='LastSupplyDate', blank=True, null=True)  # Field name made lowercase.

    objects = SupplierbookManager()

    class Meta:
        managed = False
        db_table = 'supplierbook'
        unique_together = (('supplierid', 'isbn'),)
        verbose_name = '供应商图书'
        verbose_name_plural = '供应商图书'
    
    def __str__(self):
        return f"{self.supplierid.suppliername} - {self.isbn.title} (ISBN: {self.isbn.isbn})"
