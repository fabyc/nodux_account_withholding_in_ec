#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from .invoice import *
from .account import *
from .withholding import *
from .party import *
def register():
    Pool.register(
        FiscalYear,
        Period,
        Invoice,
        Party,
        module='nodux_account_withholding_in_ec', type_='model')
    Pool.register(
        ValidatedInvoice,
        module='nodux_account_withholding_in_ec', type_='wizard')
    Pool.register(
        PrintMove,
        PrintWithholding,
        module='nodux_account_withholding_in_ec', type_='report')
