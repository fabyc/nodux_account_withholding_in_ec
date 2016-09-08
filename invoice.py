# -*- coding: utf-8 -*-
#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.model import Workflow, ModelSQL, ModelView, fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval
from trytond.wizard import Wizard, StateTransition, StateView, Button
from trytond.transaction import Transaction
from trytond.modules.company import CompanyReport
from trytond.wizard import Wizard, StateView, StateTransition, StateAction, \
    Button
from decimal import Decimal
from collections import defaultdict
from trytond.report import Report
from trytond import backend
from trytond.pyson import If, Eval, Bool, Id
from trytond.transaction import Transaction
from trytond.pool import Pool

__all__ = ['Invoice', 'ValidatedInvoice', 'PrintMove']
__metaclass__ = PoolMeta
#customer->cliente

class Invoice():
    'Invoice'
    __name__ = 'account.invoice'

    ref_withholding = fields.Char('Withholding')
    no_generate_withholding = fields.Boolean('No Generate Withholding', states={
            'readonly': Eval('state') != 'draft',
        })

    @classmethod
    def __setup__(cls):
        super(Invoice, cls).__setup__()
        cls._buttons.update({
                'cancel': {
                    'invisible': (~Eval('state').in_(['draft', 'validated'])
                        & ~((Eval('state') == 'posted')
                            & Eval('type').in_(
                                ['in_invoice', 'in_credit_note']))),
                    },
                'draft': {
                    'invisible': (~Eval('state').in_(['cancel', 'validated'])
                        | ((Eval('state') == 'cancel') & Eval('cancel_move'))),
                    'icon': If(Eval('state') == 'cancel', 'tryton-clear',
                        'tryton-go-previous'),
                    },
                'validate_invoice': {
                    'invisible': (Eval('state') != 'draft'), #|( Eval('no_generate_withholding', True)
                    },
                'post': {
                    'invisible': ~Eval('state').in_(['draft', 'validated']),
                    'readonly' : (Eval('state') == 'draft'), #(Eval('ref_withholding') == ''),
                    },
                'pay': {
                    'invisible': Eval('state') != 'posted',
                    'readonly': ~Eval('groups', []).contains(
                        Id('account', 'group_account')),
                    },
                })


    @staticmethod
    def default_ref_withholding():
        return ''

    @staticmethod
    def default_no_generate_withholding():
        return False

    @classmethod
    def withholdingOut(cls, invoices):
        '''
        Withholding and return ids of new withholdings.
        Return the list of new invoice
        '''
        MoveLine = Pool().get('account.move.line')
        Withholding = Pool().get('account.withholding')
        return Withholding.withholdingOut(invoices)

    @classmethod
    @ModelView.button_action('nodux_account_withholding_in_ec.wizard_validated')
    @Workflow.transition('validated')
    def validate_invoice(cls, invoices):
        for invoice in invoices:
            if invoice.type in ('in_credit_note'):
                invoice.set_number()
                invoice.create_move()
            elif invoice.type in ('in_invoice'):
                if invoice.no_generate_withholding == True:
                    invoice.set_number()
                    invoice.create_move()
                else:
                    pass

    @classmethod
    @ModelView.button
    @Workflow.transition('posted')
    def post(cls, invoices):
        modules = None
        modules_pos_e = None
        module_e = None
        module_pos_e = None
        w = False
        Module = Pool().get('ir.module.module')
        modules = Module.search([('name', '=', 'nodux_account_electronic_invoice_ec'), ('state', '=', 'installed')])
        modules_pos_e = Module.search([('name', '=', 'nodux_sale_pos_electronic_invoice_ec'), ('state', '=', 'installed')])
        pool = Pool()
        if modules:
            for mod in modules:
                module_e = mod
        if module_pos_e:
            for mod_e in modules_pos_e:
                module_pos_e = mod_e
        if module_e :
            Move = Pool().get('account.move')
            moves = []

            for invoice in invoices:
                invoice.limit()
                if invoice.type == u'out_invoice' or invoice.type == u'out_credit_note':
                    invoice.create_move()
                    invoice.set_number()
                    moves.append(invoice.create_move())
                    if invoice.lote == False:
                        invoice.get_invoice_element()
                        invoice.get_tax_element()
                        invoice.generate_xml_invoice()
                        invoice.get_detail_element()
                        invoice.action_generate_invoice()
                        invoice.connect_db()
                elif invoice.type == 'in_invoice':
                    Configuration = pool.get('account.configuration')
                    if Configuration(1).lote:
                        w = Configuration(1).lote
                    else:
                        pass

                    invoice.create_move()
                    if invoice.number:
                        pass
                    else:
                        invoice.set_number()
                    moves.append(invoice.create_move())
                    if w == False:
                        Withholding = Pool().get('account.withholding')
                        withholdings = Withholding.search([('number'), '=', invoice.ref_withholding])
                        for withholding in withholdings:
                        #invoice.authenticate()
                            if withholding.fisic == True:
                                pass
                            else:
                                withholding.get_invoice_element_w()
                                withholding.get_tax_element()
                                withholding.generate_xml_invoice_w()
                                withholding.get_taxes()
                                withholding.action_generate_invoice_w()
                                withholding.connect_db()
                elif invoice.type == 'out_debit_note':
                    invoice.create_move()
                    invoice.set_number()
                    moves.append(invoice.create_move())
                    """
                    if invoice.lote==False:
                        #invoice.authenticate()
                        invoice.get_tax_element()
                        invoice.get_debit_note_element()
                        invoice.get_detail_debit_note()
                        invoice.generate_xml_debit_note()
                        invoice.action_generate_debit_note()
                        invoice.connect_db()
                     """
            cls.write([i for i in invoices if i.state != 'posted'], {
                    'state': 'posted',
                    })
            Move.post([m for m in moves if m.state != 'posted'])

        else:
            Move = Pool().get('account.move')
            moves = []

            for invoice in invoices:
                invoice.set_number()
                if invoice.type == 'in_invoice':
                    invoice.create_move()
                invoice.create_move()
                moves.append(invoice.create_move())

            cls.write([i for i in invoices if i.state != 'posted'], {
                    'state': 'posted',
                    })
            Move.post([m for m in moves if m.state != 'posted'])


    def create_move(self):
        '''
        Create account move for the invoice and return the created move
        '''
        pool = Pool()
        Move = pool.get('account.move')
        Period = pool.get('account.period')
        Date = pool.get('ir.date')

        if self.move:
            return self.move
        self.update_taxes([self], exception=True)
        move_lines = self._get_move_line_invoice_line()
        move_lines += self._get_move_line_invoice_tax()
        if self.type == 'in_invoice':
            #if self.party.aplica_retencion == True:
            move_lines += self._get_move_line_invoice_withholding()
        total = Decimal('0.0')
        total_currency = Decimal('0.0')
        for line in move_lines:
            total += line['debit'] - line['credit']
            if line['amount_second_currency']:
                total_currency += line['amount_second_currency'].copy_sign(
                    line['debit'] - line['credit'])
        total = self.currency.round(total)
        term_lines = self.payment_term.compute(total, self.company.currency,
            self.invoice_date)
        remainder_total_currency = total_currency
        if not term_lines:
            term_lines = [(Date.today(), total)]
        for date, amount in term_lines:
            val = self._get_move_line(date, amount)
            if val['amount_second_currency']:
                remainder_total_currency += val['amount_second_currency']
            move_lines.append(val)
        if not self.currency.is_zero(remainder_total_currency):
            move_lines[-1]['amount_second_currency'] -= \
                remainder_total_currency

        accounting_date = self.accounting_date or self.invoice_date
        period_id = Period.find(self.company.id, date=accounting_date)

        move, = Move.create([{
                    'journal': self.journal.id,
                    'period': period_id,
                    'date': accounting_date,
                    'origin': str(self),
                    'lines': [('create', move_lines)],
                    }])
        self.write([self], {
                'move': move.id,
                })
        if self.type == 'in_invoice':
            if self.no_generate_withholding == True:
                pass
            else:
                Withholding = Pool().get('account.withholding')
                withholdings = Withholding.search([('number', '=', self.ref_withholding)])
                for w in withholdings:
                    withholding = w
                withholding.write([withholding], {
                    'move': move.id,
                    'ref_invoice':self.id,
                    })
        return move

    def _get_move_line_invoice_withholding(self):
        res = []
        pool = Pool()
        Withholding = pool.get('account.withholding')
        withholdings = Withholding.search([('number', '=', self.ref_withholding)])
        if withholdings:
            for w in withholdings:
                withholding = w
            for tax in withholding.taxes:
                val = tax.get_move_line()
                if val:
                    res.extend(val)
        return res

    def _get_move_line_invoice_line(self):
        '''
        Return list of move line values for each invoice lines
        '''
        res = []
        for line in self.lines:
            val = line.get_move_line()
            if val:
                res.extend(val)
        return res

