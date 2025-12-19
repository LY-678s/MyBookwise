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


class Bookauthor(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    isbn = models.ForeignKey(Book, models.DO_NOTHING, db_column='ISBN')  # Field name made lowercase.
    authorname = models.CharField(db_column='AuthorName', max_length=50)  # Field name made lowercase.
    authororder = models.IntegerField(db_column='AuthorOrder')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'bookauthor'


class Creditlevel(models.Model):
    levelid = models.IntegerField(db_column='LevelID', primary_key=True)  # Field name made lowercase.
    discountrate = models.DecimalField(db_column='DiscountRate', max_digits=3, decimal_places=2)  # Field name made lowercase.
    canoverdraft = models.IntegerField(db_column='CanOverdraft')  # Field name made lowercase.
    overdraftlimit = models.DecimalField(db_column='OverdraftLimit', max_digits=10, decimal_places=2)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'creditlevel'


class Customer(models.Model):
    customerid = models.AutoField(db_column='CustomerID', primary_key=True)  # Field name made lowercase.
    username = models.CharField(db_column='Username', unique=True, max_length=50)  # Field name made lowercase.
    password = models.CharField(db_column='Password', max_length=50)  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=50)  # Field name made lowercase.
    address = models.CharField(db_column='Address', max_length=200, blank=True, null=True)  # Field name made lowercase.
    email = models.CharField(db_column='Email', unique=True, max_length=100, blank=True, null=True)  # Field name made lowercase.
    balance = models.DecimalField(db_column='Balance', max_digits=10, decimal_places=2)  # Field name made lowercase.
    levelid = models.ForeignKey(Creditlevel, models.DO_NOTHING, db_column='LevelID')  # Field name made lowercase.
    overdraftlimit = models.DecimalField(db_column='OverdraftLimit', max_digits=10, decimal_places=2)  # Field name made lowercase.
    totalspent = models.DecimalField(db_column='TotalSpent', max_digits=12, decimal_places=2)  # Field name made lowercase.
    registerdate = models.DateTimeField(db_column='RegisterDate')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'customer'


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


class Orders(models.Model):
    orderid = models.AutoField(db_column='OrderID', primary_key=True)  # Field name made lowercase.
    orderno = models.CharField(db_column='OrderNo', unique=True, max_length=30)  # Field name made lowercase.
    orderdate = models.DateTimeField(db_column='OrderDate')  # Field name made lowercase.
    customerid = models.ForeignKey(Customer, models.DO_NOTHING, db_column='CustomerID')  # Field name made lowercase.
    shipaddress = models.CharField(db_column='ShipAddress', max_length=200)  # Field name made lowercase.
    totalamount = models.DecimalField(db_column='TotalAmount', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    status = models.IntegerField(db_column='Status')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'orders'


class Procurement(models.Model):
    procid = models.AutoField(db_column='ProcID', primary_key=True)  # Field name made lowercase.
    procno = models.CharField(db_column='ProcNo', unique=True, max_length=30)  # Field name made lowercase.
    supplierid = models.ForeignKey('Supplier', models.DO_NOTHING, db_column='SupplierID')  # Field name made lowercase.
    recordid = models.ForeignKey('Shortagerecord', models.DO_NOTHING, db_column='RecordID', blank=True, null=True)  # Field name made lowercase.
    createdate = models.DateTimeField(db_column='CreateDate')  # Field name made lowercase.
    status = models.IntegerField(db_column='Status')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'procurement'


class Procurementdetail(models.Model):
    detailid = models.AutoField(db_column='DetailID', primary_key=True)  # Field name made lowercase.
    procid = models.ForeignKey(Procurement, models.DO_NOTHING, db_column='ProcID')  # Field name made lowercase.
    isbn = models.ForeignKey(Book, models.DO_NOTHING, db_column='ISBN')  # Field name made lowercase.
    quantity = models.IntegerField(db_column='Quantity')  # Field name made lowercase.
    supplyprice = models.DecimalField(db_column='SupplyPrice', max_digits=10, decimal_places=2)  # Field name made lowercase.
    receivedqty = models.IntegerField(db_column='ReceivedQty')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'procurementdetail'


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


class Supplierbook(models.Model):
    supplierid = models.OneToOneField(Supplier, models.DO_NOTHING, db_column='SupplierID', primary_key=True)  # Field name made lowercase.
    isbn = models.ForeignKey(Book, models.DO_NOTHING, db_column='ISBN')  # Field name made lowercase.
    supplyprice = models.DecimalField(db_column='SupplyPrice', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    lastsupplydate = models.DateTimeField(db_column='LastSupplyDate', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'supplierbook'
        unique_together = (('supplierid', 'isbn'),)
