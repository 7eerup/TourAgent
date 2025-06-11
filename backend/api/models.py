# Django의 ORM 기능을 사용하기 위해 models 모듈을 import
from django.db import models

# Create your models here.
class User(models.Model):
    user_id             = models.AutoField(primary_key=True, null=False, verbose_name='UserID')
    username            = models.CharField(max_length=50, null=False, verbose_name='Full Name')
    password_hash       = models.CharField(max_length=255, null=False, verbose_name='Password')
    email               = models.CharField(max_length=100, null=False, unique=True, verbose_name='Email Address')
    phone_number        = models.CharField(max_length=20, null=True, verbose_name='Phone Number')
    visit_count         = models.IntegerField(default=0, verbose_name='Visit Count')
    joined_at           = models.DateTimeField(auto_now_add=True, null=False, verbose_name='Join Date')
    joined_ip           = models.CharField(max_length=50, null=True, verbose_name='Join IP Address')

    def __str__(self):
        return self.username


# class ChatSession(models.Model):
#     chat_session_id     = models.AutoField(primary_key=True, null=False, verbose_name="Chat Session ID")
#     chat_session_title  = models.CharField(max_length=255, null=False, verbose_name="Chat Session Title")
#     created_at          = models.DateTimeField(auto_now_add=True, null=False, verbose_name="Created At")
#     updated_at          = models.DateTimeField(auto_now_add=True, null=False, verbose_name="Updated At")
#     userid              = models.ForeignKey(User, on_delete=models.CASCADE, null=False, verbose_name="User ID")

#     def __str__(self):
#         return self.chat_session_title


# class ChatMessage(models.Model):
#     chat_message_id     = models.AutoField(primary_key=True, null=False, verbose_name="Chat Message ID")
#     chat_order_number   = models.IntegerField(null=False, verbose_name="Chat Order Number")
#     chat_sender         = models.CharField(max_length=10, null=False, verbose_name="Chat Sender")
#     message             = models.TextField(null=True, verbose_name="Message")
#     message_type        = models.CharField(max_length=10, null=False, verbose_name="Message Type")
#     message_time        = models.DateTimeField(auto_now_add=True, null=False, verbose_name="Message Time")
#     chat_session_id     = models.ForeignKey(ChatSession, on_delete=models.CASCADE, null=False, verbose_name="Chat Session ID")

#     def __str__(self):
#         return self.chat_sender + " - " + self.message[:50]
    



# class TourInfo(models.Models):
#     content_id          = models.AutoField(primary_key=True, null=False, verbose_name="Content ID")
#     title               = models.CharField(max_length=200, null=False, verbose_name="Title")
#     content_type_id     = models.CharField(max_length=20, null=False, verbose_name="Content Type ID")
#     address             = models.CharField(max_length=255, null=False, verbose_name="Address")
#     lDongRegnCd         = models.CharField(max_length=20, null=False, verbose_name="Local Dong Code")
#     lDongSignguCd       = models.CharField(max_length=20, null=False, verbose_name="Local Signgu Code")
#     phone_number        = models.CharField(max_length=20, null=True, verbose_name="Telephone")
#     map_x               = models.FloatField(null=True, verbose_name="Map X")
#     map_y               = models.FloatField(null=True, verbose_name="Map Y")
#     category_one        = models.CharField(max_length=50, null=True, verbose_name="Category 1")
#     category_two        = models.CharField(max_length=50, null=True, verbose_name="Category 2")
#     category_three      = models.CharField(max_length=50, null=True, verbose_name="Category 3")

#     def __str__(self):
#         return self.title


# class Restaurant(models.Model):
#     store_name           = models.AutoField(primary_key=True, max_length=100, null=False, verbose_name="Store Name")
#     address              = models.CharField(max_length=200, null=False, verbose_name="Address")
#     phone_number         = models.CharField(max_length=20, null=True, verbose_name="Phone Number")
#     rating               = models.FloatField(null=False, verbose_name="Rating")
#     visitor_review_count = models.IntegerField(null=False, verbose_name="Visitor Review Count")
#     blog_review_count    = models.IntegerField(null=False, verbose_name="Blog Review Count")
#     reservation_site     = models.CharField(max_length=255, null=True, verbose_name="Reservation Site")
#     category             = models.CharField(max_length=50, null=True, verbose_name="Category")
#     tag                  = models.CharField(max_length=20, null=True, verbose_name="Tag")
#     monday_biz_hours     = models.CharField(max_length=20, null=True, verbose_name="monday_biz_hours")
#     monday_break_time    = models.CharField(max_length=20, null=True, verbose_name="monday_break_time")
#     monday_last_order    = models.CharField(max_length=20, null=True, verbose_name="monday_last_order")
#     tuesday_biz_hours    = models.CharField(max_length=20, null=True, verbose_name="tuesday_biz_hours")
#     tuesday_break_time   = models.CharField(max_length=20, null=True, verbose_name="tuesday_break_time")
#     tuesday_last_order   = models.CharField(max_length=20, null=True, verbose_name="tuesday_last_order")
#     wednesday_biz_hours  = models.CharField(max_length=20, null=True, verbose_name="wednesday_biz_hours")
#     wednesday_break_time = models.CharField(max_length=20, null=True, verbose_name="wednesday_break_time")
#     wednesday_last_order = models.CharField(max_length=20, null=True, verbose_name="wednesday_last_order")
#     thursday_biz_hours   = models.CharField(max_length=20, null=True, verbose_name="thursday_biz_hours")
#     thursday_break_time  = models.CharField(max_length=20, null=True, verbose_name="thursday_break_time")
#     thursday_last_order  = models.CharField(max_length=20, null=True, verbose_name="thursday_last_order")
#     friday_biz_hours     = models.CharField(max_length=20, null=True, verbose_name="friday_biz_hours")
#     friday_break_time    = models.CharField(max_length=20, null=True, verbose_name="friday_break_time")
#     friday_last_order    = models.CharField(max_length=20, null=True, verbose_name="friday_last_order")
#     saturday_biz_hours   = models.CharField(max_length=20, null=True, verbose_name="saturday_biz_hours")
#     saturday_break_time  = models.CharField(max_length=20, null=True, verbose_name="saturday_break_time")
#     saturday_last_order  = models.CharField(max_length=20, null=True, verbose_name="saturday_last_order")
#     sunday_biz_hours     = models.CharField(max_length=20, null=True, verbose_name="sunday_biz_hours")
#     sunday_break_time    = models.CharField(max_length=20, null=True, verbose_name="sunday_break_time")
#     sunday_last_order    = models.CharField(max_length=20, null=True, verbose_name="sunday_last_order")

