# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import odoo


def _make_acl(env, model_name):
    """ make a dummy acl and commit it
    so we don't get warning about missing acl
    """
    model_id = env['ir.model'].search([('name', '=', model_name)]).id
    acl = env['ir.model.access'].search([('model_id', '=', model_id)])
    if acl:
        return
    with odoo.api.Environment.manage():
        with odoo.registry(env.cr.dbname).cursor() as new_cr:
            new_env = odoo.api.Environment(new_cr, env.uid, env.context)
            new_env['ir.model.access'].create(dict(
                model_id=model_id,
                name='dummy acl for ' + model_name,
            ))
            new_env.cr.commit()


def init_test_model(env, model_cls):
    model_cls._build_model(env.registry, env.cr)
    model = env[model_cls._name].with_context(todo=[])
    model._prepare_setup()
    model._setup_base(partial=False)
    model._setup_fields(partial=False)
    model._setup_complete()
    model._auto_init()
    model.init()
    model._auto_end()
    _make_acl(env, model._name)


def _zip(iter1, iter2):
    i = 0
    iter1 = iter(iter1)
    iter2 = iter(iter2)
    while True:
        i1 = next(iter1, None)
        i2 = next(iter2, None)
        if i1 is None and i2 is None:
            raise StopIteration()
        yield i, i1, i2
        i += 1


def assert_matrix(matrix, expected):
    for i, row, expected_row in _zip(matrix.iter_rows(), expected):
        if row is None and expected_row is not None:
            assert False, "not enough rows"
        if row is not None and expected_row is None:
            assert False, "too many rows"
        for j, cell, expected_val in _zip(row.iter_cells(), expected_row):
            assert (cell and cell.val) == expected_val, \
                "%s != %s in row %s col %s" % \
                (cell and cell.val, expected_val, i, j)
