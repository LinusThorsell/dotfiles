# coding: utf8

import plug
from . import schema
from collections import defaultdict
from decimal import Decimal
from munch import Munch as Bunch
from operator import attrgetter, itemgetter
import traceback
import math
from datetime import timedelta, datetime
import uuid
import myutil
from .schema import Cart


def set_cart(items, cart=None, member=None, trace=None):
    with plug.db.commit_block() as session:
        if not cart and member and member.cart_key:
            cart = session.query(schema.Cart).with_for_update().get(member.cart_key)

        if not cart:
            cart = schema.Cart(items=items, key=str(uuid.uuid4()), created=plug.date.now())
            session.add(cart)

        update_cart(cart, items, trace=trace)
        cart.updated = datetime.now()


        if member and member.cart_key != cart.key:
            member.cart_key = cart.key

    return cart


def update_cart(cart, items, trace=None):
    r = {}
    for item in cart.items:
        if item.get('rbservice_id'):
            r[item['reservation']] = True
        elif item.get('workout_id'):
            r[item['reservation']] = True
        elif item.get('workout_bookings'):
            for i in item['workout_bookings']:
                r[i['reservation']] = True

    cart.items = items
    for item in cart.items:
        if item.get('rbservice_id'):
            r[item['reservation']] = False
        elif item.get('workout_id'):
            r[item['reservation']] = False
        elif item.get('workout_bookings'):
            for i in item['workout_bookings']:
                r[i['reservation']] = False

    with plug.ctx:
        plug.ctx.reservation_ignore_wrong_key = True
        for key, cancel in r.items():
            if cancel:
                plug.resource.reservation.cancel(key)

    if trace:
        @plug.db.on_commit
        def sent_event():
            plug.net.send_channel2(cart.key, {'type': 'cart_changed', 'trace': trace})


def available_for_webshop(product):
    if product.customerCanBuy:
        return True

    session = plug.db.get_session()
    Course = plug.db.get_model('course')
    if session.query(Course).filter(Course.product_id == product.id).first():
        return True

    GC = plug.db.get_model('teamsportgameclass')
    if session.query(GC).filter(GC.product_id == product.id).first():
        return True
    return False

def get_punchcards(items, member):
    import db

    punchcards = set()
    for item in items:
        if item.get('type') == 'punchcard' and item.get('card_id') and member:
            card_id = item.get('card_id')
            card = db.session.query(db.TrainingCard).filter(db.TrainingCard.id == card_id, db.TrainingCard.user_id == member.id, db.TrainingCard.trainingsLeft > 0).first()
            if card:
                punchcards.add(card)
    return lmap(lambda x: Bunch(card=x, trainingsLeft=x.trainingsLeft), punchcards)

def get_total_of_cart(cart=None, member=None, fix_cart=False, items=None, method=None):
    discounts = []
    discount_id = set()
    giftcards = []
    giftcard_id = set()
    valuecard = 0
    valuecard_used_amount = 0
    method = method or 'unknown'
    punchcards = None

    total = 0
    total_for_payments = 0
    subs = defaultdict(Decimal)
    subs_right_now = dict()
    paid_invoice = None
    vats = {
        0: 0,
        6: 0,
        12: 0,
        25: 0
    }

    if cart or items:
        import db
        session = plug.db.get_session()

        if cart:
            source_items = cart.items
            items = source_items[:]
        else:
            assert not fix_cart
            source_items = items
        cart_changed = False

        punchcards = get_punchcards(source_items, member)

        for item in source_items:
            if item.get('type') == 'punchcard' and item.get('card_id') and member:
                card_id = item.get('card_id')
                card = session.query(db.TrainingCard).filter(db.TrainingCard.id == card_id, db.TrainingCard.user_id == member.id, db.TrainingCard.trainingsLeft > 0).first()
                if card and card not in lmap(lambda x: x.card, punchcards):
                    punchcards.append(Bunch(card=card, trainingsLeft=card.trainingsLeft))

        for itemindex, item in enumerate(source_items):
            if 'count' not in item:
                item['count'] = 1
            if item.get('rbservice_id'):
                prod = db.ResourceBookingService.getTrainingCardType(item.get('rbservice_id'))
                count = len(item['slots']) * (len(item.get('extra_person', [])) + 1)

                if punchcards:
                    booking_date = plug.date.to_datetime(item['slots'][0].get('start')).date()
                    for ct in punchcards:
                        if (ct.card.validToDate is None or ct.card.validToDate >= booking_date) and ct.trainingsLeft >= count:
                            ct.trainingsLeft -= count
                            count = 0
                            break

                rb_cost = prod.price * count
                vats[prod.vat] += myutil.getVatAmount(rb_cost, prod.vat)
                total += rb_cost
            elif item.get('workout_id'):
                workout = session.query(db.Workout).get(item['workout_id'])
                if not workout:  # workout was removed
                    if fix_cart:
                        items.remove(item)
                        cart_changed = True
                    continue
                vats[workout.workoutType.vat] += myutil.getVatAmount(workout.workoutType.price, workout.workoutType.vat)
                total += workout.workoutType.price
            elif item.get('product_id'):
                prod = session.query(db.TrainingCardType).get(item.get('product_id'))
                assert prod

                if prod.discount:
                    if not prod.discount_code or prod.discount_code != item['value']:
                        continue  # only staff can use it

                    if prod.validFromDate > plug.date.today():
                        continue

                    if prod.validToDate and prod.validToDate < plug.date.today():
                        continue

                    if prod.id in discount_id:
                        continue

                    if prod.stock is not None and prod.stock <= 0:
                        continue

                    if not prod.active:
                        continue

                    discount_id.add(prod.id)
                    discounts.append(prod)
                    continue

                if not available_for_webshop(prod):
                    raise plug.e.DataError('Invalid product or customer cannot buy it')

                if item.get('teamsportregistration'):
                    gameclass_id = item['teamsportregistration']['gameclass_id']
                    gameclass = plug.teamsport.TeamSportGameClass.getInternal(gameclass_id)
                    price = gameclass.price
                    vats[prod.vat] += myutil.getVatAmount(price, gameclass.product.vat)
                    total += price
                else:
                    if prod.payWhatYouWant:
                        price = myutil.makeDecimal(item['price'])
                        if price <= 0:
                            raise plug.e.DataError('Invalid price for payWhatYouWant product')
                        vats[prod.vat] += myutil.getVatAmount(price, prod.vat)
                        total += price
                    else:
                        if item['count'] <= 0:
                            raise plug.e.DataError('Invalid product count')

                        price = prod.price * item['count']
                        if not prod.priceType or prod.priceType == 'OneTime':
                            vats[prod.vat] += myutil.getVatAmount(price, prod.vat)
                            total += price
                        else:
                            if prod.period:
                                payments = plug.payment.generate_blank(cardtype_id=prod.id, method=method, from_date=prod.periodValidFrom, price=price, join=True)
                            else:
                                payments = plug.payment.generate_blank(cardtype_id=prod.id, method=method, from_date=plug.date.today(), price=price, join=True)
                            if payments:
                                vats[prod.vat] += myutil.getVatAmount(payments[0]['amount'], prod.vat)
                                total += payments[0]['amount']
                                subs_right_now[prod.id] = dict(amount=payments[0]['amount'], from_date=payments[0]['from_date'], to_date=payments[0]['to_date'])
                            if prod.auto or len(payments) > 1:
                                subs[prod.priceType] += Decimal(price)
            elif item.get('type') == 'giftcard':
                code = item['value']
                if code in giftcard_id:
                    continue
                giftcard_id.add(code)
                card = plug.giftcard.get(item['value'], validate=True, allow_barcode=True)
                if card:
                    giftcards.append(card)
            elif item.get('type') == 'valuecard':
                if not member:
                    continue
                valuecard = member.getMoney()
            elif item.get('payments'):
                invoice = get_invoice_by_payments(item['payments'])
                if invoice:
                    assert not paid_invoice, 'Only one invoice per time'
                    if invoice.type == 'directdebit':
                        raise plug.e.InvalidInputException('Impossible to pay autogiro invoice')
                    paid_invoice = invoice
                    total_for_payments += paid_invoice.getTotalAmountRounded() - paid_invoice.getPaidAmount()
                    reminderPayments = []
                    for ir in invoice.reminders:
                        reminderPayments.extend([ir.fee_payment, ir.rate_payment])
                    reminderPayments = lfilter(lambda x: x and x.status == 'pending', reminderPayments)
                    for p in reminderPayments:
                        total_for_payments += p.amount

                else:
                    for pid in item['payments']:
                        p = session.query(db.Payment).get(pid)
                        if p and p.status in ('pending', 'failed', 'sent'):
                            total_for_payments += p.amount
                        elif fix_cart:
                            cart_changed = True
                            items.remove(item)
                            break
                        else:
                            raise plug.e.DataError('Wrong payment')
            elif item.get('type') == 'punchcard':
                pass
            else:
                raise plug.e.DataError('Wrong item')

        if fix_cart and cart_changed:
            with plug.db.commit_block():
                cart.items = items

    if not plug.keyvalue.get('allow_multiple_discounts') and len(discounts) > 1:
        raise plug.e.DataError('Not possible to combine discounts')

    dd = []
    final_total = total
    result_percent = 0
    for d in discounts:
        i = {
            'prod_id': d.id,
            'amount': 0
        }
        for item in items:
            product_id = item.get('product_id')
            count = item['count']
            prod_user = item.get('user_id') or member and member.id
            prod_user = plug.user.get(prod_user) if prod_user else None

            if not product_id and item.get('rbservice_id'):
                r = rbooking(item, member=member, method=method, punchcards=punchcards)
                if r['payments']:
                    plug.discount.api.apply_discount(r['payments'], d, prod_user, deduct_discount=False)
                    for p in r['payments']:
                        if p.get('discount'):
                            final_total -= p['discount']
                            i['amount'] += p['discount']
            elif product_id and plug.discount.api.discountConditionsMet(product_id, d.id, prod_user):
                prod = session.query(db.TrainingCardType).get(product_id)
                price = myutil.makeDecimal(item['price']) if prod.payWhatYouWant else prod.price * count
                if prod.period:
                    payments = plug.payment.generate_blank(cardtype_id=prod.id, method=method, from_date=prod.periodValidFrom, price=price, join=True)
                else:
                    payments = plug.payment.generate_blank(cardtype_id=prod.id, method=method, from_date=plug.date.today(), price=price, join=True)

                plug.discount.api.apply_discount(payments, d, prod_user, deduct_discount=False)
                p = payments[0]

                if p.get('discount'):
                    final_total -= p['discount']
                    i['amount'] += p['discount']

        if i['amount']:
            dd.append(i)

    if result_percent:
        p = 1 - float(result_percent)/100
        for k, value in subs.items():
            subs[k] = int(round(float(value) * p))

    discount = sum(lmap(itemgetter('amount'), dd))
    final_total += total_for_payments

    if valuecard:
        if valuecard >= final_total:
            valuecard_used_amount = final_total
            final_total = 0
        else:
            valuecard_used_amount = valuecard
            final_total -= valuecard

    gc_details = []
    for card in giftcards:
        if card.price >= final_total:
            gc_details.append({
                'card_id': card.id,
                'amount': card.price,
                'used_amount': final_total
            })
            final_total = 0
        else:
            final_total -= card.price
            gc_details.append({
                'card_id': card.id,
                'amount': card.price,
                'used_amount': card.price
            })

    return Bunch(
        total=final_total,
        discount=discount,
        full_amount=total + total_for_payments,
        subscriptions=[{'price_type': price_type, 'price': price} for price_type, price in subs.items()],
        subscriptions_pay_now=subs_right_now,
        discount_details=dd,
        giftcard_details=gc_details,
        valuecard={'amount': valuecard, 'used_amount': valuecard_used_amount},
        method=method,
        vats=vats
    )


