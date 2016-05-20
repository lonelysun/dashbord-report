# -*- coding:utf-8 -*-
import os
import json
import logging
import simplejson
import werkzeug.utils
from mako import exceptions
from openerp.http import request
from openerp import SUPERUSER_ID
from openerp.addons.web import http
from mako.lookup import TemplateLookup
import xmlrpclib
import time
import hashlib
import openerp
import string
from openerp import SUPERUSER_ID
import random
from datetime import datetime, timedelta

# MAKO
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DEFAULT_THEME = "defaultApp/views"
path = os.path.join(BASE_DIR, "static", DEFAULT_THEME)
tmp_path = os.path.join(path, "tmp")
lookup = TemplateLookup(directories=[path], output_encoding='utf-8', module_directory=tmp_path)

_logger = logging.getLogger(__name__)


# 获取模版信息
def get_template(templatename, **kwargs):
    try:
        template = lookup.get_template(templatename)
        return template.render(**kwargs)
    except:
        return exceptions.html_error_template().render()


class DsReport(http.Controller):
    # 手机日报表
    @http.route(['/dsreport',
                 '/dsreport/<string:db>/<string:born_uuid>',
                 ], type='http', auth="none", csrf=False)
    def dsreport(self, db=None, born_uuid=None, **post):

        if not db or not born_uuid:
            return get_template('error.html')

        request.session.db = db
        # 获取请求日期
        web_http = openerp.tools.config['web_http']
        web_port = openerp.tools.config['web_port']
        server = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/2/ds_api' % (web_http, web_port))
        vals = {'born_uuid': born_uuid}
        ctx = {}
        result = server.open_weixin_notice(vals, ctx)

        _logger.info(result)
        if result.get('errcode') == 0:
            date_time = result.get('data').get('date_time')
            company_born_uuid = result.get('data').get('company_born_uuid')
            shop_born_uuid = result.get('data').get('shop_born_uuid')
            domain = [('born_uuid', '=', company_born_uuid)]
            company = request.env['res.company'].sudo().search(domain, limit=1)
            if not company:
                return get_template('error.html')
            request.session.company_id = company.id
            if shop_born_uuid:
                domain = [('born_uuid', '=', shop_born_uuid)]
                shop = request.env['born.shop'].sudo().search(domain, limit=1)
                if shop:
                    request.session.shop_id = shop.id
            if date_time:
                today = datetime.now()
                send_time = today.strftime("%Y-%m-%d")
                request.session.date_time = date_time
                url='/dsreport_data/%s' % (db)
                return get_template('day_report.html', send_time=send_time, send_ids=date_time,url=url)
        return get_template('error.html')

    # 获取营业数据
    @http.route(['/dsreport_data',
                 '/dsreport_data/<string:db>',
                 ], type='http', auth="none", csrf=False)
    def dsreport_data(self, db=None, **kw):

        if not db:
            data = {'errcode': 1, 'errmsg': u'没有权限查看报表'}
            return json.dumps(data)
        request.session.db = db
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        shop_id = request.session.shop_id
        company_id = request.session.company_id
        date_time = request.session.date_time

        if not date_time or not company_id:
            data = {'errcode': 1, 'errmsg': u'没有权限查看报表'}
            return json.dumps(data)

        # 总的会员
        if shop_id:
            sql = u""" select count(id) from born_member where state='done' and shop_id = %s and company_id =%s  and active=true
                """ % (shop_id, company_id)
        else:
            sql = u""" select count(id) from born_member where company_id =%s and  state='done' and active=true
                """ % (company_id)
        cr.execute(sql)
        res_count = cr.fetchall()
        total_member_cnt = int(res_count[0][0])

        date_time_dt = datetime.strptime(date_time, "%Y-%m-%d").date()
        last_five_date = date_time_dt + timedelta(days=-4)
        date_start = '%s 00:00:00' % (last_five_date)
        date_end = '%s 23:59:59' % (date_time)


        # 5天的日期
        five_dates = [
            '%s' % (datetime.strptime(date_time, "%Y-%m-%d").date() + timedelta(days=-4)),
            '%s' % (datetime.strptime(date_time, "%Y-%m-%d").date() + timedelta(days=-3)),
            '%s' % (datetime.strptime(date_time, "%Y-%m-%d").date() + timedelta(days=-2)),
            '%s' % (datetime.strptime(date_time, "%Y-%m-%d").date() + timedelta(days=-1)),
            date_time
        ]

        date_poll_show = [
            '%s' % (
                (datetime.strptime(date_time, "%Y-%m-%d").date() + timedelta(days=-4)).strftime("%m%d")),
            '%s' % (
                (datetime.strptime(date_time, "%Y-%m-%d").date() + timedelta(days=-3)).strftime("%m%d")),
            '%s' % (
                (datetime.strptime(date_time, "%Y-%m-%d").date() + timedelta(days=-2)).strftime("%m%d")),
            '%s' % (
                (datetime.strptime(date_time, "%Y-%m-%d").date() + timedelta(days=-1)).strftime("%m%d")),
            '%s' % (
                (datetime.strptime(date_time, "%Y-%m-%d").date() + timedelta(days=-0)).strftime("%m%d")),
        ]

        # 新增会员
        if shop_id:
            sql = u""" select to_char(create_date,'YYYY-MM-DD') as create_date,count(id) from born_member
                  where create_date>='%s' and create_date<='%s'  and  shop_id = %s and company_id =%s and  state='done'
                   group by to_char(create_date,'YYYY-MM-DD') order by to_char(create_date,'YYYY-MM-DD') ASC ;
                    """ % (date_start, date_end, shop_id, company_id)
        else:
            sql = u""" select to_char(create_date,'YYYY-MM-DD') as create_date,count(id) from born_member
                where create_date>='%s' and create_date<='%s'  and  company_id =%s and  state='done'
                group by to_char(create_date,'YYYY-MM-DD') order by to_char(create_date,'YYYY-MM-DD') ASC ;
                 """ % (date_start, date_end, company_id)
        cr.execute(sql)
        res = cr.fetchall()
        new_members = {}
        for (m, n) in res:
            new_members.setdefault(m, n)

        # 客流
        if shop_id:
            sql = u""" select to_char(create_date,'YYYY-MM-DD') as create_date,count(DISTINCT member_id) from born_card_operate
                          where state='done' and is_import=false and to_char(create_date,'YYYY-MM-DD') >='%s' and to_char(create_date,'YYYY-MM-DD') <='%s' and shop_id = %s and company_id=%s
                group by  to_char(create_date,'YYYY-MM-DD') order by to_char(create_date,'YYYY-MM-DD') ASC
            """ % (date_start, date_end, shop_id, company_id)
        else:
            sql = u""" select to_char(create_date,'YYYY-MM-DD') as create_date,count(DISTINCT member_id) from born_card_operate
                          where state='done' and is_import=false and to_char(create_date,'YYYY-MM-DD') >='%s' and to_char(create_date,'YYYY-MM-DD') <='%s' and  company_id=%s
                group by  to_char(create_date,'YYYY-MM-DD') order by to_char(create_date,'YYYY-MM-DD') ASC

            """ % (date_start, date_end, company_id)
        cr.execute(sql)
        res = cr.fetchall()
        passengers = {}
        for (m, n) in res:
            passengers.setdefault(m, n)

        # 累计客流
        if shop_id:
            sql = u"""SELECT SUM(cnt) from  (
             select count(DISTINCT member_id) as cnt from born_card_operate
              where state='done' and is_import=false and  create_date >= '%s' and shop_id = %s and company_id=%s GROUP BY to_char(create_date,'YYYY-MM-DD')
              ) t
            """ % (date_end, shop_id, company_id)
        else:
            sql = u"""SELECT SUM(cnt) from  (
              select count(DISTINCT member_id) as cnt from born_card_operate
                where state='done' and is_import=false and  company_id=%s GROUP BY to_char(create_date,'YYYY-MM-DD')
                ) t
              """ % (company_id)
        cr.execute(sql)
        res_count = cr.fetchall()
        passenger_amount = int(res_count[0][0])

        # 客单(元)
        if shop_id:
            sql = u""" SELECT to_char(b.create_date,'YYYY-MM-DD') as create_date,round(avg(a.amount),2)
                    from account_bank_statement_line a join born_card_operate b on a.operate_id=b.id
                        where b.state='done' and b.is_import=false and a.type!='merger'
                        and to_char(b.create_date,'YYYY-MM-DD')>='%s' and to_char(b.create_date,'YYYY-MM-DD')<='%s' and b.shop_id = %s and b.company_id=%s
                         group by to_char(b.create_date,'YYYY-MM-DD') order by to_char(b.create_date,'YYYY-MM-DD') ASC
              """ % (date_start, date_end, shop_id, company_id)
        else:
            sql = u""" SELECT to_char(b.create_date,'YYYY-MM-DD') as create_date,round(avg(a.amount),2)
                    from account_bank_statement_line a join born_card_operate b on a.operate_id=b.id
                      where b.state='done' and b.is_import=false and a.type!='merger'
                      and to_char(b.create_date,'YYYY-MM-DD')>='%s' and to_char(b.create_date,'YYYY-MM-DD')<='%s' and b.company_id=%s
                      group by to_char(b.create_date,'YYYY-MM-DD') order by to_char(b.create_date,'YYYY-MM-DD') ASC
            """ % (date_start, date_end, company_id)

        cr.execute(sql)
        res = cr.fetchall()
        avg_amounts = {}
        for (m, n) in res:
            avg_amounts.setdefault(m, n)

        # 平均客单(元)
        if shop_id:
            sql = u""" SELECT  round(avg(a.amount),2) from account_bank_statement_line a join born_card_operate b on a.operate_id=b.id
                           where b.state='done' and b.is_import=false and a.type!='merger'
                           and  b.shop_id = %s and b.company_id=%s and to_char(b.create_date,'YYYY-MM-DD')>='%s' and to_char(b.create_date,'YYYY-MM-DD')<='%s'
                 """ % (shop_id, company_id)
        else:
            sql = u""" SELECT  round(avg(a.amount),2) from account_bank_statement_line a join born_card_operate b on a.operate_id=b.id
                         where b.state='done' and b.is_import=false and a.type!='merger'
                         and  b.company_id=%s and to_char(b.create_date,'YYYY-MM-DD')>='%s' and to_char(b.create_date,'YYYY-MM-DD')<='%s'
               """ % (company_id,date_start, date_end,)

        cr.execute(sql)
        res_count = cr.fetchall()
        avg_amount = int(res_count[0][0])

        # 分组构造数据
        new_members_list = []
        passengers_list = []
        avg_amounts_list = []
        daily_amounts_list = []
        for five_date in five_dates:
            # 新会员
            if five_date in new_members.keys():
                new_members_list.append(new_members[five_date])
            else:
                new_members_list.append(0)
            # 客流
            if five_date in passengers.keys():
                passengers_list.append(passengers[five_date])
            else:
                passengers_list.append(0)
            # 客单
            if five_date in avg_amounts.keys():
                avg_amounts_list.append(avg_amounts[five_date])
            else:
                avg_amounts_list.append(0)

            # 营业额
            if shop_id:
                domain = [('shop_id', '=', shop_id), ('company_id', '=', company_id), ('account_date', '=', five_date)]
            else:
                domain = [('company_id', '=', company_id), ('account_date', '=', five_date)]
            daily_amounts = request.env['born.account.daily'].sudo().search(domain)

            total_daily_amount = 0
            _logger.info(daily_amounts)
            if daily_amounts:
                for x in daily_amounts:
                    total_daily_amount += x.total_in_amount
                _logger.info(total_daily_amount)
            else:
                total_daily_amount = 0
            daily_amounts_list.append(total_daily_amount)
            _logger.info(daily_amounts_list)

        data = {
            'member_list': new_members_list,  # 会员数
            'passenger_list': passengers_list,  # 客流数
            'money_list': avg_amounts_list,  # 客单
            'sale_list': daily_amounts_list,  # 营业额
            'report_1_1': new_members_list[4],  # 昨日新增会员
            'report_1_2': total_member_cnt,  # 总会员
            'report_2_1': passengers_list[4],  # 昨日客流
            'report_2_2': passenger_amount,  # 累计客流
            'report_3_1': format(daily_amounts_list[4], '.2f'),  # 昨日营业额
            'report_3_2': 0.00,
            'report_4_1': format(avg_amounts_list[4], '.2f'),  # 昨日客单价
            'report_4_2': format(avg_amount, '.2f'),  # 平均客单价
            'all_1': passengers_list[4],  # 昨日客流
            'all_2': passenger_amount,  # 累计客流
            'date_poll_show': date_poll_show
        }

        _logger.info(data)
        return json.dumps(data, sort_keys=True)
