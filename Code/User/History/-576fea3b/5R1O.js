import {getName} from '../util.js'
import { intersection, xor } from 'lodash';

class Booking { // Accessible as $booking or window.$booking
    getWorkoutTypes() {
        return this.settings.then(x => x.workoutTypes);
    }

    getWorkoutCategories() {
        return this.settings.then(x => x.workoutcategories);
    }

    getResourceBookingCategories() {
        return this.settings.then(x => x.resourcebookingcategories);
    }

    getCourseCategories() {
        return this.settings.then(x => x.coursecategories);
    }

    isCardValid(card, date, trainings=1, check_freeze=true) {
        var validToDate = !card.validToDate || date < card.validToDate.clone().addDays(1);
        var notvalidFromDate = card.validFromDate > date;
        var validFromDate = !notvalidFromDate;
        var trainingsLeft = trainings == 0 || card.trainingsLeft >= trainings || card.trainingsLeft === null;
        if (check_freeze && this.getActiveFreeze(card, date)) {
            return false;
        }
        if (validToDate && validFromDate && trainingsLeft) {
            return true;
        }

        return false;
    }

    getActiveFreeze(card, date) {
        return card.freezes?.find(freeze => date.withinRange(freeze.fromDate, freeze.toDate));
    }

    workoutTypeAllowsBookingWithCardType(workoutType, cardtype_id) {
        return !workoutType.cardtypes || workoutType.cardtypes.length == 0 || workoutType.cardtypes.indexOf(cardtype_id) != -1;
    }