def check_membership(items, member, payer, date=None):
    import db
    membershipCards = db.TrainingCard.getCards(member, membership=True) + plug.chain.get_memberships(member, exclude_this=True)
    if date:
        for membershipCard in membershipCards:
            if myutil.dateToDatetime(membershipCard.validToDate) >= date:
                return True
    elif membershipCards:
        return True

    for item in items:
        if item.get('product_id'):
            prod = db.session.query(db.TrainingCardType).get(item['product_id'])
            prod_user_id = item.get('user_id', payer.id)
            if prod.membership and prod_user_id == member.id:
                return True
    return False


def checkout(cart, member, method=None, total=None, is_anonym=False, option=None, items=None):
    # option: save_card, token, phone
    assert cart or items
    import db, myutil

    if total:
        total = myutil.makeDecimal(total)

    if total < 0:
        raise plug.e.InvalidInputException('Wrong amount')

    if method:
        methodo = db.PaymentMethod.getFromCache(method)
        assert methodo, 'Wrong payment method'

        if not methodo.active or not methodo.webshop:
            raise plug.e.Exception('Payment method is not suitable for this payment')

        if method == 'stripe' and not db.CardPaymentSettings._getSettings().valid() and not plug.payment.stripe.is_test():
            raise plug.e.NoSettings('Stripe is not configured')
    else:
        if total:
            raise plug.e.InvalidInputException('Payment method should be used')
        methodo = None

    if is_anonym and total:
        if methodo.builtIn and method not in ['stripe', 'swishi', 'invoice', 'unknown']:
            raise plug.e.PaymentFailedException('Anonym can not use ' + method)

    if option.get('sendToPaidBy'):
        if method not in {'unknown', 'invoice', 'directdebit'}:
            raise plug.e.InvalidInputException('Wrong payment method for sendToPaidBy')

    session = plug.db.get_session()

    #if plug.terms.get_terms_to_accept(member):
        #raise plug.e.InvalidInputException('Need to accept terms')

    if cart:
        totals = get_total_of_cart(cart, member=member, method=method)
        items = cart.items
    elif items:
        totals = get_total_of_cart(items=items, member=member, method=method)
    else:
        raise NotImplementedError

    if totals.total != total:
            db.log('Total is ' + str(totals.total) + ' and to_pay is ' + str(total))
    if totals.total != total:
        raise plug.e.Exception('Wrong amount')
    if totals.subscriptions and methodo:
        for s in totals.subscriptions:
            if s['price']:
                if not methodo.periodic:
                    raise plug.e.Exception('Payment method can not be used for periodic payments')
                break

    if method:
        methods = {method}
    else:
        methods = set()
    discount_inuse = set()

    if not items:
        raise plug.e.Exception('Cart is empty', nomail=True)

    db.log('Checkout: ' + str({
        'cart': cart.key if cart else None,
        'member_id': member.id,
        'method': method,
        'total': total,
        'is_anonym': is_anonym,
        'option': option,
        'items': items
    }))

    content = {}
    contains_membership = {}

    for item in items:
        if item.get('type') == 'giftcard':
            if method in ['directdebit', 'unknown']:
                raise plug.e.InvalidInputException('DirectDebit/Unknown cannot be used in combination with gift cards')
            methods.add('giftcard')
            if method == 'invoice' and not db.InvoiceSettings._getSettings().autosend_webshop_invoice:
                raise plug.e.InvalidInputException('Invoice cannot be used in combination with gift cards unless autosend_webshop_invoice is turned on')
            continue
        if item.get('type') == 'valuecard':
            if method in ['directdebit', 'unknown']:
                raise plug.e.InvalidInputException('DirectDebit/Unknown cannot be used in combination with value cards')
            if method == 'invoice' and not db.InvoiceSettings._getSettings().autosend_webshop_invoice:
                raise plug.e.InvalidInputException('Invoice cannot be used in combination with value cards unless autosend_webshop_invoice is turned on')
            methods.add('valuecard')
            continue
        if not item.get('product_id'):
            continue
        prod = session.query(db.TrainingCardType).get(item['product_id'])
        assert prod

        count = 1
        if prod.discount:
            count = 1
        elif prod.valuecard:
            content['prod.valuecard'] = True
            if method not in ['stripe', 'swishi', 'payson', 'adyen-card', 'adyen-swish']:
                raise plug.e.Exception('Wrong payment method to buy value card')
        elif prod.giftcard:
            content['prod.giftcard'] = True
            count = item['count']
        else:
            count = item['count']

        if prod.trial:
            if count > 1:
                raise plug.e.Exception('Can only buy one trial card')

            elif plug.user.get(item.get('user_id', member.id)).hasBoughtTrialCard(prod.id):
                raise plug.e.Exception('Customer already has trial training card', code='double_trial_card')

        if prod.discount:
            content['discount'] = True
            if not prod.discount_code or prod.discount_code != item['value']:
                raise plug.e.Exception('Discount error')

            if prod.validFromDate > plug.date.today():
                raise plug.e.Exception('Discount error')

            if prod.validToDate and prod.validToDate < plug.date.today():
                raise plug.e.Exception('Discount error')

            if prod.id in discount_inuse:
                raise plug.e.Exception('Double discount')

            if not prod.has_stock(count):
                raise plug.e.Exception('Discount is not in stock', code='discount_not_in_stock')

            if not prod.active:
                raise plug.e.Exception('Discount error', code='inactive_discount')

            discount_inuse.add(prod.id)
        else:
            if prod.needs_to_choose_variant():
                if not item.get('variant'):
                    raise plug.e.Exception('No product variant specified')

                variant = myutil.find_where(prod.variants, dict(name=item.get('variant')))
                if not variant:
                    raise plug.e.Exception('No such product variant')

            if not prod.has_stock(count, item.get('variant')):
                raise plug.e.Exception('Not enough products in stock', code='no_in_stock')

        if prod.requireMembership and db.Module.has('Membership'):
            prod_user = plug.user.get(item.get('user_id', member.id))
            if prod.course:
                if not check_membership(items, prod_user, payer=member, date=prod.course.endTime):
                    raise plug.e.Exception('MEMBERSHIP_REQUIRED', code='membership_required')
            else:
                if not check_membership(items, prod_user, payer=member):
                    raise plug.e.Exception('MEMBERSHIP_REQUIRED', code='membership_required')

        if prod.type == 'membership':
            prod_user_id = item.get('user_id', member.id)
            if contains_membership.get(prod_user_id) or ('count' in item and item['count'] > 1):
                raise plug.e.DataError('You can buy only one membership')
            contains_membership[prod_user_id] = True

    if content.get('discount') and (content.get('prod.valuecard') or content.get('prod.giftcard')):
        raise plug.e.InvalidInputException('Impossible to use discount for giftcard/valuecard')

    if len(discount_inuse) > 1 and not plug.keyvalue.get('allow_multiple_discounts'):
        raise plug.e.InvalidInputException('Not possible to combine discounts')

    giftcards = []
    multi_method = False
    if len(methods) > 1:
        multi_method = True
    elif not method:
        assert total == 0
        if not methods:
            method = 'unknown'
        elif len(methods) == 1 and 'valuecard' in methods:
            method = 'valuecard'
        elif len(methods) == 1 and 'giftcard' in methods:
            method = 'giftcard'
        else:
            method = 'unknown'
            multi_method = True

    operation = {
        'multi_method': multi_method,
        'member_id': member.id,
        'items': items,
        'invoice': None,
        'charge_giftcard': []
    }
    operation['rbookings'] = rbookings = []
    operation['payments'] = payments = []
    operation['tcards'] = tcards = []
    operation['wbookings'] = []
    operation['discount'] = []
    paid_invoice = None
    workouts_for_bookings = set()
    reservations = set()

    if 'address_for_invoice' in option and option['address_for_invoice'].get('company_invoice'):
        operation['override_payer'] = option['address_for_invoice']

    punchcards = get_punchcards(items, member)

    with plug.db.commit_block(prevent_commit=True):
        for item in items:
            if item.get('rbservice_id'):
                if not db.Module.has('ResourceBooking'):
                    raise db.PermissionException()

                reservation = plug.resource.reservation.validate(item['reservation'])
                if not reservation.result:
                    raise plug.e.ReservationError('Reservation is expired', code='resourcebooking_is_expired', nomail=True)

                if item['reservation'] in reservations:
                    raise plug.e.ReservationError('Reservation is used for another item', code='reservation_error', nomail=True)

                if plug.block.has_resourcebooking_block(member):
                    raise plug.e.ReservationError('User is blocked from making resource bookings', code='reservation_error', nomail=True)

                reservations.add(item['reservation'])

                plug.resource.reservation.renew(item['reservation'], minutes=5)

                r = rbooking(item, member=member, method='multi' if multi_method else method, punchcards=punchcards)
                payments.extend(r['payments'])
                tcards.extend(r['tcards'])

                rbookings.append({
                    'reservation': item['reservation'],
                    'rbookings': r['rbookings'],
                    'parent_id': r['parent_id'],
                    'tmp_id': r['tmp_id']
                })

                rb_total = sum(lmap(itemgetter('amount'), r['payments']))

            elif item.get('workout_id'):
                reservation = plug.resource.reservation.validate(item['reservation'])
                if not reservation.result:
                    raise plug.e.ReservationError('Reservation is expired', code='resourcebooking_is_expired')

                if item['reservation'] in reservations:
                    raise plug.e.ReservationError('Reservation is used for another item', code='reservation_error', nomail=True)

                if plug.block.has_grouptraining_block(member):
                    raise plug.e.ReservationError('User is blocked from making workout bookings', code='reservation_error', nomail=True)

                reservations.add(item['reservation'])

                assert len(reservation.workoutbookings) == 1

                plug.resource.reservation.renew(item['reservation'], minutes=5)

                workoutbooking_id = reservation.workoutbookings[0]
                wbooking = session.query(db.WorkoutBooking).get(workoutbooking_id)
                workout = wbooking.workout
                assert wbooking and workout, 'reservation error'
                assert workout.id == item['workout_id'], 'wrong workout'
                workout.workoutType.verifyBookingConditions(member)
                user_id = item.get('user_id', member.id)

                if (user_id, workout.id) in workouts_for_bookings:
                    raise plug.e.DataError('Double workout in purchase')
                workouts_for_bookings.add((user_id,workout.id))

                if workout.status != 'Ok':
                    raise plug.e.InvalidInputException('Workout is cancelled')

                if not workout.workoutType.onetime:
                    raise plug.e.InvalidInputException('Impossible to buy one time ticket')

                wbooking.user_id = user_id
                session.flush()  # lock workout booking for this customer

                cardtype = session.query(db.TrainingCardType).filter(db.TrainingCardType.workoutBooking == True).first()
                one_year_from_now = plug.date.today()
                for _ in range(12):
                    one_year_from_now = plug.date.next_month(one_year_from_now)

                card = dict(
                    id=plug.db.VirtualId(),
                    created=plug.date.now(),
                    member_id=user_id,
                    cardtype_id=cardtype.id,
                    validFromDate=plug.date.today(),
                    price=workout.workoutType.price,
                    validToDate=one_year_from_now,
                    trainingsLeft=cardtype.trainingsessions,
                    count=1
                )

                payment = dict(
                    amount=workout.workoutType.price,
                    vat=workout.workoutType.vat,
                    status='paid',
                    date=workout.startTime.date().isoformat() if method == 'unknown' else plug.date.today(),
                    trainingcard_id=card['id'],
                    user_id=user_id,
                    payer_id=member.id,
                    method=method,
                    name=workout.workoutType.name + ' ' + workout.startTime.date().isoformat() + ' ' + workout.startTime.time().isoformat()[:5],
                    workout_id=workout.id,
                    cardtype_id=cardtype.id
                )

                tcards.append(card)
                payments.append(payment)
                operation['wbookings'].append({
                    'id': workoutbooking_id,
                    'trainingcard_id': card['id'],
                    'reservation': item['reservation']
                })

            elif item.get('product_id'):
                prod = session.query(db.TrainingCardType).get(item.get('product_id'))
                assert prod

                if item.get('group_invite'):
                    operation['group_invite'] = item.get('group_invite')
                    if not plug.usergroup.get_usergroup(key=operation['group_invite']):
                        raise plug.e.InvalidInputException('wrong group invite key')

                if prod.discount:
                    for d in operation['discount']:
                        if d['prod_id'] == prod.id:
                            break
                    else:
                        operation['discount'].append({'prod_id': prod.id})
                    continue

                if not available_for_webshop(prod):
                    raise plug.e.Exception('Invalid product or customer cannot buy it')

                if prod.payWhatYouWant:
                    price = myutil.makeDecimal(item['price'])
                    if price <= 0:
                        raise plug.e.Exception('Invalid price for payWhatYouWant product')
                    count = 1
                else:
                    count = item['count']
                    if count <= 0:
                        raise plug.e.Exception('Invalid product count')

                    price = prod.price * count

                if item.get('teamsportregistration'):
                    item['teamsportregistration_id'] = plug.db.VirtualId()
                    gameclass_id = item['teamsportregistration']['gameclass_id']
                    gameclass = plug.teamsport.TeamSportGameClass.getInternal(gameclass_id)
                    price = gameclass.price
                    plug.teamsport.validate_registration_data(item['teamsportregistration'], member)

                prod_user = member
                if item.get('user_id'):
                    prod_user = plug.user.get(item['user_id'])

                if not prod.priceType or prod.priceType == 'OneTime':
                    if prod.valuecard:
                        assert not operation.get('refill_valuecard')
                        operation['refill_valuecard'] = price
                        tcard = None
                    else:
                        valid_from_date = plug.date.today()
                        if prod.validType:
                            valid_to_date = myutil.addDateFromType(valid_from_date, prod.validTime, prod.validType)
                        else:
                            valid_to_date = None

                        if prod.membership:
                            memberships = db.TrainingCard.getCards(prod_user, membership=True)
                            day = timedelta(days=1)

                            if memberships:
                                covered = max(memberships, key=lambda x: x.validToDate).validToDate
                            else:
                                covered = plug.date.today() - day

                            if prod.validFromDate:
                                valid_from_date = prod.validFromDate.replace(year=plug.date.today().year - 1)
                                while True:
                                    valid_to_date = myutil.addDateFromType(valid_from_date, prod.validTime, prod.validType)
                                    if valid_to_date < plug.date.today():
                                        valid_from_date = valid_from_date.replace(year=valid_from_date.year+1)
                                        continue
                                    if valid_to_date <= covered:
                                        valid_from_date = valid_from_date.replace(year=valid_from_date.year+1)
                                        continue
                                    break
                            else:
                                valid_from_date = max([covered + day, plug.date.today()])
                                valid_to_date = myutil.addDateFromType(valid_from_date, prod.validTime, prod.validType)

                        if prod.type == 'trainingcard':
                            valid_from_date, valid_to_date = prod.get_valid_from_valid_to(prod_user, lfilter(lambda c: c['member_id'] == prod_user.id, tcards))

                        if prod.course:
                            user_id = item.get('user_id', member.id)
                            reservation = None

                            if item.get('reservation'):
                                reservation = plug.resource.reservation.validate(item['reservation'])
                                if not reservation.result:
                                    raise plug.e.ReservationError('Reservation is expired', code='resourcebooking_is_expired', nomail=True)

                                if item['reservation'] in reservations:
                                    raise plug.e.ReservationError('Reservation is used for another item', code='reservation_error', nomail=True)

                                assert len(reservation.courses) == 1 and reservation.courses[0] == prod.course.id

                                reservations.add(item['reservation'])

                                plug.resource.reservation.renew(item['reservation'], minutes=5)

                            assert plug.course.able_to_book(prod.course.id, booker_id=member.id, user_id=user_id, reservation=reservation is not None)

                            for w in prod.course.workouts:
                                if (w.id,user_id) in workouts_for_bookings:
                                    raise plug.e.DataError('Double workout in purchase')
                                workouts_for_bookings.add((w.id,user_id))

                        trainings_left = prod.trainingsessions
                        if trainings_left:
                            trainings_left *= count
                        tcard = dict(
                            id=plug.db.VirtualId(),
                            created=plug.date.now(),
                            cardtype_id=prod.id,
                            boundToDate=None,
                            validFromDate=valid_from_date,
                            validToDate=valid_to_date,
                            trainingsLeft=trainings_left,
                            price=price,
                            generatedUntil=None,
                            count=count,
                            rbooking_id=item.get('rbooking_id'),
                            variant=item.get('variant')
                        )

                        if not prod.giftcard:
                            tcard['member_id'] = item.get('user_id', member.id)

                        tcards.append(tcard)

                    payment_from = tcard and tcard['validFromDate'] or plug.date.today()
                    for p in plug.payment.generate_blank(cardtype_id=prod.id, method=method, from_date=payment_from, price=price):
                        # one payment expected (price OneTime)
                        if tcard:
                            p['trainingcard_id'] = tcard['id']
                        if p['date'] < plug.date.today() or prod.membership:
                            p['date'] = plug.date.today()
                        p['user_id'] = item.get('user_id', member.id)
                        p['payer_id'] = member.id
                        p['status'] = 'paid'

                        if prod.course:
                            p['course_id'] = prod.course.id
                        else:
                            p['course_id'] = item.get('course_id')

                        if item.get('teamsportregistration'):
                            p['gameclass_id'] = item['teamsportregistration'].get('gameclass_id')
                            p['teamsportregistration_id'] = item['teamsportregistration_id']
                            gc = plug.teamsport.TeamSportGameClass.getInternal(p['gameclass_id'])
                            p['name'] = db.translate('Registration fee') + ' - ' + gc.competition.name + ' - ' + gc.name
                        if prod.separate_invoice:
                            p['separate_invoice'] = True
                        p['variant'] = item.get('variant')
                        p['vat'] = prod.vat
                        payments.append(p)
                else:
                    assert not prod.payWhatYouWant
                    assert not prod.valuecard
                    valid_from_date = plug.date.today()
                    if prod.validType:
                        valid_from_date, valid_to_date = prod.get_valid_from_valid_to(prod_user, lfilter(lambda c: c['member_id'] == prod_user.id, tcards))

                    elif prod.period:
                        valid_from_date = prod.periodValidFrom
                        valid_to_date = prod.periodValidTo
                    else:
                        valid_from_date, valid_to_date = prod.get_valid_from_valid_to(prod_user, lfilter(lambda c: c['member_id'] == prod_user.id, tcards))

                    price_for_tc = price

                    if prod.period:
                        plist = plug.payment.generate_blank(cardtype_id=prod.id, method=method, from_date=prod.periodValidFrom, price=price_for_tc, join=True)
                    else:
                        plist = plug.payment.generate_blank(cardtype_id=prod.id, method=method, from_date=plug.date.today(), price=price_for_tc, join=True)

                    to_date = plist[-1]['to_date']
                    generated_until = plug.date.prev_month(to_date, 31)
                    if not plug.date.is_last_day(to_date):
                        generated_until = plug.date.prev_month(generated_until, 31)
                    first_payment = plist[0]
                    first_payment['status'] = 'paid'

                    tcard = dict(
                        id=plug.db.VirtualId(),
                        created=plug.date.now(),
                        cardtype_id=prod.id,
                        boundToDate=myutil.addDateFromType(valid_from_date, prod.boundTime, prod.boundType),
                        validFromDate=valid_from_date,
                        validToDate=valid_to_date,
                        trainingsLeft=prod.trainingsessions,
                        member_id=prod_user.id,
                        price=price_for_tc,
                        generatedUntil=generated_until,
                        count=count,
                        variant=item.get('variant')
                    )
                    tcards.append(tcard)

                    for p in plist:
                        p['trainingcard_id'] = tcard['id']
                        p['user_id'] = prod_user.id
                        p['payer_id'] = member.id
                        if 'status' not in p:
                            p['status'] = 'pending'
                        if prod.separate_invoice:
                            p['separate_invoice'] = True
                        p['variant'] = item.get('variant')
                        p['vat'] = prod.vat
                        payments.append(p)

                for wb in item.get('workout_bookings') or []:
                    reservation = plug.resource.reservation.validate(wb['reservation'])
                    if not reservation.result:
                        raise plug.e.ReservationError('Reservation is expired', code='resourcebooking_is_expired', nomail=True)

                    assert len(reservation.workoutbookings) == 1

                    plug.resource.reservation.renew(wb['reservation'], minutes=5)

                    workoutbooking_id = reservation.workoutbookings[0]
                    wbooking = session.query(db.WorkoutBooking).get(workoutbooking_id)
                    workout = wbooking.workout
                    assert wbooking and workout, 'reservation error'
                    assert workout.id == wb['workout_id'], 'wrong workout'
                    workout.workoutType.verifyBookingConditions(member)

                    if workout.status != 'Ok':
                        raise plug.e.InvalidInputException('Workout is cancelled')

                    wbooking.user_id = prod_user.id
                    session.flush()  # lock workout booking for this customer

                    operation['wbookings'].append({
                        'id': workoutbooking_id,
                        'trainingcard_id': tcard['id'],
                        'reservation': wb['reservation']
                    })

            elif item.get('type') == 'giftcard':
                card = plug.giftcard.get(item['value'], validate=True, allow_barcode=True)
                if card:
                    giftcards.append(card)
            elif item.get('type') == 'valuecard':
                pass
            elif item.get('payments'):
                invoice = get_invoice_by_payments(item['payments'], error_pending_invoice=True)
                if invoice:
                    assert not paid_invoice, 'Only one invoice per time'
                    if invoice.type == 'directdebit':
                        raise plug.e.InvalidInputException('Impossible to pay autogiro invoice')
                    paid_invoice = invoice
                    operation['invoice'] = invoice.id
                else:
                    # payments without invoice
                    for pid in item['payments']:
                        p = session.query(db.Payment).get(pid)
                        assert p and p.status in ('pending', 'failed', 'sent')
                        assert p.method != 'directdebit', 'Impossible to pay directdebit'

                        payments.append({
                            'id': p.id,
                            'status': 'paid',
                            'amount': p.amount
                        })
            elif item.get('type') == 'punchcard':
                pass
            else:
                raise plug.e.Exception('Wrong item')

        apply_discounts(payments, totals, member)

        to_pay = 0
        site_id = member.getCurrentSite().id
        for p in payments:
            if p['status'] == 'paid':
                to_pay += p['amount']
            if 'site_id' not in p:
                p['site_id'] = site_id

        if option.get('sendToPaidBy'):
            for p in payments:
                p['payer_id'] = member.getPayerId()

        if paid_invoice:
            left_to_pay = paid_invoice.getTotalAmountRounded() - paid_invoice.getPaidAmount()
            reminderPayments = []
            for ir in invoice.reminders:
                reminderPayments.extend([ir.fee_payment, ir.rate_payment])
            reminderPayments = lfilter(lambda x: x and x.status == 'pending', reminderPayments)
            for p in reminderPayments:
                left_to_pay += p.amount
            to_pay += left_to_pay
            operation['invoice_amount'] = left_to_pay

        discount = 0
        payments_to_pay = lfilter(lambda p: p['status'] == 'paid', payments)
        for p in payments_to_pay:
            discount += sum(lmap(lambda d: d['amount'], p.get('discounts', [])))
        to_pay -= discount

        operation['full_amount'] = to_pay  # total amount for the purchase for all methods after discount

        bundle = db.PaymentBundle()
        session.add(bundle)
        session.flush()
        operation['bundle_id'] = bundle.id

        operation['actual_payments'] = actual_payments = []
        if 'valuecard' in methods:
            amount = option['use_valuecard']
            member.chargeValueCard(amount, nocommit=True)
            to_pay -= myutil.makeDecimal(amount)
            actual_payments.append({
                'amount': amount,
                'method': 'valuecard'
            })

        use_giftcards = {}
        for gc in option.get('use_giftcards') or []:
            use_giftcards[gc['card_id']] = gc['used_amount']

        if giftcards:
            for card in giftcards:
                amount = use_giftcards.get(card.id)
                if amount:
                    if amount > to_pay:
                        raise plug.e.Exception('Giftcard error')
                    if amount > card.price:
                        raise plug.e.Exception('Not enough money on giftcard')

                    operation['charge_giftcard'].append({'id': card.id, 'amount': amount})
                    to_pay -= myutil.makeDecimal(amount)
                    actual_payments.append({
                        'trainingcard_id': card.id,
                        'amount': amount,
                        'method': 'giftcard'
                    })

        if total != to_pay:
            db.log('Total is ' + str(total) + ' and to_pay is ' + str(to_pay))
        assert total == to_pay, 'Wrong amount'

        operation['cart_key'] = cart.key if cart else None
        operation['channel2'] = channel2 = str(uuid.uuid4())
        if total > 0:
            if not methodo.builtIn:
                paid = False
                status = 'done'
            else:
                if method == 'directdebit' and option.get('sendToPaidBy'):
                    payer = member.getPayer()
                else:
                    payer = member

                transfer = plug.payment.transfer(
                    method=method,
                    amount=total,
                    payer=payer,
                    option=option,
                    bundle=bundle,
                    channel2=channel2,
                    extra_info={'operation': operation},
                    callback_for_pending='plug.webshop.core.complete_checkout_deferred'
                )
                paid = transfer.get('paid', False)
                status = transfer.status
        elif total == 0:
            paid = True
            status = 'done'
        else:
            raise NotImplementedError

        if status == 'done':
            try:
                complete_checkout(
                    cart=cart,
                    method=method,
                    total=total,
                    bundle=bundle,
                    paid=paid,
                    operation=operation
                )
            except Exception:
                if paid and method == 'stripe' and total:
                    plug.rpc.task(None, 'plug.webshop.core.complete_as_valuecard',
                        user_id=member.id,
                        payer_id=payer.id,
                        amount=total,
                        pending_id=transfer.pending_id
                    )
                    raise plug.e.DataError('Error: money will be move to valuecard', code='error_and_valuecard')
                raise

            return {
                'status': 'done',
                'paid': paid,
                'orderconfirmation': get_order_confirmation(operation['items'], operation.get('bundle_id'))
            }
        elif status == 'failed':
            raise plug.e.PaymentFailedException
        elif status == 'pending':
            if method == 'stripe' and cart:
                cart.in_process = plug.date.now()
            return {
                'status': 'pending',
                'channel2': channel2,
                'redirect': transfer.get('redirect'),
                'client_secret': transfer.get('client_secret'),
                'transaction_id': transfer.get('transaction_id'),
                'token': transfer.get('token')
            }

        raise NotImplementedError

