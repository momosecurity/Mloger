const axios = require('axios').default;

export const getConnIp = () => {
    return axios.post('/api/get_client_ip')
}

export const setConnIp = (ip) => {
    return axios.post('/api/set_client_ip_allowed', {ip: ip})
}

export const releaseConnIp = (ip) => {
    return axios.post('/api/cancel_client_ip_allowed', {ip: ip})
}

export const getInterceptData = (query = {}, method = 'get') => {
    if (method === 'get') {
        return axios.get('/api/intercept')
    }
    return axios.post('/api/intercept', query)
}

export const getInterceptOptData = (query = {}) => {
    return axios.post('/api/intercept_op', query)
}

export const postEditLogerDesc = (payload = {id: '', describe: ''}) => {
    let data = {}
    for (let k of ['id', 'describe']) {
        if (payload[k]) {
            data[k] = payload[k]
        } else {
            throw "缺少参数:" + k
        }
    }
    return axios.post('/api/edit_req_describe', payload)
}

export const postRepeaterShareAuthID = (id, authId) => {
    let payload = {"id": id, "auth_code": authId}
    return axios.post('/api/repeater_share', payload)
}

export const getRepeaterGoData = (query) => {
    return axios.post('/api/repeater_go', query)
}

export const getRepeaterHistoryData = (query) => {
    return axios.post('/api/repeater_history', query)
}

export const getRepeaterGetData = (query) => {
    return axios.get('/api/repeater_get', {params: query})
}

export const imwsRepeaterGo = (
    conn_id = '',
    flow_content = '',
    hex_content = '',
    direction = '',
    process_cnt = 0
) => {
    let payload = {
        conn_id: conn_id,
        flow_content: flow_content,
        hex_content: hex_content,
        direction: direction,
        concurrent_num: process_cnt
    }
    if (conn_id && flow_content && (direction === 'send' || direction === 'receive')) {
        return axios.post('/api/imws_repeater_go', payload)
    }
    console.error(payload)
    throw '参数错误，请求失败'
}

export const interceptOpImws = (
    id = '',
    conn_id = '',
    type = '',
    flow_content = ''
) => {
    let payload = {
        id: id,
        conn_id: conn_id,
        flow_content: flow_content,
    }
    if (id && conn_id && type) {
        if (type === 'forward') {
            payload.forward = true
            payload.drop = false
        } else {
            payload.forward = false
            payload.drop = true
        }
        return axios.post('/api/intercept_op_imws', payload)
    }
    console.error(payload)
    throw '参数错误，请求失败'
}

export const interceptImws = (
    conn_id = '',
    status = ''
) => {
    let payload = {
        conn_id: conn_id, status: status
    }
    if (conn_id && (status === 'on' || status === 'off')) {
        return axios.post('/api/intercept_imws', payload)
    }
    console.error(payload)
    throw '拦截参数错误，请求失败'
}

export const getSearchHistoryData = (query = {
    keyword: '',
    type: 'all',
    page: 1,
    size: 20
}) => {
    if (!query.type) {
        query.type = 'all'
    }
    return axios.post('/api/search', query)
}