    transformWorkout(w) {
        w.startTime = Date.newFull(w.startTime);
        w.startDate = new Date(w.startTime).clearTime();
        w.endTime = Date.newFull(w.endTime);
        w.start = w.startTime;
        w.end = w.endTime;

        w.resources?.forEach(r => {
            if (r.resourceType == 'location') {
                w.location = r;
                r.name = r.lastname;
            } else if (r.resourceType == 'room') {
                w.room = r;
                r.name = r.lastname;
            }
        })
        w.staffs?.forEach(s => {
            s.name = getName(s);
        })

        w.getBooking = (user) => {
            user = user || this.$store.state.user;
            return this.$store.state.bookings && user && this.$store.state.bookings.workouts.find(x => x.id == w.id && x.user_id == user.id);
        }
        w.isBooked = (user) => !!w.getBooking(user);
        w.isInQueue = (user) => {
            let b = w.getBooking(user);
            return b && b.inQueue;
        }
        w.isFull = () => w.space && (w.numBooked - w.numQueue) >= w.space;
        w.getQueuePosition = (user) => {
            let b = w.getBooking(user);
            return b && b.queue;
        }
        w.canQueue = (user) => w.isFull() && !w.isBooked(user) && this.$store.state.settings?.canQueue;

        w.bookableForGroup = (user) => {
            user = user || this.$store.state.user;
            return user && w.bookable_for_groups && w.bookable_for_groups.find(group_id => user?.groups.find(group => group.id == group_id));
        }

        w.getCategory = () => {
          return this.$root.$store.state.settings?.workoutcategories?.find(cat => cat.id == w.workoutType.category_id);
        }

        w.discussionEnabled = () => {
            return w.getCategory().discussion;
        }

        w.showMembersEnabled = () => {
            return w.getCategory().showMembers;
        }

        w.firstCome = () => {
            return w.getCategory()?.firstCome;
        }

        w.hasValidTrainingCard = (user) => {
            user = user || this.$store.state.user;

            if (w.bookableForGroup(user)) {
                return true;
            }
    
            if (this.$store.state.cards) {
                let date = w.startTime;
                let groups = user.groups ? user.groups.map(x => x.id) : [];
                let cards = this.$store.state.cards.filter(card => card.user_id == user.id || intersection(groups, card.groups).length > 0);
                return !!cards.find(card => {
                    if (this.isCardValid(card, date) && !card.resourcebookingservice_id && !card.membership && card.cardtype.workout) {
                        if (w.workoutType.allowBooking && this.workoutTypeAllowsBookingWithCardType(w.workoutType, card.cardtype_id)) {
                            return true;
                        }
                    }
                })
            }
    
            return false;
        }

        w.bookable = (user) => {
            user = user || this.$store.state.user;

            if (w.status == 'Cancelled') {
                return false;
            }

            if (w.isBlocked(user)) {
                return false;
            }

            if (!w.bookableForCustomer) {
                return false;
            }

            if (w.bookableForGroup(user)) {
                return true;
            }
            
            if (!w.workoutType.allowBooking && !w.workoutType.onetime) {
                return false;
            }
            
            if (w.invalidBookingAge(user)) {
                return false;
            }

            if (w.invalidBookingGender(user)) {
                return false;
            }

            if (w.invalidBookingGroups(user)) {
                return false;
            }

            if (w.invalidBookingInterests(user)) {
                return false;
            }

            if (w.tooEarlyToBook() || w.tooLateToBook()) {
                return false;
            }

            if (w.hasReachedBookingsLimit(user)) {
                return false;
            }

            if (w.hasReachedIntervalBookingsLimit(user)) {
                return false;
            }

            if (w.hasReachedTrainingCardsBookingsLimit(user)) {
                return false;
            }
            
            return true;
        }

        w.invalidBookingAge = (user) => {
            if (w.workoutType.booking_age) {
                let birthdate = user?.birthdate
                if (!birthdate) {
                    return true;
                }
  
                let age = Date.getAge(birthdate)
                if (age < Number(w.workoutType.booking_age.from) || age > Number(w.workoutType.booking_age.to)) {
                    return true;
                }
            }

            return false;
        }

        w.invalidBookingGender = (user) => {
            if (w.workoutType.booking_gender) {
                let gender = user?.gender;
                if (gender != w.workoutType.booking_gender) {
                    return true;
                }
            }

            return false;
        }

        w.invalidBookingInterests = (user) => {
            if (w.workoutType.booking_interests && w.workoutType.booking_interests.length) {
                let i = user?.interest;
                return intersection(i, w.workoutType.booking_interests).length == 0;
            }

            return false;
        }

        w.invalidBookingGroups = (user) => {
            if (w.workoutType.booking_groups && w.workoutType.booking_groups.length) {
                let groups = user?.groups?.map(g => g.id);
                return intersection(groups, w.workoutType.booking_groups).length == 0;
            }

            return false;
        }

        w.isBlocked = (user) => {
            user = user || this.$store.state.user;
            let now = this.$store.state.now30s.clone();
            let blocks = user?.blocks?.filter(b => b.block_grouptraining && Date.newFull(b.fromDate) <= now && (!b.toDate || Date.newFull(b.toDate) >= now));
            return blocks?.length > 0;
        }

        w.getBlock = (user) => {
            user = user || this.$store.state.user;
            let now = this.$store.state.now30s.clone();
            let blocks = user?.blocks?.filter(b => b.block_grouptraining && Date.newFull(b.fromDate) <= now && (!b.toDate || Date.newFull(b.toDate) >= now));
            if (!blocks || !blocks.length) {
                return null;
            }
            let block = blocks.find(x => !x.toDate);
            if (block) {
                return block; // Blocked until further notice
            }
            blocks.sort((a, b) => Date.newFull(a.toDate) - Date.newFull(b.toDate));
            return blocks[0];
        }

        w.tooEarlyToBook = () => {
            let now = this.$store.state.now30s;
            let registerDaysBefore = w.getCategory()?.registerDaysBefore;
            let bookableFrom = w.start.clone().addMinutes(-registerDaysBefore*24*60);
  
            let releasedAt = this.$root.$store.state.settings?.wbreleasedat;
            if (releasedAt) {
                releasedAt = Date.newTime(releasedAt);
                bookableFrom.setHours(releasedAt.getHours(), releasedAt.getMinutes());
            }
  
            return now < bookableFrom && bookableFrom <= w.start;
        }

        w.bookableFrom = () => {
            let registerDaysBefore = w.getCategory()?.registerDaysBefore;
            let bookableFrom = w.start.clone().addMinutes(-registerDaysBefore*24*60);
  
            let releasedAt = this.$root.$store.state.settings?.wbreleasedat;
            if (releasedAt) {
                releasedAt = Date.newTime(releasedAt);
                bookableFrom.setHours(releasedAt.getHours(), releasedAt.getMinutes());
            }

            if (bookableFrom > w.start) {
                bookableFrom = null;
            }

            return bookableFrom;
        }

        w.tooLateToBook = () => {
            let category = w.getCategory();
            let registerHoursBefore = category?.registerHoursBefore || 0;
            let now = this.$store.state.now30s;
            let bookableTo = category?.allowBookingAfterStarted ? w.end.clone() : w.start.clone().addMinutes(-registerHoursBefore*60);
            let withinDropinPeriod = category?.dropin ? (now > w.start.clone().addMinutes(-category.dropin) && now < w.start) : false;
            return now > bookableTo && !withinDropinPeriod;
        }

        w.getBuyableCards = () => {
            if (this.$store.state.buyableCards == null) {
                return [];
            }

            let cards = this.$store.state.buyableCards.filter(card => 
                ((card.onetime && w.workoutType.onetime) || (w.workoutType.allowBooking && (!w.workoutType.cardtypes || w.workoutType.cardtypes.length == 0 || w.workoutType.cardtypes.indexOf(card.id) != -1)))
            );

            if (w.workoutType.onetime) {
                cards.push({price: w.workoutType.price, name: window.$translate('One time card'), workout: true, id: 'onetime', onetime: true});
            }

            return cards;
        }

        w.getTrialCards = () => w.getBuyableCards().filter(card => card.trial)

        w.hasBuyableCards = () => {
            return w.getBuyableCards().length > 0;
        }

        w.unbookable = (user) => {
            user = user || this.$store.state.user;
            let now = this.$store.state.now30s;
            if (now >= w.start) {
                return false;
            }

            if (w.isInQueue(user)) {
                return true;
            }

            if (w.match_id) {
                return true;
            }

            var category = w.getCategory();
            if (!category) {
                return false;
            }

            if (this.$root.$store.state.settings.wbswarninglatecancellations) {
                return true;
            }

            return now <= w.start.clone().addMinutes(-category.unregisterHoursBefore*60);
        }

        w.isCancelled = () => w.status == 'Cancelled'

        w.hasReachedBookingsLimit = (user) => {
            user = user || this.$store.state.user;
            let limit = this.$store.state.settings?.wbsbookingslimit;
            if (!limit) {
                return false;
            }

            let bookings = this.$store.state.bookings?.workouts.filter(w => w.startTime >= this.$store.state.now30s && w.user_id == user.id);
            return bookings?.length >= limit;
        }

        w.hasReachedIntervalBookingsLimit = (user) => {
            user = user || this.$store.state.user;

            let intervalType = this.$store.state.settings?.wbsbookingslimitintervaltype;
            if (!intervalType || ['day', 'week'].indexOf(intervalType) === -1) { return false; }
    
            let fromDate = w.startTime.clone().clearTime();
            let toDate;
            if (intervalType === 'day') {
                toDate = fromDate.clone().addDays(1);
            } else {
                let currentDay = fromDate.getDay();
                let diff = currentDay === 0 ? 6 : (currentDay - 1);
                fromDate = fromDate.addDays(-diff);
                toDate = fromDate.clone().addDays(7);
            }
    
            let intervalBookings = this.$store.state.bookings?.workouts.filter(function(wo) { return wo.user_id == user.id && wo.startDate.getTime() >= fromDate.getTime() && wo.startDate.getTime() < toDate.getTime(); });
            return intervalBookings && intervalBookings.length >= this.$root.$store.state.settings.wbsbookingslimitinterval;
        }

        w.getCardWhereBookingsLimitIsReached = (user) => {
            user = user || this.$store.state.user;

            let groups = user && user.groups ? user.groups.map(x => x.id) : [];
            let cards = this.$store.state.cards?.filter(card => card.user_id == user.id || intersection(groups, card.groups).length > 0);
            if (!cards || !cards.length) {
                return null;
            }
            let monday = w.startTime.monday();
            let nextMonday = monday.clone().addDays(7);
            let bookingsThisWeek = this.$store.state.bookings?.workouts.filter(w => w.startTime >= monday && w.startTime < nextMonday && w.user_id == user.id);

            if (!bookingsThisWeek || bookingsThisWeek.length == 0) {
                return null;
            }
    
            let getBookingsForCard = (card) => {
                let fromDate = w.startTime.clone().clearTime();
                let toDate;
                if (card.cardtype.bookingsLimitIntervalType === 'day') {
                    toDate = fromDate.clone().addDays(1);
                } else {
                    fromDate = monday;
                    toDate = nextMonday;
                }
                return bookingsThisWeek.filter(wo => wo.trainingcard_id === card.id && wo.startDate.getTime() >= fromDate.getTime() && wo.startDate.getTime() < toDate.getTime());
            }
    
            let startDate = w.startTime.clone().clearTime();
            let validWOCards = cards.filter(c =>
                c && c.cardtype && c.cardtype.workout && (c.trainingsLeft == null || c.trainingsLeft > 0) && (!c.validToDate || c.validToDate.getTime() >= startDate.getTime())
            )
            if (!validWOCards.length) {
                return null;
            }
    
            let resCard = null;
            for (let i = 0; i < validWOCards.length; i++) {
                let card = validWOCards[i];
                if (!card.cardtype.bookingsLimitIntervalType) {
                    return null;
                }
                if (getBookingsForCard(card).length < card.cardtype.bookingsLimitInterval) {
                    return false;
                }
                resCard = card;
            }
            return resCard;
        }

        w.hasReachedTrainingCardsBookingsLimit = (user) => {
            return !!w.getCardWhereBookingsLimitIsReached(user);
        }

        w.getState = (user) => {
            let workout = w;
            if (workout.isCancelled()) {
                return 'cancelled';
            } else if (workout.isBooked(user) && !workout.isInQueue(user)) {
                return 'cancel';
            } else if (workout.canQueue(user) && workout.hasValidTrainingCard(user) && workout.bookable(user)) {
                return 'queue';
            } else if (workout.isInQueue(user) && !(workout.firstCome() && !workout.isFull())) {
                return 'leavequeue';
            } else if (workout.bookable(user) && !workout.hasValidTrainingCard(user) && workout.hasBuyableCards()) {
                if (workout.canQueue(user)) {
                    return 'queuebuy';
                } else if (!workout.isFull()) {
                    return 'bookbuy';
                } else {
                    return 'full';
                }
            } else if (workout.bookable(user) && workout.hasValidTrainingCard(user)) {
                if (workout.isFull()) {
                    return 'full';
                } else {
                    return 'book';
                }
            } else if (workout.tooEarlyToBook() && workout.bookableFrom()) {
                return 'tooearly';
            } else if (workout.tooLateToBook()) {
                return 'toolate';
            } else {
                return 'nobook';
            }
        }

        w.cancel = (user, failCb) => {
            window.$zoeziapi.post('/api/memberapi/workoutBooking/remove', null, {workout: w.id, booked_user: user.id}).then((response) => {
                if (!response.ok) {
                    window.$store.commit('showErrorDialog', {title: 'Fel vid avbokning', text: 'Det gick inte att avboka passet'})
                    failCb && failCb();
                }
            })
        }

        w.book = (user, failCb) => {
            if(w.firstCome() && !w.isFull() && w.isInQueue(user) ){
                
                let data = {workout: w.id, user_id: user.id};
                this.$api.post('/api/memberapi/workoutBooking/join', null, data ).then((response) => {  
                    if (!response.ok) {
                        this.$store.commit('showErrorDialog', {title: 'Fel vid bokning', text: 'Det gick inte att genomföra bokningen'});
                    }
                });
            }
            else{
                window.$zoeziapi.post('/api/memberapi/workoutBooking/add', null, {workout: w.id, method: 'trainingcard', user_id: user.id}).then((response) => {
                    if (!response.ok) {
                        failCb && failCb();
                        response.json().then(x => {
                            if (x.type == 'duplicate') {
                                let text = user.name + (w.isInQueue(user) ? ' står redan i kö' : ' är redan inbokad');
                                this.$store.commit('showSnackBar', {text});
                            } else {
                                this.$store.commit('showErrorDialog', {title: 'Fel vid bokning', text: 'Det gick inte att genomföra bokningen'})
                            }
                        })
                    }
                })
            }
        }

        w.getNoBookReasons = (user) => {
            let workout = w;
            user = user || this.$store.state.user;
    
            let res = [];
            if(!workout.bookableForCustomer) {
                res.push('Passet tillåter inte bokning');
            }

            if (!workout.hasValidTrainingCard(user) && workout.bookableForCustomer) {
                res.push('Giltigt träningskort saknas');
            }

            if (workout.isBlocked(user)) {
                let block = workout.getBlock(user);
                if (block.toDate) {
                    res.push('Spärrad till ' + Date.newFull(block.toDate).yyyymmdd())
                } else {
                    res.push('Spärrad tills vidare');
                }
            }

            if (workout.hasReachedBookingsLimit(user)) {
                let suffix = this.$store.state.settings.wbsbookingslimit == 1 ? 'bokning' : 'samtidiga bokningar';
                res.push(`Bokningsgräns uppnådd, ${this.$store.state.settings.wbsbookingslimit} ${suffix}`)
            }

            if (workout.hasReachedIntervalBookingsLimit(user)) {
                let date = '';
                if (this.$store.state.settings.wbsbookingslimitintervaltype == 'day') {
                    date = Date.formatFullShort(workout.startTime)
                } else {
                    date = 'vecka ' + workout.startTime.getWeekNumber();
                }
                let suffix = this.$store.state.settings.wbsbookingslimitinterval == 1 ? 'bokning' : 'bokningar';
                res.push(`Bokningsgräns uppnådd, ${this.$store.state.settings.wbsbookingslimitinterval} ${suffix} ${date}`)
            }

            if (workout.hasReachedTrainingCardsBookingsLimit(user)) {
                let card = workout.getCardWhereBookingsLimitIsReached(user);
                let date = '';
                if (card.cardtype.bookingsLimitIntervalType == 'day') {
                    date = Date.formatFullShort(workout.startTime)
                } else {
                    date = 'vecka ' + workout.startTime.getWeekNumber();
                }
                let suffix = card.cardtype.bookingsLimitInterval == 1 ? 'bokning' : 'bokningar';
                res.push(`Bokningsgräns uppnådd, ${card.cardtype.bookingsLimitInterval} ${suffix} ${date}`)
            }

            if (workout.invalidBookingGender(user)) {
                if (workout.workoutType.booking_gender == 'male') {
                    res.push('Endast för män')
                } else if (workout.workoutType.booking_gender == 'female') {
                    res.push('Endast för kvinnor')
                } else {
                    res.push('Bokning begränsad på kön')
                }
            }

            if (workout.invalidBookingAge(user)) {
                if (workout.workoutType.booking_age.to > 90) {
                    res.push('Måste vara minst ' + workout.workoutType.booking_age.from + ' år gammal');
                } else {
                    res.push('Måste vara mellan ' + workout.workoutType.booking_age.from + ' och ' + workout.workoutType.booking_age.to + ' år');
                }
            }

            if (workout.invalidBookingInterests(user)) {
                if (!this.$store.state.interests) {
                    this.$store.dispatch('loadInterests')
                    res.push(window.$translate('Booking requires some interests'))
                } else {
                    let interests = this.$store.state.interests;
                    res.push('Kräver ' + workout.workoutType.booking_interests.map(i => interests.find(io => io.id == i).name).sort((a,b) => a.localeCompare(b)).join(', ') )
                }
            }

            if (workout.invalidBookingGroups(user)) {
                res.push('Bokning kräver viss grupptillhörighet')
            }

            return res;
        }

        w.resources.forEach(r => r.name = r.lastname);

        return w;
    }

