from django.db import models
from plans.models import Subscription,Invoice

class CronLog(models.Model):
    subscription = models.ForeignKey("plans.Subscription")
    ACTIVE = 1
    INVITE = 2
    ENDING = 3
    EXTRA = 4
    SUSPEND = 5
    BLOCKED = 6
    STATUS = (
        (ACTIVE, 'Active'), (INVITE, 'invoice_issued'),
        (ENDING, 'plan_ending_notice'), (EXTRA, 'extra_day_notice'),
        (SUSPEND, 'suspend_idevice'), (BLOCKED, 'Blocked')
    )
    status = models.IntegerField(choices=STATUS, default=ACTIVE)
    date = models.DateTimeField(auto_now_add=True)
    
    @classmethod
    def get_latest(clss,subscription):
        try:
            return clss.objects.filter(subscription=subscription).order_by("-date")[0]
        except:
            newobj = clss(subscription=subscription)
            newobj.save()
            return newobj
    
    
    def mark_as_active(self):
        newobj = CronLog(subscription=self.subscription,status=CronLog.ACTIVE)
        newobj.save()
        return newobj
    
    def mark_as_invite(self):
        newobj = CronLog(subscription=self.subscription,status=CronLog.INVITE)
        newobj.save()
        return newobj
        
    def mark_as_ending(self):
        newobj = CronLog(subscription=self.subscription,status=CronLog.ENDING)
        newobj.save()
        return newobj
        
    def mark_as_extra(self):
        newobj = CronLog(subscription=self.subscription,status=CronLog.EXTRA)
        newobj.save()
        return newobj
        
    def mark_as_suspend(self):
        newobj = CronLog(subscription=self.subscription,status=CronLog.SUSPEND)
        newobj.save()
        return newobj

    def mark_as_blocked(self):
        newobj = CronLog(subscription=self.subscription,status=CronLog.BLOCKED)
        newobj.save()
        return newobj
    
    def is_active(self):
        return self.status == CronLog.ACTIVE

    def is_blocked(self):
        return self.status == CronLog.BLOCKED
    
    def is_invite(self):
        return self.status == CronLog.INVITE
    
    def is_noticed(self):
        return self.status == CronLog.ENDING
    
    def is_extra(self):
        return self.status == CronLog.EXTRA
    
    
    
    
    def get_status(self):
        return self.get_status_display()
    
    
    
    
    class Meta:
        index_together = (('subscription','date'),)
