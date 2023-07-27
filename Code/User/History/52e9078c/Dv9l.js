import {createRouter, createWebHashHistory} from 'vue-router';
import { Userpilot } from 'userpilot';

// FIXME: Less boilerplate would be nice
const routes = [
    {
        path: '/',
        name: '/',
        exact: true,
        component: () => import('./components/Empty.vue'),
        alias: '/dashboard',
        meta: {
            breadcrumb: [{ label: 'Startpage' }],
            angular: true
        },
    },
    {
        path: '/get-started',
        name: '/get-started',
        exact: true,
        meta: {
            breadcrumb: [{ label: 'Get started' }],
            angular: true
        },
    },
    {
        path: '/customers/active',
        name: '/customers/active',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Customers', label: 'Active memberships' }],
            angular: true
        },
    },
    {
        path: '/customers/search',
        name: '/customers/search',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Customers', label: 'Search' }],
            angular: true
        },
    },
    {
        path: '/customers/add',
        name: '/customers/add',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Customers', label: 'Add' }],
            angular: true,
            command: true
        },
    },
    {
        path: '/customer/criminalrecordexcerpt',
        name: '/customer/criminalrecordexcerpt',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Customers', label: 'Criminal record excerpt' }],
            angular: true
        }
    },
    {
        path: '/customers/import',
        name: '/customers/import',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Customers', label: 'Import' }],
            angular: true
        }
    },
    {
        path: '/customers/remove',
        name: '/customers/remove',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Customers', label: 'Remove' }],
            angular: true
        }
    },
    {
        path: '/customer/show/:id',
        name: '/customer/show',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Customers', label: 'Show' }],
            angular: true
        }
    },
    {
        path: '/customer/journal/:id',
        name: '/customer/journal',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Customers', label: 'Journal' }],
            angular: true
        }
    },
    {
        path: '/staff/list',
        name: '/staff/list',
        exact: true,
        component: () => import('./components/StaffList.vue'),
        meta: {
            breadcrumb: [{ parent: 'Staff', label: 'Sök' }]
        }
    },
    {
        path: '/staff/add',
        name: '/staff/add',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Staff', label: 'Add' }],
            angular: true,
            command: true
        }
    },
    {
        path: '/staff/show/:id',
        name: '/staff/show',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Staff', label: 'Show' }],
            angular: true
        }
    },
    {
        path: '/groups',
        name: '/groups',
        exact: true,
        meta: {
            breadcrumb: [{ label: 'Groups' }],
            angular: true
        }
    },
    {
        path: '/todo/mylist',
        name: '/todo/mylist',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'ToDo', label: 'Mina uppgifter' }],
            angular: true
        }
    },
    {
        path: '/todo/all',
        name: '/todo/all',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'ToDo', label: 'Alla uppgifter' }],
            angular: true
        }
    },
    {
        path: '/todo/add',
        name: '/todo/add',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'ToDo', label: 'Add' }],
            angular: true,
            command: true
        }
    },
    {
        path: '/schedule/add',
        name: '/schedule/add',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Schedule', label: 'Add' }],
            angular: true,
            command: true
        }
    },
    {
        path: '/schedule/change',
        name: '/schedule/change',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Schedule', label: 'Change' }],
            angular: true
        }
    },
    {
        path: '/schedule/templates',
        name: '/schedule/templates',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Schedule', label: 'Templates' }],
            angular: true
        }
    },
    {
        path: '/schedule/template/:templateId',
        name: '/schedule/template',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Schedule', label: 'Template' }],
            angular: true
        }
    },
    {
        path: '/schedule/workouttypes',
        name: '/schedule/workouttypes',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Schedule', label: 'Settings' }],
            angular: true
        }
    },
    {
        path: '/schedule/show/:categoryId',
        name: '/schedule/show',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Schedule', label: 'Show' }],
            angular: true
        }
    },
    {
        path: '/schedule/all',
        name: '/schedule/all',
        exact: true,
        component: () => import('./views/AllActivities.vue'),
        meta: {
            breadcrumb: [{ parent: 'Schedule', label: 'All' }]
        }
    },
    {
        path: '/bookings',
        name: '/bookings',
        exact: true,
        meta: {
            breadcrumb: [{ label: 'Workout booking' }],
            angular: true
        }
    },
    {
        path: '/courses',
        name: '/courses',
        exact: true,
        meta: {
            breadcrumb: [{ label: 'Courses' }],
            angular: true
        }
    },
    {
        path: '/resourcebooking/overview',
        name: '/resourcebooking/overview',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Resource booking', label: 'Overview' }],
            angular: true
        }
    },
    {
        path: '/resourcebooking/unconfirmed',
        name: '/resourcebooking/unconfirmed',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Resource booking', label: 'Unconfirmed' }],
            angular: true
        }
    },
    {
        path: '/resourcebooking/services',
        name: '/resourcebooking/services',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Resource booking', label: 'Manage services' }],
            angular: true
        }
    },
    {
        path: '/resourcebooking/book/:categoryId',
        name: '/resourcebooking/book',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Resource booking', label: 'Book' }],
            angular: true
        }
    },
    {
        path: '/resource/show/:id',
        name: '/resource/show',
        exact: true,
        meta: {
            breadcrumb: [{ parent: 'Resource', label: 'Show' }],
            angular: true
        }
    },
    {
        path: '/attendance',
        name: '/attendance',
        exact: true,
        meta: {
            breadcrumb: [{label: 'Attendance' }],
            angular: true
        }
    },
    {
        path: '/attendance/show/:workoutId',
        name: '/attendance/show',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Attendance', label: 'Show' }],
            angular: true
        }
    },
    {
        path: '/entry/show',
        name: '/entry/show',
        exact: true,
        meta: {
            breadcrumb: [{label: 'Entry' }],
            angular: true
        }
    },
    {
        path: '/pages/externalentry',
        name: '/pages/externalentry',
        exact: true,
        meta: {
            breadcrumb: [{label: 'Entry (external screen)' }],
            angular: true,
            fullscreen: true
        }
    },
    {
        path: '/pages/externalentry/:doorId',
        name: '/pages/externalentrydoor',
        exact: true,
        meta: {
            breadcrumb: [{label: 'Entry (external screen)' }],
            angular: true,
            fullscreen: true
        }
    },
    {
        path: '/checkout',
        name: '/checkout',
        exact: true,
        meta: {
            breadcrumb: [{label: 'Checkout' }],
            angular: true
        }
    },
    {
        path: '/statistics/overview',
        name: '/statistics/overview',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Statistics', label: 'Overview' }],
            angular: true
        }
    },
    {
        path: '/statistics/salesoverview',
        name: '/statistics/salesoverview',
        exact: true,
        component: () => import('./pages/SalesOverview.vue'),
        meta: {
            breadcrumb: [{parent: 'Statistics', label: 'Sales overview' }],
        }
    },
    {
        path: '/statistics/greports',
        name: '/statistics/greports',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Statistics', label: 'Reports' }],
            angular: true
        }
    },
    {
        path: '/statistics/reports',
        name: '/statistics/reports',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Statistics', label: 'Special reports' }],
            angular: true
        }
    },
    {
        path: '/statistics/report/:reportId',
        name: '/statistics/report',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Statistics', label: 'Report' }],
            angular: true
        }
    },
    {
        path: '/statistics/apn',
        name: '/statistics/apn',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Statistics', label: 'Municipal contribution' }],
            angular: true
        }
    },
    {
        path: '/statistics/lok',
        name: '/statistics/lok',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Statistics', label: 'Government contribution (LOK)' }],
            angular: true
        }
    },
    {
        path: '/statistics/eventlog',
        name: '/statistics/eventlog',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Statistics', label: 'Event log' }],
            angular: true
        }
    },
    {
        path: '/statistics/newreport',
        name: '/statistics/newreport',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Statistics', label: 'Create report' }],
            angular: true
        }
    },
    {
        path: '/economy/dashboard',
        name: '/economy/dashboard',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Economy', label: 'Dashboard' }],
            angular: true
        }
    },
    {
        path: '/economy/clientaccount',
        name: '/economy/clientaccount',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Economy', label: 'Client account' }],
            angular: true
        }
    },
    {
        path: '/economy/invoices',
        name: '/economy/invoices',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Economy', label: 'Invoices' }],
            angular: true
        }
    },
    {
        path: '/economy/budgets',
        name: '/economy/budgets',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Economy', label: 'Budget' }],
            angular: true
        }
    },
    {
        path: '/economy/accounting',
        name: '/economy/accounting',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Economy', label: 'Accounting' }],
            angular: true
        }
    },
    {
        path: '/economy/stripe',
        name: '/economy/stripe',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Economy', label: 'Stripe client account' }],
            angular: true
        }
    },
    {
        path: '/economy/systemcost',
        name: '/economy/systemcost',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Economy', label: 'System cost' }],
            angular: true
        }
    },
    {
        path: '/payment/directdebit/confirm',
        name: '/payment/directdebit/confirm',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Economy', label: 'Autogiro - bekräfta betalning' }],
            angular: true
        }
    },
    {
        path: '/payment/directdebit/consents',
        name: '/payment/directdebit/consents',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Economy', label: 'Autogiro - saknade medgivanden' }],
            angular: true
        }
    },
    {
        path: '/payment/directdebit/create',
        name: '/payment/directdebit/create',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Economy', label: 'Create file' }],
            angular: true
        }
    },
    {
        path: '/payment/directdebit/files',
        name: '/payment/directdebit/files',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Economy', label: 'Files' }],
            angular: true
        }
    },
    {
        path: '/mailings/all',
        name: '/mailings/all',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Mailing', label: 'All' }],
            angular: true
        }
    },
    {
        path: '/mailings/automailings',
        name: '/mailings/automailings',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Mailing', label: 'Administration' }],
            angular: true
        }
    },
    {
        path: '/addon/shop',
        name: '/addon/shop',
        component: () => import('./components/AddonShop.vue'),
        exact: true,
        meta: {
            breadcrumb: [{label: 'Addon shop' }]
        }
    },
    {
        path: '/settings/gym',
        name: '/settings/gym',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'General' }],
            angular: true
        }
    },
    {
        path: '/settings/addons',
        name: '/settings/addons',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'My addons' }],
            angular: true
        }
    },
    {
        path: '/settings/import',
        name: '/settings/import',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'Import' }],
            angular: true
        }
    },
    {
        path: '/settings/sale',
        name: '/settings/sale',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'Sale' }],
            angular: true
        }
    },
    {
        path: '/settings/checkout',
        name: '/settings/checkout',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'Checkout' }],
            angular: true
        }
    },
    {
        path: '/settings/resources',
        name: '/settings/resources',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'Resources' }],
            angular: true
        }
    },
    {
        path: '/settings/memberpage',
        name: '/settings/memberpage',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'Memberpage' }],
            angular: true
        }
    },
    {
        path: '/settings/roles',
        name: '/settings/roles',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'Access rights' }],
            angular: true
        }
    },
    {
        path: '/settings/customerfields',
        name: '/settings/customerfields',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'Customer information' }],
            angular: true
        }
    },
    {
        path: '/settings/proxyapp',
        name: '/settings/proxyapp',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'Proxy app' }],
            angular: true
        }
    },
    {
        path: '/settings/customerstatus',
        name: '/settings/customerstatus',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'Status / Interest' }],
            angular: true
        }
    },
    {
        path: '/settings/language',
        name: '/settings/language',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Settings', label: 'Language' }],
            angular: true
        }
    },
    {
        path: '/teamsports/admin',
        name: '/teamsports/admin',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Competitions', label: 'Administer sport' }],
            angular: true
        }
    },
    {
        path: '/teamsports/overview',
        name: '/teamsports/overview',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Competitions', label: 'Overview matches' }],
            angular: true
        }
    },
    {
        path: '/teamsports/settings',
        name: '/teamsports/settings',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Competitions', label: 'Settings' }],
            angular: true
        }
    },
    {
        path: '/teamsport/:teamsportId',
        name: '/teamsport',
        meta: {
            breadcrumb: [{parent: 'Teamsport', label: 'Sport' }],
        }
    },
    {
        path: '/teamsports/competition/:competitionId',
        name: '/teamsports/competition',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Competitions', label: 'Competition' }],
            angular: true
        }
    },
    {
        path: '/teamsports/gameclass/:gameclassId',
        name: '/teamsports/gameclass',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Competitions', label: 'Gameclass' }],
            angular: true
        }
    },
    {
        path: '/teamsports/step/:stepId',
        name: '/teamsports/step',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Competitions', label: 'Step' }],
            angular: true
        }
    },
    {
        path: '/teamsports/division/:divisionId',
        name: '/teamsports/division',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Competitions', label: 'Division' }],
            angular: true
        }
    },
    {
        path: '/teamsports/match/:matchId',
        name: '/teamsports/match',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Competitions', label: 'Match' }],
            angular: true
        }
    },
    {
        path: '/admin/installations',
        name: '/admin/installations',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Administration', label: 'Installations' }],
            angular: true
        }
    },
    {
        path: '/admin/installationsnew',
        name: '/admin/installationsnew',
        component: () => import('./components/ZoeziAdmin.vue'),
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Administration', label: 'Installations' }]
        }
    },
    {
        path: '/admin/flags',
        name: '/admin/flags',
        component: () => import('./components/ZoeziFlags.vue'),
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Administration', label: 'Flags' }]
        }
    },
    {
        path: '/pages/admin/dashboard',
        name: '/pages/admin/dashboard',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Administration', label: 'Dashboard' }],
            angular: true
        }
    },
    {
        path: '/admin/bankgiro',
        name: '/admin/bankgiro',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Administration', label: 'Direct debit' }],
            angular: true
        }
    },
    {
        path: '/addon/index.html#/review',
        name: '/addon/index.html#/review',
        exact: true,
        meta: {
            breadcrumb: [{parent: 'Administration', label: 'Addon review' }],
            angular: true
        }
    }
];

const router = createRouter({
    history: createWebHashHistory(),
    routes,
    scrollBehavior () {
        return { left: 0, top: 0 };
    }
});

router.afterEach((to, from) => {
    Userpilot.reload();
});

export default router;
