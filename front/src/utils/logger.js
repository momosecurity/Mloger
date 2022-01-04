export const isReflashLogger = (data) => {
    if (!data || data.length < 1 || !data.request || !data.request._id) {
        return false
    }

    if (data.checkCnt && data.checkCnt > 3) {
        return false
    }

    if (data.request.content && data.request.content.indexOf('mzip=') === 0) {
        return true
    }

    if (data.response && Object.keys(data.response).includes('content') && data.response.content.indexOf('{') !== 0) {
        return true
    }
}

export const timestampToString = (timestamp, fmt = '%Y-%m-%d %H:%M:%S') => {
    function format(s) {
        return ('' + s).length < 2 ? '0' + s : s + ''
    }

    let dt = new Date(timestamp * 1000)
    let dtArray = {
        '%Y': format(dt.getFullYear()),
        '%m': format(dt.getMonth() + 1),
        '%d': format(dt.getDate()),
        '%H': format(dt.getHours()),
        '%M': format(dt.getMinutes()),
        '%S': format(dt.getSeconds())
    }

    let dtString = ''
    for (let idx = 0; idx < fmt.length; idx++) {
        let key = fmt.slice(idx, idx + 2)
        if (dtArray[key]) {
            dtString += dtArray[key]
            idx++
        } else {
            dtString += fmt[idx]
        }
    }
    return dtString
}


export const objectToString = (obj, kv_seq = ':', line_seq = '\n') => {
    if (typeof (obj) === 'string') {
        return obj
    }
    let obj_list = []
    for (let key in obj) {
        let v = typeof (obj[key]) === 'object' ? objectToString(obj[key], kv_seq, line_seq) : obj[key]
        obj_list.push(key + kv_seq + v)
    }
    return obj_list.join(line_seq)
}
