from typing import Type, Tuple, List, Dict, Any
import datetime as dt
from kit.exceptions import ServiceBadRequest
from sqlalchemy import Column, String, Table, Integer, DateTime, Text, Enum, Boolean, Numeric, DECIMAL, BigInteger
from sqlalchemy import func

from backend.extensions import mapper_registry
from backend.mini_core.domain.order.order import ShopOrder
from kit.repository.sqla import SQLARepository
from kit.util.sqla import id_column

__all__ = ['ShopOrderSQLARepository']

# 订单表
shop_order_table = Table(
    'shop_order',
    mapper_registry.metadata,
    id_column(),
    Column('order_no', String(64), comment='订单编号'),
    Column('order_sn', String(64), comment='订单号'),
    Column('user_id', BigInteger, comment='用户ID'),
    Column('nickname', String(64), comment='用户昵称'),
    Column('phone', String(20), comment='用户手机号'),
    Column('order_type', String(32), comment='订单类型(普通订单/套餐订单等)'),
    Column('order_source', String(32), comment='订单来源'),
    Column('status', String(32), comment='订单状态'),
    Column('refund_status', String(32), comment='退款状态'),
    Column('delivery_status', String(32), comment='配送状态'),
    Column('payment_status', String(32), comment='支付状态'),
    Column('product_name', String(32), comment='商品名称'),
    Column('product_count', Integer, comment='商品数量'),
    Column('product_amount', DECIMAL(10, 2), comment='商品金额'),
    Column('actual_amount', DECIMAL(10, 2), comment='实收金额'),
    Column('discount_amount', DECIMAL(10, 2), comment='优惠金额'),
    Column('freight_amount', DECIMAL(10, 2), comment='运费金额'),
    Column('point_amount', Integer, comment='积分抵扣'),
    Column('pay_method', String(32), comment='支付方式'),
    Column('payment_no', String(64), comment='支付单号'),
    Column('trade_no', String(64), comment='交易号'),
    Column('receiver_name', String(32), comment='收货人姓名'),
    Column('receiver_phone', String(20), comment='收货人电话'),
    Column('province', String(32), comment='省份'),
    Column('city', String(32), comment='城市'),
    Column('district', String(32), comment='区/县'),
    Column('address', String(255), comment='详细地址'),
    Column('postal_code', String(20), comment='邮编'),
    Column('id_card_no', String(32), comment='身份证号码'),
    Column('express_company', String(64), comment='快递公司名称'),
    Column('express_no', String(64), comment='快递单号'),
    Column('remark', String(255), comment='备注'),
    Column('client_remark', String(255), comment='客户备注'),
    Column('transaction_time', DateTime, comment='交易时间'),
    Column('payment_time', DateTime, comment='支付时间'),
    Column('ship_time', DateTime, comment='发货时间'),
    Column('confirm_time', DateTime, comment='确认收货时间'),
    Column('close_time', DateTime, comment='交易关闭时间'),
    Column('buyer_ip', String(64), comment='下单IP'),
    Column('delivery_platform', String(32), comment='配送平台'),
    Column('delivery_status_desc', String(64), comment='配送状态描述'),
    Column('pre_sale_time', DateTime, comment='预售日期'),
    Column('parent_order_id', BigInteger, comment='父订单ID'),
    Column('external_order_no', String(64), comment='外部订单号'),
    Column('create_time', DateTime, default=dt.datetime.now),
    Column('update_time', DateTime, default=dt.datetime.now, onupdate=dt.datetime.now),
    Column('updater', String(64), comment='更新人'),
)

# 映射
mapper_registry.map_imperatively(ShopOrder, shop_order_table)