    // Internal below
    getBookings() {
        return this.$api.get('/api/memberapi/bookings/get', {startTime: new Date().monday().dateTime()}).then(x => {
            x.workouts?.forEach(wb => {
                this.transformWorkout(wb);
            })
            this.$root.$store.commit('setBookings', x);
            return this.$root.$store.state.bookings;
        });
    }

    getCards() {
        this.$api.get('/api/memberapi/trainingcard/get/all').then(cards => {
            cards.forEach(card => {
                card.boundToDate = Date.newFull(card.boundToDate);
                card.validFromDate = Date.newFull(card.validFromDate);
                card.validToDate = Date.newFull(card.validToDate);
                if (card.freezes) {
                    card.freezes.forEach(f => {
                        f.fromDate = Date.newFull(f.fromDate);
                        f.toDate = Date.newFull(f.toDate);
                    })
                }
            })

            cards.sort((a,b) => (a.cardtype_name ? a.cardtype_name : a.id) - (b.cardtype_name ? b.cardtype_name : b.id));

            this.$root.$store.commit('setCards', cards);
        })
    }

    getBuyableCards() {
        this.$api.get('/api/public/trainingcard/type/get', {trial: true}).then(products => {
            let cards = products.filter(card => card.customerCanBuy && card.workout)
            this.$root.$store.commit('setBuyableCards', cards);
        })
    }

