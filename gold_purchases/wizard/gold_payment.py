# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class stockGoldMove(models.TransientModel):
    _name = 'stock.move.gold'
    _description = 'Generate move for all selected moves'

    move_ids = fields.Many2many('stock.production.lot', 'move_stock_group_rel', 'stock_gold', 'move_id',  'moves', readonly=False)
    pure_weight = fields.Float('pure weight')
    pure_remainning = fields.Float('pure remainning',compute="get_pure_weight_remain")

    @api.depends('move_ids')
    def get_pure_weight_remain(self):
        pure = 0.00
        for rec in self.move_ids:
            pure = pure + rec.pure_weight
        self.pure_remainning = self.pure_weight -  pure

    def compute_sheet(self):
        [data] = self.read()
        if not data['move_ids']:
            raise UserError(_("You must select move(s) to generate payment(s)."))

        active_id = self.env.context.get('active_id')
        gold_picking_type = self.env.ref('gold_purchases.gold_picking_type')

        if active_id:
            account_move = self.env['account.move'].search([('id' ,'=', active_id)])
        
        pure = 0.00
        gross_weight = 0.00
        purity = 0.00
        for move in self.env['stock.production.lot'].browse(data['move_ids']):
            pure = pure + move.pure_weight
            gross_weight = gross_weight + move.gross_weight
            purity = purity + move.purity
            product_id = move.product_id
            
            
        if pure > account_move.pure_wt_value:
            raise UserError(_("you can pay in gold" + "" + str(account_move.pure_wt_value)))
        else:
            account_move.write({'pure_wt_value': account_move.pure_wt_value - pure }) 
            pure_money = account_move.pure_wt_value * account_move.gold_rate_value
            account_move.write({'make_value_move': account_move.make_value_move - pure_money }) 
        
        if account_move.pure_wt_value == 0.00 and account_move.make_value_move == 0.00:
            account_move.write({'invoice_payment_state': "paid"}) 

        picking = self.env['stock.picking'].create({
                    'location_id': gold_picking_type.default_location_src_id.id,
                    'location_dest_id': account_move.partner_id.property_stock_supplier.id,
                    'picking_type_id': gold_picking_type.id,
                    'bill_unfixed': account_move.id,
                    'immediate_transfer': False,
                    'move_lines': [(0, 0, {
                            'name': "unfixed move",
                            'location_id': gold_picking_type.default_location_src_id.id,
                            'location_dest_id': account_move.partner_id.property_stock_supplier.id,
                            'product_id': product_id.id,
                            'product_uom': product_id.uom_id.id,
                            'picking_type_id': gold_picking_type.id,
                            'product_uom_qty': 1,
                            'pure_weight': pure,
                            'gross_weight': gross_weight,
                            'purity': purity,})]
                })
            
        # stock_move = self.env['stock.move'].create({
        #                 'name': "unfixed move",
        #                 'procure_method': "make_to_order",
        #                 'location_id': gold_picking_type.default_location_src_id.id,
        #                 'location_dest_id': account_move.partner_id.property_stock_customer.id,
        #                 'product_id': product_id.id,
        #                 'product_uom': product_id.uom_id.id,
        #                 'picking_id': picking.id,
        #                 'picking_type_id': gold_picking_type.id,
        #                 'product_uom_qty': 1,
        #                 'pure_weight': pure,
        #                 'gross_weight': gross_weight,
        #                 'purity': purity,
                       
        #             })
                            
        return {'type': 'ir.actions.act_window_close'}