def apply_discounts(payments, totals, member):
    import db
    discount_details = totals.discount_details
    if not totals.discount_details:
        return
    if not totals.discount:
        return

    for p in payments:
        for dd in discount_details:
            prod_user = plug.user.get(p.get('user_id', member.id))
            if plug.discount.api.discountConditionsMet(p['cardtype_id'], dd['prod_id'], prod_user):
                discount = db.session.query(db.TrainingCardType).get(dd['prod_id'])
                prod = db.session.query(db.TrainingCardType).get(p['cardtype_id'])
                from_date = prod.validFromDate if prod.period else plug.date.today()
                plug.discount.api.apply_discount([p], discount, prod_user, deduct_discount=False, from_date=from_date)

def get_workout_id(x):
    if 'workout_bookings' in x:
        wbs = x.get('workout_bookings')
        if len(wbs) == 1:
            x = wbs[0]
    return x.get('workout_id')


def get_order_confirmation(items, bundle_id=None):
    return lmap(lambda x: dict(title=item_to_text(x), workout_id=get_workout_id(x), bundle_id=bundle_id), items)


def complete_checkout(cart, method, bundle, paid=False, total=None, operation=None):
    import db
    db.log('Webshop.complete: ' + str({'operation': operation, 'total': total, 'method': method, 'paid': paid}))

    session = plug.db.get_session()
    multi_method = operation['multi_method']
    payments = operation['payments']
    tcards = operation['tcards']
    member_id = operation['member_id']
    rbookings = operation['rbookings']
    actual_payments = operation['actual_payments']
    transaction = None
    notify_payments = []

    if operation['full_amount'] and paid:
        member = session.query(db.User).get(member_id)
        if multi_method:
            transaction_method = 'multi'
        else:
            transaction_method = method

        # invoice
        if operation.get('invoice'):
            paid_invoice = session.query(db.Invoice).get(operation['invoice'])
            transaction, _ = plug.transaction.addInvoicePayment(payer=member, date=plug.date.now(), invoice=paid_invoice, method=transaction_method, amount=operation['full_amount'], bgcfile=None, invoice_reference=None, bundle=bundle, try_to_pay_reminders=True, commit=False)
            notify_payments += paid_invoice.bundle.getPayments()
        else:
            transaction = plug.transaction.addManual(
                payer=member,
                date=plug.date.now(),
                amount=operation['full_amount'],
                method=transaction_method,
                bundle=bundle,
                commit=False
            )

    if paid and total:
        actual_payments.append({
            'method': method,
            'amount': total
        })

    if operation.get('charge_giftcard'):
        for d in operation['charge_giftcard']:
            assert d['id']
            card = session.query(db.TrainingCard).with_for_update().get(d['id'])
            assert card.type == 'giftcard'
            assert card.price >= d['amount'], 'Not enough money on giftcard'
            card.price -= d['amount']

            plug.eventlog.add(['updated', 'used'], obj=card, obj_link=plug.json.Link('giftcard', card.id) , description='Gift card was used', links=[member, bundle])

    if operation['discount']:
        for d in operation['discount']:
            prod = session.query(db.TrainingCardType).get(d['prod_id'])
            prod.change_stock(1)

    tcard_to_rbooking = defaultdict(list)
    if tcards:
        all_tcards = []
        for t in tcards:
            prod = session.query(db.TrainingCardType).get(t['cardtype_id'])
            prod.change_stock(t['count'], t.get('variant'))
            code = None
            if prod.giftcard:
                code = plug.giftcard.allocate_new_code(plug.db.get_hostname())
            if prod.blockFee:
                m = session.query(db.User).get(member_id)
                if t['member_id'] != member_id:
                    user = plug.user.get(t['member_id'])
                    if m.canManageUser(user):
                        m = user
                    else:
                        raise db.PermissionException()
                db.Warning.removeBlock(m)

            validFromDate = prod.periodValidFrom if prod.period else t.get('validFromDate')
            validToDate = prod.periodValidTo if prod.period else t.get('validToDate')

            tcard_payment = myutil.find_where(payments, dict(trainingcard_id=t['id']))
            if tcard_payment and tcard_payment.get('discounts'):
                d = session.query(db.TrainingCardType).get(tcard_payment.get('discounts')[0]['id'])
                from_date = prod.validFromDate if prod.period else plug.date.today()
                d, discount_fixed, discount_percent, discount_to_date = plug.discount.api.calculate_discount_values_for_trainingcard(from_date, d)
                
                t['discount_id'] = d.id if d else None
                t['discount_percent'] = discount_percent
                t['discount_fixed'] = discount_fixed
                t['discount_to_date'] = discount_to_date


            tcard = db.TrainingCard(
                created=t['created'],
                cardtype_id=t['cardtype_id'],
                boundToDate=t.get('boundToDate'),
                validFromDate=validFromDate,
                validToDate=validToDate,
                trainingsLeft=t.get('trainingsLeft'),
                user_id=t.get('member_id'),
                price=t['price'],
                generatedUntil=t.get('generatedUntil'),
                count=t['count'],
                code=code,
                type=prod.type,
                payMethod=method,
                product_variant=t.get('variant'),
                site_id=t.get('site_id', db.Site.main().id),
                created_at='webshop',
                discount_id=t.get('discount_id'),
                discount_to_date=t.get('discount_to_date'),
                discount_percent=t.get('discount_percent', 0),
                discount_fixed=t.get('discount_fixed', 0)
            )
            session.add(tcard)
            session.flush()
            t['id'].assign(tcard.id)
            all_tcards.append(tcard)


            if tcard.cardtype.type == 'giftcard':
                description='Gift card was created'
                obj_link = plug.json.Link('giftcard', tcard.id)
            elif tcard.cardtype.type == 'valuecard':
                description='Value card was created'
                obj_link = plug.json.Link('valuecard', tcard.id)
            else:
                description = 'Training card was created'
                obj_link = None

            plug.eventlog.add('created', obj=tcard, obj_link=obj_link, description=description)

            if t.get('rbooking_id'):
                tcard_to_rbooking[t['rbooking_id']].append(tcard)

            if tcard.user:
                db.EntryChange.add(tcard.user, cardId=tcard.id,  operation='add', nocommit=True)
        

        @plug.db.on_commit
        def send_event():
            db.sendToChangeQueue('trainingcard', all_tcards, 'add')
            
    course_payments = {}
    teamsport_payments = defaultdict(list)
    invoice_payments = []
    for p in payments:
        status = p['status']
        if not paid:
            status = 'pending'

        if not p['amount']:
            status = 'paid'

        if multi_method and status == 'paid':
            payment_method = 'multi'
        else:
            payment_method = method

        if method == 'invoice':
            confirmed = db.InvoiceSettings._getSettings().autosend_webshop_invoice
        else:
            confirmed = False

        if p.get('id') and not isinstance(p['id'], plug.db.VirtualId):
            payment = session.query(db.Payment).get(p['id'])
            payment.status = status
            payment.method = payment_method
            plug.eventlog.add('updated', obj=payment, description='Payment was paid', extra={'paymentbundle_id': bundle.id})
            prod = session.query(db.TrainingCardType).get(payment.cardtype_id) if payment.cardtype_id else None
            notify_payments.append(payment)
        else:
            days = None
            if method == 'invoice':
                days = p.get('days', db.InvoiceSettings._getSettings().days)

            prod = session.query(db.TrainingCardType).get(p['cardtype_id'])
            if db.AccountingSettings._getSettings().vatexempt:
                vat = 0
            else:
                vat = p.get('vat')
                if not vat:
                    vat = prod.vat
            name = p.get('name')
            if not name:
                name = prod.name

            discounts = p.get('discounts', [])
            discount = sum(lmap(itemgetter('amount'), discounts))

            payment = db.Payment(
                created=plug.date.now(),
                status=status,
                amount=p['amount'] - discount,
                #currency=currency,
                vat=vat,
                date=p['date'],
                user_id=p.get('user_id') or member_id,
                #staff_id=staff_id,
                method=payment_method,
                payer_id=p.get('payer_id') or member_id,
                name=name,
                days=days,
                cardtype_id=p['cardtype_id'],
                workout_id=p.get('workout_id'),
                from_date=p.get('from_date'),
                to_date=p.get('to_date'),
                confirmed=confirmed,
                product_variant=p.get('variant'),
                site_id=p.get('site_id', db.Site.main().id),
                created_at='webshop',
                shownPriceOnReceipt=p.get('shownPriceOnReceipt'),
                hidePriceOnReceipt=p.get('hidePriceOnReceipt'),
                discount=discount,
                discounts=discounts
            )

            if 'trainingcard_id' in p:
                p['trainingcard_id'].link(payment, 'trainingcard_id')

            if 'parent_id' in p:
                p['parent_id'].link(payment, 'parent_id')

            if operation.get('override_payer'):
                o = operation['override_payer']
                payment.override_payer = dict(mail=o['mail'], firstname=None, lastname=o['name'], personalCodeNumber=None, address=o['address'], zipCode=o['zipCode'], city=o['city'])

            if p.get('separate_invoice'):
                payment.separate_invoice = True

            payment.discountstext = payment.get_discountstext()

            session.add(payment)
            session.flush()

            if method == 'invoice' and payment.confirmed and actual_payments:
                invoice_payments.append(payment)

            if p.get('id'):
                p['id'].assign(payment.id)

            plug.eventlog.add('created', obj=payment, description='Payment was created', extra={'paymentbundle_id': bundle.id})

        if payment.status == 'paid':
            payment.storeData()
            attempt = db.PaymentAttempt(
                created=plug.date.now(),
                payment_id=payment.id,
                status='paid',
                time=plug.date.now(),
                method=payment_method,
                bundle=bundle,
                invoice=bundle.invoice if bundle else None
            )
            session.add(attempt)
            if prod and prod.membership:
                plug.chain.update_chain_membership_paid(membership=payment.trainingcard)
            plug.db.on_commit(lambda: plug.block.update_automatic_debt_blocks_for_user(payment.payer))
        course_id = p.get('course_id')
        if course_id:
            if not course_payments.get( (payment.user_id, course_id) ):
                course_payments[(payment.user_id, course_id)] = []
            course_payments[(payment.user_id, course_id)].append(payment)
        if p.get('teamsportregistration_id'):
            teamsport_payments[p['teamsportregistration_id']].append(payment)
        notify_payments.append(payment._getData())

    db.sendToChangeQueue('payment', notify_payments, 'add', nocommit=True)

    if invoice_payments:
        from_valuecard = 0
        from_giftcard = 0
        for a in actual_payments:
            if a.get('method', 'valuecard') == 'valuecard':
                from_valuecard += a['amount']
            elif a.get('method', 'valuecard') == 'giftcard':
                from_giftcard += a['amount']

        @plug.db.on_commit
        def pay_invoice():
            with plug.lock.invoice_number():
                invoices = db.Invoice.generateInvoicesInternal(invoice_payments)
                invoice = invoices[0]
                if from_valuecard:
                    t, _ = plug.transaction.addInvoicePayment(payer=invoice.payer, date=plug.date.today(), invoice=invoice, method='valuecard', amount=from_valuecard, bgcfile=None, invoice_reference=None, commit=True)
                if from_giftcard:
                    t, _ = plug.transaction.addInvoicePayment(payer=invoice.payer, date=plug.date.today(), invoice=invoice, method='giftcard', amount=from_giftcard, bgcfile=None, invoice_reference=None, commit=True)
    else:
        for a in actual_payments:
            session.add(db.ActualPayment(
                created=plug.date.now(),
                bundle_id=bundle.id,
                method=a.get('method', 'valuecard'),
                amount=a['amount'],
                trainingcard_id=a.get('trainingcard_id'),
                transaction=transaction
            ))

    ready_rbookings = {}
    if rbookings:
        all_rbookings = []
        for b in rbookings:
            parent = db.MultiBooking()
            session.add(parent)
            session.flush()
            b['parent_id'].assign(parent.id)

            resourcebooking = None
            for rb in b['rbookings']:
                rb_id = rb.pop('id')
                rb['parent_id'] = rb['parent_id'].get()
                rb['trainingcard_id'] = rb['trainingcard_id'].get() if isinstance(rb['trainingcard_id'], plug.db.VirtualId) else rb['trainingcard_id']

                if b.get('tmp_id') and tcard_to_rbooking[b['tmp_id']]:
                    rb['products'] = tcard_to_rbooking[b['tmp_id']]
                    tcard_to_rbooking[b['tmp_id']] = None

                if rb.get('included_products'):
                    rb['included_products'] = lmap(lambda p: p.get(), rb['included_products'])
                    rb['products'] += lmap(lambda tcard_id: myutil.find_where(all_tcards, dict(id=tcard_id)), rb['included_products'])

                if rb.get('member_id'):
                    rb['user_id'] = rb.get('member_id')
                    rb.pop('member_id')

                punchcard_count = rb.pop('punchcard_count', 0)

                resourcebooking = db.ResourceBooking(**rb)
                session.add(resourcebooking)
                session.flush()

                if resourcebooking.punchcard:
                    resourcebooking.trainingcard.use(count=punchcard_count, nocommit=True, performer=resourcebooking.user)
                    session.flush()

                if not resourcebooking.service.continuousBooking:
                    now = plug.date.now()
                    if resourcebooking.time < now:
                        checkins = session.query(db.ContinuousResourceBooking).filter(
                            db.ContinuousResourceBooking.staff_id.in_([resourcebooking.staff_id, resourcebooking.xstaff_id]),
                            db.ContinuousResourceBooking.endTime == None
                        ).all()
                        if len(checkins):
                            db.ResourceBookingService.cancelCheckinItems(checkins, end=now, nocommit=True)
                            end = resourcebooking.time + timedelta(minutes=resourcebooking.duration)
                            resourcebooking.time = now
                            resourcebooking.duration = (end - resourcebooking.time).total_seconds // 60
                            session.flush()

                ready_rbookings[resourcebooking.parent_id] = resourcebooking
                all_rbookings.append(resourcebooking)
                rb_id.assign(resourcebooking.id)

                plug.eventlog.add('created', obj=resourcebooking, description='Resource booking was created')

            session.expire(parent)
            plug.resource.reservation.move(b['reservation'], resourcebooking)

        @plug.db.on_commit
        def send_event():
            db.sendToChangeQueue('resourcebooking', all_rbookings, 'add')
            db.Rco.writeBookingsFile()


    wbookings = operation['wbookings']
    for w in wbookings:
        plug.resource.reservation.move(w['reservation'])
        wbooking = session.query(db.WorkoutBooking).get(w['id'])

        if wbooking.workout.status != 'Ok':
            db.log('Warning: workout is cancelled')

        wbooking.reserved = False
        wbooking.trainingcard_id = w['trainingcard_id'].get()

        present = False
        if db.Module.has('Entry'):
            twoHoursBefore = wbooking.workout.startTime - timedelta(hours=2)
            twoHoursAfter = wbooking.workout.startTime + timedelta(hours=2)
            entry = session.query(db.Entry).filter(db.Entry.user_id == wbooking.user_id, db.Entry.date >= twoHoursBefore, db.Entry.date <= twoHoursAfter).first()
            if entry:
                present = True
        wbooking.present = present

        plug.eventlog.add('created', obj=wbooking, description='Workout booking was created')

        tcard = session.query(db.TrainingCard).get(wbooking.trainingcard_id)
        tcard.use(nocommit=True)

        db.sendToChangeQueue('workoutbooking', wbooking._getData(), 'change', nocommit=True)

        if db.Module.has('LoyaltyPoints'):
            # check if loyaltypoints should be given
            plug.loyaltypoints.check_loyaltypoint_terms(wbooking.user_id, booking=wbooking)

    items = operation['items']
    for i in items:
        product_id = i.get('product_id')
        if product_id:
            product = db.session.query(db.TrainingCardType).get(product_id)
            if product and product.type == 'course' and product.course:
                course = product.course
                user_id = i.get('user_id', member_id)
                tmp_id = i.get('tmp_id')
                additional_products = lmap(lambda p: dict(id=p['product_id'], count=p['count'], price=p['price'], variant=p.get('variant')), lfilter(lambda x: x != i and x.get('course_id') == course.id and (not tmp_id or tmp_id == x.get('tmp_id')), items))
                plug.course.webshop_add_booking(course, i.get('answers'), course_payments.get( (user_id, course.id), []), additional_products, user_id=user_id, booker_id=member_id, reservation=i.get('reservation'), bundle=bundle, variants_for_included_products=i.get('variants_for_included_products'))

    for i in items:
        if i.get('teamsportregistration'):
            plug.teamsport.add_registration(i.get('teamsportregistration'), teamsport_payments[i['teamsportregistration_id']], performer=session.query(db.User).get(member_id))

    amount = operation.get('refill_valuecard')
    if amount:
        member = session.query(db.User).get(member_id)
        member.refillValueCard(amount, nocommit=True)

    group_invite = operation.get('group_invite')
    if group_invite:
        member = session.query(db.User).get(member_id)
        plug.usergroup.join_with_invitekey(member, group_invite, nocommit=True)

    # clean basket
    if cart:
        update_cart(cart, [])

    if db.Module.has('LoyaltyPoints'):
        # check if loyaltypoints should be given
        if rbookings and all_rbookings:
            for rb in all_rbookings:
                plug.loyaltypoints.check_loyaltypoint_terms(member_id, booking=rb)
        if tcards and all_tcards:
            for tc in all_tcards:
                plug.loyaltypoints.check_loyaltypoint_terms(member_id, booking=tc)

    # mailing
    mailing = dict(
        member_id=member_id,
        items=operation['items'],
        method=method,
        rbookings=ready_rbookings.values(),
        paid=paid,
        bundle=bundle,
        total=total,
        override_payer=operation.get('override_payer')
    )
    if flow := plug.ctx.active_flow:
        flow.add_post_operation('plug.webshop.core.post_mailing', mailing)
    else:
        @plug.db.on_commit
        def send_mailing():
            try:
                plug.webshop.core.post_mailing(mailing)
            except Exception:
                traceback.print_exc()


