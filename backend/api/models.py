# Django의 ORM 기능을 사용하기 위해 models 모듈을 import
from django.db import models

# Create your models here.
class Api(models.Model):
    user_id      = models.CharField(max_length=20, null=False, verbose_name='UserID')
    username     = models.CharField(max_length=30, null=False, verbose_name='Full Name')
    password     = models.CharField(max_length=128, null=False, verbose_name='Password')
    email        = models.EmailField(max_length=254, null=False, verbose_name='Email Address')
    phone_number = models.CharField(max_length=20, null=False, verbose_name='Phone Number')
    visit_count  = models.IntegerField(default=0, verbose_name='Visit Count')
    joined_at    = models.DateTimeField(auto_now_add=True, null=False, verbose_name='Join Date')
    joined_ip    = models.GenericIPAddressField(null=False, verbose_name='Join IP Address')

    def __str__(self):
        return self.username
    

class Accommodation(models.Model):
    store_name        = models.CharField(max_length=255, null=False, verbose_name="Store Name")
    grade             = models.CharField(max_length=50, null=False, verbose_name="Grade")
    address           = models.CharField(max_length=500, null=False, verbose_name="Address")
    phone_number      = models.CharField(max_length=50, null=True, blank=True, verbose_name="Phone Number")
    rating            = models.FloatField(null=False, verbose_name="Rating")
    user_review_count = models.IntegerField(null=False, verbose_name="User Review Count")
    blog_review_count = models.IntegerField(null=False, verbose_name="Blog Review Count")
    reservation_site  = models.CharField(max_length=255, null=True, blank=True, verbose_name="Reservation Site")

    def __str__(self):
        return self.store_name