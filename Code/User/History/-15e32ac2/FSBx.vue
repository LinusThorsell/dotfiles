<style lang="scss">
  .zoezi-mypage .v-tabs-bar .v-tabs-bar__content {
    justify-content: center;
    .v-tab {
      min-width:50px;
      padding: 5px;
      text-transform: none;
      letter-spacing: 0;
      flex-wrap:wrap;
      font-size: 0.7em;
      .v-icon{
        display:block;
        width:90%;
      }
    }
  }

  .zoezi-mypage .tab-title {
      white-space: pre;
  }

  @media(min-width:600px){
    .zoezi-mypage .v-tabs-bar .v-tabs-bar__content {
      justify-content: left;
      .v-tab{
        font-size: .85em;
      }
    }

    .zoezi-mypage .tab-title {
      white-space: normal;
    }
  }
  @media(min-width:960px){
    .zoezi-mypage .v-tabs-bar .v-tabs-bar__content .v-tab{
      font-size: 1em;
      padding: 5px 10px;
    }

    .zoezi-mypage .tab-title {
      white-space: normal;
    }
  }
</style>
<template>
  <div v-if="$store.state.user">
    <v-tabs
      :color="$root.siteconfig.appbar.props.activeColor"
      background-color="transparent"
      v-model="selectedTab"
      class="z-no-arrows"
    >
      <v-tab v-for="tab in tabs" :key="tab.id">
        <v-icon small>{{tab.icon}}</v-icon>
        <span class="tab-title">{{tab.title}}</span><v-badge v-if="tab.badge" color="error" :content="tab.badge" class="ml-2" />
      </v-tab>
    </v-tabs>
    <v-tabs-items v-model="selectedTab">
      <v-tab-item v-if="tabs.find(x => x.id == 'start')">
        <div class="x mt-4">
          <v-row>
            <v-col cols="12">
              <v-card v-for="card in messageCards" :key="card.id" :color="card.color" class="zoezi-card-default">
                <v-card-title>{{$translate(card.title)}}</v-card-title>
                <v-card-text v-html="card.text" />
              </v-card>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12">
              <h3 v-if="sections.length == 0">Här kommer dina bokningar att visas</h3>
              <v-expansion-panels class="zoezi-my-activities" mandatory>
                <!-- Dölj paneler som är tomma, öppna första panelen som har innehåll -->
                <v-expansion-panel class="no-elevation" v-for="item in sections" :key="item.id">
                  <v-expansion-panel-header>
                    <div class="zoezi-activity-section">
                      <h3>{{item.title}}</h3>
                      <small>{{item.subtitle}}</small>
                    </div>
                    <v-badge color="grey" :content="item.bookings.length"></v-badge>
                  </v-expansion-panel-header>
                  <v-expansion-panel-content>
                      <div v-if="item.id == 'historic'" class="zoezi-card-default zoezi-card-horizontal z-clickable" @click="showHistoricalActivitiesDialog = true">
                          <div class="z-card-image">
                            <div class="z-card-image-time" :style="getBookingColorStyle({})">{{historicalActivitiesCount}} st</div>
                            <div class="z-card-image-small" :style="getBookingColorStyle({})">fr. {{historyFrom.substring(0, 7)}}</div>
                          </div>
                          <div class="z-card-content">
                            <strong>Visa alla tidigare aktiviteter</strong><br>
                            <v-icon class="ml-n1" color="primary">mdi-calendar</v-icon> Från {{Date.formatFullShorter(historyFrom)}} {{Date.newFull(historyFrom).getFullYear()}}
                          </div>
                          <div class="z-card-action pt-2 px-2">
                            <v-btn
                              class="zoezi-button-thin"
                              color="primary"
                              @click="showHistoricalActivitiesDialog"
                            >
                              Historik
                            </v-btn>
                          </div>
                      </div>

                      <div v-else class="zoezi-card-default zoezi-card-horizontal z-clickable" v-for="booking in item.bookings" :key="booking.key" @click="showActivity(booking)" :style="{background:booking.background}">
                        <div class="z-card-image" :style="{'background-image': 'url(' + $api.getImageUrl(booking.imagekey, 100) + ')' }">
                          <div class="z-card-image-time" :style="getBookingColorStyle(booking)">{{booking.start.hhmm()}}</div>
                          <div class="z-card-image-small" :style="getBookingColorStyle(booking)">{{booking.duration}} min</div>
                        </div>
                        <div class="z-card-content">
                          <strong>{{booking.text}}</strong><br>
                          <div v-if="!booking.start.isToday() && !booking.start.isTomorrow()"><v-icon color="primary">mdi-calendar</v-icon> {{Date.formatFullShort(booking.start)}}</div>
                          <div class="d-flex flex-row" v-if="booking.staffs && booking.staffs.length">
                            <div class="staff mr-2" v-for="staff in booking.staffs" :key="staff.id"><img v-if="staff.imagekey" :src="$api.getImageUrl(staff.imagekey, 100)" style="width:16px; border-radius:50%;"> {{staff.name}}</div>
                          </div>
                          <div class="location" v-if="booking.location || booking.room">
                            <v-icon class="ml-n1" color="primary">mdi-map-marker</v-icon>
                            <span v-if="booking.room">{{booking.room.name}}{{booking.location ? ', ': ' '}}</span>
                            <span v-if="booking.location">{{booking.location.name}}</span>
                          </div>
                        </div>
                        <div class="z-card-action pt-2 px-2">
                          <workout-book-button :workout="booking.workout" :info-on-unbookable="true" v-if="booking.workout" />
                          <v-btn
                            v-else-if="booking.type == 'resourcebooking'"
                            class="zoezi-button-thin"
                            color="primary"
                            @click="showActivity(booking)"
                          >
                            Info
                          </v-btn>
                        </div>

                        <div class="zoezi-booked-list" v-if="$store.state.user && booking.workout" style="flex-shrink: 0; width: 100%">
                            <workout-book-user-row
                                class="zoezi-booked-person"
                                :workout="booking.workout"
                                :user="user"
                                v-for="user in $store.state.user.canBookFor.filter(u => booking.workout.isBooked(u))"
                                :key="user.id"
                            />
                        </div>
                    </div>
                  </v-expansion-panel-content>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-col>
            <v-col>
              <!-- Utforska -->
            </v-col>
          </v-row>
          <div class='zoezi-training-overview' v-if="displayTrainingOverView">
            <h1>Min träningsöversikt</h1>
            <v-row class="mt-1">
              <v-col cols="12" md="6">
                <my-entry-stats />
              </v-col>
              <v-col cols="12" md="6">
                <my-workout-stats />
              </v-col>
            </v-row>
          </div>
        </div>

      </v-tab-item>
      <v-tab-item v-if="tabs.find(x => x.id == 'payments')" eager>
        <v-row>
          <v-col md=6 cols=12>
            <coming-payments @count="numComingPayments = $event"/>
            <receipt-list />
          </v-col>
          <v-col md=6 cols=12>
            <v-expansion-panels v-model="expandedPaymentMethodsPanel">
                <v-expansion-panel class="no-elevation" >
                    <v-expansion-panel-header>
                        <div class="zoezi-activity-section">
                            <h3>Betalsätt</h3>
                            <small>Här kan du hantera sparat betalkort och autogiromedgivande</small>
                        </div>
                    </v-expansion-panel-header>
                    <v-expansion-panel-content>
                      <my-payment-methods />
                  </v-expansion-panel-content>
                </v-expansion-panel>
            </v-expansion-panels>
          </v-col>
        </v-row>
      </v-tab-item>
      <v-tab-item v-if="tabs.find(x => x.id == 'courses')">
        <!-- Should only be visible if there are courses -->
        <div class="x mt-4">
          <v-row>
            <v-col cols="12" md="6">
              <v-expansion-panels class="zoezi-my-activities" mandatory>
                <!-- Dölj paneler som är tomma, öppna första panelen som har innehåll -->
                <v-expansion-panel class="no-elevation" v-for="item in courses" :key="item.id">
                  <v-expansion-panel-header>
                    <div class="zoezi-activity-section">
                      <h3>{{item.title}}</h3>
                      <small>{{item.subtitle}}</small>
                    </div>
                    <v-badge color="grey" :content="item.bookings.length"></v-badge>
                  </v-expansion-panel-header>
                  <v-expansion-panel-content>
                    <div class="zoezi-card-default zoezi-card-horizontal z-clickable" v-for="booking in item.bookings" :key="booking.id" @click="showCourseBooking(booking)">
                      <div class="z-card-image" :style="{'background-image': 'url(' + $api.getImageUrl(booking.imagekey, 100) + ')' }">
                        <div class="z-card-image-time" :style="getBookingColorStyle(booking)">{{Date.formatFullShorter(booking.startTime)}}</div>
                        <div class="z-card-image-small" :style="getBookingColorStyle(booking)">{{Date.formatFullShorter(booking.endTime)}}</div>
                      </div>
                      <div class="z-card-content">
                        <strong>{{booking.course_name}}</strong><br>
                        <span v-if="booking.occasions"><v-icon small class="mr-2">mdi-calendar-sync</v-icon>{{booking.occasions == 1 ? '1 tillfälle' : (booking.occasions + ' tillfällen')}}.<br></span>
                        <v-icon small class="mr-2">mdi-calendar</v-icon><span>{{Date.formatFullShort(booking.startTime).capitalize()}} - {{Date.formatFullShort(booking.endTime)}}</span>
                      </div>
                      <div class="z-card-action pt-2 px-2">
                        <v-btn block class="primary" @click="showCourseBooking(booking)">Info</v-btn>
                        <div class="z-card-action-text" v-if="getChildName(booking.user_id)">{{getChildName(booking.user_id)}} </div> <!-- Leif == den man bokat åt -->
                      </div>
                    </div>
                  </v-expansion-panel-content>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-col>
            <v-col md="6">
              <v-expansion-panels class="zoezi-my-activities" mandatory>
                <!-- Dölj paneler som är tomma, öppna första panelen som har innehåll -->
                <v-expansion-panel class="no-elevation" v-for="item in watching" :key="item.id">
                  <v-expansion-panel-header>
                    <div class="zoezi-activity-section">
                      <h3>{{item.title}}</h3>
                      <small>{{item.subtitle}}</small>
                    </div>
                    <v-badge color="grey" :content="item.bookings.length"></v-badge>
                  </v-expansion-panel-header>
                  <v-expansion-panel-content>
                    <div class="zoezi-card-default zoezi-card-horizontal z-clickable" v-for="booking in item.bookings" :key="booking.id" @click="showCourseBooking(booking)">
                      <div class="z-card-image" :style="{'background-image': 'url(' + $api.getImageUrl(booking.imagekey, 100) + ')' }">
                        <div class="z-card-image-time" :style="getBookingColorStyle(booking)">{{Date.formatFullShorter(booking.startTime)}}</div>
                        <div class="z-card-image-small" :style="getBookingColorStyle(booking)">{{Date.formatFullShorter(booking.endTime)}}</div>
                      </div>
                      <div class="z-card-content">
                        <strong>{{booking.course_name}}</strong><br>
                        <v-icon small>mdi-calendar</v-icon><span v-if="booking.occasions">{{booking.occasions == 1 ? '1 tillfälle' : (booking.occasions + ' tillfällen')}}.</span> {{Date.formatFullShort(booking.startTime).capitalize()}} - {{Date.formatFullShort(booking.endTime)}}<br>
                      </div>
                      <div class="z-card-action pt-2 px-2">
                        <v-btn block class="primary" @click="showCourseBooking(booking)">Info</v-btn>
                      </div>
                    </div>
                  </v-expansion-panel-content>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-col>
          </v-row>
        </div>
      </v-tab-item>
      <v-tab-item v-if="tabs.find(x => x.id == 'cards')">
        <v-row>
          <v-col cols=12>
            <v-expansion-panels
              v-model="expandedCardPanels"
              accordion
              flat
              multiple
              class="zoezi-my-activities"
            >
              <v-expansion-panel v-for="type in (hasMembership ? ['trainingcard', 'membership'] : ['trainingcard'])" :key="type" class="no-elevation">
                <v-expansion-panel-header>
                  <div class="zoezi-activity-section">
                    <h3 v-if="type=='trainingcard'">{{$translate('Training card')}}</h3>
                    <h3 v-if="type=='membership'">{{$translate('Membership')}}</h3>
                  </div>
                  <v-badge color="grey" :content="String(((type == 'trainingcard' ? validAndFrozenTrainingCards : validMemberships) || []).length)"></v-badge>
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                  <div v-if="type=='trainingcard' && validAndFrozenTrainingCards && validAndFrozenTrainingCards.length == 0" class="text--secondary">
                    Du har inget träningskort.
                  </div>
                  <div v-else-if="type=='membership' && validMemberships && validMemberships.length == 0" class="text--secondary">
                    Du har inget medlemskap.
                  </div>
                  <div v-else class="zoezi-card-default zoezi-card-horizontal z-clickable" v-for="card in (type == 'trainingcard' ? validAndFrozenTrainingCards : validMemberships)" :key="card.id" @click="showingCard = card; showTrainingCardDialog = true">
                    <div class="z-card-image" :style="{'background-image': 'url(' + $api.getImageUrl(card.cardtype.imagekey, 100) + ')' }">
                    </div>
                    <div class="z-card-content">
                      <strong>{{card.cardtype_name}} </strong><br>

                      <div v-if="$booking.getActiveFreeze(card, $store.state.now30s.clone())">
                        <span class="error--text">Kortet är fryst till {{Date.formatFullShort($booking.getActiveFreeze(card, $store.state.now30s.clone()).toDate) + ' ' + Date.newFull($booking.getActiveFreeze(card, $store.state.now30s.clone()).toDate).getFullYear()}}</span>
                      </div>

                      <div v-if="card.user_id != $store.state.user.id" class="d-flex">
                        <user-avatar :user="$store.state.user.canManage.find(x => x.id == card.user_id)" :size="32" />
                        <div class="ml-2">Kortet tillhör {{$store.state.user.canManage.find(x => x.id == card.user_id).name}}</div>
                      </div>

                      <div v-if="card.trainingsLeft">
                        <v-icon small>mdi-ticket</v-icon> {{card.trainingsLeft}} {{$translate('trainings left')}}
                      </div>

                      <div v-if="card.validFromDate && Date.newFull(card.validFromDate).isFutureDate()">
                          <v-icon small>mdi-calendar-clock</v-icon>
                          <span> Giltigt från {{Date.formatFullShort(card.validFromDate) + ' ' + Date.newFull(card.validFromDate).getFullYear()}}</span>
                      </div>

                      <div v-if="card.validToDate">
                        <v-icon small>mdi-calendar-clock</v-icon>
                        <span> Giltigt till och med {{Date.formatFullShort(card.validToDate) + ' ' + Date.newFull(card.validToDate).getFullYear()}}</span>
                      </div>
                      <div v-else>
                        <v-icon small>mdi-update</v-icon>
                        <span> Löpande, förlängs automatiskt</span>
                      </div>

                      <div v-if="card.boundToDate && Date.newFull(card.boundToDate).isFuture()">
                        <v-icon small>mdi-calendar-clock</v-icon>
                        <span> Bundet till och med {{Date.formatFullShort(card.boundToDate) + ' ' + Date.newFull(card.boundToDate).getFullYear()}}</span>
                      </div>
                    </div>
                    <div class="z-card-action pt-2 px-2">
                      <v-btn block class="primary my-2" @click="showingCard = card">Info</v-btn>
                    </div>
                  </div>

                </v-expansion-panel-content>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-col>
        </v-row>

      </v-tab-item>
      <v-tab-item v-if="tabs.find(x => x.id == 'family')">
        <family/>
      </v-tab-item>
      <v-tab-item v-if="tabs.find(x => x.id == 'paymentmethods')">
        <my-payment-methods />
      </v-tab-item>
      <v-tab-item v-if="tabs.find(x => x.id == 'account')">
        <v-row>
          <v-col cols="12" md="6" lg="7"><my-account/></v-col>
          <!-- <v-col md="6" lg="5">
            <v-card class="pa-4">
              <h3>Anpassa startsidan</h3>
              <p>Visa anpassaren här</p>
            </v-card>
          </v-col> -->
        </v-row>
      </v-tab-item>
    </v-tabs-items>

    <workout-dialog v-model="showWorkoutDialog" :workout="showingWorkout" v-if="showWorkoutDialog" />
    <resource-booking-dialog v-model="showResourceBookingDialog" :booking="showingResourceBooking" v-if="showResourceBookingDialog" />
    <course-booking-dialog v-model="showCourseBookingDialog" :booking="showingCourseBooking" v-if="showCourseBookingDialog" />
    <training-card-dialog v-model="showTrainingCardDialog" :card="showingCard" v-if="showTrainingCardDialog" />

    <v-dialog
        v-model="showHistoricalActivitiesDialog"
        max-width="800"
        scrollable
    >
      <v-card>
          <v-card-title class="headline pa-2 primary primarytext--text d-flex fill-width">
              Tidigare aktiviteter
              <v-spacer />
              <v-btn icon @click="showHistoricalActivitiesDialog = false" ><v-icon class="primary primarytext--text">mdi-close</v-icon></v-btn>
          </v-card-title>
          <v-card-text>
              <historical-bookings :from-date="historyFrom" :to-date="Date.today().addDays(-1)" />
          </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import MyAccount from "./MyAccount.vue";
