import Vue from 'vue'
import VueRouter from 'vue-router';
import App from './App.vue';
import Routers from './router.js';
import ViewUI from 'view-design';
import 'view-design/dist/styles/iview.css';

Vue.config.productionTip = false

Vue.use(VueRouter);
Vue.use(ViewUI);

const RouterConfig = {
    routes: Routers
};
const router = new VueRouter(RouterConfig);

new Vue({
    el: '#app',
    router: router,
    render: h => h(App)
});

router.beforeEach((to, from, next) => {
    if (from && from.name === 'logger') {
        let query = ''
        if (to.name === 'intercept') {
            let logger = localStorage.getItem('loggerPage')
            if (logger) {
                logger = JSON.parse(logger)
                if (logger.ip && logger.ip.length > 0) {
                    query = `?ip=${logger.ip}`
                }
            }
        }
        window.open(`/#${to.fullPath}${query}`, '_blank')
        return
    }
    if (!to.name) {
        next({
            name: 'logger'
        })
    } else {
        document.title = "MLOGER - " + (to.meta.title || to.name);
        next()
    }
})