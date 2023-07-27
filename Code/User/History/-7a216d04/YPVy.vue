<template>
    <Button :disabled="isFavouriteable" :icon="isFavourite ? 'pi pi-star-fill' : 'pi pi-star'" :severity="isFavourite ? 'primary' : 'secondary'" rounded aria-label="Favourite" @click="setFavourite" />
</template>

<script>
import { useMainStore } from '../service/StoreService'
import Button from 'primevue/button';
import { ref } from 'vue'
export default {
    components: {
        Button
    },
    data() {
      return {
        staff: [],
        customer: [],
        whitelist: [ // Disable button on routes not in whitelist.
          "test_url"
        ]
      }
    },
    mounted() {
      this.getData();
    },
    computed: {
        isFavourite() {
            return useMainStore().isFavourite(this.$route.path);
        },
        isFavouriteable() {
            console.log(this.$route.path)
            return false;
        }
    },
    methods: {
        setFavourite() {
            let favourite = !this.isFavourite;
            let route = this.$route.path;
            useMainStore().setFavourite({name: route, label: this.getLabel(route)}, favourite);
        },
        getData() {
            let fields = ['id', 'name'];
            this.$api.get('/api/staff/get', {inactive:true, compact:true, fields:fields}).then(data => {
                this.staff = data;
            });

            this.$api.get('/api/member/get/full').then(data => {
                this.customer = data;
            });
        },
        getLabel(path) {
          let parts = path.split('/')
          let id = parseInt(parts[parts.length - 1]);

          if (path.includes('/staff/show')) {
            const foundStaff = this.staff.find(staff => staff.id === id);
            if (foundStaff) { return foundStaff.name }
          }

          else if (path.includes('/customer/show')) {
            const foundCustomer = this.customer.find(customer => customer.id === id);
            if (foundCustomer) { return `${foundCustomer.firstname} ${foundCustomer.lastname}` }
          }

          return null;
        }
    }
}

</script>