class ValidatedInvoice(Wizard):
    'Generar Retencion'
    __name__ = 'account.invoice.validate_invoice'

    start = StateView('account.withholding',
        'nodux_account_withholding_out_ec.withholding_view_form', [
            Button('Cerrar', 'end', 'tryton-ok', default=True),
            ])

    def default_start(self, fields):

        Invoice = Pool().get('account.invoice')
        Journal = Pool().get('account.journal')
        Date = Pool().get('ir.date')
        fecha_actual = Date.today()

        default = {}
        journals = Journal.search([('type', '=', 'expense')])
        for j in journals:
            journal = j

        invoice = Invoice(Transaction().context.get('active_id'))

        invoice.set_number()
        #invoice.create_move()

        pool = Pool()
        Taxes = pool.get('account.tax')
        taxes_1 = Taxes.search([('type', '=', 'percentage')])

        if invoice.type == 'in_invoice':
            default['type'] = 'in_withholding'

        if invoice.reference:
            default['number_w'] = invoice.reference

        default['account'] = j.id
        default['withholding_address'] = invoice.invoice_address.id
        default['description'] = invoice.description
        default['reference'] = invoice.number
        default['comment']=invoice.comment
        default['company']=invoice.company.id
        default['party']=invoice.party.id
        default['currency']=invoice.currency.id
        default['journal']= journal.id
        default['taxes']=[]
        if invoice.taxes:
            default['base_imponible'] = invoice.taxes[0].base
            default['iva']= invoice.taxes[0].amount
        else:
            self.raise_user_error('Verifique los impuestos de la factura')
        default['withholding_date']= fecha_actual

        if invoice.party.impuesto_iva and invoice.party.impuestos_renta:
            pool = Pool()
            Tax = pool.get('account.tax')
            w_iva = invoice.party.impuesto_iva
            w_renta = invoice.party.impuestos_renta
            amount_i = Tax.compute([w_iva], invoice.taxes[0].amount, 1)
            amount_r = Tax.compute([w_renta], invoice.taxes[0].base, 1 )
            for value in amount_i:
                amount_w_i = value['amount']
            for value in amount_r:
                amount_w_r = value['amount']
            taxes = {
                'tax': w_iva.id,
                'manual':True,
                'base': invoice.taxes[0].amount,
                'amount': amount_w_i,
                'tipo':'IVA',
                }
            default['taxes'].append(taxes)
            taxes= {
                'tax': w_renta.id,
                'manual':True,
                'base': invoice.taxes[0].base,
                'amount': amount_w_r,
                'tipo':'RENTA',
                }
            default['taxes'].append(taxes)
            return default
        else:
            return self.raise_user_error('No ha configurado los impuestos de retencion del proveedor')

class PrintMove(CompanyReport):
    'Print Move'
    __name__ = 'account.invoice.print_move'

    @classmethod
    def __setup__(cls):
        super(PrintMove, cls).__setup__()

    @classmethod
    def parse(cls, report, objects, data, localcontext=None):
        pool = Pool()
        Move = pool.get('account.move')
        sum_debit = Decimal('0.0')
        sum_credit = Decimal('0.0')
        invoice = Transaction().context.get('move')
        for invoice in objects:
            for line in invoice.move.lines:
                sum_debit += line.debit
                sum_credit += line.credit

        localcontext['company'] = Transaction().context.get('company')
        localcontext['move'] = Transaction().context.get('company')
        localcontext['invoice'] = Transaction().context.get('invoice')
        localcontext['sum_debit'] = sum_debit
        localcontext['sum_credit'] = sum_credit

        return super(PrintMove, cls).parse(report,
                objects, data, localcontext)
