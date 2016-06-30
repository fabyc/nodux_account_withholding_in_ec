#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
#! -*- coding: utf8 -*-
from trytond.pool import *
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pyson import Id
from trytond.pool import Pool, PoolMeta
from trytond import backend
from trytond.transaction import Transaction

__all__ = ['Party']

class Party:
    __metaclass__ = PoolMeta
    __name__ = 'party.party'

    aplica_retencion = fields.Boolean('Aplica Retencion')

    impuestos_renta = fields.Many2One('account.tax', 'FUENTE')

    impuesto_iva = fields.Many2One('account.tax', 'IVA')


    @classmethod
    def __setup__(cls):
        super(Party, cls).__setup__()