def items_to_text(items, skip_payment=False):
    import db
    session = plug.db.get_session()
    result = u''

    for item in items:
        if 'product_id' in item:
            tc = session.query(db.TrainingCardType).filter(db.TrainingCardType.id == item['product_id']).first()

            count = item.get('count', 1)
            if count != 1:
                result += str(count) + u' x '
            name = tc.name
            if item.get('variant'):
                name += ' - ' + item['variant']
            if item.get('teamsportregistration'):
                gc = plug.teamsport.TeamSportGameClass.getInternal(item['teamsportregistration'].get('gameclass_id'))
                name = db.translate('Registration fee') + ' - ' + gc.competition.name + ' - ' + gc.name

            result += name + u"<br>"
        elif 'rbservice_id' in item:
            rb = session.query(db.ResourceBookingService).get(item['rbservice_id'])
            result += rb.name + u"<br>"
        elif 'workout_id' in item:
            w = session.query(db.Workout).get(item['workout_id'])
            result += w.workoutType.name + u"<br>"
        elif not skip_payment and item.get('payments'):
            for pid in item['payments']:
                p = session.query(db.Payment).get(pid)
                result += p.name + u"<br>"
    return result

def item_to_text(item):
    import db
    session = plug.db.get_session()
    result = u''

    if 'product_id' in item:
        tc = session.query(db.TrainingCardType).filter(db.TrainingCardType.id == item['product_id']).first()

        count = item.get('count', 1)
        if count != 1:
            result += str(count) + u' x '

        name = tc.name
        if item.get('variant'):
            name += ' - ' + item['variant']
        if item.get('teamsportregistration'):
            gc = plug.teamsport.TeamSportGameClass.getInternal(item['teamsportregistration'].get('gameclass_id'))
            name = db.translate('Registration fee') + ' - ' + gc.competition.name + ' - ' + gc.name

        result += name
    elif 'rbservice_id' in item:
        rb = session.query(db.ResourceBookingService).get(item['rbservice_id'])
        result += rb.name
    elif 'workout_id' in item:
        w = session.query(db.Workout).get(item['workout_id'])
        result += w.workoutType.name
    elif item.get('payments'):
        names = []
        for pid in item['payments']:
            p = session.query(db.Payment).get(pid)
            names.append(p.name)
        result = ', '.join(names)
    return result