import CourseBookingDialog from '../components/CourseBookingDialog.vue'
import WorkoutDialog from '../components/WorkoutDialog.vue'
import ResourceBookingDialog from '../components/ResourceBookingDialog.vue'
import ReceiptList from '../views/ReceiptList.vue'
import ComingPayments from '../views/ComingPayments.vue'
import WorkoutBookButton from '../components/WorkoutBookButton.vue'
import TrainingCardDialog from '../components/TrainingCardDialog.vue'
import WorkoutBookUserRow from '../components/WorkoutBookUserRow.vue'
import MyPaymentMethods from '../views/MyPaymentMethods.vue'
import Family from './Family.vue'
import UserAvatar from '../components/UserAvatar.vue'
import HistoricalBookings from '../views/HistoricalBookings.vue'
import MyEntryStats from '../views/MyEntryStats.vue'
import MyWorkoutStats from '../views/MyWorkoutStats.vue'

export default {
  name: "zoezi-mypage",

  zoezi: {
    title: "Min sida",
    icon: "mdi-account-box-outline",
  },

  components: {
    MyAccount,
    CourseBookingDialog,
    WorkoutDialog,
    ResourceBookingDialog,
    ReceiptList,
    ComingPayments,
    WorkoutBookButton,
    TrainingCardDialog,
    WorkoutBookUserRow,
    MyPaymentMethods,
    Family,
    UserAvatar,
    HistoricalBookings,
    MyEntryStats,
    MyWorkoutStats,
  },

  props: {
    showHistoricActivities: {
      title: 'Visa tidigare aktiviteter',
      type: Boolean,
      default: true
    },
    historyMonths: {
      title: 'Antal månader gamla aktiviteter',
      type: Number,
      default: 12
    },
    displayTrainingOverView: {
      title: 'Visa träningsöversikt',
      type: Boolean,
      default: true
    }
  },
  watch: {
    '$store.state.user'(user) {
      if (user) {
        if (this.$route.query.accountrequest) {
          this.selectedTab = this.tabs.findIndex(x => x.id == 'family');
        } else if (this.$route.query.showinvoice) {
          this.selectedTab = this.tabs.findIndex(x => x.id == 'payments');
        }
      }
    },
    '$store.state.cards'(cards) {
      if (this.showingCard) {
        this.showingCard = cards.find(x => x.id == this.showingCard.id);
        if (!this.showingCard) {
          this.showTrainingCardDialog = false;
        }
      }
    },
    showHistoricActivities: {
      immediate: true,
      handler() {
        this.getHistoricalActivitiesCount();
      }
    },
    historyMonths: {
      immediate: true,
      handler() {
        this.getHistoricalActivitiesCount();
      }
    }

  },
  computed: {
    numberOfBlockedManagedAccounts(){ // FIXME: Why do we have this?
      return this.$store.state.user.canManage.filter(x => x.warnedUntil !=null ).length || 0;
    },
    bookings() {
      return this.$store.getters.comingBookings;
    },
    courseBookings() {
      return this.bookings?.coursebookings?.concat().sort((a,b) => Date.newFull(a.startTime).getTime() - Date.newFull(b.startTime).getTime());
    },
    ongoingCourses() {
      return this.courseBookings?.filter(b => this.$store.state.now30s.withinRange(Date.newFull(b.startTime), Date.newFull(b.endTime)));
    },
    comingCourses() {
      return this.courseBookings?.filter(b => Date.newFull(b.startTime).isFutureDate(true)).sort((a,b) => Date.newFull(a.startTime).getTime() - Date.newFull(b.startTime).getTime());
    },
    courseWatches() {
      return this.bookings?.coursewatches?.concat().sort((a,b) => Date.newFull(a.startTime).getTime() - Date.newFull(b.startTime).getTime());
    },
    workoutBookingsAndResourceBookings() {
      let res = [];
      if (this.bookings) {
          this.bookings.workouts.forEach(wb => {
              if (res.find(x => x.key ==  'wb' + wb.id)) {
                return;
              }

              res.push({
                key: 'wb' + wb.id,
                type: 'workout',
                id: wb.id,
                start: Date.newFull(wb.startTime),
                color: wb.workoutType.color,
                text: wb.workoutType.name,
                imagekey: wb.workoutType.imagekey,
                duration: (Date.newFull(wb.endTime).getTime() - Date.newFull(wb.startTime).getTime()) / (60 * 1000),
                staffs: wb.staffs,
                location: wb.location,
                room: wb.room,
                workout: wb,
                background: wb.status == 'Cancelled' ? '#fbeeed' : (wb.isInQueue() ? '#fed' : null)
              });
          })

          this.bookings.resourcebookings.forEach(rb => {
                res.push({
                  key: 'rb' + rb.id,
                  type: 'resourcebooking',
                  id: rb.id,
                  rb,
                  start: Date.newFull(rb.time),
                  text: rb.servicename,
                  imagekey: rb.service_imagekey,
                  duration: rb.duration,
                  staffs: [{id: rb.staff_id, name: rb.staffname, imagekey: rb.staff_imagekey}]
                });
          });
      }
      return res;
    },
    activities() {
      return this.workoutBookingsAndResourceBookings.concat().sort((a,b) => a.start.getTime() - b.start.getTime());
    },
    courses() {
      return [
          {id: 'ongoing', title: 'Pågående', subtitle: 'kurser du deltar i', bookings: this.ongoingCourses },
          {id: 'coming', title: 'Kommande', subtitle: 'kurser du är inbokad på', bookings: this.comingCourses }
      ].filter(c => c.bookings?.length);
    },
    hasMembership() {
      return this.$store.state?.settings?.membership;
    },
    cardsAndMemberships() {
      let canManage = (card) => card.user_id == this.$store.state.user.id || !!this.$store.state.user.canManage.find(x => x.id == card.user_id);
      let now = this.$store.state.now30s.clone().clearTime();
      let isHistoric = (card) => !this.$booking.isCardValid(card, now, 1, false) && card.validToDate && card.validToDate.isPastDate();
      return this.$store.state.cards?.filter(card => canManage(card) && !isHistoric(card))
    },
    validAndFrozenTrainingCards() {
      return this.cardsAndMemberships?.filter(c => !c.membership);
    },
    validMemberships() {
      return this.cardsAndMemberships?.filter(c => c.membership);
    },
    tabs() {
      if (!this.$store.state.user) {
        return [];
      }
      let bookings = this.$store.state.bookings;
      let showCourses = bookings?.coursebookings?.length > 0 || bookings?.coursewatches?.length > 0;
      let cardsTitle = this.hasMembership && !this.$vuetify.breakpoint.mobile ? `${this.$translate('Training card')} &\n ${this.$translate('Membership')}` : this.$translate('Träningskort');
      if (cardsTitle == `${this.$translate('Training card')} & ${this.$translate('Membership')}`) {
        cardsTitle = `${this.$translate('Training card')} &\n ${this.$translate('Membership')}`;
      }
      
      return [
         { id: 'start', title: 'Översikt', icon: 'mdi-calendar-today'},
         { id: 'payments', title: 'Betalningar', icon: 'mdi-wallet', badge: this.numComingPayments},
         showCourses && { id: 'courses', title: 'Kurser', icon: 'mdi-school'},
         { id: 'cards', title: cardsTitle, icon: 'mdi-ticket'},
         { id: 'family', title: 'Familj', icon: 'mdi-account-multiple', badge: this.$store.state.user.requests.length + this.numberOfBlockedManagedAccounts},
         { id: 'account', title: 'Konto', icon: ' mdi-account-circle'}
       ].filter(x => !!x)
    },
    watching() {
      return [{id: 'watching', title: 'Bevakningar', subtitle: 'där du väntar på en plats', bookings: this.courseWatches },
      ].filter(c => c.bookings?.length);
    },
    sections() {
      let today = this.$store.state.now30s.clone().clearTime();
      let tomorrow = today.clone().addDays(1);

      let activitiesToday = this.activities.filter(a => Date.dateEquals(a.start, today));
      let activitiesTomorrow = this.activities.filter(a => Date.dateEquals(a.start, tomorrow));
      let activitiesLater = this.activities.filter(a => a.start.clone().clearTime().getTime() > tomorrow);
      let activitiesEarlier = [];
      if (this.historicalActivitiesCount) {
        activitiesEarlier = Array.apply(null, Array(this.historicalActivitiesCount)).map(() => ({id: 0}));
      }

      return [
          {id: 'today', title: 'Idag', subtitle: this.getDateSubTitle(today), bookings: activitiesToday},
          {id: 'tomorrow', title: 'Imorgon', subtitle: this.getDateSubTitle(tomorrow), bookings: activitiesTomorrow },
          {id: 'later', title: 'Senare', subtitle: 'bokningar efter imorgon', bookings: activitiesLater},
          {id: 'historic', title: 'Tidigare aktiviteter', subtitle: `${activitiesEarlier.length} tidigare aktivitet${activitiesEarlier.length == 1 ? '' : 'er'}`, bookings: activitiesEarlier, singleCard: true }
      ].filter(c => c.bookings?.length);
    },
    historyFrom() {
      return Date.today().addMonths(-this.historyMonths).yyyymmdd();
    },
    messageCards() {
      const blocktypes = [
        {id: 'block_entry', name: 'Entry'},
        {id: 'block_autogiro', name: 'Sign direct debit'},
        {id: 'block_grouptraining', name: 'Group workout'},
        {id: 'block_course', name: 'Course booking'},
        {id: 'block_resourcebooking', name: 'Resource booking'}
      ];

      let blocks = this.$store.state.user.blocks;
      return blocks.map(block => {
        let blocklist = blocktypes.filter(t => block[t.id]).map(t => this.$translate(t.name).toLowerCase()).join(', ')
        let until = block.toDate ? (this.$translate('until') + ' <b>' + Date.formatFullShorter(block.toDate) + '.</b>') : ' ' + this.$translate('until furhter notice');
        let message = block.message ? (`<br><br>${block.message}<br><br>`) : '<br>';

        return {
          id: 'block.' + block.id,
          color: '#fcb2b2',
          title: 'Blocked',
          text: this.$translate('You have been blocked from {0}{1}The block is valid {2}').format(blocklist, message, until)
        };
      });
    }
  },
  data: () => ({
    selectedTab: "start",
    showWorkoutDialog: false,
    showingWorkout: null,
    showResourceBookingDialog: false,
    showingResourceBooking: null,
    showCourseBookingDialog: false,
    showingCourseBooking: null,
    numComingPayments: null,
    showTrainingCardDialog: false,
    showingCard: null,
    expandedCardPanels: [0,1],
    expandedPaymentMethodsPanel: 0,
    historicalActivitiesCount: null,
    showHistoricalActivitiesDialog: false,
  }),
  
  methods: {
    getChildName(user_id) {
      let canBookFor = this.$store.state?.user?.canBookFor;
      if (canBookFor && this.$store.state.user.id != user_id) {
        let user = canBookFor.find(u => u.id == user_id);
        return user ? user.name : null;
      }
    },
    showCourseBooking(booking) {
      this.showingCourseBooking = booking
      this.showCourseBookingDialog = true;
    },
    getDateSubTitle(date) {
      date = Date.newFull(date);

      let weekday = window.$translate(date.getWeekDayString())
      let lc = (x) => window.$store.state.language == 'sv' ? x.toLowerCase() : x;

      return `${lc(weekday)} ${date.getDate()} ${lc(window.$translate(date.getMonthName()))}`;
    },
    showActivity(booking) {
      if (booking.type == 'workout') {
          this.$api.get('/api/memberapi/workout/get', {id: booking.id}).then(x => {
              this.$booking.transformWorkout(x);
              this.showWorkoutDialog = true;
              this.showingWorkout = x;
          }).catch(() => {
              this.$store.commit('showErrorDialog', {title: 'Fel vid visning av bokning', text: 'Det gick inte att visa bokningen'})
          })
      } else if (booking.type == 'resourcebooking') {
          this.showingResourceBooking = booking.rb;
          this.showResourceBookingDialog = true;
      }
    },
    getBookingColorStyle(booking) {
      return {
        'background-color': booking.color ? (booking.color+'b4') : 'rgba(192,160,0,0.7)'
      }
    },
    getHistoricalActivitiesCount() {
      this.historicalActivitiesCount = null;
      if (this.showHistoricActivities) {
        let startDate = this.historyFrom;
        let endDate = Date.today().addDays(-1).yyyymmdd();
        this.$api.get('/api/memberapi/bookings/get', {startTime: startDate, endTime: endDate, returnCount: true}).then(x => {
          this.historicalActivitiesCount = x;
        })
      }
    }
  }
};
</script>
