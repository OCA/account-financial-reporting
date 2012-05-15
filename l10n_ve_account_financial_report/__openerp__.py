# -*- encoding: utf-8 -*-
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################
{
	"name" : "Reportes Financieros",
	"version" : "0.3",
	"author" : "Vauxoo & Industrias Diana C.A.",
	"website" : "http://wiki.openerp.org.ve/",
	"depends" : ["base","account"],
	"category" : "Localisation/Accounting",
	"description": """
                Modulo para Generar reportes financieros
                   """,
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [
            "wizard_report_report.xml",
            "wizard/account_report_wizard.xml",
            #~ "wizard/account_mayor_analitico.xml",
	],
	"active": False,
	"installable": True,
}