#     def __str__(self):
#         return self.store_name



# class Accommodation(models.Model):
#     store_name          = models.AutoField(primary_key=True, max_length=100, null=False, verbose_name="Store Name")
#     grade               = models.CharField(max_length=50, null=False, verbose_name="Grade")
#     address             = models.CharField(max_length=255, null=False, verbose_name="Address")
#     phone_number        = models.CharField(max_length=20, null=True, verbose_name="Phone Number")
#     rating              = models.FloatField(null=False, verbose_name="Rating")
#     user_review_count   = models.IntegerField(null=False, verbose_name="User Review Count")
#     blog_review_count   = models.IntegerField(null=False, verbose_name="Blog Review Count")
#     reservation_site    = models.CharField(max_length=255, null=True, verbose_name="Reservation Site")

#     def __str__(self):
#         return self.store_name
    

# class Weather(models.Model):
#     weather_id          = models.AutoField(primary_key=True, null=False, verbose_name="Weather ID")
#     area_nm             = models.ForeignKey(max_length=50, null=False, verbose_name="Area Name")
#     base_date           = models.DateField(null=False, verbose_name="Base Date")
#     pcp                 = models.IntegerField(null=False, verbose_name="Precipitation")
#     pop                 = models.IntegerField(null=False, verbose_name="Probability of Precipitation")
#     pty                 = models.IntegerField(null=False, verbose_name="Precipitation Type")
#     reh                 = models.IntegerField(null=False, verbose_name="Relative Humidity")
#     sno                 = models.IntegerField(null=False, verbose_name="Snowfall")
#     sky                 = models.IntegerField(null=False, verbose_name="Sky Condition")
#     tmp                 = models.IntegerField(null=False, verbose_name="Temperature")
#     tmn                 = models.IntegerField(null=False, verbose_name="Minimum Temperature")
#     tmx                 = models.IntegerField(null=False, verbose_name="Maximum Temperature")
#     wsd                 = models.IntegerField(null=False, verbose_name="Wind Direction")
#     base_time           = models.CharField(primary_key=True, max_length=4, null=False, verbose_name="Base Time")
#     fcst_data           = models.DateField(primary_key=True, null=False, verbose_name="Forecast Data")
#     fcst_time           = models.CharField(max_length=4, null=False, verbose_name="Forecast Time")
#     nx                  = models.IntegerField(primary_key=True, null=False, verbose_name="NX")
#     ny                  = models.IntegerField(primary_key=True, null=False, verbose_name="NY")
    

#     def __str__(self):
#         return self.area_nm
    


# class CongestionData(models.Model):
#     congestion_data_id  = models.AutoField(primary_key=True, null=False, verbose_name="Congestion Data ID")
#     area_cd             = models.CharField(max_length=20, null=False, verbose_name="Area Code")
#     area_nm             = models.CharField(max_length=100, null=False, verbose_name="Area Name")
#     area_congest_lvl    = models.CharField(max_length=20, null=False, verbose_name="Area Congestion Level")
#     area_congest_msg    = models.TextField(null=False, verbose_name="Area Congestion Message")
#     area_ppltn_min      = models.IntegerField(null=False, verbose_name="Area Population Min")
#     area_ppltn_max      = models.IntegerField(null=False, verbose_name="Area Population Max")
#     male_ppltn_rate     = models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="")
#     female_ppltn_rate   = models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="")
#     ppltn_rate_0        = models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="Population Rate 0")
#     ppltn_rate_10       = models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="Population Rate 10")
#     ppltn_rate_20       = models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="Population Rate 20")
#     ppltn_rate_30       = models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="Population Rate 30")
#     ppltn_rate_40       = models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="Population Rate 40")
#     ppltn_rate_50       = models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="Population Rate 50")
#     ppltn_rate_60       = models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="Population Rate 60")
#     ppltn_rate_70       = models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="Population Rate 70")
#     resnt_ppltn_rate    = models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="Resident Population Rate")
#     non_resnt_ppltn_rate= models.DecimalField(max_digits=5, decimal_places=2, null=False, verbose_name="Non-Resident Population Rate")
#     replace_yn          = models.CharField(max_length=2, null=False, verbose_name="Replace YN")
#     ppltn_time          = models.DateTimeField(primary_key=True, auto_now_add=True, null=False, verbose_name="Population Time")
#     fcst_yn             = models.CharField(max_length=2, null=False, verbose_name="Forecast YN")
#     fcst_time           = models.DateTimeField(null=True, verbose_name="Forecast Time")
#     fcst_congest_lvl    = models.CharField(max_length=20, null=True, verbose_name="Forecast Congestion Level")
#     fcst_ppltn_min      = models.IntegerField(null=True, verbose_name="Forecast Population Min")
#     fcst_ppltn_max      = models.IntegerField(null=True, verbose_name="Forecast Population Max")

#     def __str__(self):
#         return self.area_nm