def post_mailing(mailing):
    with plug.db.commit_block():
        send_mails(member=plug.user.get(mailing.pop('member_id')), **mailing)


def send_mails(items, member, total, method=None, rbookings=None, paid=False, bundle=None, override_payer=None):
    import db

    methods = {
        'invoice': 'Invoice',
        'directdebit': 'Direct debit',
        'payson': 'Card- or direct payment',
        'unknown': 'Pay on site',
        'valuecard': 'Value card',
        'stripe': 'Card payment',
        'swishi': 'Swish'
    }

    methodText = methods.get(method, db.PaymentMethod.getFromCache(method).name)
    if total == 0 and method == 'unknown':
        methodText = 'No payments'
    paymentMethod = plug.string.translate(methodText)

    products = items_to_text(items, skip_payment=True)
    if products:
        settings = db.Settings._getSettings()
        fromName = member.name
        link = member.getLinkToCustomerCard()
        keys = dict(purchasedFromName=fromName, products=items_to_text(items), paymentMethod=paymentMethod, link=link, LINKTO=plug.string.format(plug.string.translate('LINKTO', fromName)))
        plug.mailing.send_automatic_mailing(plug.mailing.Autotypes.PURCHASE_MAIL, settings, keys)

    # Send order confirmation mail
    from functools import partial
    keys = dict(products=items_to_text(items), paymentMethod=paymentMethod, mailFromName=db.getMailFromName())
    attachments = None
    receiptPdfAttachment = member.getReceiptPdfAttachment(bundle)
    if receiptPdfAttachment:
        attachments = [receiptPdfAttachment]
    member = override_payer or member
    plug.mailing.send_automatic_mailing(plug.mailing.Autotypes.ORDER_CONFIRMATION, member, keys, attachments=attachments)

    if rbookings:
        for aBooking in rbookings:
            if aBooking.confirmed:
                aBooking.sendConfirmMail()
                aBooking.sendDoorAccessCode()
            aBooking.sendBookingMailToStaff()


