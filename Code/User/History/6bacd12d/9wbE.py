# -*- coding: utf-8 -*-

import base64
import os
import plug
import json
import datetime
from dateutil.relativedelta import relativedelta
import adminutil
from operator import itemgetter


db = None  # load later


@plug.on('migrate', priority=-100)
def set_db():
    global db
    import db as dblib
    db = dblib


@plug.on('migrate')
def migration_2021():
    import db
    db.resources_resourcebookingservice.create(db.engine, checkfirst=True)

    plug.db.ensure_column(db.PaymentMethod.__tablename__, 'imagekey', 'varchar(40)')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'imagekey', 'varchar(40)')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'product_category_id', 'int(11)')
    plug.db.ensure_column(db.TrainingCardType._json)

    plug.db.ensure_column(db.ResourceBookingService.__tablename__, 'enable_capacity', 'tinyint(1)')
    plug.db.ensure_column(db.ResourceBookingService.__tablename__, '_json', 'text')

    plug.db.ensure_column(db.ResourceBooking.__tablename__, '_json', 'text')
    plug.db.ensure_column(db.ResourceBooking.__tablename__, 'present', 'tinyint(1)')

    plug.db.ensure_column(db.PendingDirectPayment.__tablename__, '_json', 'text')
    plug.db.ensure_column(db.PendingDirectPayment.status)
    plug.db.ensure_column(db.PendingDirectPayment.amount)
    plug.db.ensure_index('pendingdirectpayment_index', 'pendingdirectpayment', ('method', 'status'))

    plug.db.ensure_column(db.CashRegister.__tablename__, '_json', 'text')
    plug.db.ensure_column(db.PaymentBundle.__tablename__, '_json', 'text')
    plug.db.ensure_column(db.ToDo.__tablename__, '_json', 'text')

    plug.db.ensure_column(db.SystemRequest.__tablename__, 'version', 'varchar(20)')

    plug.db.ensure_column(db.Field.__tablename__, 'required_for_staff', 'tinyint(1)')
    plug.db.ensure_column(db.Settings.economy_responsible_staff_id)
    plug.db.ensure_column(db.Settings.economy_responsible_group_id)

    if plug.db.get_column_type(db.DirectDebitFile.__tablename__, 'filename') != 'varchar(96)':
        plug.db.change_column_type(db.DirectDebitFile.__tablename__, 'filename', 'varchar(96)')

    if plug.db.get_column_type(db.User.__tablename__, 'memberNumber') != 'bigint':
        plug.db.change_column_type(db.User.__tablename__, 'memberNumber', 'bigint')

    plug.db.ensure_column(db.ToDo.__tablename__, 'transaction_id', 'int(11)')
    plug.db.ensure_column(db.Settings.__tablename__, 'accountingJournals', 'tinyint(1)')
    plug.db.ensure_column(db.DirectDebitSettings.__tablename__, 'payoutBankgiroNumber', 'int(11)')
    plug.db.ensure_column(db.CheckoutReceipt.__tablename__, 'bundle_id', 'int(11)')
    plug.db.ensure_column(db.ZReport.__tablename__, 'accounting', 'mediumtext')
    plug.db.ensure_column(db.CheckoutReceipt.__tablename__, 'seqnr', 'int(11)')

    plug.db.ensure_column(db.Payment.__tablename__, 'from_date', 'date')
    plug.db.ensure_column(db.Payment.__tablename__, 'to_date', 'date')
    plug.db.ensure_column(db.Payment.parent_id)

    plug.db.ensure_column(db.CheckoutReceipt.__tablename__, 'zreport_id', 'int(11)')
    plug.db.ensure_index('zreport_index', 'checkoutreceipt', 'zreport_id')
    plug.db.ensure_column(db.Workout.__tablename__, 'description', 'text')
    plug.db.ensure_column(db.PayoutFile.__tablename__, 'payoutDate', 'date')
    plug.db.ensure_column(db.PayoutFile.__tablename__, 'status', 'varchar(10)')
    plug.db.ensure_column(db.Settings.__tablename__, 'textColor', 'varchar(10)')

    plug.db.ensure_column(db.PaymentMethod.__tablename__, 'external', 'tinyint(1)')
    plug.db.ensure_column(db.PaymentMethod.__tablename__, 'periodic', 'tinyint(1)')
    plug.db.ensure_column(db.PaymentMethod.__tablename__, '_id', 'int(11)', not_null=True, auto_increment=True)

    pm_id = plug.db.describe_column(db.PaymentMethod.__tablename__, '_id')
    if pm_id['null'] or pm_id['extra'] != 'auto_increment':
        plug.db.ensure_index('UNIQUE__ID', db.PaymentMethod.__tablename__, '_id', type='UNIQUE')
        plug.db.change_column_type(db.PaymentMethod.__tablename__, '_id', 'int(11)', not_null=True, auto_increment=True)

    plug.db.ensure_column(db.Entry.__tablename__, 'charged', 'tinyint(1)')
    plug.db.ensure_column(db.Entry.__tablename__, 'card_id', 'int(11)')
    plug.db.ensure_index('entrycard_index', 'entry', 'card_id')
    plug.db.ensure_column(db.Settings.__tablename__, 'autoconfirm', 'tinyint(1)')
    plug.db.ensure_column(db.InvoiceSettings.__tablename__, 'account', 'int(11)')
    plug.db.ensure_column(db.InvoiceSettings.autosend_webshop_invoice)
    plug.db.ensure_column(db.ToDo.__tablename__, 'removed', 'datetime')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'giftcard', 'tinyint(1)')
    db.ActualPayment.__table__.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.TrainingCard.__tablename__, 'code', 'varchar(40)')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'discount_fixed', 'decimal(18, 5)')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'discount_percent', 'int(11)')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'discount_code', 'varchar(40)')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'validFromDate', 'date')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'validToDate', 'date')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'misc', 'tinyint(1)')
    plug.db.ensure_column(db.CashRegister.__tablename__, 'ips', 'text')
    plug.db.ensure_column(db.ActualPayment.__tablename__, 'created', 'datetime')
    db.InvoiceReminderSettings.__table__.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.Invoice.__tablename__, 'remindersEnabled', 'tinyint(1)')
    plug.db.ensure_column(db.Invoice.__tablename__, 'reminderFee', 'decimal(18, 5)')
    plug.db.ensure_column(db.Invoice.__tablename__, 'reminderRate', 'decimal(18, 5)')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'reminderFee', 'tinyint(1)')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'reminderRate', 'tinyint(1)')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'invoiceFee', 'tinyint(1)')

    plug.db.ensure_column(db.WorkoutBooking.__tablename__, 'reserved', 'tinyint(1)')

    if plug.db.get_column_type(db.TrainingCardType.__tablename__, 'validFromDate') != 'date':
        plug.db.change_column_type(db.TrainingCardType.__tablename__, 'validFromDate', 'date')

    if plug.db.get_column_type(db.TrainingCardType.__tablename__, 'validToDate') != 'date':
        plug.db.change_column_type(db.TrainingCardType.__tablename__, 'validToDate', 'date')

    plug.db.ensure_column(db.ActualPayment.__tablename__, 'transaction_id', 'int(11)')
    plug.db.ensure_index('actualpaymenttransaction_index', 'actualpayment', 'transaction_id')
    plug.db.ensure_column(db.Settings.__tablename__, 'test', 'tinyint(1)')
    plug.db.ensure_column(db.InvoiceSettings.__tablename__, 'fee', 'decimal(18, 5)')
    db.Warning.__table__.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.WorkoutBookingSettings.__tablename__, 'warningPeriod', 'int(11)')
    plug.db.ensure_column(db.TrainingCardType.__tablename__, 'blockFee', 'tinyint(1)')
    plug.db.ensure_index('invoicecreditedinvoice_index', 'invoice', 'credited_invoice_id')
    plug.db.ensure_column(db.Sms.__tablename__, 'count', 'int(11)')
    plug.db.ensure_column(db.Invoice.__tablename__, 'type', 'varchar(20)')
    plug.db.ensure_column(db.Invoice.__tablename__, 'amount', 'decimal(18, 5)')
    plug.db.ensure_column(db.Invoice.__tablename__, 'vatAmount', 'decimal(18, 5)')
    plug.db.ensure_column(db.Payment.__tablename__, 'checkoutreceipt_id', 'int(11)')
    plug.db.ensure_index('paymentcheckoutreceipt_index', 'payment', 'checkoutreceipt_id')
    plug.db.ensure_column(db.CheckoutReceipt.__tablename__, 'staff_id', 'int(11)')
    plug.db.ensure_index('checkoutreceiptstaff_index', 'checkoutreceipt', 'staff_id')
    plug.db.ensure_column(db.CheckoutReceipt.__tablename__, 'amount', 'decimal(18, 5)')
    plug.db.ensure_index('paymentpaymentmethod_index', 'payment', 'method')
    plug.db.ensure_index('trainingcardtypeproductcategory_index', 'trainingcardtype', 'product_category_id')
    db.PermissionTask.__table__.create(db.engine, checkfirst=True)
    db.role_permissiontask.create(db.engine, checkfirst=True)
    db.User.__table__.create(db.engine, checkfirst=True)
    db.UserSession.__table__.create(db.engine, checkfirst=True)
    db.UserStatus.__table__.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.Card.created)  # new way to create columns
    plug.db.ensure_column(db.User.stripe_3ds)
    plug.db.ensure_column(db.StripePayment.refund_time)
    plug.db.ensure_column(db.Invoice.paydate)
    plug.db.ensure_column(db.PermissionTask.created)
    plug.db.ensure_column(db.PermissionTask.removed)
    plug.db.ensure_column(db.PermissionTask.builtIn)

    plug.db.ensure_column(db.PermissionTask._id)
    plug.db.ensure_index('permissiontask__id_auto', db.PermissionTask.__tablename__, '_id', auto_increment=True)

    if plug.db.get_column_type(db.TrainingCardType.__tablename__, 'account') != 'varchar(20)':
        plug.db.change_column_type(db.TrainingCardType.__tablename__, 'account', 'varchar(20)')

    plug.db.ensure_column(db.Settings.sparOption)

    plug.db.ensure_column(db.TrainingCardType.barcode)
    plug.db.ensure_column(db.CashRegister.registercoins)

    db.trainingcard_usergroup.create(db.engine, checkfirst=True)

    db.ProtectedField.__table__.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.ProtectedField.name)
    plug.db.ensure_column(db.User.gender)
    plug.db.ensure_column(db.User.birthdate)
    plug.db.ensure_column(db.User._json)
    plug.db.ensure_column(db.User.einvoice_status)
    plug.db.ensure_column(db.Payment.comment)
    plug.db.ensure_column(db.CashRegister.site_id)
    plug.db.ensure_column(db.Site.created)
    plug.db.ensure_column(db.Site.removed)
    plug.db.ensure_column(db.Site.address)
    plug.db.ensure_column(db.Site.zipCode)
    plug.db.ensure_column(db.Site.city)
    plug.db.ensure_column(db.Workout.site_id)
    plug.db.ensure_column(db.Workout.extra_title)
    plug.db.ensure_column(db.Workout.collection_time)
    db.site_workouttype.create(db.engine, checkfirst=True)
    db.site_resourcebookingcategory.create(db.engine, checkfirst=True)
    db.site_resourcebookingservice.create(db.engine, checkfirst=True)
    db.site_trainingcardtype.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.User.homesite_id)
    plug.db.ensure_column(db.UserSession.site_id)
    db.AccountingSettings.__table__.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.AccountingSettings.longaccounts)

    plug.db.ensure_column(db.WorkoutBookingSettings.entryDuration)
    plug.db.ensure_column(db.WorkoutBookingSettings.allowCreateWorkoutType)
    plug.db.ensure_column(db.WorkoutBookingSettings.warningLateCancellations)

    plug.db.drop_foreign_key(db.Payment.method)
    plug.db.ensure_column(db.CashRegister.created)
    plug.db.ensure_column(db.CashRegister.removed)

    plug.db.ensure_column(db.TrainingCardType.membership)
    plug.db.ensure_column(db.TrainingCardType.requireMembership)
    db.WorkoutCategory.__table__.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.WorkoutType.category_id)
    plug.db.ensure_column(db.User.mailing_hash_id)
    plug.db.ensure_column(db.User.mailing_options)
    plug.db.ensure_column(db.WorkoutCategory.order)
    plug.db.ensure_column(db.WorkoutCategory.firstCome)
    plug.db.ensure_column(db.WorkoutBooking.inQueue)

    db.site_workoutcategory.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.WorkSchedule.site_id)
    plug.db.ensure_column(db.ResourceBooking.site_id)
    plug.db.ensure_column(db.WorkoutCategory.show)
    plug.db.ensure_column(db.WorkoutType.sisu)
    plug.db.ensure_column(db.WorkoutType.is_global)
    plug.db.ensure_column(db.WorkoutType.subcategory)
    plug.db.ensure_column(db.Settings.customStyling)
    plug.db.ensure_column(db.WorkoutCategory.showMembers)
    plug.db.ensure_column(db.User.hideforothers)
    plug.db.ensure_column(db.TrainingCard.type)
    plug.db.ensure_column(db.TrainingCardType.type)

    if plug.db.get_column_type(db.TrainingCard.__tablename__, 'type') != 'varchar(20)':
        plug.db.change_column_type(db.TrainingCard.__tablename__, 'type', 'varchar(20)')

    if plug.db.get_column_type(db.TrainingCard.__tablename__, 'count') != 'decimal(18,5)':
        plug.db.change_column_type(db.TrainingCard.__tablename__, 'count', 'decimal(18,5)')

    if plug.db.get_column_type(db.TrainingCardType.__tablename__, 'type') != 'varchar(20)':
        plug.db.change_column_type(db.TrainingCardType.__tablename__, 'type', 'varchar(20)')

    db.workout_usergroup.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.Mail.text_suffix)
    plug.db.ensure_column(db.WorkoutCategory.permission)
    plug.db.ensure_column(db.WorkoutCategory.discussion)
    plug.db.ensure_column(db.User.open_door_permission)
    plug.db.ensure_column(db.Field.unique)
    plug.db.ensure_column(db.TrainingCardType.supplier)
    plug.db.ensure_column(db.TrainingCardType.purchase_price)
    plug.db.ensure_column(db.TidomatSettings.extended_integration)
    plug.db.ensure_column(db.PaymentMethod.apikey)
    plug.transaction.CostCenter.__table__.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.TrainingCardType.costcenter_id)
    plug.db.ensure_column(db.WorkoutType.costcenter_id)
    plug.db.ensure_column(db.Settings.requireMembership)
    plug.db.ensure_column(db.Journal.created)
    plug.db.ensure_column(db.Journal.removed)
    plug.db.ensure_column(db.WorkoutCategory.registerDaysBefore)
    plug.db.ensure_column(db.WorkoutCategory.registerHoursBefore)
    plug.db.ensure_column(db.WorkoutCategory.unregisterHoursBefore)
    plug.db.ensure_column(db.WorkoutCategory.allowBookingAfterStarted)
    plug.db.ensure_column(db.ApiLog.user_id)
    plug.db.ensure_column(db.Settings.keep_userdata_time)
    plug.db.ensure_column(db.User.marked_for_removal)
    plug.db.ensure_column(db.Settings.auto_remove_users)
    plug.db.ensure_column(db.Settings.login_member_mail)
    plug.db.ensure_column(db.Settings.login_member_facebook)
    plug.db.ensure_column(db.Settings.login_member_bankid)
    plug.db.ensure_column(db.Settings.login_staff_mail)
    plug.db.ensure_column(db.Settings.login_staff_facebook)
    plug.db.ensure_column(db.Settings.login_staff_bankid)
    plug.db.ensure_column(db.PaymentMethod.company_invoice)
    plug.db.ensure_column(db.Payment._json)

    plug.db.ensure_column(db.ApiLog.duration)
    plug.db.ensure_column(db.ApiLog.status)
    plug.db.ensure_column(db.ApiLog.response_size)
    plug.db.ensure_column(db.ApiLog.ip)
    plug.db.ensure_column(db.ApiLog.path)

    plug.db.ensure_column(db.SwishSettings.api_cert)
    plug.db.ensure_column(db.SwishSettings.api_csr)
    plug.db.ensure_column(db.SwishSettings.api_key)

    plug.db.ensure_column(db.ToDo.group_id)

    plug.db.ensure_column(db.Settings.blocked)
    plug.db.ensure_column(db.Settings.softBlocked)

    plug.db.ensure_column(db.TrainingCardType.periodValidFrom)
    plug.db.ensure_column(db.TrainingCardType.periodValidTo)
    plug.db.ensure_column(db.TrainingCardType.period)
    plug.db.ensure_column(db.Invoice.openedMail)

    plug.db.ensure_column(db.Field.changeable_by_member)

    plug.db.ensure_column(db.InvoiceReminderSettings.ignoreUnpaidReminders)

    plug.db.ensure_column(db.CardPaymentSettings.automaticStripeAccounting)
    plug.db.ensure_column(db.CardPaymentSettings.accountingAccount)
    plug.db.ensure_column(db.CardPaymentSettings.transactionCostAccount)

    plug.db.ensure_column(db.User.zoezi)

    plug.db.ensure_column(db.TrainingCard.termsOfPayment)
    plug.db.ensure_column(db.TrainingCard.payMethod)

    if plug.db.get_column_type(db.Mail.__tablename__, 'subject') != 'text':
        plug.db.change_column_type(db.Mail.__tablename__, 'subject', 'text')

    if plug.db.get_column_type(db.TrainingCardType.__tablename__, 'name') != 'text':
        plug.db.change_column_type(db.TrainingCardType.__tablename__, 'name', 'text')

    if plug.db.describe_column('sharedtext', 'text')['collation'] != 'utf8mb4_unicode_ci':
        plug.db.change_column_type('sharedtext', 'text', 'mediumtext', collation='utf8mb4_unicode_ci')

    db.door_trainingcardtype.create(db.engine, checkfirst=True)

    plug.db.ensure_column(db.TidomatSettings.canChangePin)

    plug.db.ensure_column(db.AccountingSettings.vatinboundaccount)
    plug.db.ensure_column(db.User.login_key)
    #plug.db.drop_index('user', 'mail')
    plug.db.ensure_index('mail', 'user', 'mail')

    plug.db.ensure_column(db.ToDo.consentError)

    db.door_resourcebookingservice.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.ResourceBookingService.doorAccess)
    plug.db.ensure_column(db.ResourceBookingService.doorAccessBefore)
    plug.db.ensure_column(db.ResourceBookingService.doorAccessAfter)

    plug.db.ensure_column(db.Settings.sparOptionMember)

    plug.db.ensure_column(db.TrainingCard.accessKeyId)
    plug.db.ensure_column(db.EntryChange.operation)
    db.user_workouts.create(db.engine, checkfirst=True)

    plug.db.ensure_column(db.AccountingSettings.vatexempt)
    plug.db.ensure_column(db.AccountingSettings.registered_for_ftax)

    plug.db.ensure_column(db.TrainingCard.renewReminderSent)

    plug.db.ensure_column(db.Settings.memberCancel)
    plug.db.ensure_column(db.Settings.periodOfNotice)

    plug.db.ensure_column(db.User.qrcode_entry_id)
    plug.db.ensure_column(db.User.connect_qrcode_entry)

    plug.db.ensure_column(db.WorkoutBookingSettings.bookingsLimitIntervalType)
    plug.db.ensure_column(db.WorkoutBookingSettings.bookingsLimitInterval)

    plug.db.ensure_column(db.ResetPasswordLink.show)

    db.ProxyAppSettings.__table__.create(db.engine, checkfirst=True)
    db.ProxyAppInputConfig.__table__.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.ProxyAppInputConfig.app_id)
    plug.db.ensure_column(db.ProxyAppInputConfig.activeTime)
    db.ProxyAppInput.__table__.create(db.engine, checkfirst=True)

    plug.db.ensure_column(db.Workout.queueGiveback)
    plug.db.ensure_column(db.CashRegister.selfcheckout)
    plug.db.ensure_column(db.CashRegister.cardreader_id)

    plug.db.ensure_column(db.TrainingCardType.bookingsLimitIntervalType)
    plug.db.ensure_column(db.TrainingCardType.bookingsLimitInterval)
    plug.db.ensure_column(db.TrainingCardType.showSelfCheckout)
    plug.db.ensure_column(db.TrainingCardType.product_webshop_category_id)

    plug.db.ensure_column(db.PaymentMethod.selfCheckout)

    db.multiresource_resource.create(db.engine, checkfirst=True)

    plug.db.ensure_column(db.ResourceBookingService.continuousBooking)
    plug.db.ensure_column(db.ResourceBookingService.initialFreeType)
    plug.db.ensure_column(db.ResourceBookingService.initialFree)
    plug.db.ensure_column(db.ResourceBookingService.maxDuration)
    db.ContinuousResourceBooking.__table__.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.ContinuousResourceBooking.rbooking_id)
    plug.db.ensure_column(db.ContinuousResourceBooking.checkoutReason)
    plug.db.ensure_column(db.ContinuousResourceBooking.checkoutFailed)
    plug.db.ensure_column(db.ContinuousResourceBooking.site_id)

    plug.db.ensure_column(db.User.noPcode)

    plug.db.ensure_column(db.Settings.use_visit_address)
    plug.db.ensure_column(db.Settings.visit_address)
    plug.db.ensure_column(db.Settings.visit_zipCode)
    plug.db.ensure_column(db.Settings.visit_city)
    plug.db.ensure_column(db.Settings.homepage)

    if plug.db.get_column_type(db.User.__tablename__, 'type') != "enum('user','resource','hiddenuser')":
        plug.db.change_column_type(db.User.__tablename__, 'type', "enum('user','resource','hiddenuser')")

    plug.db.ensure_column(db.DirectDebitSettings.billingDate)

    plug.db.ensure_column(db.Entry.reason)
    if plug.db.get_column_type(db.Entry.__tablename__, 'reason') != 'varchar(32)':
        plug.db.change_column_type(db.Entry.__tablename__, 'reason', 'varchar(32)')

    db.WorkoutBookingRequest.__table__.create(db.engine, checkfirst=True)

    plug.db.ensure_column(db.User.stripe_expire_date)
    plug.db.ensure_column(db.User.stripe_expire_last_mailing)

    plug.db.ensure_column(db.Module._id)
    plug.db.ensure_index('module__id_auto', db.Module.__tablename__, '_id', auto_increment=True)

    plug.db.ensure_column(db.AccountingSettings.account)
    plug.db.ensure_column(db.WorkoutCategory.for_group)


    plug.db.ensure_column(db.User.allowPush)

    plug.db.ensure_column(db.ToDo.creator_id)
    db.RoleChange.__table__.create(db.engine, checkfirst=True)

    plug.db.ensure_column(db.TrainingCard.product_variant)
    plug.db.ensure_column(db.Payment.product_variant)

    plug.db.ensure_column(db.Module.version_id)
    plug.db.ensure_column(db.Invoice.generateCode)

    plug.db.ensure_column(db.Workout.video)
    plug.db.ensure_column(db.Workout.video_url)
    plug.db.ensure_column(db.Workout.auto_attendance)

    plug.db.ensure_column(db.WorkoutBookingRequest.comment)

    plug.db.ensure_column(db.TrainingCardType.autoRenewSessions)
    plug.db.ensure_column(db.TrainingCardType.autoRenewSessionsMax)
    plug.db.ensure_column(db.TrainingCard.lastRenewDate)

    plug.db.ensure_column(db.User.description)
    plug.db.ensure_column(db.User.work_description)

    plug.db.ensure_column(db.InvoiceSettings.minAmount)
    plug.db.ensure_column(db.DirectDebitSettings.minAmount)

    plug.db.ensure_column(db.Invoice.sentTo)

    plug.db.ensure_column(db.User.allowInvoiceAt16)

    plug.db.ensure_column(db.Settings.vueMemberPage)
    plug.db.ensure_column(db.Settings.defaultMethod)
    plug.db.ensure_column(db.WorkoutType.imagekey)

    plug.db.ensure_column(db.User.supplier)

    plug.db.ensure_column(db.TrainingCardType.entryWhenBooked)
    plug.db.ensure_column(db.TrainingCardType.entryWhenBookedBefore)

    plug.db.ensure_column(db.CashRegister.memberpage)
    plug.db.ensure_column(db.User.google_id)
    plug.db.ensure_column(db.Settings.login_member_google)
    plug.db.ensure_column(db.Settings.login_staff_google)

    plug.db.ensure_column(db.Settings.area)
    plug.db.ensure_column(db.Settings.averageVisitorTime)
    plug.db.ensure_column(db.Settings.showPandemicVisitorStatus)
    
    plug.db.ensure_column(db.Settings.show_getstarted)

    plug.db.ensure_column(db.Workout.players_can_register_self)
    plug.db.ensure_column(db.Workout.bookings_confirmed)

    plug.db.ensure_column(db.ResourceBookingService.imagekey)

    if plug.db.get_column_type(db.Invoice.__tablename__, 'referenceNumber') != 'bigint':
        plug.db.change_column_type(db.Invoice.__tablename__, 'referenceNumber', 'bigint')

    plug.db.ensure_column(db.Field.child)
    plug.db.ensure_column(db.Field.required_child)
    plug.db.ensure_column(db.Settings.stockPerSite)
    db.ProductVariant.__table__.create(db.engine, checkfirst=True)
    db.ProductStock.__table__.create(db.engine, checkfirst=True)

    db.visible_site_trainingcardtype.create(db.engine, checkfirst=True)
    plug.db.ensure_column(db.PaymentBundle.original_id)


    plug.db.ensure_column(db.Payment.site_id)

    plug.db.ensure_column(db.Site.costcenter_id)

    plug.db.ensure_column(db.WorkoutType._json)
    plug.db.ensure_column(db.Settings.use_zoezi_cert)

    db.SystemTag.__table__.create(db.engine, checkfirst=True)
    db.workouttype_systemtag.create(db.engine, checkfirst=True)
    db.workout_systemtag.create(db.engine, checkfirst=True)
    db.resourcebookingservice_systemtag.create(db.engine, checkfirst=True)
    db.trainingcardtype_systemtag.create(db.engine, checkfirst=True)

    plug.db.ensure_column(db.ResourceBookingCategory.imagekey)
    plug.db.ensure_column(db.Settings.limitStaffSiteAccess)

    db.UserConnection.__table__.create(db.engine, checkfirst=True)

    plug.db.ensure_column(db.ResourceBookingCategory.order)
    plug.db.ensure_column(db.ResourceBookingCategory.created)
    plug.db.ensure_column(db.ResourceBookingCategory.removed)

    plug.db.ensure_column(db.GrantBookingPrivilegeLink.book)
    plug.db.ensure_column(db.GrantBookingPrivilegeLink.manage)
    plug.db.ensure_column(db.Settings.integration_domains)
    plug.db.ensure_column(db.WorkoutCategory.dropin)

    plug.db.ensure_column(db.Payment.seller_id)
    plug.db.ensure_column(db.Payment.created_at)
    plug.db.ensure_column(db.TrainingCard.seller_id)
    plug.db.ensure_column(db.TrainingCard.created_at)
    plug.db.ensure_column(db.TrainingCard.site_id)
    plug.db.ensure_column(db.TrainingCard.barcode)
    plug.db.ensure_column(db.TrainingCard.payer_id)

    plug.db.ensure_column(db.Warning.workout_id)
    plug.db.ensure_column(db.UserSession.realname)

    plug.db.ensure_column(db.Payment.discount)
    plug.db.ensure_column(db.Payment.discountstext)

    plug.db.ensure_column(db.TrainingCard.discount_id)
    plug.db.ensure_column(db.TrainingCard.discount_fixed)
    plug.db.ensure_column(db.TrainingCard.discount_percent)
    plug.db.ensure_column(db.TrainingCard.discount_to_date)
    plug.db.ensure_column(db.Mail.provider)
    plug.db.ensure_column(db.TrainingCardType.lockerRental)
    plug.db.ensure_column(db.TrainingCardType.receiptComment)
    plug.db.ensure_column(db.CashRegister.require_barcode)

    db.AccrualAccountingSettings.__table__.create(db.engine, checkfirst=True)

    db.ScheduleTemplate.__table__.create(db.engine, checkfirst=True)


