## -*- coding: utf-8 -*-
<!DOCTYPE html SYSTEM
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <style type="text/css">
            .total{
               font-weight:bold;
            }
            .break{
                display: block;
                clear: both;
                page-break-after: always;
            }

            ${css}
        </style>
    </head>

    <%!
    def amount(text):
        # replace by a non-breaking hyphen (it will not word-wrap between hyphen and numbers)
        return text.replace('-', '&#8209;')

    %>
    <body>
    %for idx, partner in enumerate(objects):
        <%setLang(partner.lang)%>
        %if idx > 0:
            <div class="break"></div>
        %endif
        <br/>
        <br/>
        <%from datetime import date %>
        ${_('Date')}: ${formatLang(str(date.today()), date=True)}
        <br>
        ${_('Partner')}: ${partner.name}
        <br>
        ${_('Subject')}: <b>${_('Overdue Statement')}</b>
        <br/>
        <br/>
        %if show_message:
            %for message_line in message(partner, company):
                <p>
                ${message_line}
                </p>
            %endfor
        %endif
        <br>
        ${user.name}
        <br>
        <br>
        %if (partner.credit + partner.debit == 0) :
            <div class="title">${_('Nothing due for this partner')}</div>
        %else:
            <div class="title">${_('Aged Balance')}</div>
            <br>
        %if get_balance(partner, company):
            <table class="basic_table" style="width: 100%;">
                <tr>
                    <th>${_('Not Due')}</th>
                    <th>${_('0-30')}</th>
                    <th>${_('30-60')}</th>
                    <th>${_('60-90')}</th>
                    <th>${_('90-120')}</th>
                    <th>${_('+120')}</th>
                    <th>${_('Total')}</th>
                    <th>${_('Currency')}</th>
                </tr>
                %for l in get_balance(partner, company):
                <tr>
                    <td>${ l['not_due'] }</td>
                    <td>${ l['30'] }</td>
                    <td>${ l['3060'] }</td>
                    <td>${ l['6090'] }</td>
                    <td>${ l['90120'] }</td>
                    <td>${ l['120'] }</td>
                    <td>${ l['total'] }</td>
                    <td>${ l['currency_name']}</td>
                </tr>
                %endfor
            </table>
        %endif
        <br>
        <br>
        <div class="title">${_('List of Due Invoices')}</div>
        %if getLines30(partner, company):
            <br>
            <div class="total">${_('0-30')}</div>
            <table class="basic_table" style="width: 100%;">
                <tr>
                    <th>${_('Date')}</th>
                    <th>${_('Description')}</th>
                    <th>${_('Reference')}</th>
                    <th>${_('Due date')}</th>
                    <th>${_('Amount')}</th>
                    <th>${_('Paid')}</th>
                    <th>${_('Total')}</th>
                    <th>${_('Currency')}</th>
                </tr>
                %for line in getLines30(partner, company):
                <tr>
                    <td>${ formatLang(line['date_original'], date=True) }</td>
                    <td>${ line['name'] }</td>
                    <td>${ line['ref'] }</td>
                    <td>${ line['date_due'] and formatLang(line['date_due'], date=True) or '' }</td>
                    <td style="text-align: right;">${ formatLang(line['amount_original']) }</td>
                    <td style="text-align: right;">${ formatLang(line['amount_original'] - line['amount_unreconciled']) }</td>
                    <td style="text-align: right;">${ formatLang(line['amount_unreconciled']) }</td>
                    <td>${ line['currency_name'] }</td>
                </tr>
                %endfor  ## for line in getLines30(partner, company)
            </table>
        %endif  ## if getLines30(partner, company)
        %if getLines3060(partner, company):
            <br/>
            <div class="total">${_('30-60')}</div>
            <table class="basic_table" style="width: 100%;">
                <tr>
                    <th>${_('Date')}</th>
                    <th>${_('Description')}</th>
                    <th>${_('Reference')}</th>
                    <th>${_('Due date')}</th>
                    <th>${_('Amount')}</th>
                    <th>${_('Paid')}</th>
                    <th>${_('Total')}</th>
                    <th>${_('Currency')}</th>
                </tr>
                %for line in getLines3060(partner, company):
                <tr>
                    <td>${ formatLang(line['date_original'], date=True) }</td>
                    <td>${ line['name'] }</td>
                    <td>${ line['ref'] }</td>
                    <td>${ line['date_due'] and formatLang(line['date_due'], date=True) or '' }</td>
                    <td style="text-align: right;">${ formatLang(line['amount_original']) }</td>
                    <td style="text-align: right;">${ formatLang(line['amount_original'] - line['amount_unreconciled']) }</td>
                    <td style="text-align: right;">${ formatLang(line['amount_unreconciled']) }</td>
                    <td>${ line['currency_name'] }</td>
                </tr>
                %endfor  ## for line in getLines3060(partner, company)
            </table>
        %endif  ## if getLines3060(partner, company)
        %if getLines60(partner, company):
            <br/>
            <div class="total">${_('+60')}</div>
            <table class="basic_table" style="width: 100%;">
                <tr>
                    <th>${_('Date')}</th>
                    <th>${_('Description')}</th>
                    <th>${_('Reference')}</th>
                    <th>${_('Due date')}</th>
                    <th>${_('Amount')}</th>
                    <th>${_('Paid')}</th>
                    <th>${_('Total')}</th>
                    <th>${_('Currency')}</th>
                </tr>
                %for line in getLines60(partner, company):
                <tr>
                    <td>${ formatLang(line['date_original'], date=True) }</td>
                    <td>${ line['name'] }</td>
                    <td>${ line['ref'] }</td>
                    <td>${ line['date_due'] and formatLang(line['date_due'], date=True) or '' }</td>
                    <td style="text-align: right;">${ formatLang(line['amount_original']) }</td>
                    <td style="text-align: right;">${ formatLang(line['amount_original'] - line['amount_unreconciled']) }</td>
                    <td style="text-align: right;">${ formatLang(line['amount_unreconciled']) }</td>
                    <td>${ line['currency_name'] }</td>
                </tr>
                %endfor  ## for line in getLines60(partner, company)
            </table>
        %endif  ## if getLines60(partner)
        %endif  ## if (partner.credit + partner.debit == 0
    %endfor  ## for partner in objects
    </body>
</html>