class ShopOrderSQLARepository(SQLARepository):
    @property
    def model(self) -> Type[ShopOrder]:
        return ShopOrder
    @property
    def query_params(self):
        return ('status')
    @property
    def in_query_params(self) -> Tuple:
        return ('order_no', 'order_sn', 'user_id', 'status', 'payment_status', 'delivery_status', 'refund_status',
                'order_type', 'order_source', 'product_id', 'sku_id')

    @property
    def fuzzy_query_params(self) -> Tuple:
        return ('nickname', 'phone', 'receiver_name', 'receiver_phone', 'address', 'product_name', 'express_no')

    @property
    def range_query_params(self) -> Tuple:
        return ('create_time', 'payment_time', 'ship_time', 'transaction_time', 'confirm_time', 'close_time',
                'product_amount', 'actual_amount')

    def get_order_stats(self) -> Dict[str, Any]:
        """获取订单统计信息"""
        total = self.query().count()
        pending_payment = self.query().filter(ShopOrder.payment_status == '待支付').count()
        pending_delivery = self.query().filter(ShopOrder.delivery_status == '待发货').count()
        delivering = self.query().filter(ShopOrder.delivery_status == '已发货').count()
        completed = self.query().filter(ShopOrder.status == '已完成').count()
        cancelled = self.query().filter(ShopOrder.status == '已取消').count()

        # 今日订单数
        today_start = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = self.query().filter(ShopOrder.create_time >= today_start).count()

        # 今日销售额
        today_sales = self.session.query(func.sum(ShopOrder.actual_amount)).filter(
            ShopOrder.create_time >= today_start,
            ShopOrder.payment_status == '已支付'
        ).scalar() or 0

        # 各订单来源统计
        source_stats = self.session.query(
            ShopOrder.order_source,
            func.count(ShopOrder.id).label('count')
        ).group_by(ShopOrder.order_source).all()

        # 各订单类型统计
        type_stats = self.session.query(
            ShopOrder.order_type,
            func.count(ShopOrder.id).label('count')
        ).group_by(ShopOrder.order_type).all()

        return {
            'total': total,
            'pending_payment': pending_payment,
            'pending_delivery': pending_delivery,
            'delivering': delivering,
            'completed': completed,
            'cancelled': cancelled,
            'today_orders': today_orders,
            'today_sales': float(today_sales),
            'source_stats': [{'source': s[0], 'count': s[1]} for s in source_stats],
            'type_stats': [{'type': t[0], 'count': t[1]} for t in type_stats]
        }

    def get_user_orders(self, user_id: int) -> List[ShopOrder]:
        """获取用户的所有订单"""
        return self.find_all(user_id=user_id)

    def get_by_order_sn(self, order_sn: str) -> ShopOrder:
        """通过订单号获取订单"""
        return self.find(order_sn=order_sn)

    def get_by_order_no(self, order_no: str) -> ShopOrder:
        """通过订单编号获取订单"""
        return self.find(order_no=order_no)

    def update_order_status(self, order_no: str, status: str) -> ShopOrder:
        """更新订单状态"""
        order = self.find(order_no=order_no)
        if order:
            order.status = status
            self.session.commit()
        return order

    def update_payment_status(self, order_id: int, payment_status: str) -> ShopOrder:
        """更新支付状态"""
        order = self.get_by_id(order_id)
        if order:
            order.payment_status = payment_status
            if payment_status == '已支付':
                order.payment_time = dt.datetime.now()
            self.session.commit()
        return order

    def update_delivery_status(self, order_id: int, delivery_status: str) -> ShopOrder:
        """更新配送状态"""
        order = self.get_by_id(order_id)
        if order:
            order.delivery_status = delivery_status
            if delivery_status == '已发货':
                order.ship_time = dt.datetime.now()
            elif delivery_status == '已签收':
                order.confirm_time = dt.datetime.now()
            self.session.commit()
        return order

    def close_order(self, order_id: int) -> ShopOrder:
        """关闭订单"""
        order = self.get_by_id(order_id)
        if order:
            order.status = '已关闭'
            order.close_time = dt.datetime.now()
            self.session.commit()
        return order

    def confirm_receipt_with_points(self, order_no: str, order_update_data: Dict,
                                    user_update_data: Dict) -> Dict[str, Any]:
        """确认收货并奖励积分的数据库操作"""
        from backend.mini_core.repository import shop_user_sqla_repo
        from backend.mini_core.service import distribution_service,distribution_income_service
        try:
            # 获取订单
            order = self.find(order_no=order_no)
            if not order:
                return dict(data=None, code=404, message="订单不存在")
            dis_order_data = distribution_income_service.repo.find(order_no=order_no)
            # 更新订单状态
            order.delivery_status = order_update_data['delivery_status']
            order.status = order_update_data['status']
            order.confirm_time = order_update_data['confirm_time']
            order.updater = order_update_data['updater']

            # 更新用户积分
            user = shop_user_sqla_repo.find(user_id=order.user_id)
            user.points = user_update_data['points']
            shop_user_sqla_repo.update(user.id, user,commit=False)
            if dis_order_data:
                dis_order_data.status = 0
                dis_user_father_id = dis_order_data.user_father_id
                distribution_amount = dis_order_data.distribution_amount
                parent_user = distribution_service.get_by_user_id(user_id=dis_user_father_id)
                if parent_user:
                    user_father_frozen_amount = parent_user.frozen_amount  # 冻结金额
                    user_father_wait_amount = parent_user.wait_amount
                    user_father_frozen_amount= user_father_frozen_amount if user_father_frozen_amount else 0
                    user_father_wait_amount = user_father_wait_amount if user_father_wait_amount else 0
                    user_father_frozen_amount = float(user_father_frozen_amount)- float(distribution_amount)
                    user_father_wait_amount = float(user_father_wait_amount) + float(distribution_amount)
                    parent_user.wait_amount = user_father_wait_amount
                    parent_user.frozen_amount = user_father_frozen_amount

                    self.session.add(parent_user)
                self.session.add(dis_order_data)
            # 更新订单
            self.update(commit=False,entity_id=order.id,entity= order)

            # 提交事务
            self.session.commit()

            return dict(
                data={
                    'order': order,
                    'points_reward': user_update_data['points'] - (user.points - user_update_data['points']),
                    'new_points': user_update_data['points']
                },
                code=200,
                message="确认收货成功，积分已奖励"
            )

        except Exception as e:
            # 回滚事务
            raise ServiceBadRequest(f"确认收货失败：{str(e)}")

    def get_monthly_sales(self) -> List[Dict[str, Any]]:
        """获取按月统计的销售额"""
        query = """
        SELECT DATE_FORMAT(payment_time, '%Y-%m') as month,
               COUNT(id) as order_count,
               SUM(actual_amount) as total_sales
        FROM shop_order
        WHERE payment_status = '已支付'
        GROUP BY DATE_FORMAT(payment_time, '%Y-%m')
        ORDER BY month DESC
        LIMIT 12
        """
        result = self.session.execute(query).fetchall()
        return [{'month': r[0], 'order_count': r[1], 'total_sales': float(r[2])} for r in result]

    def order_create(self, args: dict):
        """
        创建订单及相关操作（订单详情、删除购物车项、更新商品库存）
        使用事务确保所有操作要么全部成功，要么全部回滚

        Args:
            args: 包含订单数据的字典，应包含：
                - order_data_to_save: 订单数据
                - cart_items: 购物车项列表
                - order_no: 订单编号
                - user_data : 用户数据

        Returns:
            Dict: 包含操作结果的字典
        """
        from backend.mini_core.domain.order.order_detail import OrderDetail
        from backend.mini_core.domain.order.shop_order_cart import ShopOrderCart
        from backend.mini_core.domain.shop import ShopProduct
        from sqlalchemy.exc import SQLAlchemyError
        from backend.mini_core.utils.redis_utils.order_queue import RedisOrderQueue
        from backend.mini_core.domain.t_user import ShopUser
        from backend.mini_core.service import shop_user_service

        order_data_to_save = args["order_data_to_save"]
        cart_items = args["cart_items"]
        order_no = args["order_no"]
        user_data = args["user_data"]

        # 开始事务
        try:
            # 创建订单
            order = ShopOrder(**order_data_to_save)
            self.session.add(order)
            self.session.flush()  # 确保获取到主键ID
            # 创建订单详情
            order_details = []
            for item in cart_items:
                detail_data = {
                    'order_no': order_no,
                    'order_item_id': f"{order_no}_{item['product_id']}",
                    'sku_id': str(item['product_id']),
                    'product_id': item['product_id'],
                    'product_name': item['product_name'],
                    'product_img': item['product_img'],
                    'price': item['price'],
                    'actual_price': item['price'],
                    'num': item['number'],
                    'quantity': item['number'],
                    'unit_price': item['price'],
                    'total_price': item['subtotal'],
                    'is_gift': 0,
                    'refund_status': 0
                }
                order_detail = OrderDetail(**detail_data)
                order_details.append(order_detail)
                self.session.add(order_detail)

            # 删除购物车项
            cart_ids = [item['cart_id'] for item in cart_items]
            if cart_ids:
                # 优化：批量操作
                self.session.query(ShopOrderCart).filter(
                    ShopOrderCart.id.in_(cart_ids)
                ).delete(synchronize_session='fetch')

            # 更新商品库存
            for item in cart_items:
                product_id = item['product_id']
                number = item['number']
                # 使用update语句直接更新库存，避免竞态条件
                self.session.query(ShopProduct).filter(
                    ShopProduct.id == product_id
                ).update(
                    {"stock": ShopProduct.stock - number},
                    synchronize_session='evaluate'
                )
            # 提交事务
            RedisOrderQueue.add_pending_order(order_no, order_data_to_save)

            points_used = user_data["points_used"]
            user_int_id = user_data["user_int_id"]
            remaining_points = user_data["remaining_points"]
            if points_used>0:
                user = shop_user_service.get(user_int_id)
                user.points = remaining_points
                shop_user_service.repo.update(user_int_id, user, commit=False)

            self.session.commit()
            return dict(data=order, code=200, message="订单创建成功")

        except SQLAlchemyError as e:
            # 发生异常时回滚事务
            self.session.rollback()
            print(e)
            return dict(data=None, code=500, message=f"订单创建失败: {str(e)}")

    def get_order_msg(self, user_id, args: dict):
        """
        获取订单消息数据，通过连表查询同时获取订单和订单详情数据

        Args:
            user_id (str): 用户ID，可以查询用户的所有订单
            args (dict): 包含查询参数的字典

        Returns:
            Dict: 包含订单信息和订单详情的字典
        """
        from backend.mini_core.domain.order.order_detail import OrderDetail
        from sqlalchemy import and_, or_, desc, func, outerjoin
        from dataclasses import asdict

        # 添加查询条件
        order_no = args.get('order_no')
        status = args.get('status')
        size = args.get('size', 10)
        page = args.get('page', 1)
        filter_conditions = []
        if order_no:
            filter_conditions.append(self.model.order_no == order_no)
        if user_id:
            filter_conditions.append(self.model.user_id == user_id)
        if isinstance(status,str):
            filter_conditions.append(self.model.status == status)
        elif isinstance(status,list):
            filter_conditions.append(self.model.status.in_(status))

        if not filter_conditions:
            return {"code": 400, "message": "必须提供至少一个查询条件"}
        filter_expr = and_(*filter_conditions)

        # 查询订单总数
        total_count = self.session.query(func.count(self.model.id)).filter(filter_expr).scalar()

        # 如果没有订单，直接返回空结果
        if total_count == 0:
            return {"data": [], "code": 200, "total": 0, "page": page, "size": size}

        # 计算分页参数
        offset = (page - 1) * size

        # 查询分页后的订单数据
        paginated_orders = self.session.query(self.model).filter(filter_expr).order_by(
            desc(self.model.create_time)).offset(offset).limit(size).all()

        # 获取这些订单的ID列表
        order_nos = [order.order_no for order in paginated_orders]

        # 使用连表查询获取订单和订单详情
        results = self.session.query(OrderDetail).filter(OrderDetail.order_no.in_(order_nos)).all()
        order_details={}
        for result in results:
            if not result.order_no in order_details:
                order_details[result.order_no] = [asdict(result)]
            else:
                order_details[result.order_no].append(asdict(result))
        # 组装最终结果
        result_data = []
        for order in paginated_orders:
            order_details_list = order_details.get(order.order_no, [])
            # 计算订单总数和总金
            order_data = {
                "order_info": asdict(order),
                "order_details": order_details_list,
            }
            result_data.append(order_data)
        return {
            "data": result_data,
            "code": 200,
            "total": total_count,
            "page": page,
            "size": size,
            "pages": (total_count + size - 1) // size  # 总页数
        }

    def change_to_paid(self, order_id: int) -> ShopOrder:
        """将订单从待支付变更为已支付状态"""
        order = self.get_by_id(order_id)
        return order

    def get_and_complete_delivered_orders(self, fourteen_days_ago: dt.datetime):
        """
            查询并自动完成符合条件的已发货订单

            参数:
                fourteen_days_ago: 14天前的时间
            """
        query = self.session.query(ShopOrder).filter(
            self.model.delivery_status == '已发货',
            self.model.transaction_time >= fourteen_days_ago,
            self.model.transaction_time <= dt.datetime.now(),
            self.model.payment_no.isnot(None),
            self.model.payment_no != ''
        )
        return query.all()