@plug.on('migrate')
def migration_new():
    import db
    plug.db.ensure_index('task_status_index', 'task', 'status')
    plug.db.ensure_column(db.CashRegister.can_change_price)
    plug.db.ensure_column(db.Settings.zoeziMyBusiness)
    plug.db.ensure_column(db.Freeze.old)
    plug.db.change_column_type(db.User.__tablename__, 'resourceType', "enum('resource','location','room','door','qrcode_entry','multiresource','schedule','metralockercluster')")

    plug.db.ensure_column(db.ToDo.unique)
    plug.db.ensure_index('todo_unique_index', 'todo', 'unique')


@plug.on('migrate.data', priority=-10)
def addStandardPaymentMethods():
    with plug.db.commit_block() as session:
        def addPaymentMethod(id, name='', builtIn=True, active=False, imageSrc='', checkout=False, create=False, change=False, webshop=False, refund=False, markAsPaid=False, **kw):
            p = session.query(db.PaymentMethod).get(id)
            if p:
                return

            session.add(db.PaymentMethod(
                id=id,
                name=name,
                builtIn=builtIn,
                active=True,
                imageSrc=imageSrc,
                checkout=checkout,
                create=create,
                change=change,
                webshop=webshop,
                refund=refund,
                markAsPaid=markAsPaid,
                **kw
            ))

        addPaymentMethod(id='cash', name=u'Cash', account=1910, checkout=True, refund=True, imageSrc='/assets/img/cash.png')
        addPaymentMethod(id='payson', name=u'Payson', account=1990, webshop=True, modules='Payson', imageSrc='/assets/img/payson.jpg')
        addPaymentMethod(id='directdebit', name=u'Direct debit', account=1930, modules='DirectDebit', checkout=True, create=True, change=True, webshop=True, imageSrc='/assets/img/bgc.ico')
        addPaymentMethod(id='bank', name=u'Bank', account=1930, markAsPaid=True, refund=True, refill=True, imageSrc='/assets/img/bank.jpg')
        addPaymentMethod(id='invoice', name=u'Invoice', account=1930, modules='Invoice', checkout=True, create=True, change=True, webshop=True, imageSrc='/assets/img/invoice.png')
        addPaymentMethod(id='xcard', name=u'Card payment', account=1910, modules='Checkout', checkout=True, refund=True, imageSrc='/assets/img/creditcard.png')
        addPaymentMethod(id='valuecard', name=u'Value card', account=2421, checkout=False, create=True, webshop=True, change=True, refund=True, imageSrc='/assets/img/valuecard.png')
        addPaymentMethod(id='stripe', name=u'Card payment Internet', account=1990, modules='CardPayment', webshop=True, imageSrc='/assets/img/creditcard.png')
        addPaymentMethod(id='swish', name=u'Swish', account=1930, modules='Checkout,Swish', checkout=True, imageSrc='/assets/img/swish_logo_primary_idshape_RGB.png')
        addPaymentMethod(id='swishi', name=u'Swish Internet', account=1930, modules='Swish', webshop=True, imageSrc='/assets/img/swish_logo_primary_idshape_RGB.png')
        addPaymentMethod(id='customerloss', name=u'Confirmed customerloss', account=6351, markAsPaid=True, imageSrc='/assets/img/customerloss.png')
        addPaymentMethod(id='unknown', name=u'Payment method is selected later', account=1910, create=True, change=True, webshop=True, markAsPaid=False, refill=False, imageSrc='/assets/img/unknown.png')
        addPaymentMethod(id='giftcard', name=u'Gift card', account=2421, checkout=False, create=False, webshop=False, change=False, refund=False, markAsPaid=True, imageSrc='/assets/img/giftcard.png')


