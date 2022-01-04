import DiffMatchPatch from "diff-match-patch";

export const showResponseData = (data = {}) => {
    if (!data || !Object.keys(data).length) {
        return ''
    }
    let result = [data.http_version + " " + data.status_code + " " + data.reason];
    for (let k in data.headers) {
        result.push(k + " : " + data.headers[k]);
    }
    result.push("");
    result.push(data.content);
    return result.join("\r\n");
}

export const showRequestData = (data = {}) => {
    if (!data || !Object.keys(data).length) {
        return ''
    }
    let result = [data.method + " " + data.path + " " + data.http_version, "Host: " + data.host];
    for (let k in data.headers) {
        if (k === "Host") {
            continue;
        }
        result.push(k + ": " + data.headers[k]);
    }
    result.push("");
    result.push(data.content);
    return result.join("\r\n");
}

export const makeAuthID = (count = 24) => {
    let result = [];
    let characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let charactersLength = characters.length;
    for (let i = 0; i < count; i++) {
        result.push(characters.charAt(Math.floor(Math.random() * charactersLength)));
    }
    return result.join('');
}

export const getEncodeVar = (encode_str = '', delimiters = '§', full_line = false) => {
    if (encode_str.length < 1) {
        throw '字符串不允许为空'
    }
    let vars = []
    let line = []
    let tmpIdx = -1
    for (let idx = 0; idx < encode_str.length; idx++) {
        if (encode_str[idx] === delimiters) {
            if (tmpIdx > -1) {
                vars.push(`${encode_str.slice(tmpIdx, idx)}${delimiters}`)
                tmpIdx = -1
            } else {
                tmpIdx = idx
            }
        } else if (full_line && tmpIdx === -1) {
            if (encode_str[idx] === '\n') {
                vars.push(line.join('').trim())
                line = []
            } else {
                line.push(encode_str[idx])
            }
        }
    }
    if (full_line && line.join('').trim().length) {
        vars.push(line.join(''))
    }
    if (tmpIdx !== -1) {
        console.warn('字符串存在不闭合标识')
    }
    return vars
}

export const diff_prettyHtml = function (diffs) {
    var html = [];
    var pattern_amp = /&/g;
    var pattern_lt = /</g;
    var pattern_gt = />/g;
    var pattern_para = /\n/g;
    for (var x = 0; x < diffs.length; x++) {
        var op = diffs[x][0];
        var data = diffs[x][1];
        var text = data.replace(pattern_amp, '&amp;').replace(pattern_lt, '&lt;')
            .replace(pattern_gt, '&gt;').replace(pattern_para, '&para;<br>');
        switch (op) {
            case DiffMatchPatch.DIFF_INSERT:
                html[x] = '<ins style="background:#e6ffe6;">' + text + '</ins>';
                break;
            case DiffMatchPatch.DIFF_DELETE:
                html[x] = '<del style="background:#ffe6e6;">' + text + '</del>';
                break;
            case DiffMatchPatch.DIFF_EQUAL:
                html[x] = '<span>' + text + '</span>';
                break;
        }
    }
    return html.join('');
};

export const evalRange = (range_str = '') => {
    if (!range_str.trim().startsWith('range:')) {
        return range_str
    }
    let line = range_str.trim()
    line = line.replace('range:', '')
    if (!line.includes(':') && !line.includes(',')) {
        return range_str
    }
    let delimiters = ','
    if (line.includes(':')) {
        delimiters = ':'
    }
    let range = line.split(delimiters, 3)
    if (range.length < 2 || !range[1]) {
        return range_str
    }
    let start = range[0] ? parseInt(range[0]) ? parseInt(range[0]) : range[0].charCodeAt() : 0,
        stop = range[1] ? parseInt(range[1]) ? parseInt(range[1]) : range[1].charCodeAt() : 0,
        step = range.length > 2 ? parseInt(range[2]) ? parseInt(range[2]) : range[2].charCodeAt() : 1,
        isAscii = parseInt(range[0]).toString() == 'NaN' || parseInt(range[1]).toString() == 'NaN'

    let res = []
    for (; start < stop;) {
        res.push(isAscii ? String.fromCharCode(start) : start)
        start += step
    }
    return res.join('\n')
}

