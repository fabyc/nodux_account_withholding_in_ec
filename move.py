#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard, StateTransition, StateView, StateAction, \
    Button
from trytond.report import Report
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta


__all__ = [ 'Line']
__metaclass__ = PoolMeta

class Line():
    'Account Move Line'
    __name__ = 'account.move.line'

    @classmethod
    def __setup__(cls):
        super(Line, cls).__setup__()

        cls._order[0] = ('id', 'ASC')
