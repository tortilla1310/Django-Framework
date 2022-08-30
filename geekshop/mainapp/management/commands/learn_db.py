from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q, F, When, Case, IntegerField, DecimalField

from adminapp.views import db_profile_by_type
from mainapp.models import Product
from ordersapp.models import OrderItem


class Command(BaseCommand):
    def handle(self, *args, **options):
        # test_products = Product.objects.filter(
        #     Q(category__name='Модерн') |
        #     Q(category__name="Офис")
        #
        # )
        #
        # print(len(test_products))
        #
        # db_profile_by_type('learn_db', '', connection.queries)

        ACTION_1 = 1
        ACTION_2 = 2
        ACTION_EXPIRED = 3

        action_1__discount = 0.3
        action_2__discount = 0.15
        action_expired__discount = 0.5

        action_1__time_delta = timedelta(hours=12)
        action_2__time_delta = timedelta(days=1)

        action_1__condition = Q(order__updated__lte=F('order__created') + action_1__time_delta)
        action_2__condition = Q(order__updated__gt=F('order__created') + action_1__time_delta) & \
                              Q(order__updated__lte=F('order__created') + action_2__time_delta)
        action_expired__condition = Q(order__updated__gt=F('order__created') + action_2__time_delta)

        action_1__price = When(action_1__condition, then=F('product__price') * F('quantity') * action_1__discount)
        action_2__price = When(action_2__condition, then=F('product__price') * F('quantity') * action_2__discount)
        action_expired__price = (When(action_expired__condition, then=F('product__price') * F('quantity') *
                                                                     action_expired__discount))

        action_1__order = When(action_1__condition, then=ACTION_1)
        action_2__order = When(action_1__condition, then=ACTION_2)
        action_expired__order = When(action_expired__condition, then=ACTION_EXPIRED)

        test_orders = OrderItem.objects.annotate(
            action_order=Case(
                action_1__order,
                action_2__order,
                action_expired__order,
                output_field=IntegerField(),
            )).annotate(
            total_price=Case(
                action_1__price,
                action_2__price,
                action_expired__price,
                output_field=DecimalField(),
            )).order_by('action_order', 'total_price').select_related()

        for orderitem in test_orders:
            print(f'{orderitem.action_order:2}: заказ №{orderitem.pk:3}:'
                  f'{orderitem.product.name:25}: скидка {abs(orderitem.total_price):12.5f} руб. | '
                  f'{orderitem.order.updated - orderitem.order.created}'
                  )
