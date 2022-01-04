import Intercept from './components/Intercept/Index'
import Logger from './components/Logger/Index'
import Repeater from './components/Repeater/Index'
import IMWS from './components/Imws/Index'
import SearchHistory from './components/History/Index'
import Manual from './components/Manual/Index'


export default [
    {
        name: 'index',
        path: '/',
        title: 'MLOGER',
        redirect: {name: 'logger'},
        isTheme: true
    },
    {
        path: '/intercept',
        name: 'intercept',
        title: 'HTTP拦截',
        component: Intercept
    },
    {
        path: '/logger',
        name: 'logger',
        title: 'HTTP记录',
        component: Logger
    },
    {
        path: '/repeater',
        name: 'repeater',
        title: 'HTTP重放',
        component: Repeater
    },
    {
        path: '/imws',
        name: 'imws',
        title: 'TCP/WS测试',
        component: IMWS
    },
    {
        path: '/history',
        name: 'history',
        title: '历史记录',
        component: SearchHistory
    },
    {
        path: '/manual',
        name: 'manual',
        title: '使用手册',
        component: Manual
    }

]
