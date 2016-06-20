# -*- coding: utf-8 -*-
#This file is part of the nodux_account_voucher_ec module for Tryton.
#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import ModelSingleton, ModelView, ModelSQL, fields, Workflow
from trytond.transaction import Transaction
from trytond.pyson import Eval, In, If, Bool, Id
from trytond.pool import Pool
from trytond.report import Report
import pytz
from datetime import datetime,timedelta
import time
from sql import Literal
from trytond.wizard import Wizard, StateView, StateTransition, StateAction, \
    Button
from trytond import backend
from trytond.tools import reduce_ids, grouped_slice
from sql.conditionals import Coalesce, Case
from sql.aggregate import Count, Sum
from sql.functions import Abs, Sign
from trytond.modules.company import CompanyReport

__all__ = ['PrintWithholding']


class PrintWithholding(CompanyReport):
    'Print Withholding'
    __name__ = 'account.withholding.print_withholding'

    @classmethod
    def __setup__(cls):
        super(PrintWithholding, cls).__setup__()

    @classmethod
    def parse(cls, report, objects, data, localcontext=None):
        localcontext['company'] = Transaction().context.get('company')
        #localcontext['invoice'] = Transaction().context.get('invoice')
        return super(PrintWithholding, cls).parse(report,
                objects, data, localcontext)
