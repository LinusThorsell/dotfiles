<template>
    <Button :disabled="isFavouriteable" :icon="isFavourite ? 'pi pi-star-fill' : 'pi pi-star'" :severity="isFavourite ? 'primary' : 'secondary'" rounded aria-label="Favourite" @click="setFavourite" />
</template>

<script>
import { inject } from 'vue'
import FavouriteButton from './FavouriteButton.vue';

export default {
  components: {
    FavouriteButton
  },
  setup() {
    const mainStore = inject('mainStore')

    // If data fetching needs to be in this component
    const { staff, customer } = mainStore.fetchData(['id', 'name'])

    const isFavourite = mainStore.isFavourite(this.$route.path)

    const isFavouriteable = computed(() => {
      const whitelist = [
        {
          url: "/staff/list",
          exact: true,
        },
        {
          url: "/staff/show/",
          exact: false,
        }
      ]

      let isOnWhiteList = false;
      whitelist.forEach(url => {
        if (url.exact && url.url === this.$route.path) {
          isOnWhiteList = true;
        } else if (this.$route.path.includes(url.url)) {
          isOnWhiteList = true;
        }
      });
    
      return !isOnWhiteList
    })

    const setFavourite = () => {
      const favourite = !isFavourite.value
      const route = this.$route.path
      const label = getLabel(route)
      mainStore.setFavourite({name: route, label}, favourite)
    }

    const getLabel = (path) => {
      let parts = path.split('/')
      let id = parseInt(parts[parts.length - 1]);

      if (path.includes('/staff/show')) {
        const foundStaff = staff.find(staff => staff.id === id);
        if (foundStaff) { return foundStaff.name }
      }

      else if (path.includes('/customer/show')) {
        const foundCustomer = customer.find(customer => customer.id === id);
        if (foundCustomer) { return `${foundCustomer.firstname} ${foundCustomer.lastname}` }
      }

      return null;
    }

    return {
      isFavourite,
      isFavouriteable,
      setFavourite
    }
  }
}

</script>