@plug.on('migrate.data')
def fix_payment_workout_foreign_key():
    with plug.db.commit_block() as session:
        if plug.keyvalue.get('migrate:fix_payment_workout_foreign_key') == 1:
            return

        for p in session.query(db.Payment).filter(db.Payment.workout_id != None):
            if p.workout_id and p.workout is None:
                p.workout_id = None

        plug.keyvalue.set('migrate:fix_payment_workout_foreign_key', 1)

    plug.db.ensure_foreign_key(db.Payment.workout_id)

@plug.on('migrate.post')
def post_migration(argv):
    uniq = plug.keyvalue.get('db:uniq8')
    if not uniq:
        uniq = plug.string.random(8)
        plug.keyvalue.set('db:uniq8', uniq, commit=True)

    valuecardmap = plug.keyvalue.get('db:pmvaluecardmap')
    if not valuecardmap:
        session = plug.db.get_session()
        import db
        session.query(db.PaymentMethod).get('valuecard').markAsPaid = True
        plug.keyvalue.set('db:pmvaluecardmap', 1)
        session.commit()


@plug.migrate_once
def migrate_pending_payments(session):
    for p in session.query(db.PendingDirectPayment):
        if not p._json:
            continue
        _json = p._json.copy()
        if 'status' in _json:
            p.status = _json.pop('status')
        if 'amount' in _json:
            p.amount = _json.pop('amount')
        p._json = _json