    isMembershipRequired(items) {
        return this.getUsersWhichRequireMembership(items).length > 0;
    }

    // Checks if a membership is required but membership(s) must be added to items
    isMembershipStillRequired(items) {
        return this.getUsersWhichRequireMembership(items).filter(user_id => {
            let membershipsInBasket = items.find(item => item.product.membership && item.users.includes(user_id));
            return !membershipsInBasket;
        }).length > 0;
    }

    getUsersWhichRequireMembership(items) {
        if (!this.$store.state.settings?.membership) {
            return [];
        }

        let allcards = this.$store.state.cards;
        if (!allcards) {
            return [];
        }

        let validFromDate = new Date();
        let requiredForUsers = [];
        items.forEach(item => {
            if (item.product?.requireMembership) {
                item.users?.forEach(user_id => {
                    let cards = allcards.filter(card => card.user_id == user_id && card.membership);
                    let validMembership = cards.find(card => this.isCardValid(card, validFromDate));
                    if (!validMembership && !requiredForUsers.includes(user_id)) {
                        requiredForUsers.push(user_id);
                    }
                })
            }
        })

        return requiredForUsers;
    }

    setVueRoot($root) {
        this.$root = $root;
        this.$api = this.$root.$api;
        this.$store = this.$root.$store;

        this.settings = new Promise((resolve) => {
            let cancel = this.$root.$watch('$store.state.settings', (settings) => {
                cancel();
                resolve(settings);
            })
        })

        this.$root.$watch('$store.state.isLoggedIn', () => {
            if (this.$root.$store.state.user) {
                this.getBookings();
                this.getCards();
            } else {
                this.$root.$store.commit('setBookings', null);
                this.$root.$store.commit('setCards', null);
            }
        });

        this.$root.$api.subscribe({type: 'workoutbooking', callback: (_, event) => {
            if (event.data.find(item => {
                let bookings = this.$store.state.bookings;
                let user = this.$store.state.user;
                return (bookings && bookings.workouts.find(x => x.id == item.workout)) || (user && item.user_id && user.canBookFor.find(x => x.id == item.user_id));
            })) {
                this.getBookings();
            }
        }})

        this.$root.$api.subscribe({type: 'resourcebooking', callback: (_, event) => {
            if (event.data.find(item => this.$store.state.user?.id == item.user_id)) {
                this.getBookings();
            }
        }});

        this.$root.$api.subscribe({type: 'coursebooking', callback: (_, event) => {
            if (event.data.find(item => this.$store.state.user?.id == item.user_id || this.$store.state.user?.id == item.booker_id)) {
                this.getBookings();
            }
        }});

        this.$root.$api.subscribe({type: 'coursewatcher', callback: (_, event) => {
            if (event.data.find(item => this.$store.state.user?.id == item.user_id)) {
                this.getBookings();
            }
        }});

        this.$root.$api.subscribe({type: 'trainingcard', callback: () => this.getCards() });

        this.$root.$api.subscribe({type: 'payment', callback: () => this.getCards() });

        this.$root.$api.subscribe({type: 'user', callback: (_, event) => {
            if (event.data.find(item => this.$store.state.user?.id == item.id)) {
                let old_family = this.$store.state.user.canManage.map(x => x.id).concat(this.$store.state.user.canBookFor.map(x => x.id));
                this.$api.get('/api/memberapi/get/current').then(user => {
                    console.log('Got new user info');
                    this.$store.commit('setUserData', {user})

                    // Refetch training cards if family has changed
                    let new_family = user.canManage.map(x => x.id).concat(user.canBookFor.map(x => x.id));
                    if (xor(old_family, new_family).length) {
                        this.getCards();
                    }
                }, () => {}).catch();
            }
        }});

        this.$root.$api.subscribe({type: 'usersession', callback: (_, event) => {
            if (event.action == 'remove' && event.data.find(us => us.session == this.$store.state.user?.session)) {
                this.$store.commit('setLoggedIn', {isLoggedIn: false});
            }
        }})

        this.getWorkoutCategories().then(x => this.workoutCategories = x)

        this.getBuyableCards();
    }

    constructor(Vue) {
        Vue.prototype.$booking = this;
        window.$booking = this;
    }
}

export default {
    install(Vue) {
        new Booking(Vue);
    }
}