import Vue from 'vue'
import Vuex from 'vuex'
import {getName, isExpoApp, getUrlParameterThis, setCookie} from '../util.js'
import * as Sentry from "@sentry/browser";

function initStore() {
    Vue.use(Vuex);

    const saveInLocalStorage = ['editMenu', 'carts', 'selectedSiteId', 'codeMaximizeWindow'];

    let updateUserData = (user) => {
      user.name = getName(user);

      let isBlocked = (user, type) => {
        let blocks = user.blocks?.filter(t => t[type]);
        if (!blocks || !blocks.length) {
          return null;
        }
        let block = blocks.find(x => !x.toDate);
        if (block) {
            return block; // Blocked until further notice
        }
        blocks = blocks.concat();
        blocks.sort((a, b) => Date.newFull(a.toDate) - Date.newFull(b.toDate));
        return blocks[0];
      }

      user.isBlocked = (type) => isBlocked(user, type);

      if (user.canBookFor) {
        user.canBookFor.forEach(x => {
          x.isBlocked = (type) => isBlocked(x, type);
        })
        user.canBookFor = user.canBookFor.sort((a,b) => {
          if (a.id == user.id) {
            return -1;
          }

          if (b.id == user.id) {
            return 1;
          }

          return a.name.localeCompare(b.name);
        })
      }
      let self = user.canBookFor?.find(x => x.id == user.id)
      if (self) {
        Object.assign(self, user);
      }
    };

    const store = new Vuex.Store({
      state: {
        // Module: general
        now30s: new Date(),              // Current date, updated every 30 second
        showMobileMenu: false,
        errorDialog: {
          show: false,
          title: '',
          text: '',
          action: null,
          actionText: 'Ok'
        },
        snackBar: {
          show: 0,
          text: ''
        },
        confirmDialog: {
          show: false,
          title: '',
          text: '',
          action: null,
          actionText: ''
        },
        language: 'sv',
        translations: {},
        googleMapsApiKey: 'AIzaSyAkUAkjyqsYAb-FCtpUY7WdetIQUv1-slQ',
        settings: null,
        interests: null,
        loadingInterests: false,
        carts: {
        },
        checkoutDoneDialog: {
          show: false,
          orderconfirmation: {},
          totalFromServer: 0,
          paidByMethod: null
        },
        addUserDialog: {
          show: false,
          homesite_id: null,
          title: null,
          booking_fields: false,
          callback: null
        },
        changeUserDialog: {
          show: false,
          callback: null,
          user_id: null
        },
        checkoutHidden: false,

        // Module: user/account
        isCheckingIfLoggedIn: false,
        isLoggedIn: false,
        user: null,
        bookings: null,
        buyableCards: null,
        cards: null,
        isConnected: false,
        missingMemberFields: {
          show: false,
          disabled: false
        },
        selectedSiteId: null,
        
        // Module: edit
        editModeInitializing: false,
        editComponent: null,
        editComponentConfig: null,
        saving: false,
        needToSave: false,
        editMenu: false,
        fonts: null,
        copiedComponent: null,
        codeMaximizeWindow: false
      },
      mutations: {
        // Module: general
        updateNow(state) {
          state.now30s = new Date();
        },
        setShowMobileMenu(state, show) {
          state.showMobileMenu = show;
        },
        showErrorDialog(state, {title, text, action, actionText}) {
          if (!actionText) {
            actionText = 'Ok';
          }
          if (!action) {
            action = () => state.errorDialog.show = false;
          }

          Object.assign(state.errorDialog, {title, text, action, actionText, show: true});
        },
        hideErrorDialog(state) {
          state.errorDialog.show = false;
        },
        showSnackBar(state, {text, color}) {
          state.snackBar.show = true;
          state.snackBar.text = text;
          state.snackBar.color = color || 'error';
        },
        hideSnackBar(state) {
          state.snackBar.show = false;
        },
        showConfirmDialog(state, {title, text, action, actionText}) {
          state.confirmDialog.show = true;
          state.confirmDialog.title = title;
          state.confirmDialog.text = text;
          state.confirmDialog.action = action;
          state.confirmDialog.actionText = actionText;
        },
        showMissingMemberFields(state, show) {
          state.missingMemberFields.show = show;
        },
        disableMissingMemberFields(state, disabled) {
          state.missingMemberFields.disabled = disabled;
        },
        setTranslations(state, translations) {
          state.translations = translations;
        },
        setSettings(state, settings) {
          state.settings = settings;
          settings.fields.forEach(field => {
            if (field.type == 'select') {
                field.data = field.data.map(i => ({
                    value: i.id || i,
                    text: i.name || i
                }))
                if (field.builtIn) {
                  field.format = 'translated';
                }
            }

            if (field.type == 'date' && field.builtIn && field.name == 'birthdate') {
              field.max = Date.today().yyyymmdd();
            }
          })

          settings.webshopcategories?.forEach(cat => {
            cat.parent = settings.webshopcategories.find(x => x.id == cat.parent_id)
            let getTopCategory = (c) => {
              if (c.parent && !c.parent.parent) {
                return c.parent;
              } else if (c.parent) {
                return getTopCategory(c.parent)
              } else {
                return c;
              }
            }
            cat.top_category = getTopCategory(cat);
          })

          Sentry.configureScope(scope =>
            scope.addEventProcessor(
              event =>
                new Promise(resolve =>
                  resolve({
                    ...event,
                    release: settings.version
                  })
                )
            )
          );
        },
        showCheckoutDoneDialog(state, {orderconfirmation, totalFromServer, paidByMethod}) {
          Object.assign(state.checkoutDoneDialog, {orderconfirmation, totalFromServer, paidByMethod, show: true});
        },
        showAddUserDialog(state, {homesite_id, title, booking_fields, callback}) {
          Object.assign(state.addUserDialog, {homesite_id, title, booking_fields, callback, show: true});
        },
        showChangeUserDialog(state, {callback, user_id}) {
          Object.assign(state.changeUserDialog, {callback, user_id, show: true});
        },
        setCheckoutHidden(state, hidden) {
          state.checkoutHidden = hidden;
        },

        // Module: user/account
        setLoggedIn (state, {isLoggedIn, user}) {
          state.isLoggedIn = isLoggedIn;
          if (isLoggedIn) {
            updateUserData(user);
          }
          
          state.user = isLoggedIn ? user : null;
          state.isCheckingIfLoggedIn = false;
          if (user && !state.selectedSiteId) {
            state.selectedSiteId = user.site;
          }
        },
        setUserData (state, {user}) {
          updateUserData(user);
          state.user = user;
        },
        setBookings( state, bookings) {
          state.bookings = bookings;
        },
        setIsConnected(state, isConnected) {
          state.isConnected = isConnected;
        },
        setCards(state, cards) {
          state.cards = cards;
        },
        setBuyableCards(state, cards) {
          state.buyableCards = cards;
        },

        // Module: edit
        setEditComponent(state, editComponent) {
          state.editComponent = editComponent;
          state.editComponentConfig = editComponent ? editComponent.$parent._props.config : null;
        },
        setEditModeInitializing(state, value) {
          state.editModeInitializing = value;
        },
        setSaving(state, value) {
          state.saving = value;
        },
        setNeedToSave(state, value) {
          state.needToSave = value;
        },
        setEditMenu(state, value) {
          state.editMenu = value;
        },
        setFonts(state, value) {
          state.fonts = value;
        },
        copyComponent(state, component) {
          state.copiedComponent = component;
        },
        setCodeMaximizeWindow(state, value) {
          state.codeMaximizeWindow = value;
        }
      },
      actions: {
        setVueRoot({state}) {
          saveInLocalStorage.forEach(prop => {
            this._vm.$watch( () => state[prop], (value) => {
              value = JSON.stringify(value);
              window.localStorage.setItem('zoezi.' + prop, value);
            }, {deep: true})
          })
        },
        logout({commit, state}) {
          this._vm.$api.post('/api/memberapi/logout').then(() => commit('setLoggedIn', {isLoggedIn: false}));
          state.carts = {};
          if(isExpoApp() && window.ReactNativeWebView) {
            window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'session', data: '' }));
          }
        },
        checkIfLoggedIn({commit, state}) {
          state.isCheckingIfLoggedIn = true;

          let session = getUrlParameterThis('session');
          if (session) {
            setCookie('session', session, 365*10, true);
            const url = new URLSearchParams(window.location.search);
            url.delete('session');
            const queryString = url.toString();
            const newUrl = queryString ? `${window.location.pathname}?${queryString}` : window.location.pathname;
            window.history.replaceState({}, '', newUrl);
          }

          this._vm.$api.get('/api/memberapi/get/current').then((user) =>
            commit('setLoggedIn', {isLoggedIn: true, user})
          ).catch(() => commit('setLoggedIn', {isLoggedIn: false}) )
        },
        setEditComponentConfig({state}, {config, parentComponent}) {
          let locateComponent = (node) => {
            if (node?.$options?.name == 'EditPanel') {
              return null;
            }
            if (node?._props?.config == config) {
                return node.$children[0];
            }

            let res = null;
            node.$children.forEach(x => {
                let c = locateComponent(x);
                if (!res) {
                    res = c;
                }
            })

            return res;
        };

          Vue.nextTick(() => {
            let root = document.getElementsByClassName('zoezi-root')[0].__vue__;
            let vuecomponent = locateComponent(root);

            if (vuecomponent && config == vuecomponent.$parent._props.config) {
              state.editComponent = vuecomponent;
              state.editComponentConfig = vuecomponent.$parent._props.config;
            } else {
              if (parentComponent && parentComponent.findChild) {
                parentComponent.findChild(config.id);
                Vue.nextTick(() => {
                  let vuecomponent = locateComponent();
                  if (vuecomponent) {
                    state.editComponent = vuecomponent;
                    state.editComponentConfig = vuecomponent.$parent._props.config;
                  }
                });
              } else {
                state.editComponent = null;
                state.editComponentConfig = config;
              }
            }
          });
        },
        setLanguage({state}, language) {
          this._vm.$translations.fetchLanguageFile(language).then(() => {
            state.language = language;
            window.$vuetify.lang.current = language;
          })
        },
        loadInterests({state}) {
          if (state.loadingInterests || state.interests) {
            return;
          }
          state.loadingInterests = true;

          this._vm.$api.get('/api/memberapi/interest/get').then((interests) => {
            state.interests = interests;
            state.loadingInterests = false;
          })
        },
        addToCart({state}, {cartName, product_id, count, variant, price, site_id}) {
          cartName = cartName || '';
          if (!state.carts) {
            state.carts = {};
          }
          let cart = state.carts[cartName];
          if (!cart) {
            site_id = site_id || 1;
            cart = {
              items: [],
              site_id,
              showBottomBar: false,
              showCheckout: false
            };
            Vue.set(state.carts, cartName, cart)
          }
          if (!count) {
            count = 1;
          }
          
          let item = cart.items.find(i => i.product_id == product_id && i.variant == variant);
          if (!item) {
            item = {product_id: product_id, variant: variant, count: 0, users: new Array(count).fill(state.user ? state.user.id : null)};
            cart.items.push(item);
          }

          if (price !== undefined) {
            item.price = price;
          }

          item.count += count;

          state.carts = Object.assign({}, state.carts);
        },
        changeItemCountInCart({state}, {cartName, product_id, variant, count}) {
          cartName = cartName || '';
          if (!state.carts) {
            state.carts = {};
          }
          let cart = state.carts[cartName];
          if (cart === undefined) {
            return;
          }

          let existing = cart.items.find(x => x.product_id == product_id && x.variant == variant)
          if (existing) {
              existing.count = count;
              if (existing.users) {
                  existing.users = existing.users.slice(0, count);
              }
              if (count == 0) {
                  cart.items.splice(cart.items.indexOf(existing), 1)
              }
          }

          state.carts = Object.assign({}, state.carts);
        },
        changeItemUsersInCart({state}, {cartName, product_id, variant, users}) {
          cartName = cartName || '';
          if (!state.carts) {
            state.carts = {};
          }
          let cart = state.carts[cartName];
          if (cart === undefined) {
            return;
          }

          let existing = cart.items.find(x => x.product_id == product_id && x.variant == variant)
          if (existing) {
            existing.users = users.concat();
          }

          state.carts = Object.assign({}, state.carts);
        },
        removeCart({state}, {cartName}) {
          cartName = cartName || '';
          if (!state.carts) {
            state.carts = {};
          }
          let cart = state.carts[cartName];
          if (cart) {
            delete state.carts[cartName];
          }

          state.carts = Object.assign({}, state.carts);
        },
        setCartVisibility({state}, {cartName, showBottomBar, showCheckout}) {
          cartName = cartName || '';
          if (!state.carts) {
            state.carts = {};
          }
          let cart = state.carts[cartName];
          if (showBottomBar || showCheckout) {
            Object.values(state.carts).forEach(cart => {
              cart.showBottomBar = false;
              cart.showCheckout = false;
            })
          }
          if (cart) {
            cart.showBottomBar = showBottomBar;
            cart.showCheckout = showCheckout;
          }
          state.carts = Object.assign({}, state.carts);
        },
        setSite({state}, {siteId}) {
          state.selectedSiteId = siteId;

          if (state.user && state.user.site != siteId) {
            this._vm.$api.post('/api/memberapi/setsite', null, {id: siteId});
          }
        }
      },
      getters: {
        comingBookings: (state) => {
          if (!state.bookings) {
            return null
          }

          let res = {};
          res.workouts = state.bookings.workouts?.filter(w => w.startTime >= state.now30s) || [];
          res.resourcebookings = [];

          state.bookings.resourcebookings?.forEach(rcat => {
            res.resourcebookings = res.resourcebookings.concat(rcat.bookings.filter(rb => !rb.cancelled && Date.newFull(rb.time) >= state.now30s))
          })

          res.coursebookings = state.bookings.coursebookings
          res.coursewatches = state.bookings.coursewatches

          return res;
        }
      }
    })

    saveInLocalStorage.forEach(prop => {
      try {
        let item = window.localStorage.getItem('zoezi.' + prop);
        if (item !== undefined) {
          item = JSON.parse(item);
          store.state[prop] = item;
        }
      } catch (e) {
        // Most probably inside an iframe
      }
    })

    setInterval(() => store.commit('updateNow'), 30*1000)

    window.$store = store;
  
    return store;
  }

  export {initStore};