def rbooking(booking, member, method, punchcards):
    import db

    session = plug.db.get_session()
    rbservice = session.query(db.ResourceBookingService).get(booking['rbservice_id'])
    cardtype = db.ResourceBookingService.getTrainingCardType(rbservice.id)
    assert rbservice

    site_id = booking.get('site_id', db.Site.main().id) or db.Site.main().id
    assert site_id
    assert myutil.find(rbservice.sites, lambda site: site.id == site_id)

    extra_person = booking.get('extra_person')
    if booking.get('extended_info'):
        extended_info = plug.string.unicode(db.jsonify(booking['extended_info']))
    else:
        extended_info = None

    slots = booking['slots']
    for slot in slots:
        slot['start'] = plug.date.to_datetime(slot['start'])
        slot['end'] = plug.date.to_datetime(slot['end'])
    slots = plug.resourcebooking.combine_slots(slots)

    if rbservice.minimum_booking_time and rbservice.category.multiBooking:
        total_duration = 0
        for slot in slots:
            total_duration += (slot['end'] - slot['start']).total_seconds() // 60
        if total_duration < rbservice.minimum_booking_time:
            raise plug.e.InvalidInputException('duration per service ({}) < minimum_booking_time ({})'.format(
                total_duration, rbservice.minimum_booking_time))

    parent_id = plug.db.VirtualId()
    tcards = []
    payments = []
    rbookings = []
    for slot in slots:
        duration = (slot['end'] - slot['start']).total_seconds() // 60

        count = int(math.ceil(float(duration) / rbservice.duration))
        count_of_people = 1
        if extra_person:
            count_of_people += len(extra_person)
            count *= count_of_people

        # Deduct punchcards
        punchcard = None
        punchcard_count = count
        if punchcards and count:
            booking_date = slots[0]['start'].date()
            for ct in punchcards:
                if (ct.card.validToDate is None or ct.card.validToDate >= booking_date) and ct.trainingsLeft >= count:
                    ct.trainingsLeft -= count
                    count = 0
                    punchcard = ct.card
                    break

        price = cardtype.price * count
        if not punchcard:
            tcard_id = plug.db.VirtualId()

            tcards.append(dict(
                id=tcard_id,
                created=plug.date.now(),
                cardtype_id=cardtype.id,
                #boundToDate=None,
                validFromDate=plug.date.today(),
                #validToDate=None,
                trainingsLeft=0,
                member_id=member.id,
                price=price,
                count=count
            ))

        duedate = slot['start'].date()

        if method == 'directdebit':
            if duedate.day > 25:
                duedate = plug.date.next_month(duedate)
            duedate = plug.date.change_day(duedate, 28)

        included_products = []
        if price > 0:
            included_sum = count * (sum(lmap(int, rbservice.included_products_amount.values())) if rbservice.included_products_amount else 0)
            p = {
                'amount': price - included_sum,
                'status': 'paid',
                'date': duedate,
                'member_id': member.id,
                'method': method,
                'payer_id': member.id,
                'trainingcard_id': tcard_id,
                'cardtype_id': cardtype.id,
                'vat': cardtype.vat,
                'name': rbservice.name + ' ' + slot['start'].date().isoformat() + ' ' + slot['start'].time().isoformat()[:5],
                'site_id': site_id
            }
            if included_sum:
                p['shownPriceOnReceipt'] = price

            payments.append(p)

            for product_id in rbservice.included_products or []:
                amount = rbservice.included_products_amount.get(str(product_id)) or 0
                tcard = dict(
                    id=plug.db.VirtualId(),
                    created=plug.date.now(),
                    member_id=member.id,
                    cardtype_id=product_id,
                    validFromDate=None,
                    price=count * int(amount),
                    count=count
                )
                included_products.append(tcard['id'])
                tcards.append(tcard)
                p = dict(
                    amount=count * int(amount),
                    date=duedate,
                    status='paid',
                    trainingcard_id=tcard['id'],
                    cardtype_id=product_id,
                    member_id=member.id,
                    payer_id=member.id,
                    method=method,
                    hidePriceOnReceipt=True,
                    site_id=site_id
                )
                payments.append(p)


        rb = dict(
            id=plug.db.VirtualId(),
            service_id=booking['rbservice_id'],
            time=slot['start'],
            staff_id=slot['staff_id'],
            xstaff_id=slot.get('xstaff_id'),
            member_id=member.id,
            price=price,
            duration=duration,
            created=plug.date.now(),
            cancelled=False,
            #note=note,
            parent_id=parent_id,
            extendedInfo=extended_info,
            confirmed=not rbservice.manualConfirm,
            products=[],
            booker_id=member.id,
            extra_person=extra_person,
            present=False,
            trainingcard_id=punchcard.id if punchcard else tcard_id,
            punchcard=True if punchcard else False,
            site_id=site_id,
            punchcard_count=punchcard_count if punchcard else 0,
            included_products=included_products
        )
        rbookings.append(rb)

    return {
        'parent_id': parent_id,
        'rbookings': rbookings,
        'tcards': tcards,
        'payments': payments,
        'vat': cardtype.vat,
        'tmp_id': booking.get('tmp_id')
    }


