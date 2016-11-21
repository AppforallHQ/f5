# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plans', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankPayment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.CharField(default=None, max_length=64, null=True)),
                ('pay_time', models.DateTimeField(auto_now_add=True)),
                ('gateway', models.CharField(max_length=32)),
                ('invoice_number', models.CharField(max_length=32)),
                ('user_mail', models.CharField(max_length=256)),
                ('session_key', models.CharField(max_length=64)),
                ('amount', models.PositiveIntegerField()),
                ('ref_id', models.CharField(max_length=64)),
                ('res_code', models.CharField(default=b'-1', max_length=10)),
                ('payment_card', models.CharField(max_length=32)),
                ('sale_reference_id', models.CharField(max_length=32)),
                ('invoice', models.ForeignKey(default=None, to='plans.Invoice', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(editable=False, max_digits=20, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)])),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('successful_payment', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DepositTransaction',
            fields=[
                ('transaction_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='payment.Transaction')),
            ],
            options={
            },
            bases=('payment.transaction',),
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.ForeignKey(related_name='wallet', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WalletDeposit',
            fields=[
                ('deposittransaction_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='payment.DepositTransaction')),
                ('deposited_via_id', models.PositiveIntegerField(null=True, blank=True)),
                ('deposited_via_content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
            },
            bases=('payment.deposittransaction',),
        ),
        migrations.CreateModel(
            name='WalletTransaction',
            fields=[
                ('transaction_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='payment.Transaction')),
            ],
            options={
            },
            bases=('payment.transaction',),
        ),
        migrations.CreateModel(
            name='WalletWithdrawal',
            fields=[
                ('wallettransaction_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='payment.WalletTransaction')),
            ],
            options={
            },
            bases=('payment.wallettransaction',),
        ),
        migrations.CreateModel(
            name='WithdrawalTransaction',
            fields=[
                ('transaction_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='payment.Transaction')),
                ('hamkharid_object_id', models.PositiveIntegerField()),
            ],
            options={
            },
            bases=('payment.transaction',),
        ),
        migrations.CreateModel(
            name='BankTransaction',
            fields=[
                ('withdrawaltransaction_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='payment.WithdrawalTransaction')),
                ('gateway_transaction_id', models.CharField(max_length=30, editable=False, blank=True)),
                ('ref_id', models.CharField(max_length=30, blank=True)),
                ('res_code', models.CharField(default=b'-1', max_length=10)),
            ],
            options={
            },
            bases=('payment.withdrawaltransaction',),
        ),
        migrations.AddField(
            model_name='withdrawaltransaction',
            name='hamkharid_object_content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='wallettransaction',
            name='wallet',
            field=models.ForeignKey(editable=False, to='payment.Wallet'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='bankpayment',
            unique_together=set([('gateway', 'invoice_number')]),
        ),
        migrations.AlterIndexTogether(
            name='bankpayment',
            index_together=set([('gateway', 'invoice_number'), ('session_key',), ('user_id',)]),
        ),
    ]
