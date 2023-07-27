<template>
    <main>
        <h1>Hello World</h1>
        <DateRangePicker />
    </main>
</template>

<script>
import DateRangePicker from '../components/DateRangePicker.vue'

export default {
  components: {
    DateRangePicker
  },
  data: () => ({
    salesData: null,
    options: [
      { name: 'Day', value: 'day' },
      { name: 'Week', value: 'week' },
      { name: 'Month', value: 'month' },
    ],
    dateRangeInterface: null,
    today: new Date(),
    minDate: new Date(2019, 10, 1),
    dates: [null, null],
    selectedSites: [],
    sites: null
  }),
  computed: {
    dateRangeMode() {
      return this.dateRangeInterface?.mode;
    },
  },
  methods: {
    dateChanged(dates) {
      this.dates = dates;
      this.fetchSales();
    },
    modeUpdated(mode) {
    },
    changeMode(value) {
      this.dateRangeInterface.setMode(value.value)
    },
    setDateRangeInterface(inputInterface) {
      this.dateRangeInterface = inputInterface;
    },
    fetchSales() {
      if (this.dates.every(d => d instanceof Date)) {
        this.$api.get('/api/payment/stats/get', { from_date: this.dates[0].yyyymmdd(), to_date: this.dates[1].yyyymmdd(), sites: this.selectedSites && this.selectedSites.map(item => item.id).join(',') }).then((response) => {
          this.salesData = response;
        });
      }
    }
  },
  created() {
    this.preSelection = this.options.find(option => option.value === 'month');
    this.$api.get('/api/site/get/all').then((response) => {
      this.sites = response;
    });
    this.fetchSales();
  },
}
</script>