@plug.on('migrate.post')
def valuecard_account():
    with plug.db.commit_block() as session:
        pm = session.query(db.PaymentMethod).get('valuecard')
        prod = db.TrainingCardType.getValueCard()

        account = pm.account or 2421
        if not pm.account:
            pm.account = account

        if not prod.account or int(prod.account) != account:
            prod.account = str(account)


@plug.on('migrate.post')
def migrate_fields(argv):
    if plug.keyvalue.get('fields_migrated'):
        return

    session = plug.db.get_session()
    import db

    for field in session.query(db.Field).all():
        field.required_for_staff = field.required

    plug.keyvalue.set('fields_migrated', 1)
    session.commit()


@plug.on('migrate.post')
def migrate_checkoutreceiptseqnr(argv):
    if plug.keyvalue.get('checkoutreceiptseqnr_migrated'):
        return

    session = plug.db.get_session()
    import db

    for r in session.query(db.CheckoutReceipt).all():
        d = json.loads(r.data)
        r.seqnr = d.get('seqnr')

    plug.keyvalue.set('checkoutreceiptseqnr_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_checkoutreceiptzreport(argv):
    if plug.keyvalue.get('crzreport_migrated'):
        return

    session = plug.db.get_session()
    import db

    zreports = db.session.query(db.ZReport).all()
    for z in zreports:
        data = json.loads(z.data)
        firstReceipt = data.get('firstReceipt')
        lastReceipt = data.get('lastReceipt')
        if firstReceipt:
            for r in range(firstReceipt, lastReceipt+1):
                cr = db.session.query(db.CheckoutReceipt).filter(db.CheckoutReceipt.cashregister_id == z.cashregister_id, db.CheckoutReceipt.seqnr == r).first()
                if cr:
                    cr.zreport = z

    plug.keyvalue.set('crzreport_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_payoutfile(argv):
    if plug.keyvalue.get('payoutfile_migrated'):
        return

    session = plug.db.get_session()
    import db

    for pf in db.session.query(db.PayoutFile).all():
        if not pf.status:
            pf.status = 'sent'

    plug.keyvalue.set('payoutfile_migrated', 1)
    session.commit()


@plug.on('migrate.post')
def migrate_textcolor(argv):
    if plug.keyvalue.get('textcolor_migrated'):
        return

    session = plug.db.get_session()
    import db

    settings = session.query(db.Settings).first()
    if not settings.textColor:
        settings.textColor = '#000'

    plug.keyvalue.set('textcolor_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_entrycharged(argv):
    if plug.keyvalue.get('entrycharged_migrated'):
        return

    session = plug.db.get_session()
    import db

    entries = session.query(db.Entry).filter(db.Entry.success == True)
    for e in entries:
        e.charged = True

    plug.keyvalue.set('entrycharged_migrated', 1)
    session.commit()


@plug.on('migrate.post')
def migrate_paymentmethods():
    if plug.keyvalue.get('db:paymentmethods_mg'):
        return
    import db
    with plug.db.commit_block() as session:
        session.query(db.PaymentMethod).get('unknown').periodic = True
        session.query(db.PaymentMethod).get('invoice').periodic = True
        session.query(db.PaymentMethod).get('directdebit').periodic = True
        session.query(db.PaymentMethod).get('stripe').periodic = True
        plug.keyvalue.set('db:paymentmethods_mg', 1)


@plug.migrate_once
def migrate_valuecard(session):
    session.query(db.PaymentMethod).get('valuecard').change = False


@plug.on('migrate.post')
def migrate_paymentmethods2():
    if plug.keyvalue.get('db:unknown_for_webshop'):
        return
    import db
    with plug.db.commit_block() as session:
        webshop = False
        for t in session.query(db.TrainingCardType).all():
            if not t.active or not t.customerCanBuy:
                continue
            if t.methods and 'unknown' in t.methods:
                webshop = True
                break
        else:
            for t in session.query(db.WorkoutType).all():
                if not t.active or not t.onetime:
                    continue
                if t.methods and 'unknown' in t.methods:
                    webshop = True
                    break

        if webshop:
            session.query(db.PaymentMethod).get('unknown').webshop = True

        plug.keyvalue.set('db:unknown_for_webshop', 1)


@plug.on('migrate.post')
def migrate_valuecardrefund(argv):
    if plug.keyvalue.get('valuecardrefund_migrated'):
        return

    session = plug.db.get_session()
    import db

    session.query(db.PaymentMethod).filter(db.PaymentMethod.id == 'valuecard').first().refund = True

    plug.keyvalue.set('valuecardrefund_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_unknownmarkaspaid(argv):
    if plug.keyvalue.get('unknownmarkaspaid_migrated'):
        return

    session = plug.db.get_session()
    import db

    unknown = session.query(db.PaymentMethod).filter(db.PaymentMethod.id == 'unknown').first()
    unknown.markAsPaid = False
    unknown.refill = False

    plug.keyvalue.set('unknownmarkaspaid_migrated', 1)
    session.commit()

@plug.migrate_once
def fix_valuecard(session):
    import myutil
    valuecardtype = db.TrainingCardType.getValueCard()
    valuecardtype.validTime = 120
    valuecardtype.validType = 'Month'

    for t in session.query(db.TrainingCard).filter(db.TrainingCard.cardtype_id == valuecardtype.id, db.TrainingCard.validToDate == None):
        assert t.validFromDate
        t.validToDate = myutil.addDateFromType(t.validFromDate, valuecardtype.validTime, valuecardtype.validType)

@plug.on('migrate.post')
def migrate_claimaccount():
    if plug.keyvalue.get('claimaccount_migrated'):
        return

    session = plug.db.get_session()
    import db

    session.query(db.InvoiceSettings).first().account = 1510

    plug.keyvalue.set('claimaccount_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_checkoutlogmethods(argv):
    if plug.keyvalue.get('checkoutlogmethods_migrated'):
        return

    session = plug.db.get_session()
    import db

    events = session.query(db.CheckoutLog).all()
    for e in events:
        data = json.loads(e.data)
        if data.get('type') == 'purchase' and not data.get('methods') and data.get('method'):
            method = data.get('method')
            del data['method']
            data['methods'] = [{'method': method, 'amount': data['amount']}]
            e.data = db.jsonify(data)

    plug.keyvalue.set('checkoutlogmethods_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_addmisccard(argv):
    if plug.keyvalue.get('misccardadded_migrated'):
        return

    session = plug.db.get_session()
    import db

    card = db.TrainingCardType(name=u'Other incomes', misc=True, customerCanBuy=False, vat=0, account=3690)
    db.session.add(card)

    a = db.session.query(plug.transaction.Account).get(3690)
    if not a:
        a = plug.transaction.Account(id=3690, name=u'Övriga sidointäkter')
        db.session.add(a)

    plug.keyvalue.set('misccardadded_migrated', 1)
    session.commit()


@plug.on('migrate.post')
def migrate_stripetoap(argv):
    if plug.keyvalue.get('stripetoap_migrated'):
        return

    session = plug.db.get_session()
    import db

    bundles = []
    attempts = db.session.query(db.PaymentAttempt).join(db.Payment).filter(db.PaymentAttempt.method == 'stripe', (db.PaymentAttempt.status == 'paid') | ((db.PaymentAttempt.status == 'credited') & (db.Payment.refunded == None))).options(db.joinedload('payment')).all()
    for a in attempts:
        if a.bundle and a.bundle not in bundles:
            bundles.append(a.bundle)
    for bundle in bundles:
        if not bundle.methods:
            bundle.createActualPaymentFromBundle(commit=False)

    plug.keyvalue.set('stripetoap_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_invremindersettings(argv):
    if plug.keyvalue.get('invremindersettings_migrated'):
        return

    session = plug.db.get_session()
    import db

    ir = db.InvoiceReminderSettings(firstReminder=5, fee=60, rate=8)
    session.add(ir)

    plug.keyvalue.set('invremindersettings_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_addreminder(argv):
    if plug.keyvalue.get('remindercardadded_migrated'):
        return

    session = plug.db.get_session()
    import db

    fee = db.TrainingCardType(name=u'Reminder fee', reminderFee=True, customerCanBuy=False, vat=0, account=3591, price=db.InvoiceReminderSettings()._getSettings().fee)
    db.session.add(fee)

    rate = db.TrainingCardType(name=u'Reminder rate', reminderRate=True, customerCanBuy=False, vat=0, account=8313)
    db.session.add(rate)

    a = db.session.query(plug.transaction.Account).get(fee.account)
    if not a:
        a = plug.transaction.Account(id=fee.account, name=u'Övriga fakturerade kostnader')
        db.session.add(a)

    a = db.session.query(plug.transaction.Account).get(rate.account)
    if not a:
        a = plug.transaction.Account(id=rate.account, name=u'Ränteintäkter från kortfristiga fordringar')
        db.session.add(a)

    plug.keyvalue.set('remindercardadded_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_addinvoicefee(argv):
    if plug.keyvalue.get('invoicefee_migrated'):
        return

    session = plug.db.get_session()
    import db

    fee = db.TrainingCardType(name=u'Invoice fee', invoiceFee=True, customerCanBuy=False, vat=0, account=3540, price=0)
    db.session.add(fee)

    a = db.session.query(plug.transaction.Account).get(fee.account)
    if not a:
        a = plug.transaction.Account(id=fee.account, name=u'Faktureringsavgifter')
        db.session.add(a)

    plug.keyvalue.set('invoicefee_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_invoicefee2(argv):
    if plug.keyvalue.get('invoicefee2_migrated'):
        return

    session = plug.db.get_session()
    import db

    db.InvoiceSettings()._getSettings().fee = db.TrainingCardType.getInvoiceFeeCard().price

    plug.keyvalue.set('invoicefee2_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_wbwarningperiod(argv):
    if plug.keyvalue.get('wbwarningperiod_migrated'):
        return

    session = plug.db.get_session()
    import db

    wbs = db.WorkoutBookingSettings()._getSettings()
    if wbs.warningPeriod is None:
        wbs.warningPeriod = 365

    plug.keyvalue.set('wbwarningperiod_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_warnings(argv):
    if plug.keyvalue.get('warnings_migrated'):
        return

    session = plug.db.get_session()
    import db

    try:
        members = plug.db.get_engine().execute('select id,warnings from member where warnings>0 and not removed')
    except:
        members = []

    for m in members:
        member_id = m[0]
        warnings = m[1]

        for x in range(warnings):
            db.Warning.addInternal(member_id=member_id, workoutbooking_id=None, reason=db.translate('Attendance'), commit=False)

    session.commit()

    try:
        plug.db.drop_column('member', 'warnings')
    except:
        pass

    session.commit()
    plug.keyvalue.set('warnings_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_addblockfee(argv):
    if plug.keyvalue.get('blockfee_migrated'):
        return

    session = plug.db.get_session()
    import db

    fee = db.TrainingCardType(name=u'Spärravgift gruppträning', blockFee=True, customerCanBuy=False, vat=25, account=3000, price=100)
    db.session.add(fee)

    plug.keyvalue.set('blockfee_migrated', 1)
    session.commit()

@plug.on('migrate.post')
def migrate_memberpagegcd():
    if plug.keyvalue.get('memberpagegcd_migrated'):
        return

    session = plug.db.get_session()
    import db

    val = db.hostnameForDatabase != 'metodikum.lokalsystem.se'

    s = db.Settings._getSettings()
    mp = s.memberpage or '{}'
    mp = json.loads(mp)
    mp['giftcards'] = val
    mp['discounts'] = val
    s.memberpage = db.jsonify(mp)

    plug.keyvalue.set('memberpagegcd_migrated', 1)
    session.commit()

@plug.migrate_once()
def add_options_statistics():
    import db
    session = plug.db.get_session()

    settings = db.Settings._getSettings()
    mp = settings.memberpage or '{}'
    mp = json.loads(mp)
    mp['statistics'] = True
    settings.memberpage = db.jsonify(mp)
    session.commit()

@plug.migrate_once
def migrate_sms(session):
    import db
    for sms in session.query(db.Sms):
        sms.count = plug.sms.calc_size(sms.text.text)


@plug.on('migrate.post')
def migrate_invoicetype(argv):
    if plug.keyvalue.get('invoicetype_migrated'):
        return

    session = plug.db.get_session()
    import db

    invoices = session.query(db.Invoice).filter(db.Invoice.type == None, db.Invoice.created >= plug.date.to_datetime('2016-01-01')).options(db.joinedload_all('bundle.attempts.payment'))
    for invoice in invoices:
        type = 'invoice'
        if len(invoice.bundle.attempts) and invoice.referenceNumberSequence == 'invoice':
            a = invoice.bundle.attempts[0]
            if not a.payment:
                if a.method == 'directdebit':
                    type = 'directdebit'
            elif a.payment.method == 'directdebit':
                type = 'directdebit'
        invoice.type = type

    plug.keyvalue.set('invoicetype_migrated', 1)
    session.commit()


@plug.on('migrate.post')
def migrate_invoiceamount(argv):
    if plug.keyvalue.get('invoiceamount_migrated'):
        return

    session = plug.db.get_session()
    import db

    invoices = session.query(db.Invoice).filter(db.Invoice.amount == None).options(db.joinedload_all('bundle.attempts.payment'))
    for invoice in invoices:
        invoice.setAmount()

    plug.keyvalue.set('invoiceamount_migrated', 1)
    session.commit()


@plug.migrate_once
def migrate_payment_checkoutreceipt(session):
    import db
    for receipt in session.query(db.CheckoutReceipt).filter(db.CheckoutReceipt.bundle != None).options(db.joinedload_all('bundle.attempts.payment')):
        for p in receipt.bundle.getPayments():
            p.checkoutreceipt = receipt

@plug.migrate_once
def migrate_invoicereminderdays(session):
    import db
    if not session.query(db.Module).get('InvoiceReminder').started:
        s = db.InvoiceReminderSettings._getSettings()
        s.firstReminder = 10
        s.secondReminder = 30

@plug.migrate_once
def migrate_invoicepaydatecreditdate(session):
    import db

    joinedload = db.joinedload
    joinedload_all = db.joinedload_all
    invoices = session.query(db.Invoice).filter(db.Invoice.created >= plug.date.to_datetime('2016-01-01')).options(joinedload_all('bundle.attempts.payment')).options(joinedload('bundle.attempts')).options(joinedload('bundle.attempts.payment.trainingcard')).options(joinedload_all('bundle.attempts.payment.trainingcard.resourcebookings')).options(joinedload_all('bundle.attempts.invoice')).options(joinedload_all('bundle.attempts.invoice.transactions')).options(joinedload_all('bundle.attempts.invoice.reminders'))
    for i in invoices:
        i.setPayDate()

@plug.migrate_once
def migrate_required_for_staff_fields():
    import db

    fields = db.session.query(db.Field).filter(db.Field.required_for_staff == None, db.Field.builtIn == True).all()
    for f in fields:
        if f.name in ['firstname', 'lastname', 'mail']:
            f.required_for_staff = True

@plug.migrate_once
def migrate_changeable_by_member_fields():
    import db
    session = plug.db.get_session()
    fields = session.query(db.Field).filter(db.Field.changeable_by_member == None).all()
    for f in fields:
        if f.name in ['phone', 'oldphone', 'address', 'zipCode', 'city']:
            f.changeable_by_member = True
        else:
            f.changeable_by_member = False

@plug.migrate_once
def migrate_protected_user_permission():
    import db
    pt = db.PermissionTask(id=u'Mark customer protected', description=u'Allows marking customer as protected identity')
    db.session.add(pt)

@plug.migrate_once
def migrate_protected_user_permission2():
    import db

    pt = db.session.query(db.PermissionTask).get(u'Mark customer protected')

    owner = db.session.query(db.Role).get(1)
    if owner:
        owner.tasks.append(pt)
    admin = db.session.query(db.Role).filter(db.Role.name == u'Administrator').first()
    if admin:
        admin.tasks.append(pt)


@plug.migrate_once
def migrate_gender():
    import db

    g = db.Field(table='user', type=u'select', data=u'[{"id":"male","name":"Male"},{"id":"female","name":"Female"},{"id":"other","name":"GENDER_OTHER"}]', name=u'gender', title=u'Gender', show=True, register=False, required=False, required_for_staff=False, changeable_by_member=False, builtIn=True, icon='icon fa fa-genderless')
    b = db.Field(table='user', type=u'date', data=None, name=u'birthdate', title=u'Birthdate', show=True, register=False, required=False, required_for_staff=False, changeable_by_member=False, builtIn=True, icon='icon fa fa-birthday-cake')
    db.session.add_all([g, b])

    # Set gender and birthdate based on personalCodeNumber
    users = db.session.query(db.User).filter(db.User.gender == None, db.User.personalCodeNumber != None, db.User.company == False, db.User.type == 'user')
    for u in users:
        u.gender = db.myutil.getGender(u.personalCodeNumber)
        try:
            u.birthdate = db.myutil.getBirthdate(u.personalCodeNumber)
            if u.birthdate.year < 1900:
                u.birthdate = None
        except ValueError:
            u.birthdate = None

@plug.migrate_once
def update_gender_other():
    import db

    f = db.session.query(db.Field).filter(db.Field.name == u'gender').first()
    if not f:
        return
    f.data = u'[{"id":"male","name":"Male"},{"id":"female","name":"Female"},{"id":"other","name":"GENDER_OTHER"}]'

@plug.migrate_once
def migrate_mainsite_address():
    import db

    s = db.Settings._getSettings()

    main_site = db.Site.main()
    main_site.address = s.address
    main_site.city = s.city
    main_site.zipCode = s.zipCode
    main_site.created = adminutil.getHostnameCreationTime(db.hostnameForDatabase)

@plug.migrate_once
def migrate_mainsite_cashregister():
    import db

    main_site = db.Site.main()

    for cr in db.session.query(db.CashRegister).all():
        cr.site = main_site

@plug.migrate_once
def migrate_workout_site():
    import db

    main_site = db.Site.main()

    for w in db.session.query(db.Workout).filter(db.Workout.site_id == None).all():
        w.site = main_site

@plug.migrate_once
def migrate_resource_site():
    import db

    main_site = db.Site.main()

    for r in db.session.query(db.User).filter(db.User.type == 'resource').options(db.joinedload('sites')).all():
        if not r.sites:
            r.sites = [main_site]

@plug.migrate_once
def migrate_resourcebooking_site():
    import db

    main_site = db.Site.main()

    for r in db.session.query(db.ResourceBookingCategory).options(db.joinedload('sites')).all():
        if not r.sites:
            r.sites = [main_site]

    for r in db.session.query(db.ResourceBookingService).options(db.joinedload('sites')).all():
        if not r.sites:
            r.sites = [main_site]

@plug.migrate_once
def migrate_staff_site():
    import db

    main_site = db.Site.main()

    for s in db.session.query(db.User).filter(db.User.type == 'user').options(db.joinedload('sites')).options(db.joinedload_all('roles.tasks')).all():
        if s.hasPermission('Admin') and not s.sites:
            s.sites = [main_site]

@plug.migrate_once
def migrate_workouttype_site():
    import db

    main_site = db.Site.main()

    for w in db.session.query(db.WorkoutType).options(db.joinedload('sites')).all():
        if not w.sites:
            w.sites = [main_site]

@plug.migrate_once
def migrate_trainingcardtype_site():
    import db

    main_site = db.Site.main()

    for t in db.session.query(db.TrainingCardType).filter((db.TrainingCardType.entry == True) | (db.TrainingCardType.workout == True) | (db.TrainingCardType.resourcebookingservice_id != None)).options(db.joinedload('sites')).all():
        if not t.sites:
            t.sites = [main_site]

@plug.migrate_once
def migrate_homesite():
    import db

    main_site = db.Site.main()

    for u in db.session.query(db.User).filter(db.User.homesite_id == None, db.User.type == 'user').all():
        u.homesite = main_site

@plug.migrate_once
def migrate_usersession_site():
    import db

    main_site = db.Site.main()

    for u in db.session.query(db.UserSession).filter(db.UserSession.site_id == None).all():
        u.site = main_site

@plug.migrate_once
def migrate_accountingsettings_20200323():
    import db

    s = db.AccountingSettings._getSettings()
    if not s:
        s = db.AccountingSettings(vat25account=2610, vat12account=2620, vat6account=2630)
        db.session.add(s)

    s.registered_for_ftax = True


@plug.migrate_once
def migrate_wbs_entryduration():
    import db

    value = 2
    if db.hostnameForDatabase == 'boostersund.gymsystem.se':
        value = 500

    db.session.query(db.WorkoutBookingSettings).first().entryDuration = value

@plug.migrate_once
def migrate_workoutcategoryorder():
    import db

    categories = db.session.query(db.WorkoutCategory).order_by(db.WorkoutCategory.name).all()
    for i, category in enumerate(categories):
        category.order = i

@plug.migrate_once
def migrate_workoutcategory_site():
    import db

    main_site = db.Site.main()

    for w in db.session.query(db.WorkoutCategory).options(db.joinedload('sites')).all():
        if not w.sites:
            w.sites = [main_site]

@plug.migrate_once
def migrate_workschedule_site():
    import db

    main_site = db.Site.main()

    for ws in db.session.query(db.WorkSchedule).options(db.joinedload('site')):
        if not ws.site:
            ws.site = main_site

@plug.migrate_once
def migrate_resourcebookingb_site():
    import db

    main_site = db.Site.main()

    for rb in db.session.query(db.ResourceBooking).options(db.joinedload('site')):
        if not rb.site:
            rb.site = main_site

@plug.migrate_once
def migrate_workoutcategoryshow():
    import db

    gt = db.session.query(db.WorkoutCategory).filter(db.WorkoutCategory.name == db.translate('Group workout')).first()
    if gt:
        gt.show = True

@plug.migrate_once
def migrate_rbextendedinfo():
    import db

    nameMap = {}

    for rbs in db.session.query(db.ResourceBookingService).filter(db.ResourceBookingService.extendedInfo != None).all():
        e = json.loads(rbs.extendedInfo)
        for q in e:
            nameMap[q['id']] = q['title']
            q['name'] = q['title']
            del q['title']
            del q['id']
            if q.get('options'):
                q['data'] = lmap(lambda x: x.get('name'), q['options'])
                del q['options']
        rbs.extendedInfo = db.jsonify(e)
        for rb in db.session.query(db.ResourceBooking).filter(db.ResourceBooking.extendedInfo != None, db.ResourceBooking.service == rbs).all():
            ex = json.loads(rb.extendedInfo)
            for key in ex.keys():
                if nameMap.get(key):
                    newKey = nameMap[key]
                    ex[newKey] = ex[key]
                    if key != newKey:
                        del ex[key]
                    if type(ex[newKey]) == list:
                        ex[newKey] = lmap(lambda x: x and x.get('name'), ex[newKey])
                    elif type(ex[newKey]) == dict:
                        ex[newKey] = ex[newKey] and ex[newKey].get('name')

            rb.extendedInfo = db.jsonify(ex)
        nameMap = {}

@plug.migrate_once(version=2, priority=20)
def fix_valuecard_image(session):
    ct = session.query(db.TrainingCardType).filter(db.TrainingCardType.type == 'valuecard').first()
    if ct.imagekey:
        try:
            plug.file.load_by_key(ct.imagekey)
            return
        except Exception:  # wrong file
            pass

    ct.imagekey = plug.file.get_file_object_by_name(u'Valuecard', origin_type='product:inbuilt')['key']

@plug.migrate_once(version=3)
def trainingcard_type(session):
    import db

    for t in session.query(db.TrainingCardType):
        t.setType()

    for t in session.query(db.TrainingCard).join(db.TrainingCardType):
        if t.cardtype and t.type != t.cardtype.type:
            t.type = t.cardtype.type

@plug.migrate_once
def courses_price():
    import db
    if plug.chain.get_chain() not in ['korpen', 'korpentest']:
        db.session.query(db.Module).get('Courses').price = '99'

@plug.migrate_once
def korpen_global_login():
    if plug.chain.get_chain() in ['korpen', 'korpentest']:
        plug.korpen.add_korpen_global_admin()

@plug.migrate_once
def permission_workoutcategory():
    import db
    for wc in db.session.query(db.WorkoutCategory).filter(db.WorkoutCategory.permission == None):
        wc.permission = u'Schedule handling'

@plug.on('migrate.post')
def korpen_language():
    import db
    if plug.chain.get_chain() in ['korpen', 'korpentest']:
        plug.korpen.apply_translations()


@plug.migrate_once(priority=5)
def set_default_site(session):
    if db.Module.has('MultiSite'):
        return

    for t in session.query(db.TrainingCardType):
        if not t.sites:
            t.sites = [db.Site.main()]

@plug.migrate_once
def fieldunique():
    import db
    fields = db.session.query(db.Field).filter(db.Field.table == 'user').all()
    for f in fields:
        f.unique = f.name in ['memberNumber', 'mail', 'personalCodeNumber']

@plug.on('migrate.post')
def brucepassmethod():
    with plug.db.commit_block() as session:
        pm = session.query(db.PaymentMethod).get('brucepass')
        if pm:
            if not pm.external:
                pm.external = True
        else:
            pm = db.PaymentMethod(id='brucepass', name=u'Brucepass', builtIn=True, imageSrc='/assets/img/brucepass.png', active=True, external=True, modules='Brucepass', checkout=False, create=False, change=False, webshop=False, refund=False, periodic=False, markAsPaid=False, refill=False, account=1930, apikey='f411d90e24b7466d90259124e52e04cc8a9b779f560e9765ede68c17f29f24bf')
            session.add(pm)

@plug.migrate_once
def requiremembershipforkorpen():
    import db
    if plug.chain.get_chain() in ['korpen', 'korpentest'] and db.hostnameForDatabase != 'korpenriks.zoezi.se':
        db.Settings._getSettings().requireMembership = True

@plug.migrate_once
def getuserdatapt():
    import db
    pt = db.PermissionTask(id=u'Get user data', description=u'Allows getting personal user data for a customer')
    db.session.add(pt)
    owner = db.session.query(db.Role).get(1)
    if owner:
        owner.tasks.append(pt)

@plug.migrate_once
def apiloguser(session):
    exist_users = set(lmap(itemgetter(0), session.query(db.User.id).all()))
    for a in session.query(db.ApiLog):
        if a.request:
            try:
                r = json.loads(a.request)
                if r.get('user') and r['user']['id'] in exist_users:
                    a.user_id = r['user']['id']
            except:
                pass

@plug.migrate_once
def default_keep_user_time():
    import db
    db.Settings()._getSettings().keep_userdata_time = 12

@plug.migrate_once
def remove_izettle():
    import db
    c1 = db.session.query(db.Payment).filter(db.Payment.method == 'izettle').count()
    c2 = db.session.query(db.PaymentAttempt).filter(db.PaymentAttempt.method == 'izettle').count()
    c3 = db.session.query(plug.transaction.Transaction).filter(plug.transaction.Transaction.method == 'izettle').count()
    if c1 == 0 and c2 == 0 and c3 == 0:
        izettle = db.session.query(db.PaymentMethod).filter(db.PaymentMethod.id == 'izettle').first()
        if izettle:
            db.session.delete(izettle)

@plug.migrate_once
def setcardpaymentpayoutaccounts():
    import db
    cps = db.session.query(db.CardPaymentSettings).first()
    cps.accountingAccount = 1930
    cps.transactionCostAccount = 6570

@plug.migrate_once
def renameunknownpaymentmethod():
    import db
    pm = db.session.query(db.PaymentMethod).get('unknown')
    pm.name = u'Payment method is selected later'

@plug.migrate_once
def setpaymethodfortrainingcardtypeauto():
    import db
    trainingCards = db.session.query(db.TrainingCard).join(db.TrainingCardType).options(db.joinedload('cardtype')).filter(db.TrainingCardType.auto).all()
    for tc in trainingCards:
        payMethod = tc.getPaymentMethod()
        if payMethod in ['invoice', 'directdebit', 'stripe']:
            tc.payMethod = payMethod

@plug.migrate_once
def invoicereminderparentid():
    import db
    irModule = db.session.query(db.Module).get('InvoiceReminder')
    irModule.parent_id = 'Invoice'

@plug.migrate_once
def setdefaultinqueuevalue():
    import db
    for w in db.session.query(db.Workout).options(db.joinedload('bookings')):
        for i, wb in enumerate(w.bookings):
            wb.inQueue = w.space and i >= w.space
            wb.sentQueueMessage = False

@plug.migrate_once
def newinboundvataccount():
    a = plug.transaction.schema.Account(id=2640, name=u'Ingående moms')
    if db.session.query(plug.transaction.schema.Account).get(a.id):
        return
    db.session.add(a)

@plug.migrate_once
def set_login_key():
    import db
    users = db.session.query(db.User).filter(db.User.removed == None, db.User.login_key == None, db.User.mail != None)
    for user in users:
        user.login_key = plug.string.unicode(user.mail)

@plug.migrate_once
def mail_field_not_unique():
    import db
    db.session.query(db.Field).filter(db.Field.table == 'user', db.Field.name == u'mail').first().unique = False

@plug.migrate_once
def add_login_key_field():
    import db
    f = db.Field(table='user', type=u'text', name=u'login_key', title=u'Username', show=True, register=True, required=True, required_for_staff=True, changeable_by_member=True, builtIn=True, icon='icon glyphicon glyphicon-user', unique=True)
    db.session.add(f)

@plug.migrate_once
def allow_changemailetc():
    import db
    db.session.query(db.Field).filter(db.Field.table == 'user', db.Field.name == u'mail').first().changeable_by_member = True
    db.session.query(db.Field).filter(db.Field.table == 'user', db.Field.name == u'firstname').first().changeable_by_member = True
    db.session.query(db.Field).filter(db.Field.table == 'user', db.Field.name == u'lastname').first().changeable_by_member = True

@plug.migrate_once
def add_password_field():
    import db
    f = db.Field(table='user', type=u'password', name=u'password', title=u'Password', show=True, register=True, required=True, required_for_staff=False, changeable_by_member=True, builtIn=True, icon='icon glyphicon glyphicon-asterisk', unique=False)
    db.session.add(f)

@plug.migrate_once
def change_mail_type():
    import db
    db.session.query(db.Field).filter(db.Field.table == 'user', db.Field.name == u'mail').first().type = u'email'

@plug.migrate_once()
def temporarily_hide_module_fitnesscollection():
    import db
    fcModule = db.session.query(db.Module).get('FitnessCollection')
    if not fcModule:
        return
    fcModule.available = False

@plug.migrate_once()
def responsible_type():
    import db
    f = db.session.query(db.Field).filter(db.Field.name == u'responsible', db.Field.table == 'user', db.Field.builtIn == True).first()
    if f:
        f.type = u'customer'

@plug.migrate_once()
def personalcodeicon():
    import db
    f = db.session.query(db.Field).filter(db.Field.name == u'personalCodeNumber', db.Field.table == 'user', db.Field.builtIn == True).first()
    if f:
        f.icon = u'icon glyphicon glyphicon-barcode'

@plug.migrate_once()
def responsible_icon():
    import db
    f = db.session.query(db.Field).filter(db.Field.name == u'responsible', db.Field.table == 'user', db.Field.builtIn == True).first()
    if f:
        f.icon = u'icon glyphicon glyphicon-eye-open'

@plug.migrate_once()
def invoicemail_type():
    import db
    f = db.session.query(db.Field).filter(db.Field.name == u'invoiceMail', db.Field.table == 'user', db.Field.builtIn == True).first()
    if f:
        f.type = u'email'
        f.register = False
        f.changeable_by_member = True

@plug.migrate_once(version=2)
def setconsenterrortodoflag():
    import db, re
    todos = db.session.query(db.ToDo).filter(db.ToDo.todo == 'Bankgiro: medgivandefel').all()
    for todo in todos:
        todo.consentError = True
        personalCodeNumber = re.search('Personnummer: (.*)<br/>', todo.description)
        todo.personalCodeNumber = personalCodeNumber.group(1) if personalCodeNumber else None


def password_unique():
    import db
    f = db.session.query(db.Field).filter(db.Field.name == u'password', db.Field.table == 'user', db.Field.builtIn == True).first()
    if f:
        f.unique = False

@plug.migrate_once()
def stripemethodforstaff():
    import db
    stripe = db.session.query(db.PaymentMethod).get('stripe')
    stripe.checkout = True
    stripe.create = True
    stripe.change = True

@plug.migrate_once
def migrate_remove_user_permission():
    import db
    pt = db.PermissionTask(id=u'Remove customer', description=u'Allows removing customers')
    db.session.add(pt)

    owner = db.session.query(db.Role).get(1)
    if owner:
        owner.tasks.append(pt)
    admin = db.session.query(db.Role).filter(db.Role.name == u'Administrator').first()
    if admin:
        admin.tasks.append(pt)

@plug.migrate_once
def pcodecanchange():
    import db
    f = db.session.query(db.Field).filter(db.Field.name == u'personalCodeNumber', db.Field.table == 'user', db.Field.builtIn == True).first()
    f.changeable_by_member = True

@plug.migrate_once
def hide_rbdooraccessmodule_for_korpen():
    rbDoorAccessModule = db.session.query(db.Module).get('RBDoorAccess')
    if plug.korpen.is_korpen() and rbDoorAccessModule is not None:
        rbDoorAccessModule.available = False

@plug.migrate_once
def disable_infozoezise_mailings():
    import db
    zoeziAB = db.User.getZoezi()
    if zoeziAB is not None:
        plug.mailing.set_mailing_options(zoeziAB, mail=False, sms=False, commit=True)

@plug.migrate_once
def add_image_field():
    import db
    f = db.Field(table='user', type=u'image', name=u'image', title=u'Image', show=True, register=False, required=False, required_for_staff=False, changeable_by_member=True, builtIn=True, icon=None, unique=False)
    db.session.add(f)

@plug.migrate_once
def register_hide_password():
    import db
    pwField = db.session.query(db.Field).filter(db.Field.name == u'password').first()
    if pwField:
        pwField.register = False

@plug.migrate_once
def migrate_bankmarkaspaid():
    import db
    if db.Settings._getSettings().servicebureau:
        db.session.query(db.PaymentMethod).get('bank').markAsPaid = False

@plug.migrate_once
def teamsportsmodule_available_for_korpen():
    teamsportsModule = db.session.query(db.Module).get('TeamSports')
    if plug.korpen.is_korpen() and teamsportsModule is not None:
        teamsportsModule.available = True

@plug.migrate_once
def addproxyappsettings():
    import db
    if db.session.query(db.ProxyAppSettings).count() == 0:
        s = db.ProxyAppSettings()
        db.session.add(s)

@plug.migrate_once
def set_queuegiveback_for_postprocessed():
    import db
    workouts = db.session.query(db.Workout).filter(db.Workout.postProcessed == True, db.Workout.queueGiveback == False).all()
    for wo in workouts:
        wo.queueGiveback = True

@plug.migrate_once(priority=-5, version=8)
def save_image_from_sourcecode():
    static_images = [
        ('/assets/img/bank.jpg', u'Bank'),
        ('/assets/img/bgc.png', u'Autogiro'),
        ('/assets/img/cash.png', u'Cash'),
        ('/assets/img/creditcard.png', u'Credit card'),
        ('/assets/img/invoice.png', u'Invoice'),
        ('/assets/img/valuecard.png', u'Valuecard'),
        ('/assets/img/customerloss.png', u'customerloss'),
        ('/assets/img/profile_resource.png', u'Default product')
    ]

    for path, name in static_images:
        if plug.file.get_file_object_by_name(name, origin_type='product:inbuilt'):
            continue
        plug.file.save(path, name=name, storage='link', origin_type='product:inbuilt')

    # Save Korpen's images (Hide it for now, waiting for YES from Korpen)
    # if plug.korpen.is_korpen():
    #     plug.file.save('/assets/img/korpen_medlemskort.jpg', name=u'Medlemskort', storage='link', origin_type='product:inbuilt')
    #     plug.file.save('/assets/img/korpen_presentkort.jpg', name=u'Presentkort', storage='link', origin_type='product:inbuilt')
    #     plug.file.save('/assets/img/korpen_traingskort_allmant.jpg', name=u'Traingskort allmant', storage='link', origin_type='product:inbuilt')

@plug.migrate_once(priority=15)
def change_image_type_20190111(session):
    File = plug.db.get_model('file')
    f = session.query(File).filter(File.data == b'/assets/img/valuecard.png', File.storage == 5).first()
    if f:
        f.origin_id = plug.json.Link('product:inbuilt', 0).get_uid()

    f = session.query(File).filter(File.data == b'/assets/img/zoezi_icon.png', File.storage == 5).first()
    if f:
        f.origin_id = plug.json.Link('product:inbuilt', 0).get_uid()


@plug.migrate_once(priority=20)
def change_autogiro_image_20190411(session):
    method = session.query(db.PaymentMethod).get('directdebit')
    if not method.imagekey:
        method.imagekey = plug.file.get_file_object_by_name(u'Autogiro', origin_type='product:inbuilt')['key']
    method = session.query(db.PaymentMethod).get('valuecard')
    if not method.imagekey:
        method.imagekey = plug.file.get_file_object_by_name(u'Valuecard', origin_type='product:inbuilt')['key']

@plug.on('migrate.data')
def confirmed_customerloss():
    session = plug.db.get_session()
    Account = plug.db.get_model('account')
    account_id = 6351
    if session.query(Account).get(account_id):
        return
    session.add(Account(id=account_id, name=u'Konstaterad kundförlust'))
    session.commit()


@plug.on('migrate.data')
def add_premission():
    session = plug.db.get_session()

    def add(id, description, owner=False, admin=False):
        if session.query(db.PermissionTask).get(id):
            return
        p = db.PermissionTask(id=id, description=description)
        session.add(p)
        if owner or admin:
            p.addToRoles(owner=owner, admin=admin)
        session.commit()

    add(u'Download customer register', u'Allow staff to download customers to excel', True, True)
    add(u'Show system cost', u'Allows showing system cost', True, False)


@plug.migrate_once
def change_address_field_type():
    f = db.session.query(db.Field).filter(db.Field.name == u'address', db.Field.builtIn == True).first()
    f.type = u'textarea'
    db.session.commit()

@plug.migrate_once
def update_products_and_trainingcards_showSelfCheckout():
    tc = db.session.query(db.TrainingCardType)
    # Ensure that products don't appear in selfcheckout that are not supposed to
    for card in tc:
        card.showSelfCheckout = card.customerCanBuy
        if card.resourcebookingservice_id is not None:
            card.showSelfCheckout = False

@plug.migrate_once
def korpenuserhidden_20190920():
    import db
    if not plug.korpen.is_korpen():
        return
    riks = db.session.query(db.User).filter(db.User.type == 'user', db.User.mail == 'info@korpen.se').first()
    if riks:
        riks.type = 'hiddenuser'

@plug.migrate_once
def korpensetting_20220620():
    import db
    if not plug.korpen.is_korpen():
        return
    s = db.WorkoutBookingSettings._getSettings()
    s.allowCreateWorkoutType = False

@plug.migrate_once
def migrate_checked_in_members_to_table():
    services = db.session.query(db.ResourceBookingService).filter(db.ResourceBookingService.active == True, db.ResourceBookingService.continuousBooking == True)
    services = lfilter(lambda s: s.checked_in_members_old is not None, services)

    for service in services:
        for item in service.checked_in_members_old:
            contRb = db.ContinuousResourceBooking(user_id=item.get('id'), service_id=service.id, time=item.get('time'), staff_id=item.get('staff'))
            db.session.add(contRb)

@plug.migrate_once
def make_family_default_visible():
    import db
    s = db.Settings._getSettings()
    memberpage = json.loads(s.memberpage) if s.memberpage is not None else {}
    memberpage['family'] = True
    s.memberpage = db.jsonify(memberpage)

@plug.migrate_once
def gs344920191119():
    if plug.chain.get_chain() != 'korpen':
       return

    plug.webhook.schema.WebhookEndpoint.addInternal(dict(
        name=u'korpen.se',
        url='https://kit-webhooklive.azurewebsites.net/api/HttpTrigger1?code=7nqFurU3gzhUMaZGGvkZVve4tJ/3IPeMr4arxFPG7hz8543NDIpIUg==', secret='5234857asdFJADFN##!',
        active=True,
        events=['korpen.activity', 'korpen.club', 'korpen.course', 'korpen.news', 'korpen.competition']
    ), performer=None)

@plug.migrate_once
def account_to_accountingsettings_20191125():
    ''' Move accounting accout from InvoiceSettings to AccountingSettings '''
    import db
    asettings = db.AccountingSettings._getSettings()
    asettings.account = db.InvoiceSettings._getSettings().account

@plug.migrate_once
def set_default_continuousresourcebooking_site():
    import db
    crBookings = db.session.query(db.ContinuousResourceBooking).filter(db.ContinuousResourceBooking.endTime == None).all()
    for crb in crBookings:
        if crb.site is not None:
            continue
        staffSites = crb.staff.sites
        crb.site = staffSites[0] if len(staffSites) else db.Site.main()
        db.session.flush()

@plug.on('migrate.post')
def add_proxyapp_inputs():
    import db
    now = plug.date.now()
    for port in [7, 11, 12, 13, 15, 16, 18]:
        if db.ProxyAppInput.getInternal(filter=(db.ProxyAppInput.port == port)):
            continue
        i = db.ProxyAppInput(created=now, port=port)
        db.session.add(i)
        db.session.flush()

    db.session.commit()

@plug.migrate_once
def kontaktperson_korpen_riks_to_foreningens_kontaktperson_20200302():
    import db
    if not plug.korpen.is_korpen():
        return
    contact_person = db.session.query(db.RoleChange).filter(db.RoleChange.rolename == u'Kontaktperson Korpen Riks', db.RoleChange.toDate == None).first()
    if contact_person:
        contact_person.rolename = u'Föreningens kontaktperson'
        korpen_setting = plug.setting.get('korpen') or {}
        roles = korpen_setting.get('roles', {})
        if u'Kontaktperson Korpen Riks' in roles.keys():
            roles[u'Föreningens kontaktperson'] = roles.pop(u'Kontaktperson Korpen Riks')
            plug.setting.set('korpen', korpen_setting)

@plug.migrate_once
def set_old_invoice_generateCode_false_20200505():
    import db
    invoices = db.session.query(db.Invoice).all()
    for invoice in invoices:
        invoice.generateCode = False

@plug.migrate_once
def replace_korpen_old_logo_20200610():
    if not plug.korpen.is_korpen():
        return
    logo1 = plug.file.save('/assets/img/korpen.jpg', name='korpen.jpg', storage='link', origin_type='logo')
    plug.setting.update('logo', {'1': logo1})
    logo2 = plug.file.save('/assets/img/korpen_vit.png', name='korpen_vit.png', storage='link', origin_type='logo')
    plug.setting.update('logo', {'2': logo2})

@plug.migrate_once
def zoezi_company_20200505():
    import db
    zoezi = db.session.query(db.User).filter(db.User.removed == None, db.User.zoezi).first()
    if zoezi:
        zoezi.company = True

@plug.migrate_once
def sync_korpen_info_20200522():
    import db
    if not plug.korpen.is_korpen():
        return

    settings = db.Settings._getSettings()
    sync = {}
    for field in {'visit_address', 'visit_zipCode', 'visit_city', 'homepage'}:
        if getattr(settings, field):
            sync[field] = getattr(settings, field)
    if sync:
        sync['hostname'] = plug.db.get_hostname()
        plug.sync.sync_customer_system(sync)

@plug.migrate_once
def add_allowInvoiceAt16_field_20201008():
    import db
    f = db.Field(table='user', type=u'checkbox', name=u'allowInvoiceAt16', title=u'Allow invoice purchases from 16', show=True, register=False, required=False, required_for_staff=False, changeable_by_member=False, builtIn=True, icon=None, unique=False)
    db.session.add(f)

@plug.migrate_once
def add_einvoice_consent_permissiontask_20201127():
    import db

    if not db.Module.has('EInvoice'):
        return

    if db.session.query(db.PermissionTask).get(u'EInvoice consent handling'):
        return

    pt = db.PermissionTask(id=u'EInvoice consent handling', created=plug.date.now(), description=u'Allows adding and removing EInvoice consents', module_id='EInvoice', builtIn=True)
    db.session.add(pt)
    db.session.flush()

    roles = db.session.query(db.Role).outerjoin(db.role_permissiontask).filter(db.role_permissiontask.c.permissiontask_id == u'Economy').all()
    for role in roles:
        role.tasks.append(pt)

@plug.pubsub.subscribe_decorator('module.status.einvoice')
def onTravelBillStatusChange(started):
    import db
    if started:

        if db.session.query(db.PermissionTask).get(u'EInvoice consent handling'):
            return

        pt = db.PermissionTask(id=u'EInvoice consent handling', created=plug.date.now(), description=u'Allows adding and removing EInvoice consents', module_id='EInvoice', builtIn=True)
        db.session.add(pt)
        db.session.flush()

        roles = db.session.query(db.Role).outerjoin(db.role_permissiontask).filter(db.role_permissiontask.c.permissiontask_id == u'Economy').all()
        for role in roles:
            role.tasks.append(pt)

        db.session.commit()

@plug.migrate_once
def set_child_fields_20210325():
    import db

    firstname = db.session.query(db.Field).filter(db.Field.table == 'user', db.Field.name == u'firstname', db.Field.builtIn).first()
    firstname.child = True
    firstname.required_child = True

    lastname = db.session.query(db.Field).filter(db.Field.table == 'user', db.Field.name == u'lastname', db.Field.builtIn).first()
    lastname.child = True
    lastname.required_child = True

    mail = db.session.query(db.Field).filter(db.Field.table == 'user', db.Field.name == u'mail', db.Field.builtIn).first()
    mail.child = True
    mail.required_child = False

@plug.migrate_once
def variantsintables_20201127():
    import db, json, copy

    with_barcode = db.session.query(db.TrainingCardType).filter(db.TrainingCardType.barcode != None).all()
    barcodes = lmap(lambda tc: tc.barcode, with_barcode)

    for tc in with_barcode:
        def get_duplicates():
            dups = []
            for x in with_barcode:
                if x != tc and x.barcode == tc.barcode:
                    dups.append(x)
            return dups

        dups = get_duplicates()
        for dup in dups:
            dup.barcode = None
    db.session.flush()

    main_site = db.Site.main()
    cardtypes = lfilter(lambda p: p.isProduct() and not p.valuecard and not p.misc and not p.reminderFee and not p.blockFee and not p.discount and not p.rounding and not p.invoiceFee and not p.reminderRate, db.session.query(db.TrainingCardType).all())
    for ct in cardtypes:
        has_variants = False
        if ct._json:
            variants = ct._json.get('variants')
            if variants:
                for v in variants:
                    pv = db.ProductVariant(product=ct, name=v['name'], barcode=ct.barcode)
                    db.session.add(pv)
                    ps = db.ProductStock(variant=pv, site=main_site, stock=v.get('stock'))
                    db.session.add(ps)
                    has_variants = True
        if not has_variants:
            pv = db.ProductVariant(product=ct, name=None, barcode=ct.barcode)
            db.session.add(pv)
            ps = db.ProductStock(variant=pv, site=main_site, stock=ct.stock)
            db.session.add(ps)

    # TrainingCardType.stock has been converted to a computed value (hybrid property)
    # The following code tries to read the old stock value. If it does so, it uses the .stock setter to set the value
    try:
        rows = db.engine.execute('select id,stock from trainingcardtype where stock is not null')
        for row in rows:
            if not myutil.find_where(cardtypes, dict(id=row[0])):
                ct = db.session.query(db.TrainingCardType).get(row[0])
                ct.stock = row[1]
                print('Fixing stock for ' + str(ct.id))
    except:
        # This will fail if there is no stock column - which is ok
        pass

@plug.migrate_once
def add_homesite():
    import db
    f = db.Field(table='user', type=u'site', name=u'homesite_id', title=u'Homesite', show=True, register=False, required=True, required_for_staff=True, changeable_by_member=False, builtIn=True, icon='icon glyphicon glyphicon-home', unique=False)
    db.session.add(f)

@plug.migrate_once
def phonetype_20210514():
    phone = db.session.query(db.Field).filter(db.Field.name == u'phone', db.Field.builtIn).first()
    if phone:
        phone.type = u'phone'

@plug.migrate_once
def default_payment_site():
    payments = db.session.query(db.Payment).filter(db.Payment.site_id == None).all()

    site_id = db.Site.main().id
    for p in payments:
        p.site_id = site_id

@plug.migrate_once
def homesite_20210529():
    nohs = db.session.query(db.User).filter(db.User.removed == None, db.User.type == 'user', db.User.homesite_id == None)
    for u in nohs:
        u.homesite_id = db.Site.main().id

@plug.migrate_once
def add_group_20210601():
    import db
    f = db.Field(table='user', type=u'usergroups', name=u'groups', title=u'Groups', show=True, register=False, required=False, required_for_staff=False, changeable_by_member=False, builtIn=True, icon='icon glyphicon glyphicon-th', unique=False)
    db.session.add(f)

@plug.migrate_once
def add_systemtag_permissiontask_2021_08_30():
    import db
    pt = db.PermissionTask(id=u'System tag handling', created=plug.date.now(), description=u'Allows adding new system tags', builtIn=True)
    db.session.add(pt)
    db.session.flush()
    owner = db.session.query(db.Role).get(1)
    if owner:
        owner.tasks.append(pt)

@plug.migrate_once
def move_use_zoezi_cert_setting_20210919():
    use_zoezi_cert = True
    if db.Module.has('Contract') or db.Module.has('BankIdLogin'):
        use_zoezi_cert = plug.setting.get_system_settings('bankid.use_zoezi_cert')
    db.Settings._getSettings().use_zoezi_cert = use_zoezi_cert

@plug.migrate_once
def zoezi_my_business_setting_20211019():
    flex = db.Settings._getSettings().vueMemberPage
    db.Settings._getSettings().zoeziMyBusiness = 'flex' if flex else 'disabled'

@plug.migrate_once
def add_showresources_permissiontask_2021_10_26():
    import db
    pt = db.PermissionTask(id=u'Show resources', created=plug.date.now(), description=u'Allows showing resources', builtIn=True)
    db.session.add(pt)
    db.session.flush()
    owner = db.session.query(db.Role).get(1)
    if owner:
        owner.tasks.append(pt)

# @plug.migrate_once
# def bookers_to_userconnections_20211123():
#     import db
#     for user in db.session.query(db.User).options(db.joinedload('canBookFor')):
#         for u2 in user.canBookFor:
#             c = db.session.query(db.UserConnection).filter(db.UserConnection.left_id == user.id, db.UserConnection.right_id == u2.id).first()
#             if not c:
#                 c = db.UserConnection(left=user, right=u2)
#                 db.session.add(c)
#             c.book = True
    

@plug.migrate_once
def set_rbcat_order_2021_12_06():
    import db
    cats = db.session.query(db.ResourceBookingCategory).filter(db.ResourceBookingCategory.order == None).all()
    for c in cats:
        c.order = c.id


@plug.migrate_once
def mark_old_freezes_20220127(session):
    future = plug.date.next_month(plug.date.today(), 31) + plug.date.day
    session.query(db.Freeze).filter(db.Freeze.fromDate < future).update({db.Freeze.old: True})

# @plug.on('migrate.data', priority=-10)
# def create_nps_addon():
# 	plug.addon.create_addon(
# 		id=u'NPS',
# 		name=u'Kundundersökning',
# 		category='staff',
#         internal=True
# 	)

# @plug.migrate_once
# def start_nps():
#     plug.addon.add_addon('NPS', exist_ok=True)

@plug.migrate_once
def warning_workoutbooking_to_workout():
    for w in db.session.query(db.Warning).filter(db.Warning.workoutbooking_id != None):
        w.workout_id = w.workoutbooking.workout_id

@plug.migrate_once
def methods_set_to_json_2022_04_06():
    if not plug.db.has_column('trainingcardtype', 'methods'):
        return
    for id, methods in db.engine.execute(db.text('select id,methods from trainingcardtype where methods')):
        db.session.query(db.TrainingCardType).get(id).methods = methods.split(',')

@plug.migrate_once
def discount_conditions_20220606():
    for tc in db.session.query(db.TrainingCardType).filter(db.TrainingCardType.discount).all():
        if not tc.discount_condition:
            dc = {}
            dc['trainingcards'] = True
            dc['memberships'] = True
            dc['punchcards'] = True
            dc['products'] = True
            dc['courses'] = True
            dc['services'] = True
            dc['period_limit'] = None
            tc.discount_condition = dc

@plug.migrate_once
def settings_set_keep_userdata_time():
    db.session.query(db.Settings).filter(db.Settings.keep_userdata_time == None).update({db.Settings.keep_userdata_time: 12})

@plug.migrate_once
def set_zoezi_brand_20221108():
    s = db.Settings._getSettings()
    if s.brand != 'Zoezi':
        s.brand = 'Zoezi'