def complete_checkout_deferred(success=None, amount=None, extra_info=None, method=None, reason=None, **kargs):
    import db
    operation = extra_info['operation']

    def notify():
        if not operation.get('bundle_id') or not operation['items'] or len(operation['items']) == 0:
            plug.send_error('No items in operation: ' + str(operation))

        plug.net.send_channel2(operation['channel2'], {
            'type': 'payment',
            'success': success,
            'orderconfirmation': get_order_confirmation(operation['items'], operation.get('bundle_id')),
            'reason': reason
        })

    if success:
        with plug.db.commit_block(prevent_commit=True) as session:
            cart = session.query(schema.Cart).get(operation['cart_key']) if operation['cart_key'] else None
            if cart:
                cart.in_process = None
            bundle = session.query(db.PaymentBundle).get(operation['bundle_id'])

            if method == 'swishi':
                bundle.transaction_id = kargs.get('swish_transaction')

            complete_checkout(
                cart=cart,
                method=method,
                total=amount,
                bundle=bundle,
                paid=True,
                operation=operation
            )

            plug.db.on_commit(notify)
    else:
        with plug.db.commit_block(prevent_commit=True) as session:
            cart = session.query(schema.Cart).get(operation['cart_key']) if operation['cart_key'] else None
            if cart:
                cart.in_process = None

            member_id = operation['member_id']
            member = session.query(db.User).get(member_id)

            actual_payments = operation.get('actual_payments')
            if actual_payments:
                for a in actual_payments:
                    if a['method'] == 'valuecard':
                        tcard_id = a.get('trainingcard_id')
                        if tcard_id:
                            tcard = session.query(db.TrainingCard).get(tcard_id)
                            tcard.price += a['amount']
                        else:
                            member.refillValueCard(a['amount'], nocommit=True)

            plug.db.on_commit(notify)


