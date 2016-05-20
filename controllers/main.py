# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from openerp import http

from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
from openerp.tools.translate import _
import openerp
import time, datetime, calendar
import logging
import json
from mako import exceptions
from mako.lookup import TemplateLookup
import base64
import os
import werkzeug.utils

_logger = logging.getLogger(__name__)

# MAKO
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# 服务APP
SER_THEME = "defaultApp/views"
ser_path = os.path.join(BASE_DIR, "static", SER_THEME)
ser_tmp_path = os.path.join(ser_path, "tmp")
ser_lookup = TemplateLookup(directories=[ser_path], output_encoding='utf-8', module_directory=ser_tmp_path)


# 获取模版信息
def serve_template(templatename, **kwargs):
    try:
        template = ser_lookup.get_template(templatename)
        return template.render(**kwargs)
    except:
        return exceptions.html_error_template().render()


class BornDashboard(http.Controller):
    @http.route('/except_dashboard', type='http', auth="none", csrf=False)
    def Exception(self, **post):
        return serve_template('except.html')

    @http.route('/dashboard', type='http', auth="none", csrf=False)
    def manager_index(self, **post):

        uid = request.session.uid
        if not uid:
            werkzeug.exceptions.abort(werkzeug.utils.redirect('/except_dashboard', 303))

        users_obj = request.registry.get('res.users')
        user = users_obj.browse(request.cr, SUPERUSER_ID, uid)

        return serve_template('index.html', user=user)

    # 收银统计
    @http.route('/dashboard/getcashier', type='http', auth="none", csrf=False)
    def getcashier(self, **post):

        uid = request.session.uid
        if not uid:
            werkzeug.exceptions.abort(werkzeug.utils.redirect('/except_dashboard', 303))

        today = datetime.date.today()
        # 门店
        user = request.env['res.users'].sudo().browse(uid)
        user_shop_ids = [l.id for l in user.shop_ids]
        if user.shop_id:
            user_shop_ids.append(user.shop_id.id)

        if not user_shop_ids:
            data = {'errcode': 1, 'errmsg': u'没有权限查看报表'}
            return json.dumps(data)

        if len(user_shop_ids) == 1:
            user_shop_ids.append(user_shop_ids[0])
        company_id = user.company_id.id

        if post.get('display') == 'day':
            date_start = today.strftime("%Y-%m-%d 00:00:00")
            date_end = today.strftime("%Y-%m-%d 23:59:59")
        elif post.get('display') == 'week':
            current_seven_date = today + datetime.timedelta(days=-7)
            date_start = current_seven_date.strftime("%Y-%m-%d 00:00:00")
            date_end = today.strftime("%Y-%m-%d 23:59:59")
        elif post.get('display') == 'month':
            current_month = today + datetime.timedelta(days=-30)
            date_start = current_month.strftime("%Y-%m-%d 00:00:00")
            date_end = today.strftime("%Y-%m-%d 23:59:59")
        elif post.get('display') == 'none':
            date_start = post.get('start_time')
            date_end = post.get('end_time')

        sql = u""" select * from (
            select  round(sum(a.amount),2) as amount,b.name
            from account_bank_statement_line a  join account_journal b on a.journal_id=b.id
            where a.create_date>='%s' and a.create_date<='%s' and a.shop_id in %s and a.company_id=%s group by b.name)tmp
            where tmp.amount>0 order by tmp.amount desc
        """ % (date_start, date_end, tuple(user_shop_ids), company_id)
        request.cr.execute(sql)
        pay_way = request.cr.dictfetchall()
        all_amount = 0
        for pay in pay_way:
            all_amount += pay['amount']

        sql_two = u"""  select b.name_template as name,a.cnt from (
                select product_id,count( product_id) as cnt from born_product_line
                where  create_date>='%s' and create_date<='%s' and shop_id in %s and company_id=%s
                and import_qty=0 and parent_product_id is  NULL group by product_id order by count( product_id) desc limit 8
                ) a join product_product  b on a.product_id=b.id order by a.cnt desc;
        """ % (date_start, date_end, tuple(user_shop_ids), company_id)
        request.cr.execute(sql_two)
        rank = request.cr.dictfetchall()

        data = {
            'rank': rank,
            'all_amount': format(all_amount, '.2f'),
            'pay_way': pay_way,
            'errcode': 0
        }

        return json.dumps(data, sort_keys=True)

    # 营业统计
    @http.route('/dashboard/getsale', type='http', auth="none", csrf=False)
    def getsale(self, **post):

        cr, uid, context, pool = request.cr, request.session.uid, request.context, request.registry
        if not uid:
            werkzeug.exceptions.abort(werkzeug.utils.redirect('/except_dashboard', 303))

        today = datetime.date.today()

        # 门店
        user = request.env['res.users'].sudo().browse(uid)

        user_shop_ids = [l.id for l in user.shop_ids]
        if user.shop_id:
            user_shop_ids.append(user.shop_id.id)

        if not user_shop_ids:
            data = {'errcode': 1, 'errmsg': u'没有权限查看报表'}
            return json.dumps(data)

        if len(user_shop_ids) == 1:
            user_shop_ids.append(user_shop_ids[0])
        company_id = user.company_id.id

        if post.get('display') == 'day':
            date_start = today.strftime("%Y-%m-%d")
            date_end = today.strftime("%Y-%m-%d")
        elif post.get('display') == 'week':
            current_seven_date = today + datetime.timedelta(days=-7)
            date_start = current_seven_date.strftime("%Y-%m-%d")
            date_end = today.strftime("%Y-%m-%d")
        elif post.get('display') == 'month':
            current_month = today + datetime.timedelta(days=-30)
            date_start = current_month.strftime("%Y-%m-%d")
            date_end = today.strftime("%Y-%m-%d")
        elif post.get('display') == 'none':
            date_start = post.get('start_time')
            date_end = post.get('end_time')

        domain = [('shop_id', 'in', user_shop_ids), ('company_id', '=', company_id), ('account_date', '>=', date_start),
                  ('account_date', '<=', date_end)]
        dailys = request.env['born.account.daily'].sudo().search(domain)

        sale_amount = 0  # 销售额
        recharge_amount = 0  # 办卡、充值
        course_arrears_amount = 0  # 消费欠款
        recharge_arrears_amount = 0  # 充值欠款
        repayment_amount = 0  # 还款
        refund_amount = 0  # 退款
        product_consume_amount = 0  # 产品销售
        item_consume_amount = 0  # 项目消耗
        for daily in dailys:
            sale_amount += daily.sale_amount  # 销售额
            recharge_amount += daily.recharge_amount  # 办卡、充值
            course_arrears_amount += daily.course_arrears_amount  # 消费欠款
            recharge_arrears_amount += daily.recharge_arrears_amount  # 充值欠款
            repayment_amount += daily.repayment_amount  # 还款
            refund_amount += daily.refund_amount  # 退款
            product_consume_amount += daily.product_consume_amount  # 产品销售
            item_consume_amount += daily.item_consume_amount  # 项目消耗
        arrears_amount = course_arrears_amount + recharge_arrears_amount  # 欠款总和
        all_amount = arrears_amount + sale_amount + recharge_amount + repayment_amount + refund_amount  # 营业额总和
        consumed_amount = item_consume_amount + product_consume_amount  # 消耗额总和

        # 客流
        sql = u""" select count(DISTINCT member_id) from born_card_operate
          where state='done' and is_import=false and  create_date>='%s' and create_date<='%s' and shop_id in %s and company_id=%s
        """ % (date_start, date_end, tuple(user_shop_ids), company_id)
        cr.execute(sql)
        res_count = cr.fetchall()
        passenger = int(res_count[0][0])

        # 平均客单(元)
        sql = u""" SELECT sum(a.amount) from account_bank_statement_line a join born_card_operate b on a.operate_id=b.id
                    where b.state='done' and b.is_import=false and a.type!='merger'
                    and b.create_date>='%s' and b.create_date<='%s' and b.shop_id in %s and b.company_id=%s
          """ % (date_start, date_end, tuple(user_shop_ids), company_id)
        cr.execute(sql)
        res_count = cr.fetchall()
        if passenger > 0:
            total_money = int(res_count[0][0])
            avg = format(total_money / passenger, '.2f')
        else:
            avg = 0

        # 预约
        sql = u""" select count(*) from born_reservation where  state in ('approved','billed','done') and  create_date>='%s' and create_date<='%s' and shop_id in %s and company_id=%s
          """ % (date_start, date_end, tuple(user_shop_ids), company_id)
        cr.execute(sql)
        res_count = cr.fetchall()
        reservation = int(res_count[0][0])

        data = {
            'all_amount': format(all_amount, '.2f'),
            'recharge_amount': format(recharge_amount, '.2f'),
            'repayment_amount': format(repayment_amount, '.2f'),
            'refund_amount': format(refund_amount, '.2f'),
            'sale_amount': format(sale_amount, '.2f'),
            'item_consume_amount': format(item_consume_amount, '.2f'),
            'arrears_amount': format(arrears_amount, '.2f'),
            'consumed_amount': format(consumed_amount, '.2f'),
            'passenger': passenger,
            'avg': avg,
            'reservation': reservation,
            'product_consume_amount': format(product_consume_amount, '.2f'),
            'errcode': 0
        }
        return json.dumps(data, sort_keys=True)

    # 会员报表
    @http.route('/dashboard/getmember', type='http', auth="none", csrf=False)
    def getmember(self, **post):

        cr, uid, context, pool = request.cr, request.session.uid, request.context, request.registry
        if not uid:
            werkzeug.exceptions.abort(werkzeug.utils.redirect('/except_dashboard', 303))

        today = datetime.date.today()

        # 门店
        user = request.env['res.users'].sudo().browse(uid)
        user_shop_ids = [l.id for l in user.shop_ids]
        if user.shop_id:
            user_shop_ids.append(user.shop_id.id)

        if not user_shop_ids:
            data = {'errcode': 1, 'errmsg': u'没有权限查看报表'}
            return json.dumps(data)

        if len(user_shop_ids) == 1:
            user_shop_ids.append(user_shop_ids[0])
        company_id = user.company_id.id

        if post.get('display') == 'day':
            date_start = today.strftime("%Y-%m-%d")
            date_end = today.strftime("%Y-%m-%d")
        elif post.get('display') == 'week':
            current_seven_date = today + datetime.timedelta(days=-7)
            date_start = current_seven_date.strftime("%Y-%m-%d")
            date_end = today.strftime("%Y-%m-%d")
        elif post.get('display') == 'month':
            current_month = today + datetime.timedelta(days=-30)
            date_start = current_month.strftime("%Y-%m-%d")
            date_end = today.strftime("%Y-%m-%d")
        elif post.get('display') == 'none':
            start_time = post.get('start_time')
            end_time = post.get('end_time')

        # 总的会员
        sql = u"""
          select count(id) from born_member where shop_id in %s and company_id =%s
            """ % (tuple(user_shop_ids), company_id)
        cr.execute(sql)
        res_count = cr.fetchall()
        total_member_cnt = int(res_count[0][0])

        # 活跃会员
        sql = u"""
         select count(a.id) from  born_member a
            where a.id in (select tx.member_id from (
                select t.member_id,count(t.*) as ct  from
                (select member_id,count(*) as consume_count
                from born_card_operate where  shop_id in %s and company_id =%s and create_date>now() - interval '2 month' group by member_id,TO_CHAR(create_date,'YYYY-MM') order by member_id
                ) t where t.consume_count>=%s group by t.member_id
                ) tx where tx.ct>=3)
            """ % (tuple(user_shop_ids), company_id, user.company_id.active_member_threshold)
        cr.execute(sql)
        res_count = cr.fetchall()
        active_member_cnt = int(res_count[0][0])

        # 沉睡会员
        sql = u"""
            with  tmp_operate as (select member_id,extract (days from (now()-max(create_date))) as days from born_card_operate  group by member_id)
            select  count(a.id ) from born_member a join tmp_operate c on a.id=c.member_id
            where c.days>='%s'  and a.company_id=%s and a.shop_id in %s and  a.is_default_customer=false
               """ % (user.company_id.sleep_member_threshold, company_id, tuple(user_shop_ids))
        cr.execute(sql)
        res_count = cr.fetchall()
        sleep_member_cnt = int(res_count[0][0])

        # 普通会员
        normal_member_cnt = total_member_cnt - active_member_cnt - sleep_member_cnt

        # 储值余额
        sql = u"""
            select sum(amount) from born_card  where state='active'
            and  company_id=%s and  shop_id in %s and  is_default_customer=false
               """ % (company_id, tuple(user_shop_ids))
        cr.execute(sql)
        total_amount = cr.fetchone()[0] or 0.0

        # 卡内项目
        sql = u"""
            with tmp_1 as (
             select a.member_id,sum(COALESCE(a.price_unit,0)*(COALESCE(a.qty,0)-COALESCE(t1.consume_qty,0)-COALESCE(t2.exchange_qty,0))) course_amount from born_product_line a
                        left join ( select lines_id,sum(COALESCE(qty,0)) as consume_qty from born_consume_line where state='done' and lines_id>0 group by lines_id
                        ) t1 on t1.lines_id=a.id left join ( select lines_id,sum(COALESCE(exchange_qty,0)) as exchange_qty from born_exchange_line where state='done' and lines_id>0 group by lines_id
                        )t2 on t2.lines_id=a.id where  a.born_category=2 and a.limited_qty=false and a.state='done'  and a.type in ('buy','merger')
            group by a.member_id
             union all
            select a.member_id,sum(COALESCE(a.price_unit,0)*(COALESCE(a.qty,0) -COALESCE(t2.exchange_qty,0))) course_amount from born_product_line a
                        left join ( select lines_id,sum(COALESCE(exchange_qty,0)) as exchange_qty from born_exchange_line where state='done' and lines_id>0 group by lines_id
                        )t2 on t2.lines_id=a.id where  a.born_category=2 and  a.limited_qty=true and  a.limited_date>=now()   and a.state='done'  and a.type in ('buy','merger')
            group by a.member_id)
            select  sum(course_amount) course_amount from tmp_1
            join born_member b on b.id=tmp_1.member_id where  b.company_id=%s and  b.shop_id in %s and  b.is_default_customer=false
             group by member_id
               """ % (company_id, tuple(user_shop_ids))
        cr.execute(sql)
        res_count = cr.fetchall()
        if res_count:
            consume_amount = int(res_count[0][0])
        else:
            consume_amount = 0
        # 新增会员
        sql = u"""
              select count(id) from born_member where create_date>='%s' and create_date<='%s' and  shop_id in %s and company_id =%s and  state='active'
                """ % (date_start, date_end, tuple(user_shop_ids), company_id)
        cr.execute(sql)
        res_count = cr.fetchall()
        new_member_cnt = int(res_count[0][0])

        # 开通微卡数
        sql = u"""
              select count(id) from born_member where is_vip_customer=true and register_wevip_date>='%s' and register_wevip_date<='%s' and  shop_id in %s and company_id =%s and  state='active'
                """ % (date_start, date_end, tuple(user_shop_ids), company_id)
        cr.execute(sql)
        res_count = cr.fetchall()
        vip_member_cnt = int(res_count[0][0])

        # 生日会员数
        # 重新计算开始结束日期,计算生日要计算从今天开始的日期
        if post.get('display') == 'day':
            date_start = today.strftime("%Y-%m-%d")
            date_end = today.strftime("%Y-%m-%d")
        elif post.get('display') == 'week':
            current_seven_date = today + datetime.timedelta(days=+7)
            date_start = current_seven_date.strftime("%Y-%m-%d")
            date_end = today.strftime("%Y-%m-%d")
        elif post.get('display') == 'month':
            current_month = today + datetime.timedelta(days=+30)
            date_start = current_month.strftime("%Y-%m-%d")
            date_end = today.strftime("%Y-%m-%d")
        elif post.get('display') == 'none':
            start_time = post.get('start_time')
            end_time = post.get('end_time')

        # 生日
        sql = u"""
              with tmp_1 as (
                SELECT
                to_date(TO_CHAR(current_date,'YYYY') || '-' || to_char(birth_date,'mm') || '-' || to_char(birth_date,'dd'), 'YYYY-MM-DD') AS birth_date
                From born_member WHERE birth_date IS NOT NULL AND SHOP_ID in %s and company_id=%s
                )
                SELECT count(*) FROM  tmp_1 where birth_date>='%s' and birth_date<='%s'
                """ % (tuple(user_shop_ids), company_id, date_start, date_end)
        cr.execute(sql)
        res_count = cr.fetchall()
        birth_cnt = int(res_count[0][0])

        data = {
            'total_member_cnt': total_member_cnt,
            'active_member_cnt': active_member_cnt,
            'sleep_member_cnt': sleep_member_cnt,
            'normal_member_cnt': normal_member_cnt,
            'total_amount': total_amount,
            'yuanyu_amount': total_amount + consume_amount,
            'consume_amount': consume_amount,
            'new_member_cnt': new_member_cnt,
            'vip_member_cnt': vip_member_cnt,
            'birth_cnt': birth_cnt,
            'errcode': 0
        }

        return json.dumps(data, sort_keys=True)
