<template>
    <main>
        <div class="grid-nogutter flex flex-wrap sm:flex-wrap mb-3">
            <SelectButton class="w-full col-12 md:col-fixed md:w-max grid-nogutter m-1" 
                v-model="dateRangeMode"
                :options="options"
                optionValue="value"
                :unselectable="false"
                @change="changeMode">
                <template #option="slotProps">
                <div class="text-center p-2">
                    <div>{{ $t(slotProps.option.name) }}</div>
                </div>
                </template>
            </SelectButton>
            <date-range-picker class="col-12 md:col-fixed md:w-max m-1"
                @interface="setDateRangeInterface"
                @change="dateChanged"
                @mode="modeUpdated"
                :maxDate="today"
                :minDate="minDate" />
            <div class="col-12 md:col-fixed md:w-max m-1">
                <MultiSelect v-model="selectedSites" :options="sites" filter optionLabel="name" :placeholder="$t('All sites')" class="p-2 w-full md:w-20rem" />
            </div>
        </div>

        <!-- List Activities -->
        <h1>List of activiies</h1>
    </main>
</template>

<script>
import DateRangePicker from '../components/DateRangePicker.vue'
import MultiSelect from 'primevue/multiselect';
import SelectButton from 'primevue/selectbutton';

export default {
  components: {
    DateRangePicker,
    MultiSelect,
    SelectButton
  },
  data: () => ({
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
    },
    modeUpdated(mode) {
    },
    changeMode(value) {
      this.dateRangeInterface.setMode(value.value)
    },
    setDateRangeInterface(inputInterface) {
      this.dateRangeInterface = inputInterface;
    },
  },
  created() {
    this.preSelection = this.options.find(option => option.value === 'month');
    // this.$api.get('/api/site/get/all').then((response) => {
    //   this.sites = response;
    // });
  },
}
</script>