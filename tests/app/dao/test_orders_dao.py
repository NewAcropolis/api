import pytest

from app.dao.orders_dao import dao_get_orders
from app.models import Order

from tests.db import create_order


class WhenUsingOrdersDao:

    def it_gets_orders_for_a_year(self, db_session):
        # within year
        order1 = create_order(created_at='2021-06-01 12:00')  # within year
        order2 = create_order(created_at='2021-01-01 00:00')  # start of year

        # outside year
        create_order(created_at='2020-10-01 12:00')  # before year
        create_order(created_at='2022-01-01 00:01')  # after year

        orders = dao_get_orders(2021)

        assert len(orders) == 2
        assert set([o.id for o in orders]) == set([order1.id, order2.id])

    def it_gets_all_orders(self, db_session):
        create_order(created_at='2021-06-01 12:00')
        create_order(created_at='2021-01-01 00:00')
        create_order(created_at='2020-10-01 12:00')
        create_order(created_at='2022-01-01 00:01')

        orders = dao_get_orders()

        assert len(orders) == 4