def get_invoice_by_payments(payment_ids, error_pending_invoice=False):
    from db import Payment, Invoice

    session = plug.db.get_session()
    payment_bundles = set()
    for pid in payment_ids:
        p = session.query(Payment).get(pid)
        assert p and p.status in ('pending', 'failed', 'sent')

        if error_pending_invoice and p.method in ('invoice', 'einvoice') and p.status != 'sent':
            raise plug.e.InvalidInputException('Only sent invoice can be paid')

        # check for invoice:
        for a in p.attempts:
            if a.method in ('invoice', 'directdebit'):
                payment_bundles.add(a.bundle_id)

        # able to pay?
        if p.cardtype and p.cardtype.methods:
            if not {'stripe', 'valuecard', 'swishi', 'payson'} & set(p.cardtype.methods):
                raise plug.e.Exception('No payment methods to pay a payment')

    if not payment_bundles:
        return None

    invoice = None
    for bundle_id in payment_bundles:
        for i in session.query(Invoice).filter(Invoice.bundle_id == bundle_id):
            if i.credited:
                continue
            if invoice and invoice != i:
                raise plug.e.Exception('Impossible pay a few invoices')
            invoice = i

    if not invoice:
        raise plug.e.Exception('No invoice for a bundle')

    # match payments
    pl = set()
    for p in invoice.bundle.getPayments():
        pl.add(p.id)
    for r in invoice.reminders:
        if r.fee_payment:
            pl.add(r.fee_payment.id)
        if r.rate_payment:
            pl.add(r.rate_payment.id)

    if pl != set(payment_ids):
        raise plug.e.Exception('Payments doesn\'t match invoice')

    return invoice


def empty_cart():
    import db
    # remove broken carts
    db.engine.execute(db.text('update cart set _json = \'{"items": []}\', updated = null where updated is not null and length(cart._json) > 16000000'))

    check_time = datetime.now() - timedelta(hours=48)
    with plug.db.commit_block() as session:
        session.rollback()
        carts = session.query(Cart).filter(Cart.removed == None, Cart.updated != None, Cart.updated < check_time).all()
        for cart in carts:
            update_cart(cart, [])
            cart.updated = None


def complete_as_valuecard(user_id, payer_id, amount, pending_id, bundle_id=None):
    import db

    with plug.db.commit_block() as session:
        cardtype_id = db.TrainingCardType.getValueCard().id
        user = plug.user.get(user_id)
        assert user_id and user

        if bundle_id:
            bundle = session.query(db.PaymentBundle).get(bundle_id)
        else:
            bundle = db.PaymentBundle()
            session.add(bundle)

        if pending_id:
            pending = session.query(db.PendingDirectPayment).get(pending_id)
            pending.status = 'done-valuecard'
            if not bundle.transaction_id:
                bundle.transaction_id = pending.external_id

        db.Payment.addInternal(payments=[dict(
            amount=amount,
            date=plug.date.today(),
            method='stripe',
            paid=True,
            user_id=user_id,
            payer_id=payer_id,
            cardtype_id=cardtype_id,
            created_at='webshop'
        )], bundle=bundle, nocommit=True)

        transaction = plug.transaction.addManual(
            payer=user,
            date=plug.date.now(),
            amount=amount,
            method='stripe',
            bundle=bundle,
            commit=False
        )

        session.add(db.ActualPayment(
            created=plug.date.now(),
            bundle=bundle,
            method='stripe',
            amount=amount,
            transaction=transaction
        ))

        user.refillValueCard(amount, nocommit=True)
