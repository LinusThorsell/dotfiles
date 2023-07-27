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
        <div class="card shadow-2">
            <DataTable v-model:filters="filters" v-model:selection="selected" :value="shownStaff" sortMode="multiple" removableSort stripedRows tableStyle="min-width: 50rem" @row-click="rowClick" @click="tableClick" ref="datatable">
                <template #header>
                    <div class="flex flex-wrap align-items-center justify-content-between gap-2">
                    <span class="text-xl text-900 font-bold">{{ translate("Manage Staff") }}</span>
                    <div>
                        <InputText v-model="filters['global'].value" :placeholder="translate('Search')" />
                        <!-- <Button v-tooltip.bottom="'Click to proceed'" icon="pi pi-refresh" severity="primary" outlined rounded  class="m-1" @click="resetSorting()"/> -->
                        <Button v-if="showInactive" v-tooltip.bottom="$t('Activate')" icon="pi pi-plus" severity="primary" :disabled="selected.length <= 0" outlined rounded class="m-1" @click="activateDialog = !activateDialog"/>
                        <Button v-else v-tooltip.bottom="$t('Add new')" icon="pi pi-plus" severity="primary" outlined rounded class="m-1" @click="navigateToAdd()"/>
                        <!-- <Button v-if="!showInactive" v-tooltip.bottom="$t('Inactivate')" icon="pi pi-trash" severity="danger" :disabled="selected.length <= 0" outlined rounded class="m-1" @click="confirmDialog = !confirmDialog"/> -->
                    </div>
                    </div>
                </template>
                <Column selectionMode="multiple" header=""></Column>
                <Column header="">
                    <template #body="prop">
                    <Avatar :image="getImage(prop.data)" class="shadow-2 mr-2" size="xlarge" shape="circle"/>
                    </template>
                </Column>
                <Column sortable field="name" :header="translate('Name')" style="border-radius:0">
                </Column>
                <Column sortable field="phone" :header="translate('Phone number')" style="border-radius:0">
                </Column>
                <Column sortable field="mail" :header="translate('Mail')" style="border-radius:0">
                </Column>
                <!-- TODO: FIX FILTER -->
                <Column :header="translate('Roles')">
                    <template #body="prop">
                    <div>
                        <Tag v-for="r in prop.data.roles" :value="translate(r.name)" rounded class="m-1"/>
                    </div>
                    </template>
                </Column>
                <template #footer> Totalt {{ shownStaff ? shownStaff.length : 0 }} anställda. </template>
            </DataTable>
        </div>
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